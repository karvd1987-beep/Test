from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.domain.interfaces import AIAnalyzer, LocationRepository, NotificationChannel, ReviewRepository, UserRepository
from app.domain.models import Location, Review, Severity, User


@dataclass(slots=True)
class MonitoringRunResult:
    scanned_locations: int
    new_reviews: int
    alerts_sent: int


def _severity_order(severity: Severity) -> int:
    order = {
        Severity.LOW: 0,
        Severity.MEDIUM: 1,
        Severity.HIGH: 2,
        Severity.CRITICAL: 3,
    }
    return order[severity]


class MonitoringService:
    def __init__(
        self,
        users_repo: UserRepository,
        locations_repo: LocationRepository,
        reviews_repo: ReviewRepository,
        source_adapter: Any,
        analyzer: AIAnalyzer,
        channels: list[NotificationChannel],
    ) -> None:
        self.users_repo = users_repo
        self.locations_repo = locations_repo
        self.reviews_repo = reviews_repo
        self.source_adapter = source_adapter
        self.analyzer = analyzer
        self.channels = channels

    def run_for_user(self, user_id: str) -> MonitoringRunResult:
        user = self.users_repo.get(user_id)
        if not user:
            raise ValueError("Пользователь не найден")

        locations = self.locations_repo.list_for_user(user.id)
        new_reviews_total = 0
        alerts_total = 0

        for location in locations:
            alerts_total += self.run_for_location(user, location)
            new_reviews_total += self._new_reviews_count_for_location(location.id)

        return MonitoringRunResult(
            scanned_locations=len(locations),
            new_reviews=new_reviews_total,
            alerts_sent=alerts_total,
        )

    def run_for_location(self, user: User, location: Location) -> int:
        candidates = self.source_adapter.fetch_reviews(location)
        alerts_sent = 0
        inserted_for_location = 0

        for candidate in candidates:
            if self.reviews_repo.exists(location.id, candidate.external_review_id):
                continue

            analysis = self.analyzer.analyze(candidate)
            review = Review(
                location_id=location.id,
                external_review_id=candidate.external_review_id,
                author=candidate.author,
                rating=candidate.rating,
                text=candidate.text,
                published_at=candidate.published_at,
                severity=analysis.severity,
                sentiment=analysis.sentiment,
                topics=analysis.topics,
                recommendation=analysis.recommendation,
                suggested_reply=analysis.suggested_reply,
                is_new=True,
            )
            self.reviews_repo.save(review)
            inserted_for_location += 1

            if _severity_order(review.severity) >= _severity_order(user.min_alert_severity):
                subject = f"Новый отзыв {review.severity.value} для {location.name}"
                body = (
                    f"Оценка: {review.rating}/5\n"
                    f"Автор: {review.author}\n"
                    f"Текст: {review.text}\n\n"
                    f"Рекомендация: {review.recommendation}\n"
                    f"Черновик ответа: {review.suggested_reply}"
                )
                for channel in self.channels:
                    channel.send(user, subject, body)
                    alerts_sent += 1

        location.last_checked_at = datetime.utcnow()
        self.locations_repo.save(location)
        return alerts_sent

    def _new_reviews_count_for_location(self, location_id: str) -> int:
        reviews = self.reviews_repo.list_for_location(location_id)
        return sum(1 for review in reviews if review.is_new)

from __future__ import annotations

from collections import Counter

from app.domain.models import AccountStatus, Review, TrialReport, User


class ReportingService:
    def build_trial_report(self, user: User, reviews: list[Review]) -> TrialReport:
        severity_counter = Counter(review.severity.value for review in reviews)
        top_issue_candidates = Counter(topic for review in reviews for topic in review.topics)
        key_issues = [topic for topic, _ in top_issue_candidates.most_common(5)]

        if not reviews:
            summary = "За период trial новых отзывов не обнаружено."
        elif severity_counter.get("critical", 0) + severity_counter.get("high", 0) > 0:
            summary = "Обнаружены высоко-критичные отзывы — нужен быстрый контроль качества сервиса."
        else:
            summary = "Тональность отзывов стабильна, критичных инцидентов минимум."

        cta = (
            "Оформите подписку, чтобы продолжить мониторинг без остановки и подключить до 5 точек."
            if user.account_status != AccountStatus.ACTIVE
            else "Подписка активна — добавляйте новые точки и масштабируйте мониторинг."
        )

        return TrialReport(
            user_id=user.id,
            total_reviews=len(reviews),
            severity_breakdown=dict(severity_counter),
            key_issues=key_issues,
            summary=summary,
            payment_cta=cta,
        )

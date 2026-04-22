from __future__ import annotations

from typing import Protocol

from app.domain.models import AIAnalysis, Location, Review, ReviewCandidate, User


class ReviewSourceAdapter(Protocol):
    """Платформенный адаптер: Яндекс сейчас, другие позже."""

    source_name: str

    def fetch_reviews(self, location: Location) -> list[ReviewCandidate]:
        ...


class AIAnalyzer(Protocol):
    """Обособленный AI-модуль анализа."""

    def analyze(self, candidate: ReviewCandidate) -> AIAnalysis:
        ...

    def summarize_demo(self, source_url: str, candidates: list[ReviewCandidate]):
        ...


class NotificationChannel(Protocol):
    """Изолированный канал доставки уведомлений."""

    name: str

    def send(self, user: User, subject: str, body: str) -> None:
        ...


class UserRepository(Protocol):
    def save(self, user: User) -> None:
        ...

    def get(self, user_id: str) -> User | None:
        ...

    def get_by_email(self, email: str) -> User | None:
        ...


class SubscriptionRepository(Protocol):
    def save(self, subscription) -> None:
        ...

    def get_by_user(self, user_id: str):
        ...


class LocationRepository(Protocol):
    def save(self, location: Location) -> None:
        ...

    def get(self, location_id: str) -> Location | None:
        ...

    def list_for_user(self, user_id: str) -> list[Location]:
        ...


class ReviewRepository(Protocol):
    def save(self, review: Review) -> None:
        ...

    def exists(self, location_id: str, external_review_id: str) -> bool:
        ...

    def list_for_location(self, location_id: str) -> list[Review]:
        ...

    def list_for_user(self, locations: list[Location]) -> list[Review]:
        ...


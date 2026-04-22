from __future__ import annotations

from collections import defaultdict
from typing import DefaultDict

from app.domain.interfaces import (
    LocationRepository,
    NotificationChannel,
    ReviewRepository,
    SubscriptionRepository,
    UserRepository,
)
from app.domain.models import AccountStatus, Location, Review, Subscription, User


class InMemoryUserRepository(UserRepository):
    def __init__(self) -> None:
        self._users: dict[str, User] = {}

    def save(self, user: User) -> None:
        self._users[user.id] = user

    def get(self, user_id: str) -> User | None:
        return self._users.get(user_id)

    def get_by_email(self, email: str) -> User | None:
        normalized = email.strip().lower()
        for user in self._users.values():
            if user.email == normalized:
                return user
        return None


class InMemoryLocationRepository(LocationRepository):
    def __init__(self) -> None:
        self._locations: dict[str, Location] = {}

    def save(self, location: Location) -> None:
        self._locations[location.id] = location

    def list_for_user(self, user_id: str) -> list[Location]:
        return sorted(
            [location for location in self._locations.values() if location.user_id == user_id],
            key=lambda item: item.created_at,
        )

    def get(self, location_id: str) -> Location | None:
        return self._locations.get(location_id)


class InMemorySubscriptionRepository(SubscriptionRepository):
    def __init__(self) -> None:
        self._subscriptions: dict[str, Subscription] = {}

    def save(self, subscription: Subscription) -> None:
        self._subscriptions[subscription.user_id] = subscription

    def get_by_user(self, user_id: str) -> Subscription | None:
        return self._subscriptions.get(user_id)

    def location_limit(self, user_id: str) -> int:
        subscription = self._subscriptions.get(user_id)
        if not subscription:
            return 0
        return subscription.locations_limit()


class InMemoryReviewRepository(ReviewRepository):
    def __init__(self) -> None:
        self._reviews: DefaultDict[str, dict[str, Review]] = defaultdict(dict)

    def save(self, review: Review) -> None:
        self._reviews[review.location_id][review.external_review_id] = review

    def exists(self, location_id: str, external_review_id: str) -> bool:
        return external_review_id in self._reviews.get(location_id, {})

    def list_for_location(self, location_id: str) -> list[Review]:
        return sorted(self._reviews.get(location_id, {}).values(), key=lambda item: item.published_at)

    def list_for_user(self, locations: list[Location]) -> list[Review]:
        merged: list[Review] = []
        for location in locations:
            merged.extend(self.list_for_location(location.id))
        return sorted(merged, key=lambda item: item.published_at)


class PrintNotificationChannel(NotificationChannel):
    def __init__(self, name: str) -> None:
        self.name = name
        self.outbox: list[dict[str, str]] = []

    def send(self, user: User, subject: str, body: str) -> None:
        self.outbox.append(
            {
                "channel": self.name,
                "recipient": user.email,
                "subject": subject,
                "body": body,
            }
        )

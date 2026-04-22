from __future__ import annotations

from dataclasses import dataclass

from app.domain.interfaces import LocationRepository, SubscriptionRepository, UserRepository
from app.domain.models import AccountStatus, Location, Subscription, User


def _validate_yandex_maps_url(source_url: str) -> str:
    url = source_url.strip()
    lower = url.lower()
    if not lower.startswith(("http://", "https://")):
        raise ValueError("Ссылка должна начинаться с http/https.")
    if "yandex." not in lower or "/maps" not in lower:
        raise ValueError("Для MVP поддерживаются только ссылки Яндекс Карт.")
    return url


@dataclass(slots=True)
class OnboardingService:
    user_repo: UserRepository
    subscription_repo: SubscriptionRepository
    location_repo: LocationRepository
    trial_days: int = 7

    def register_user_with_trial(self, email: str, full_name: str, source_url: str) -> User:
        normalized_email = email.strip().lower()
        if not normalized_email:
            raise ValueError("Email обязателен.")
        if not full_name.strip():
            raise ValueError("Имя обязательно.")

        existing = self.user_repo.get_by_email(normalized_email)
        if existing:
            return existing

        user = User(email=normalized_email, full_name=full_name.strip())
        self.user_repo.save(user)
        self.subscription_repo.save(Subscription(user_id=user.id, trial_days=self.trial_days))
        self.add_location(user.id, source_url)
        return user

    def add_location(self, user_id: str, source_url: str) -> Location:
        user = self.user_repo.get(user_id)
        if not user:
            raise ValueError("Пользователь не найден.")
        clean_url = _validate_yandex_maps_url(source_url)
        subscription = self.subscription_repo.get_by_user(user_id)
        if not subscription:
            raise ValueError("Подписка пользователя не найдена.")

        existing = self.location_repo.list_for_user(user_id)
        if len(existing) >= subscription.locations_limit():
            raise ValueError("Достигнут лимит подключенных точек для текущего тарифа.")

        location = Location(
            user_id=user_id,
            source_url=clean_url,
            external_place_id=self._extract_external_place_id(clean_url),
        )
        self.location_repo.save(location)
        return location

    def activate_subscription(self, user_id: str) -> None:
        user = self.user_repo.get(user_id)
        subscription = self.subscription_repo.get_by_user(user_id)
        if not user or not subscription:
            raise ValueError("Пользователь или подписка не найдены.")
        user.account_status = AccountStatus.ACTIVE
        subscription.status = AccountStatus.ACTIVE
        self.user_repo.save(user)
        self.subscription_repo.save(subscription)

    @staticmethod
    def _extract_external_place_id(source_url: str) -> str:
        parts = [part for part in source_url.rstrip("/").split("/") if part]
        return parts[-1] if parts else "unknown"

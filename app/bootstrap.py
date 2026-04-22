from app.config import settings
from app.infrastructure.fake_sources import FakeYandexMapsAdapter
from app.infrastructure.inmemory import (
    InMemoryLocationRepository,
    InMemoryReviewRepository,
    InMemorySubscriptionRepository,
    InMemoryUserRepository,
    PrintNotificationChannel,
)
from app.services.analysis import AnalysisService, SimpleAIAnalyzer
from app.services.monitoring import MonitoringService
from app.services.onboarding import OnboardingService
from app.services.reporting import ReportingService


class Container:
    def __init__(self) -> None:
        self.users_repo = InMemoryUserRepository()
        self.locations_repo = InMemoryLocationRepository()
        self.reviews_repo = InMemoryReviewRepository()
        self.subscriptions_repo = InMemorySubscriptionRepository()

        self.source_adapter = FakeYandexMapsAdapter()
        self.analyzer = SimpleAIAnalyzer()
        self.channels = [
            PrintNotificationChannel("email"),
            PrintNotificationChannel("telegram"),
            PrintNotificationChannel("max"),
        ]

        self.analysis_service = AnalysisService(source_adapter=self.source_adapter, analyzer=self.analyzer)
        self.onboarding_service = OnboardingService(
            user_repo=self.users_repo,
            subscription_repo=self.subscriptions_repo,
            location_repo=self.locations_repo,
            trial_days=settings.trial_days,
        )
        self.monitoring_service = MonitoringService(
            users_repo=self.users_repo,
            locations_repo=self.locations_repo,
            reviews_repo=self.reviews_repo,
            source_adapter=self.source_adapter,
            analyzer=self.analyzer,
            channels=self.channels,
        )
        self.reporting_service = ReportingService()

    def as_dict(self) -> dict:
        return {
            "users_repo": self.users_repo,
            "locations_repo": self.locations_repo,
            "reviews_repo": self.reviews_repo,
            "subscriptions_repo": self.subscriptions_repo,
            "analysis_service": self.analysis_service,
            "onboarding_service": self.onboarding_service,
            "monitoring_service": self.monitoring_service,
            "reporting_service": self.reporting_service,
        }


container = Container()

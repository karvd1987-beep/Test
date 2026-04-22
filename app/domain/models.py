from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from uuid import uuid4


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AccountStatus(str, Enum):
    TRIAL = "trial"
    ACTIVE = "active"
    EXPIRED = "expired"


class LocationStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(slots=True)
class User:
    email: str
    full_name: str
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=utc_now)
    trial_ends_at: datetime = field(default_factory=lambda: utc_now() + timedelta(days=7))
    account_status: AccountStatus = AccountStatus.TRIAL
    min_alert_severity: Severity = Severity.HIGH


@dataclass(slots=True)
class Subscription:
    user_id: str
    status: AccountStatus = AccountStatus.TRIAL
    trial_days: int = 7
    trial_started_at: datetime = field(default_factory=utc_now)
    trial_ends_at: datetime = field(default_factory=lambda: utc_now() + timedelta(days=7))
    trial_location_limit: int = 1
    paid_location_limit: int = 5

    def __post_init__(self) -> None:
        self.trial_ends_at = self.trial_started_at + timedelta(days=self.trial_days)

    def locations_limit(self) -> int:
        if self.status == AccountStatus.ACTIVE:
            return self.paid_location_limit
        return self.trial_location_limit


@dataclass(slots=True)
class Location:
    user_id: str
    source_url: str
    external_place_id: str
    name: str = "Яндекс Точка"
    source: str = "yandex_maps"
    status: LocationStatus = LocationStatus.ACTIVE
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=utc_now)
    last_checked_at: datetime | None = None


@dataclass(slots=True)
class ReviewCandidate:
    external_review_id: str
    author: str
    rating: int
    text: str
    published_at: datetime


@dataclass(slots=True)
class AIAnalysis:
    severity: Severity
    sentiment: str
    topics: list[str]
    recommendation: str
    suggested_reply: str


@dataclass(slots=True)
class Review:
    location_id: str
    external_review_id: str
    author: str
    rating: int
    text: str
    published_at: datetime
    severity: Severity
    sentiment: str
    topics: list[str]
    recommendation: str
    suggested_reply: str
    id: str = field(default_factory=lambda: str(uuid4()))
    ingested_at: datetime = field(default_factory=utc_now)
    is_new: bool = True


@dataclass(slots=True)
class DemoAnalysis:
    source_url: str
    total_reviews: int
    average_rating: float
    severity_breakdown: dict[str, int]
    main_topics: list[str]
    recommendations: list[str]


@dataclass(slots=True)
class TrialReport:
    user_id: str
    total_reviews: int
    severity_breakdown: dict[str, int]
    key_issues: list[str]
    summary: str
    payment_cta: str


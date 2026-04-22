from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
    app_name: str = "Review Radar MVP"
    app_env: str = "dev"
    secret_key: str = "change-me"
    trial_days: int = 7
    trial_location_limit: int = 1
    paid_location_limit: int = 5
    monitoring_interval_minutes: int = 30


settings = Settings()


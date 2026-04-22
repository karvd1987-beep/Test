from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import sha256

from app.domain.interfaces import ReviewSourceAdapter
from app.domain.models import Location, ReviewCandidate


class FakeYandexMapsAdapter(ReviewSourceAdapter):
    source_name = "yandex_maps"

    def fetch_reviews(self, location: Location) -> list[ReviewCandidate]:
        seed = sha256(location.source_url.encode("utf-8")).hexdigest()[:8]
        now = datetime.now(timezone.utc)
        return [
            ReviewCandidate(
                external_review_id=f"{seed}-1",
                author="Иван",
                rating=5,
                text="Отличное место, быстро обслужили.",
                published_at=now - timedelta(hours=4),
            ),
            ReviewCandidate(
                external_review_id=f"{seed}-2",
                author="Мария",
                rating=2,
                text="Долго ждали заказ, персонал не помог.",
                published_at=now - timedelta(hours=1),
            ),
        ]

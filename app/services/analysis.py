from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from app.domain.interfaces import AIAnalyzer, ReviewSourceAdapter
from app.domain.models import AIAnalysis, DemoAnalysis, ReviewCandidate, Severity


@dataclass(slots=True)
class SimpleAIAnalyzer(AIAnalyzer):
    negative_keywords: tuple[str, ...] = (
        "ужас",
        "гряз",
        "хам",
        "долго",
        "отрав",
        "плохо",
        "не советую",
        "обман",
        "не помог",
        "грубо",
    )

    def analyze(self, candidate: ReviewCandidate) -> AIAnalysis:
        text = candidate.text.lower()
        matched_topics = [word for word in self.negative_keywords if word in text]

        if candidate.rating <= 2:
            severity = Severity.CRITICAL
        elif candidate.rating == 3 or matched_topics:
            severity = Severity.HIGH
        elif candidate.rating == 4:
            severity = Severity.MEDIUM
        else:
            severity = Severity.LOW

        sentiment = (
            "negative"
            if severity in {Severity.HIGH, Severity.CRITICAL}
            else "neutral" if severity == Severity.MEDIUM else "positive"
        )
        topics = matched_topics[:3] if matched_topics else ["общее впечатление"]
        recommendation = (
            "Ответьте быстро: извинитесь, признайте проблему и предложите конкретный шаг решения."
            if severity in {Severity.HIGH, Severity.CRITICAL}
            else "Поблагодарите за отзыв и уточните, что можно улучшить."
        )
        suggested_reply = (
            "Спасибо за сигнал. Нам жаль, что опыт оказался негативным. "
            "Напишите в личные сообщения, чтобы мы исправили ситуацию."
            if severity in {Severity.HIGH, Severity.CRITICAL}
            else "Спасибо за отзыв! Мы продолжаем работать над качеством сервиса."
        )
        return AIAnalysis(
            severity=severity,
            sentiment=sentiment,
            topics=topics,
            recommendation=recommendation,
            suggested_reply=suggested_reply,
        )

    def summarize_demo(self, source_url: str, candidates: list[ReviewCandidate]) -> DemoAnalysis:
        if not candidates:
            return DemoAnalysis(
                source_url=source_url,
                total_reviews=0,
                average_rating=0.0,
                severity_breakdown={},
                main_topics=[],
                recommendations=["Недостаточно данных для анализа."],
            )

        avg = sum(candidate.rating for candidate in candidates) / len(candidates)
        analyses = [self.analyze(candidate) for candidate in candidates]
        breakdown = Counter(analysis.severity.value for analysis in analyses)

        topics: list[str] = []
        for analysis in analyses:
            for topic in analysis.topics:
                if topic not in topics:
                    topics.append(topic)

        recommendations: list[str] = []
        high_and_critical = breakdown.get(Severity.CRITICAL.value, 0) + breakdown.get(Severity.HIGH.value, 0)
        if high_and_critical:
            recommendations.append("Внедрите SLA реакции на негативные отзывы до 1 часа.")
        if avg < 4:
            recommendations.append("Проработайте стандарты сервиса и контроль качества смен.")
        if not recommendations:
            recommendations.append("Поддерживайте высокий уровень сервиса и просите гостей делиться фидбеком.")

        return DemoAnalysis(
            source_url=source_url,
            total_reviews=len(candidates),
            average_rating=round(avg, 2),
            severity_breakdown=dict(breakdown),
            main_topics=topics[:5],
            recommendations=recommendations,
        )


@dataclass(slots=True)
class AnalysisService:
    source_adapter: ReviewSourceAdapter
    analyzer: SimpleAIAnalyzer = field(default_factory=SimpleAIAnalyzer)

    def analyze_demo_url(self, source_url: str) -> DemoAnalysis:
        lower = source_url.strip().lower()
        if not lower.startswith(("http://", "https://")):
            raise ValueError("Ссылка должна начинаться с http/https.")
        if "yandex." not in lower or "/maps" not in lower:
            raise ValueError("Для MVP поддерживаются только ссылки Яндекс Карт.")

        from app.domain.models import Location

        location = Location(
            user_id="demo",
            source_url=source_url.strip(),
            external_place_id="demo-place",
            name="Демо точка",
        )
        candidates = self.source_adapter.fetch_reviews(location)
        return self.analyzer.summarize_demo(location.source_url, candidates)

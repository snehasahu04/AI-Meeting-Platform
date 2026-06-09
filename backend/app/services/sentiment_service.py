# -*- coding: utf-8 -*-
"""Sentiment analysis using TextBlob. Returns score in [-1, +1]."""

from backend.app.utils.logger import get_logger

logger = get_logger(__name__)


def analyse_sentiment(text: str) -> dict:
    from textblob import TextBlob
    blob = TextBlob(text)
    score = float(blob.sentiment.polarity)
    subjectivity = float(blob.sentiment.subjectivity)
    if score > 0.1:
        label = "positive"
    elif score < -0.1:
        label = "negative"
    else:
        label = "neutral"
    return {"score": round(score, 4), "label": label, "subjectivity": round(subjectivity, 4)}


def analyse_batch(texts: list) -> list:
    return [analyse_sentiment(t) for t in texts]


def aggregate_sentiment(sentiments: list) -> dict:
    if not sentiments:
        return {"avg_score": 0.0, "trend": [], "overall_label": "neutral"}
    scores = [s["score"] for s in sentiments]
    avg = round(sum(scores) / len(scores), 4)
    label = "positive" if avg > 0.1 else "negative" if avg < -0.1 else "neutral"
    return {"avg_score": avg, "trend": scores, "overall_label": label}

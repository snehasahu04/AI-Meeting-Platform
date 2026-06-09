# -*- coding: utf-8 -*-
"""Anomaly detection using Isolation Forest."""

import numpy as np
from sklearn.ensemble import IsolationForest
from backend.app.utils.logger import get_logger

logger = get_logger(__name__)


def detect_anomalies(embeddings: list, contamination: float = 0.1) -> dict:
    if not embeddings or len(embeddings) < 2:
        return {"anomaly_indices": [], "predictions": [], "anomaly_count": 0}

    X = np.array(embeddings, dtype=np.float32)
    model = IsolationForest(contamination=contamination, random_state=42)
    preds = model.fit_predict(X).tolist()
    anomaly_indices = [i for i, p in enumerate(preds) if p == -1]
    return {"anomaly_indices": anomaly_indices, "predictions": preds, "anomaly_count": len(anomaly_indices)}

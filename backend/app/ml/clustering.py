# -*- coding: utf-8 -*-
"""K-Means clustering on embedding vectors."""

import numpy as np
from sklearn.cluster import KMeans


def cluster_topics(embeddings: list, num_clusters: int = 3):
    if not embeddings:
        return np.array([]), None
    X = np.array(embeddings, dtype=np.float32)
    k = min(num_clusters, len(embeddings))
    model = KMeans(n_clusters=k, random_state=42, n_init="auto")
    labels = model.fit_predict(X)
    return labels, model

# -*- coding: utf-8 -*-
"""Topic clustering using TF-IDF + K-Means."""

import numpy as np
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from backend.app.utils.logger import get_logger

logger = get_logger(__name__)


def cluster_transcript_chunks(chunks: list, num_clusters: int = 3) -> dict:
    if not chunks:
        return {"labels": [], "clusters": {}, "top_terms": {}}

    k = min(num_clusters, len(chunks))
    vectorizer = TfidfVectorizer(max_features=200, stop_words="english")
    X = vectorizer.fit_transform(chunks)
    feature_names = vectorizer.get_feature_names_out()

    model = KMeans(n_clusters=k, random_state=42, n_init="auto")
    labels = model.fit_predict(X).tolist()

    clusters = {i: [] for i in range(k)}
    for idx, label in enumerate(labels):
        clusters[label].append(chunks[idx])

    top_terms = {}
    for cid in range(k):
        centroid = model.cluster_centers_[cid]
        top_idx = centroid.argsort()[-10:][::-1]
        top_terms[cid] = [feature_names[i] for i in top_idx]

    return {"labels": labels, "clusters": clusters, "top_terms": top_terms}

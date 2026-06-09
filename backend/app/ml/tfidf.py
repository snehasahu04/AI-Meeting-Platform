# -*- coding: utf-8 -*-
"""TF-IDF utilities."""

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer


def get_tfidf_matrix(texts: list, max_features: int = 200):
    vectorizer = TfidfVectorizer(max_features=max_features, stop_words="english")
    X = vectorizer.fit_transform(texts)
    return X, vectorizer.get_feature_names_out().tolist()


def top_keywords(texts: list, top_n: int = 10) -> list:
    if not texts:
        return []
    X, feature_names = get_tfidf_matrix(texts)
    scores = np.asarray(X.sum(axis=0)).flatten()
    top_indices = scores.argsort()[-top_n:][::-1]
    return [feature_names[i] for i in top_indices]

# -*- coding: utf-8 -*-
"""FAISS vector store - stores transcript embeddings and supports similarity search."""

import os
import pickle
import numpy as np
import faiss

from backend.app.config import settings
from backend.app.utils.logger import get_logger

logger = get_logger(__name__)


class FAISSStore:
    def __init__(self, index_path=None, meta_path=None, dimension=None):
        self.index_path = index_path or settings.VECTOR_STORE_PATH
        self.meta_path = meta_path or settings.METADATA_PATH
        self.dimension = dimension or settings.EMBEDDING_DIM

        os.makedirs(os.path.dirname(self.index_path) if os.path.dirname(self.index_path) else ".", exist_ok=True)

        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
            logger.info(f"Loaded FAISS index ({self.index.ntotal} vectors).")
        else:
            self.index = faiss.IndexFlatL2(self.dimension)
            logger.info("Created new FAISS index.")

        if os.path.exists(self.meta_path):
            with open(self.meta_path, "rb") as f:
                self.metadata = pickle.load(f)
        else:
            self.metadata = []

    def add_vector(self, meeting_id, chunk_id, text, vector):
        vec = np.array([vector], dtype=np.float32)
        self.index.add(vec)
        faiss_idx = self.index.ntotal - 1
        self.metadata.append({"meeting_id": meeting_id, "chunk_id": chunk_id, "text": text, "faiss_index": faiss_idx})
        self._save()
        return faiss_idx

    def add_vectors_batch(self, meeting_id, chunks, vectors):
        if not chunks or not vectors:
            return []
        X = np.array(vectors, dtype=np.float32)
        start_idx = self.index.ntotal
        self.index.add(X)
        indices = []
        for i, (chunk, _) in enumerate(zip(chunks, vectors)):
            faiss_idx = start_idx + i
            self.metadata.append({"meeting_id": meeting_id, "chunk_id": i, "text": chunk, "faiss_index": faiss_idx})
            indices.append(faiss_idx)
        self._save()
        logger.info(f"Added {len(chunks)} vectors for meeting '{meeting_id}'.")
        return indices

    def search(self, query_vector, k=5):
        if self.index.ntotal == 0:
            return []
        vec = np.array([query_vector], dtype=np.float32)
        k = min(k, self.index.ntotal)
        distances, indices = self.index.search(vec, k)
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if 0 <= idx < len(self.metadata):
                entry = dict(self.metadata[idx])
                entry["distance"] = float(dist)
                results.append(entry)
        return results

    def _save(self):
        os.makedirs(os.path.dirname(self.index_path) if os.path.dirname(self.index_path) else ".", exist_ok=True)
        faiss.write_index(self.index, self.index_path)
        with open(self.meta_path, "wb") as f:
            pickle.dump(self.metadata, f)

    def total_vectors(self):
        return self.index.ntotal


faiss_store = FAISSStore()

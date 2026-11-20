"""FAQ data loading and precomputed TF-IDF/cosine-similarity matching."""

import json
import logging

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from nlp.preprocessing import preprocess

logger = logging.getLogger(__name__)


class FAQDataError(Exception):
    """Raised when the FAQ dataset is missing or malformed."""


class FAQMatcher:
    def __init__(self, path, threshold=0.24):
        self.path = path
        self.threshold = float(threshold)
        if not 0 <= self.threshold <= 1:
            raise ValueError("Similarity threshold must be between 0 and 1.")
        self.faqs = self._load_faqs()
        self._build_index()

    def _load_faqs(self):
        try:
            with open(self.path, "r", encoding="utf-8") as dataset:
                faqs = json.load(dataset)
        except FileNotFoundError as exc:
            raise FAQDataError("Dataset file was not found: {}".format(self.path)) from exc
        except json.JSONDecodeError as exc:
            raise FAQDataError("Dataset contains invalid JSON: {}".format(exc)) from exc
        except OSError as exc:
            raise FAQDataError("Dataset could not be read: {}".format(exc)) from exc

        if not isinstance(faqs, list) or not faqs:
            raise FAQDataError("Dataset must be a non-empty JSON array.")

        required = {"id", "category", "question", "answer", "alternatives"}
        ids = set()
        for index, faq in enumerate(faqs):
            if not isinstance(faq, dict) or not required.issubset(faq):
                raise FAQDataError("FAQ at position {} is missing required fields.".format(index))
            if (not isinstance(faq["question"], str) or not faq["question"].strip()
                    or not isinstance(faq["answer"], str) or not faq["answer"].strip()
                    or not isinstance(faq["category"], str) or not faq["category"].strip()
                    or not isinstance(faq["alternatives"], list)
                    or any(not isinstance(item, str) for item in faq["alternatives"])):
                raise FAQDataError("FAQ at position {} has invalid field values.".format(index))
            if isinstance(faq["id"], bool) or not isinstance(faq["id"], (int, str)):
                raise FAQDataError("FAQ at position {} has an invalid ID.".format(index))
            if faq["id"] in ids:
                raise FAQDataError("FAQ IDs must be unique; duplicate ID: {}".format(faq["id"]))
            ids.add(faq["id"])
        return faqs

    def _build_index(self):
        self._faq_indices = []
        documents = []
        for faq_index, faq in enumerate(self.faqs):
            for question in [faq["question"]] + faq["alternatives"]:
                normalized = preprocess(question)
                if normalized:
                    documents.append(normalized)
                    self._faq_indices.append(faq_index)
        if not documents:
            raise FAQDataError("FAQ questions did not contain any indexable text.")

        self._vectorizer = TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(2, 5),
            sublinear_tf=True,
        )
        self._document_vectors = self._vectorizer.fit_transform(documents)

    def match(self, question):
        normalized = preprocess(question)
        if not normalized:
            return self._fallback()

        query_vector = self._vectorizer.transform([normalized])
        variant_scores = cosine_similarity(query_vector, self._document_vectors)[0]
        faq_scores = [0.0] * len(self.faqs)
        for variant_index, score in enumerate(variant_scores):
            faq_index = self._faq_indices[variant_index]
            faq_scores[faq_index] = max(faq_scores[faq_index], float(score))

        best_index = max(range(len(faq_scores)), key=faq_scores.__getitem__)
        confidence = faq_scores[best_index]
        if confidence < self.threshold:
            return self._fallback(confidence)

        faq = self.faqs[best_index]
        return {
            "matched": True,
            "answer": faq["answer"],
            "category": faq["category"],
            "confidence": round(confidence, 4),
            "faq_id": faq["id"],
            "suggestions": [],
        }

    def _fallback(self, confidence=0.0):
        return {
            "matched": False,
            "answer": "I'm sorry, I couldn't find a relevant answer. Could you please rephrase your question?",
            "category": None,
            "confidence": round(confidence, 4),
            "faq_id": None,
            "suggestions": [faq["question"] for faq in self.faqs[:3]],
        }

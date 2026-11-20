"""Focused tests for FAQ matching and Flask API behavior."""

import json
import os
import tempfile
import unittest

from app import create_app
from config import Config
from nlp.similarity import FAQMatcher


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAQS_PATH = os.path.join(ROOT, "faqs.json")


class TestFAQMatcher(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matcher = FAQMatcher(FAQS_PATH, threshold=0.30)

    def test_exact_faq_question(self):
        result = self.matcher.match("What is Python?")
        self.assertTrue(result["matched"])
        self.assertEqual(result["faq_id"], 6)

    def test_reworded_question(self):
        result = self.matcher.match("How do I keep several values together in Python?")
        self.assertTrue(result["matched"])
        self.assertEqual(result["faq_id"], 7)

    def test_case_and_punctuation_are_ignored(self):
        result = self.matcher.match("EXPLAIN THE JAVA VIRTUAL MACHINE!!!")
        self.assertTrue(result["matched"])
        self.assertEqual(result["faq_id"], 12)

    def test_spelling_variation(self):
        result = self.matcher.match("What does pythn do?")
        self.assertTrue(result["matched"])
        self.assertEqual(result["faq_id"], 6)

    def test_unrelated_question_returns_fallback_and_suggestions(self):
        result = self.matcher.match("How do I bake a chocolate cake?")
        self.assertFalse(result["matched"])
        self.assertIsNone(result["category"])
        self.assertEqual(len(result["suggestions"]), 3)

    def test_empty_normalized_question_returns_fallback(self):
        self.assertFalse(self.matcher.match("!!!")["matched"])


class TestChatAPI(unittest.TestCase):
    def setUp(self):
        class TestConfig(Config):
            TESTING = True
            FAQS_PATH = FAQS_PATH
            SIMILARITY_THRESHOLD = 0.30

        self.app = create_app(TestConfig)
        self.client = self.app.test_client()

    def test_empty_question_is_bad_request(self):
        response = self.client.post("/chat", json={"question": "  "})
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    def test_multiple_questions_in_one_session(self):
        first = self.client.post("/chat", json={"question": "What is HTML?"})
        second = self.client.post("/chat", json={"question": "What is SQL?"})
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.get_json()["category"], "Web Development")
        self.assertEqual(second.get_json()["category"], "Databases")

    def test_faq_and_health_endpoints(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(len(self.client.get("/faqs").get_json()["faqs"]), 50)
        self.assertEqual(self.client.get("/health").status_code, 200)

    def test_missing_dataset_is_reported_as_unavailable(self):
        class MissingDataConfig(Config):
            TESTING = True
            FAQS_PATH = os.path.join(tempfile.gettempdir(), "faq-chatbot-file-that-does-not-exist.json")

        missing_client = create_app(MissingDataConfig).test_client()
        self.assertEqual(missing_client.post("/chat", json={"question": "What is Python?"}).status_code, 503)
        self.assertEqual(missing_client.get("/health").status_code, 503)

    def test_invalid_dataset_json_is_reported_as_unavailable(self):
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".json", delete=False) as dataset:
            dataset.write("{invalid json")
            dataset_path = dataset.name
        try:
            class InvalidDataConfig(Config):
                TESTING = True
                FAQS_PATH = dataset_path

            invalid_client = create_app(InvalidDataConfig).test_client()
            self.assertEqual(invalid_client.get("/faqs").status_code, 503)
        finally:
            os.unlink(dataset_path)

    def test_non_json_and_invalid_json_shape_are_rejected(self):
        self.assertEqual(self.client.post("/chat", data="question").status_code, 400)
        self.assertEqual(self.client.post("/chat", json=["question"]).status_code, 400)


if __name__ == "__main__":
    unittest.main()

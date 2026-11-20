"""Flask application for the local, NLP-based FAQ assistant."""

import logging

from flask import Flask, jsonify, render_template, request

from config import Config
from nlp.similarity import FAQMatcher, FAQDataError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    try:
        matcher = FAQMatcher(
            app.config["FAQS_PATH"],
            threshold=app.config["SIMILARITY_THRESHOLD"],
        )
    except FAQDataError as exc:
        logger.error("FAQ chatbot could not load its dataset: %s", exc)
        matcher = None

    app.extensions["faq_matcher"] = matcher

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.post("/chat")
    def chat():
        if not request.is_json:
            return jsonify(error="Request body must be valid JSON."), 400

        payload = request.get_json(silent=True)
        question = payload.get("question") if isinstance(payload, dict) else None
        if not isinstance(question, str) or not question.strip():
            return jsonify(error="Please enter a non-empty question."), 400
        if len(question) > app.config["MAX_QUESTION_LENGTH"]:
            return jsonify(
                error="Question is too long.",
                max_length=app.config["MAX_QUESTION_LENGTH"],
            ), 400

        if matcher is None:
            return jsonify(error="FAQ data is unavailable. Please try again later."), 503

        result = matcher.match(question)
        return jsonify(result)

    @app.get("/faqs")
    def faqs():
        if matcher is None:
            return jsonify(error="FAQ data is unavailable. Please try again later."), 503
        return jsonify(faqs=matcher.faqs)

    @app.get("/health")
    def health():
        status = "ok" if matcher is not None else "degraded"
        http_status = 200 if matcher is not None else 503
        return jsonify(status=status, faq_count=len(matcher.faqs) if matcher else 0), http_status

    return app


app = create_app()

if __name__ == "__main__":
    app.run(
        host=app.config["HOST"],
        port=app.config["PORT"],
        debug=app.config["DEBUG"],
    )

# FAQ Assistant

A responsive FAQ chatbot for general technology and computer science topics. The Flask backend preprocesses questions with NLTK-compatible tokenization, stopword removal, and lemmatization, then uses precomputed TF-IDF character n-gram vectors and cosine similarity to find the best FAQ. It does not call generative AI services: every answer comes from `faqs.json`.

## Features

- 50 curated FAQs across programming, Python, Java, AI, machine learning, web development, databases, computer networks, operating systems, and cybersecurity.
- Questions and alternative phrasings are normalized and indexed once at startup.
- Configurable similarity threshold, confidence score, and deterministic suggestions when no FAQ is a good match.
- Responsive chat interface, timestamps, typing indicator, suggested questions, clear-chat control, and in-page conversation history.
- JSON API with input validation, status codes, health check, and explicit handling for missing or invalid FAQ data.

## Project structure

```text
faq-chatbot/
├── app.py
├── config.py
├── faqs.json
├── requirements.txt
├── nlp/
│   ├── __init__.py
│   ├── preprocessing.py
│   └── similarity.py
├── static/
│   ├── css/style.css
│   └── js/script.js
├── templates/index.html
└── tests/test_chatbot.py
```

## Setup and run

Python 3.9 or newer is recommended.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000). To use another port, set `PORT` before running. For example, in PowerShell: `$env:PORT=8000; python app.py`.

NLTK's tokenizer does not require downloaded data. If NLTK stopwords or WordNet data are installed, preprocessing uses them. If those corpora are unavailable (including offline installations), the application uses bundled English stopwords and a small conservative lemmatization fallback so startup and matching still work. To install the optional corpora:

```powershell
python -c "import nltk; nltk.download('stopwords'); nltk.download('wordnet'); nltk.download('omw-1.4')"
```

## Configuration

| Environment variable | Default | Description |
|---|---:|---|
| `SIMILARITY_THRESHOLD` | `0.30` | Minimum cosine score from 0 to 1 required to return an FAQ answer |
| `FAQS_PATH` | `faqs.json` in the project directory | Dataset path |
| `HOST` | `127.0.0.1` | Flask bind address |
| `PORT` | `5000` | Flask port |
| `FLASK_DEBUG` | `0` | Set to `1` for Flask debug mode |

Example:

```powershell
$env:SIMILARITY_THRESHOLD="0.28"
python app.py
```

Raise the threshold to be more conservative; lower it to accept looser matches. Generic request phrasing is removed during preprocessing to reduce superficial matches. The returned confidence is a cosine similarity score, not a calibrated probability.

## NLP matching

1. Lowercase the question and remove punctuation.
2. Tokenize with NLTK's resource-free Treebank tokenizer (or a built-in fallback), remove English stopwords, and lemmatize with NLTK WordNet when available.
3. Normalize each FAQ question and its alternatives once during application startup.
4. Fit a TF-IDF vectorizer over character-boundary n-grams (2–5 characters). These features allow modest spelling and wording variations to retain useful overlap.
5. At request time, transform the input and calculate cosine similarity against the precomputed document vectors. For each FAQ, keep the strongest score among its question and alternatives.
6. Return only the highest-scoring FAQ when its score meets the configured threshold; otherwise return the specified fallback plus three dataset-backed suggestions.

## API

### `POST /chat`

Request:

```json
{"question": "How do Python lists work?"}
```

Successful response:

```json
{
  "matched": true,
  "answer": "A Python list is an ordered, mutable collection...",
  "category": "Python",
  "confidence": 0.62,
  "faq_id": 7,
  "suggestions": []
}
```

Empty or invalid questions return `400`; unavailable FAQ data returns `503`.

### `GET /faqs`

Returns `{"faqs": [...]}` with the complete dataset.

### `GET /health`

Returns the service status and loaded FAQ count. The endpoint returns `503` if the FAQ dataset could not be loaded.

## Tests

```powershell
python -m unittest discover -s tests -v
```

The tests cover exact matches, rewording, letter case, punctuation, spelling variation, unrelated input, empty requests, sequential questions, and missing FAQ data. The browser also reports backend/network errors in the chat rather than failing silently.

## Sample questions

- What is Python?
- How do I store multiple values in Python?
- explain the java virtual machine!!!
- How do computers learn from data?
- What's the difference between TCP and UDP?
- How can I make my password safer?
- Tell me about photosynthesis (expected fallback)

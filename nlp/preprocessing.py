"""Lightweight text normalization with optional NLTK WordNet resources."""

import re
import string

try:
    from nltk.corpus import stopwords
    from nltk.stem import WordNetLemmatizer
    from nltk.tokenize import TreebankWordTokenizer
except ImportError:
    stopwords = None
    WordNetLemmatizer = None
    TreebankWordTokenizer = None


_FALLBACK_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "being", "but",
    "by", "can", "could", "did", "do", "does", "for", "from", "had",
    "has", "have", "he", "her", "here", "hers", "him", "his", "how",
    "i", "if", "in", "into", "is", "it", "its", "me", "my", "of", "on",
    "or", "our", "ours", "she", "so", "than", "that", "the", "their",
    "them", "there", "these", "they", "this", "those", "to", "us", "was",
    "we", "were", "what", "when", "where", "which", "who", "why", "will",
    "with", "would", "you", "your", "about", "describe", "define", "explain",
    "mean", "please", "tell",
}

_TOKENIZER = TreebankWordTokenizer() if TreebankWordTokenizer else None
_LEMMATIZER = WordNetLemmatizer() if WordNetLemmatizer else None
_STOPWORDS = None
_WORDNET_AVAILABLE = None
_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def _get_stopwords():
    global _STOPWORDS
    if _STOPWORDS is None:
        try:
            _STOPWORDS = set(stopwords.words("english")) if stopwords else _FALLBACK_STOPWORDS
        except LookupError:
            _STOPWORDS = _FALLBACK_STOPWORDS
    return _STOPWORDS


def _fallback_lemma(token):
    irregular = {
        "better": "good", "children": "child", "feet": "foot", "geese": "goose",
        "indices": "index", "mice": "mouse", "ran": "run", "teeth": "tooth",
        "was": "be", "were": "be", "written": "write",
    }
    if token in irregular:
        return irregular[token]
    if len(token) > 5 and token.endswith("ies"):
        return token[:-3] + "y"
    if len(token) > 5 and token.endswith("ing"):
        stem = token[:-3]
        if len(stem) > 2 and stem[-1] == stem[-2]:
            stem = stem[:-1]
        return stem
    if len(token) > 4 and token.endswith("ed"):
        stem = token[:-2]
        if len(stem) > 2 and stem[-1] == stem[-2]:
            stem = stem[:-1]
        return stem
    if len(token) > 4 and token.endswith("es") and token[-3] in "sxz":
        return token[:-2]
    if len(token) > 3 and token.endswith("s") and not token.endswith(("ss", "us", "is")):
        return token[:-1]
    return token


def _lemmatize(token):
    global _WORDNET_AVAILABLE
    if _LEMMATIZER is None or _WORDNET_AVAILABLE is False:
        return _fallback_lemma(token)
    try:
        lemma = _LEMMATIZER.lemmatize(token)
        _WORDNET_AVAILABLE = True
        return lemma
    except LookupError:
        _WORDNET_AVAILABLE = False
        return _fallback_lemma(token)


def preprocess(text):
    """Lowercase, tokenize, remove punctuation/stopwords, and lemmatize."""
    lowered = text.lower().translate(str.maketrans("", "", string.punctuation))
    if _TOKENIZER:
        raw_tokens = _TOKENIZER.tokenize(lowered)
    else:
        raw_tokens = _TOKEN_PATTERN.findall(lowered)

    ignored = _get_stopwords()
    tokens = [
        _lemmatize(token)
        for token in raw_tokens
        if _TOKEN_PATTERN.fullmatch(token) and token not in ignored
    ]
    return " ".join(tokens)

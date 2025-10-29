# ai_summary.py
from transformers import pipeline
import os

os.environ['TRANSFORMERS_CACHE'] = os.path.join(os.getcwd(), 'transformers_cache')

_summarizer = None

MAX_CHARS = 1000  # ou 1024 tokens approximativement

def split_text(text, max_chars=MAX_CHARS):
    segments = []
    start = 0
    while start < len(text):
        end = start + max_chars
        segments.append(text[start:end])
        start = end
    return segments

def generate_summary(text):
    global _summarizer
    if _summarizer is None:
        _summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

    segments = split_text(text)
    summaries = []
    for segment in segments:
        result = _summarizer(segment, max_length=150, min_length=40, do_sample=False)
        summaries.append(result[0]['summary_text'])
    return " ".join(summaries)

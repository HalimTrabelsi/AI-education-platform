import os
import requests
from dotenv import load_dotenv

load_dotenv()

HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

def analyze_text_with_ai(text):
    """Call AI API (like Hugging Face) for NSFW, plagiarism, or risk analysis."""
    if not text.strip():
        return {
            "is_nsfw": False,
            "is_plagiarism": False,
            "ai_confidence": 0.0,
            "ai_flags": "",
            "risk_label": "Safe"
        }

    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
    payload = {"inputs": text}

    try:
        response = requests.post(
            "https://api-inference.huggingface.co/models/facebook/bart-large-mnli",
            headers=headers, json=payload, timeout=10
        )
        result = response.json()

        # Example mock logic
        confidence = 0.75  # Placeholder for real model output
        is_nsfw = "nsfw" in text.lower()
        is_plagiarism = "copy" in text.lower() or "source" in text.lower()
        flags = []

        if is_nsfw: flags.append("NSFW")
        if is_plagiarism: flags.append("Plagiarism")
        risk_label = "Risky" if confidence > 0.7 else "Safe"

        return {
            "is_nsfw": is_nsfw,
            "is_plagiarism": is_plagiarism,
            "ai_confidence": confidence,
            "ai_flags": ", ".join(flags),
            "risk_label": risk_label
        }
    except Exception as e:
        print("AI Analysis failed:", e)
        return {
            "is_nsfw": False,
            "is_plagiarism": False,
            "ai_confidence": 0.0,
            "ai_flags": "AI Error",
            "risk_label": "Safe"
        }

# moderation/ai_tools.py
import os
import requests
from dotenv import load_dotenv

load_dotenv()
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def ai_analyze_report(title, description, resource_url=None):
    """Analyze a report for plagiarism, NSFW, and AI cheating."""

    text_to_analyze = f"{title}\n{description}"

    # 1️⃣ NSFW / inappropriate content detection via Hugging Face
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
    hf_url = "https://api-inference.huggingface.co/models/facebook/opt-1.3b"  # example: moderation model
    response = requests.post(hf_url, headers=headers, json={"inputs": text_to_analyze})
    hf_result = response.json() if response.status_code == 200 else {}

    is_nsfw = any(label.get('label') in ["NSFW", "sexual", "violence"] for label in hf_result.get('labels', []))
    
    # 2️⃣ Plagiarism / AI cheat detection via OpenAI (or other Hugging Face models)
    # Here we simply ask the AI to rate plagiarism likelihood
    openai_url = "https://api.openai.com/v1/chat/completions"
    headers_openai = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    prompt = f"""
    Analyze the following text for plagiarism and AI-generated content:
    Text: {text_to_analyze}
    Return JSON with:
    is_plagiarism: true/false
    ai_confidence: 0.0-1.0
    ai_flags: comma-separated labels like ["copied", "AI-generated"]
    risk_label: Low/Medium/High
    """

    openai_resp = requests.post(openai_url, headers=headers_openai, json={
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0
    })

    ai_data = openai_resp.json()
    try:
        content = ai_data['choices'][0]['message']['content']
        import json
        result = json.loads(content)
    except:
        result = {
            "is_plagiarism": False,
            "ai_confidence": 0.0,
            "ai_flags": "",
            "risk_label": "Low"
        }

    # Merge NSFW detection
    result['is_nsfw'] = is_nsfw
    return result

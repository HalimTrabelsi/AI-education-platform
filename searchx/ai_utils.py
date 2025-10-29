from django.conf import settings
import openai
import requests
from PIL import Image
import pytesseract
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

import torch

# Advanced AI: HuggingFace Transformers
try:
    from transformers import pipeline, AutoTokenizer, AutoModel
    HF_AVAILABLE = True
except Exception:
    HF_AVAILABLE = False

# Génération de texte avec HuggingFace
def hf_generate_text(prompt, model_name="gpt2", max_length=100):
    try:
        if not HF_AVAILABLE:
            return "Erreur génération HF: transformers non installé"
        generator = pipeline("text-generation", model=model_name)
        result = generator(prompt, max_length=max_length, num_return_sequences=1)
        return result[0]["generated_text"]
    except Exception as e:
        return f"Erreur génération HF: {str(e)}"

# Embedding sémantique avec HuggingFace
def hf_get_embedding(text, model_name="sentence-transformers/all-MiniLM-L6-v2"):
    try:
        if not HF_AVAILABLE:
            return f"Erreur embedding HF: transformers non installé"
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModel.from_pretrained(model_name)
        inputs = tokenizer(text, return_tensors="pt")
        with torch.no_grad():
            outputs = model(**inputs)
            embeddings = outputs.last_hidden_state.mean(dim=1).squeeze().numpy()
        return embeddings
    except Exception as e:
        return f"Erreur embedding HF: {str(e)}"

# Classification de texte avec HuggingFace
def hf_classify_text(text, model_name="distilbert-base-uncased-finetuned-sst-2-english"):
    try:
        if not HF_AVAILABLE:
            return f"Erreur classification HF: transformers non installé"
        classifier = pipeline("text-classification", model=model_name)
        result = classifier(text)
        return result
    except Exception as e:
        return f"Erreur classification HF: {str(e)}"


def extract_concepts_from_text(text):
    """Extrait une liste courte de concepts depuis un texte (français).
    Tente d'utiliser OpenAI si disponible, sinon heuristique simple.
    Retourne une liste de chaînes.
    """
    import json as _json
    import re
    text = (text or "").strip()
    if not text:
        return []
    if getattr(settings, 'OPENAI_API_KEY', None):
        try:
            resp = openai.ChatCompletion.create(
                model=getattr(settings, 'OPENAI_MODEL', 'gpt-3.5-turbo'),
                messages=[
                    {"role": "system", "content": "Vous êtes un assistant qui extrait des noms de concepts courts et pertinents à partir d'un texte pédagogique en français. Répondez uniquement par un JSON tableau de chaînes, par ex: [\"Pile\", \"File\", \"Structure de données linéaire\"]"},
                    {"role": "user", "content": f"Texte:\n{text}"},
                ],
                temperature=0,
            )
            content = resp.choices[0].message.content.strip()
            # try to find a JSON array in the content
            try:
                return _json.loads(content)
            except Exception:
                # try to extract a bracketed list on any line
                for line in content.splitlines():
                    line = line.strip()
                    if line.startswith('[') and line.endswith(']'):
                        try:
                            return _json.loads(line)
                        except Exception:
                            pass
                # fallback: split by commas and return capitalized tokens
                parts = re.split(r',|;|\n', content)
                concepts = [p.strip().strip('"\'') for p in parts if p.strip()]
                return concepts[:10]
        except Exception:
            # Log or return later; fallback to heuristics
            pass
    # Fallback simple heuristic: extract noun-like phrases (capitalized words or common patterns)
    tokens = re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ'-]+(?: [A-Za-zÀ-ÖØ-öø-ÿ'-]+){0,2}", text)
    # pick unique words longer than 3 chars, favor capitalized
    seen = set()
    concepts = []
    for t in tokens:
        tt = t.strip()
        if len(tt) < 3:
            continue
        key = tt.lower()
        if key in seen:
            continue
        if tt[0].isupper() or ' ' in tt:
            concepts.append(tt)
            seen.add(key)
        if len(concepts) >= 10:
            break
    return concepts


def ai_answer_question(question, context=None):
    """Répond à une question en utilisant OpenAI (ou une réponse basique si indisponible)."""
    question = (question or "").strip()
    if not question:
        return ""
    if getattr(settings, 'OPENAI_API_KEY', None):
        try:
            messages = [
                {"role": "system", "content": "Vous êtes un assistant de recherche précis et concis, répondez en français si la question est en français."}
            ]
            if context:
                messages.append({"role": "user", "content": f"Contexte:\n{context}"})
            messages.append({"role": "user", "content": f"Question: {question}. Répondez de manière concise."})
            resp = openai.ChatCompletion.create(
                model=getattr(settings, 'OPENAI_MODEL', 'gpt-3.5-turbo'),
                messages=messages,
                temperature=0,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            return f"Erreur AI: {str(e)}"
    # OpenRouter fallback when OpenAI is not configured
    if getattr(settings, 'OPENROUTER_API_KEY', None):
        try:
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                # Optional but recommended headers for OpenRouter routing/limits context
                "HTTP-Referer": getattr(settings, 'BASE_URL', ''),
                "X-Title": "AI Education Platform",
            }
            messages = [
                {"role": "system", "content": "Vous êtes un assistant de recherche précis et concis, répondez en français si la question est en français."}
            ]
            if context:
                messages.append({"role": "user", "content": f"Contexte:\n{context}"})
            messages.append({"role": "user", "content": f"Question: {question}. Répondez de manière concise."})
            payload = {
                "model": getattr(settings, 'OPENROUTER_MODEL', 'openrouter/auto'),
                "messages": messages,
                "temperature": 0,
            }
            r = requests.post(url, headers=headers, json=payload, timeout=30)
            if r.status_code >= 400:
                return f"Erreur OpenRouter: {r.status_code} {r.text[:200]}"
            data = r.json()
            content = (
                data.get('choices', [{}])[0]
                    .get('message', {})
                    .get('content', '')
            )
            return (content or '').strip()
        except Exception as e:
            return f"Erreur OpenRouter: {str(e)}"
    # fallback simple canned answers for a few known questions
    q = question.lower()
    if 'tri rapide' in q or 'quick sort' in q:
        return "Le tri rapide a une complexité moyenne en O(n log n) mais peut être O(n²) dans le pire des cas."
    return "Désolé, je ne peux pas répondre sans une clé API configurée."

# Configuration OpenAI
if getattr(settings, 'OPENAI_API_KEY', None):
    openai.api_key = settings.OPENAI_API_KEY
    OPENAI_AVAILABLE = True
else:
    OPENAI_AVAILABLE = False

try:
    # test tesseract availability
    TESSERACT_AVAILABLE = True if pytesseract.get_tesseract_version() else False
except Exception:
    TESSERACT_AVAILABLE = False




def transcribe_audio(audio_path, language="fr"):
    """Transcrit un fichier audio."""
    try:
        audio_file = open(audio_path, "rb")
        transcript = openai.Audio.transcribe(
            model="whisper-1",
            file=audio_file,
            language=language
        )
        return transcript.text
    except Exception as e:
        return f"Erreur de transcription: {str(e)}"


def get_ai_status():
    """Retourne un petit diagnostic sur la disponibilité des dépendances AI."""
    info = {
        'openai_key_set': bool(getattr(settings, 'OPENAI_API_KEY', None)),
        'openai_available': bool(OPENAI_AVAILABLE),
        'hf_available': bool(HF_AVAILABLE),
        'tesseract_available': bool(TESSERACT_AVAILABLE),
    }
    return info

# Cache pour les vecteurs TF-IDF
vectorizer = None
concept_vectors = None
concept_ids = None

def semantic_expand(query):
    """Retourne des suggestions liées au texte de la requête.
    Format: liste de dicts {title, description, source, relevance}.
    Utilise OpenAI si disponible, sinon un fallback heuristique simple.
    """
    import json as _json
    q = (query or '').strip()
    if not q:
        return []
    if getattr(settings, 'OPENAI_API_KEY', None):
        try:
            prompt = (
                "Donne 5 ressources ou idées étroitement liées au concept suivant en français: \n"
                f"\"{q}\".\n"
                "Réponds UNIQUEMENT en JSON (liste) où chaque élément a les clés exactes: \n"
                "title, description, source, relevance (entre 0 et 1)."
            )
            resp = openai.ChatCompletion.create(
                model=getattr(settings, 'OPENAI_MODEL', 'gpt-3.5-turbo'),
                messages=[
                    {"role": "system", "content": "Tu es un assistant qui propose des ressources éducatives concises au format JSON uniquement."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            )
            content = (resp.choices[0].message.content or '').strip()
            try:
                data = _json.loads(content)
                items = []
                for it in data if isinstance(data, list) else []:
                    title = str(it.get('title') or '').strip()
                    if not title:
                        continue
                    desc = str(it.get('description') or '').strip()
                    source = str(it.get('source') or it.get('source_type') or 'external_ai').strip() or 'external_ai'
                    rel = it.get('relevance')
                    try:
                        rel = float(rel)
                    except Exception:
                        rel = 0.6
                    rel = max(0.0, min(1.0, rel))
                    items.append({
                        'title': title,
                        'description': desc,
                        'source': source,
                        'relevance': rel,
                    })
                return items[:5]
            except Exception:
                return []
        except Exception:
            return []
    # Fallback simple: générer quelques pistes basées sur des patrons connus
    seeds = [
        {'title': f"Introduction à {q}", 'description': f"Vue d'ensemble des bases de {q}.", 'source': 'ai_generated', 'relevance': 0.7},
        {'title': f"Applications pratiques de {q}", 'description': f"Exemples d'utilisation de {q} dans le monde réel.", 'source': 'ai_generated', 'relevance': 0.65},
        {'title': f"Outils et frameworks pour {q}", 'description': f"Présentation d'outils utiles autour de {q}.", 'source': 'ai_generated', 'relevance': 0.6},
        {'title': f"Comparatif: {q} vs alternatives", 'description': f"Points forts et limites de {q}.", 'source': 'ai_generated', 'relevance': 0.55},
        {'title': f"Ressources avancées sur {q}", 'description': f"Lectures et cours pour aller plus loin sur {q}.", 'source': 'ai_generated', 'relevance': 0.5},
    ]
    return seeds

def compute_similarity(text1, text2):
    """Calcule la similarité entre deux textes."""
    try:
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform([text1, text2])
        return cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
    except Exception as e:
        return 0.0
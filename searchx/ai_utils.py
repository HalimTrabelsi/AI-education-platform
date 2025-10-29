from django.conf import settings
import openai
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


def generate_quiz_from_text(context_text, max_questions=5):
    """Génère une liste de questions/réponses à partir d'un texte de contexte.
    Retourne une liste de dicts {question, answer}.
    """
    import json as _json
    context_text = (context_text or "").strip()
    if not context_text:
        return []
    if getattr(settings, 'OPENAI_API_KEY', None):
        try:
            prompt = (
                "Vous êtes un assistant pédagogique qui génère un quiz court basé sur le texte fourni. "
                "Retournez uniquement un JSON avec une clé 'quiz' contenant une liste d'objets {question, answer}. "
                "Fournissez des questions claires et des réponses concises.\n\nTexte:\n" + context_text
            )
            resp = openai.ChatCompletion.create(
                model=getattr(settings, 'OPENAI_MODEL', 'gpt-3.5-turbo'),
                messages=[
                    {"role": "system", "content": "Assistant pédagogique pour générer des quiz en français."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            )
            content = resp.choices[0].message.content.strip()
            try:
                data = _json.loads(content)
                return data.get('quiz') or data
            except Exception:
                # try to extract question/answer pairs heuristically
                lines = [l.strip() for l in content.splitlines() if l.strip()]
                quiz = []
                q = None
                for line in lines:
                    if line.lower().startswith('q') or line.lower().startswith('question'):
                        q = line.split(':',1)[-1].strip()
                    elif line.lower().startswith('a') or line.lower().startswith('réponse') or line.lower().startswith('answer'):
                        a = line.split(':',1)[-1].strip()
                        if q:
                            quiz.append({'question': q, 'answer': a})
                            q = None
                return quiz[:max_questions]
        except Exception:
            pass
    # Fallback: create simple factual questions from first sentences
    sentences = context_text.split('.')
    quiz = []
    for i, s in enumerate(sentences):
        s = s.strip()
        if not s:
            continue
        if len(quiz) >= max_questions:
            break
        quiz.append({'question': f"Qu'est-ce que: {s[:80]}?", 'answer': s})

    return quiz


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

def summarize_text(text, max_sentences=3):
    """Résume un texte en utilisant GPT."""
    try:
        response = openai.ChatCompletion.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": f"Résumez ce texte en {max_sentences} phrases maximum. Gardez les points importants."},
                {"role": "user", "content": text}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Erreur de résumé: {str(e)}"

def extract_formulas(text):
    """Extrait les formules mathématiques d'un texte."""
    try:
        response = openai.ChatCompletion.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "Extrayez et listez toutes les formules mathématiques dans ce texte. Retournez-les en format LaTeX."},
                {"role": "user", "content": text}
            ]
        )
        formulas = [
            {"type": "formula", "latex": formula.strip()}
            for formula in response.choices[0].message.content.split('\n')
            if formula.strip()
        ]
        return formulas
    except Exception as e:
        return [{"type": "error", "message": str(e)}]

def ocr_image(image_path):
    """Effectue l'OCR sur une image."""
    try:
        # Configure Tesseract path si défini
        if hasattr(settings, 'TESSERACT_CMD') and settings.TESSERACT_CMD:
            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
        
        # Open and process image
        image = Image.open(image_path)
        try:
            text = pytesseract.image_to_string(image, lang='fra+eng')
            return text.strip()
        except pytesseract.TesseractNotFoundError:
            return "Erreur: Tesseract n'est pas installé. Veuillez installer Tesseract OCR depuis https://github.com/UB-Mannheim/tesseract/wiki"
        except pytesseract.TesseractError as e:
            return f"Erreur Tesseract: {str(e)}"
    except Exception as e:
        return f"Erreur OCR: {str(e)}"

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

def compute_similarity(text1, text2):
    """Calcule la similarité entre deux textes."""
    try:
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform([text1, text2])
        return cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
    except Exception as e:
        return 0.0
# feed/ai_services.py

import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import warnings
warnings.filterwarnings('ignore')


class AIWritingAssistant:
    """
    Assistant d'écriture IA (version basique + avancée intégrée)
    """
    
    def __init__(self):
        # Initialiser les modèles ML (optionnels)
        self.sentiment_analyzer = None
        self.classifier = None
        
        try:
            from transformers import pipeline
            print("🤖 Chargement des modèles IA...")
            
            # Sentiment Analysis
            self.sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model="nlptown/bert-base-multilingual-uncased-sentiment",
                device=-1
            )
            print("✅ Sentiment analyzer chargé")
        except Exception as e:
            print(f"⚠️ Sentiment analyzer non disponible: {e}")
        
        try:
            from transformers import pipeline
            # Zero-shot Classification
            self.classifier = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli",
                device=-1
            )
            print("✅ Classifier chargé")
        except Exception as e:
            print(f"⚠️ Classifier non disponible: {e}")
    
    def check_grammar(self, text: str) -> List[Dict]:
        """
        Vérifications grammaticales basiques
        """
        suggestions = []
        
        # Doubles espaces
        if '  ' in text:
            suggestions.append({
                'type': 'grammar',
                'message': 'Espaces multiples détectés',
                'replacements': [text.replace('  ', ' ')],
                'context': 'Utilisez un seul espace',
            })
        
        # Ponctuation manquante
        if len(text) > 20 and not text.rstrip().endswith(('.', '!', '?')):
            suggestions.append({
                'type': 'grammar',
                'message': 'Le texte ne se termine pas par une ponctuation',
                'replacements': [],
                'context': 'Ajoutez un point final',
            })
        
        # Majuscule au début
        if text and not text[0].isupper() and not text[0].isdigit():
            suggestions.append({
                'type': 'grammar',
                'message': 'Le texte devrait commencer par une majuscule',
                'replacements': [text[0].upper() + text[1:]],
                'context': 'Première lettre en majuscule',
            })
        
        # Fautes courantes
        common_errors = {
            r'\bsa\b': 'ça',
            r'\bmalgres\b': 'malgré',
            r'\bparmis\b': 'parmi',
            r'\bbiensur\b': 'bien sûr',
        }
        
        for pattern, correction in common_errors.items():
            if re.search(pattern, text, re.IGNORECASE):
                suggestions.append({
                    'type': 'grammar',
                    'message': f'Orthographe possible: "{correction}"',
                    'replacements': [correction],
                    'context': 'Vérifiez l\'orthographe',
                })
        
        return suggestions[:5]
    
    def suggest_improvements(self, text: str, content_type: str) -> List[str]:
        """
        Suggestions d'amélioration selon le type de contenu
        """
        suggestions = []
        
        # Vérifications générales
        if len(text) < 20:
            suggestions.append("📝 Message trop court. Ajoutez plus de détails.")
        
        if len(text) > 1000:
            suggestions.append("✂️ Message long. Résumez ou structurez en points.")
        
        sentences = text.count('.') + text.count('!') + text.count('?')
        if sentences == 0 and len(text) > 50:
            suggestions.append("💬 Ajoutez de la ponctuation pour structurer.")
        
        # Suggestions par type
        if content_type == 'programme':
            keywords = ['chapitre', 'cours', 'leçon', 'séance', 'module']
            if not any(word in text.lower() for word in keywords):
                suggestions.append("📚 Ajoutez des détails sur le contenu (chapitres, leçons).")
            
            if not re.search(r'\d+', text):
                suggestions.append("🔢 Ajoutez des références numériques.")
        
        elif content_type == 'echeance':
            date_keywords = ['date', 'deadline', 'avant', 'jusqu\'au', 'limite']
            if not any(word in text.lower() for word in date_keywords):
                suggestions.append("📅 Précisez la date limite.")
            
            submission_keywords = ['rendu', 'soumission', 'dépôt', 'livrer']
            if not any(word in text.lower() for word in submission_keywords):
                suggestions.append("📤 Indiquez le mode de soumission.")
        
        elif content_type == 'difficulte':
            if '?' not in text:
                suggestions.append("❓ Ajoutez une question précise.")
        
        elif content_type == 'ressource':
            link_keywords = ['http', 'www', 'lien', 'document', 'pdf']
            if not any(word in text.lower() for word in link_keywords):
                suggestions.append("🔗 Ajoutez un lien vers la ressource.")
        
        # Vérification du ton
        tone_suggestion = self._check_tone(text, content_type)
        if tone_suggestion:
            suggestions.append(tone_suggestion)
        
        return suggestions
    
    def _check_tone(self, text: str, content_type: str) -> str:
        """Vérifie si le ton est approprié"""
        urgent_words = ['urgent', 'immédiat', 'vite', 'rapidement', 'asap']
        formal_words = ['veuillez', 'merci de', 'prière de', 'cordialement']
        
        has_urgent = any(word in text.lower() for word in urgent_words)
        has_formal = any(word in text.lower() for word in formal_words)
        
        if content_type == 'programme' and has_urgent:
            return "⚠️ Ton urgent. Un programme devrait être informatif."
        
        if content_type == 'echeance' and not has_urgent and not has_formal:
            return "💼 Ajoutez des formules de politesse."
        
        if content_type == 'annonce' and not has_formal:
            return "📢 Une annonce devrait avoir un ton formel."
        
        return ""
    
    def adapt_tone(self, text: str, content_type: str) -> str:
        """Adapte le ton selon le type"""
        if content_type == 'programme':
            if not text.startswith('📚'):
                return "📚 " + text
        
        elif content_type == 'echeance':
            if not any(word in text.lower() for word in ['merci', 'cordialement']):
                return text + "\n\n⏰ Merci de respecter cette échéance."
        
        elif content_type == 'annonce':
            if not text.startswith('📢'):
                return "📢 " + text
        
        return text
    
    # ========== FONCTIONNALITÉS IA AVANCÉES ==========
    
    def analyze_sentiment(self, text: str) -> Dict:
        """
        Analyse le sentiment avec IA (positif/négatif/neutre)
        """
        if not self.sentiment_analyzer or len(text) < 10:
            return {
                'sentiment': 'neutre',
                'emoji': '😐',
                'confidence': 0.0,
                'score': 3,
                'method': 'default'
            }
        
        try:
            result = self.sentiment_analyzer(text[:512])[0]
            stars = int(result['label'].split()[0])
            
            if stars >= 4:
                sentiment = 'positif'
                emoji = '😊'
            elif stars <= 2:
                sentiment = 'négatif'
                emoji = '😞'
            else:
                sentiment = 'neutre'
                emoji = '😐'
            
            return {
                'sentiment': sentiment,
                'emoji': emoji,
                'confidence': round(result['score'], 2),
                'score': stars,
                'method': 'AI'
            }
        except Exception as e:
            return {
                'sentiment': 'neutre',
                'emoji': '😐',
                'confidence': 0.0,
                'score': 3,
                'method': 'error'
            }
    
    def detect_emotion(self, text: str) -> Dict:
        """
        Détecte l'émotion avec zero-shot classification
        """
        if not self.classifier or len(text) < 10:
            return {
                'emotion': 'neutre',
                'emoji': '😐',
                'confidence': 0.0,
                'method': 'default'
            }
        
        try:
            emotions = ['joie', 'colère', 'tristesse', 'peur', 'surprise', 'neutre']
            result = self.classifier(text[:512], candidate_labels=emotions)
            
            emotion_emojis = {
                'joie': '😄', 'colère': '😠', 'tristesse': '😢',
                'peur': '😰', 'surprise': '😲', 'neutre': '😐'
            }
            
            emotion = result['labels'][0]
            
            return {
                'emotion': emotion,
                'emoji': emotion_emojis.get(emotion, '😐'),
                'confidence': round(result['scores'][0], 2),
                'all_scores': dict(zip(result['labels'], result['scores'])),
                'method': 'AI'
            }
        except Exception as e:
            return {
                'emotion': 'neutre',
                'emoji': '😐',
                'confidence': 0.0,
                'method': 'error'
            }
    
    def predict_engagement(self, text: str, content_type: str) -> Dict:
        """
        Prédit le niveau d'engagement potentiel
        """
        score = 0.5
        factors = {
            'length': 0, 'questions': 0, 'emojis': 0,
            'urgency': 0, 'readability': 0, 'sentiment': 0
        }
        
        # 1. Longueur optimale
        length = len(text)
        if 100 <= length <= 500:
            factors['length'] = 0.2
        elif 50 <= length < 100 or 500 < length <= 800:
            factors['length'] = 0.1
        
        # 2. Questions
        factors['questions'] = min(text.count('?') * 0.1, 0.2)
        
        # 3. Emojis
        emoji_pattern = re.compile(r'[\U0001F300-\U0001F9FF]|[\u2600-\u26FF]')
        emoji_count = len(emoji_pattern.findall(text))
        factors['emojis'] = min(emoji_count * 0.05, 0.15)
        
        # 4. Urgence
        urgent_words = ['urgent', 'important', 'attention', 'nouveau', 'exclusif']
        urgency_count = sum(1 for word in urgent_words if word in text.lower())
        factors['urgency'] = min(urgency_count * 0.08, 0.15)
        
        # 5. Lisibilité
        sentences = text.count('.') + text.count('!') + text.count('?')
        if sentences > 0:
            words = len(text.split())
            avg_sentence_length = words / sentences
            if avg_sentence_length < 20:
                factors['readability'] = 0.15
            elif avg_sentence_length < 30:
                factors['readability'] = 0.1
        
        # 6. Sentiment
        sentiment_result = self.analyze_sentiment(text)
        if sentiment_result['sentiment'] == 'positif':
            factors['sentiment'] = 0.15
        elif sentiment_result['sentiment'] == 'neutre':
            factors['sentiment'] = 0.05
        
        score += sum(factors.values())
        score = min(score, 1.0)
        
        if score >= 0.8:
            level, emoji, color = 'Très élevé', '🔥', 'success'
        elif score >= 0.6:
            level, emoji, color = 'Élevé', '📈', 'info'
        elif score >= 0.4:
            level, emoji, color = 'Moyen', '📊', 'warning'
        else:
            level, emoji, color = 'Faible', '📉', 'danger'
        
        suggestions = []
        if factors['length'] < 0.1:
            suggestions.append("✍️ Ajustez la longueur (100-500 caractères)")
        if factors['questions'] == 0:
            suggestions.append("❓ Ajoutez une question")
        if factors['emojis'] < 0.05:
            suggestions.append("😊 Utilisez des emojis")
        if factors['sentiment'] < 0.1:
            suggestions.append("🌟 Ton plus positif")
        
        return {
            'score': round(score, 2),
            'percentage': round(score * 100),
            'level': level,
            'emoji': emoji,
            'color': color,
            'factors': {k: round(v, 2) for k, v in factors.items()},
            'suggestions': suggestions
        }
    
    def calculate_quality_score(self, text: str, content_type: str) -> float:
        """Score de qualité global (0-10)"""
        score = 5.0
        
        # Grammaire
        grammar_issues = self.check_grammar(text)
        if len(grammar_issues) == 0:
            score += 1.5
        elif len(grammar_issues) <= 2:
            score += 0.5
        
        # Longueur
        if 100 <= len(text) <= 1000:
            score += 1.0
        elif 50 <= len(text) < 100 or len(text) > 1000:
            score += 0.5
        
        # Structure
        punctuation = sum(text.count(p) for p in ['.', '!', '?', ','])
        if punctuation >= 3:
            score += 0.5
        
        # Sentiment
        sentiment = self.analyze_sentiment(text)
        if sentiment['sentiment'] == 'positif':
            score += 1.0
        elif sentiment['sentiment'] == 'neutre':
            score += 0.5
        
        # Pertinence
        type_keywords = {
            'programme': ['cours', 'chapitre', 'module', 'leçon'],
            'echeance': ['date', 'deadline', 'avant', 'rendu'],
            'difficulte': ['aide', 'question', 'problème'],
            'ressource': ['lien', 'document', 'fichier'],
            'annonce': ['important', 'information', 'note']
        }
        
        keywords = type_keywords.get(content_type, [])
        matches = sum(1 for kw in keywords if kw in text.lower())
        score += min(matches * 0.3, 1.0)
        
        return min(round(score, 1), 10.0)
    
    def detect_spam_likelihood(self, text: str) -> Dict:
        """Détecte la probabilité de spam"""
        spam_indicators = 0
        reasons = []
        
        if text.isupper() and len(text) > 20:
            spam_indicators += 2
            reasons.append("Texte en MAJUSCULES")
        
        if text.count('!') > 5:
            spam_indicators += 1
            reasons.append(f"Trop de '!' ({text.count('!')})")
        
        spam_words = ['gratuit', 'cliquez ici', 'argent', 'gagnez']
        if sum(1 for word in spam_words if word in text.lower()) >= 2:
            spam_indicators += 2
            reasons.append("Mots suspects")
        
        if len(re.findall(r'http[s]?://', text)) > 3:
            spam_indicators += 1
            reasons.append("Trop de liens")
        
        if spam_indicators >= 4:
            likelihood, is_spam, color = 'Très élevé', True, 'danger'
        elif spam_indicators >= 2:
            likelihood, is_spam, color = 'Moyen', False, 'warning'
        else:
            likelihood, is_spam, color = 'Faible', False, 'success'
        
        return {
            'is_spam': is_spam,
            'likelihood': likelihood,
            'score': spam_indicators,
            'color': color,
            'reasons': reasons
        }
    
    def suggest_title(self, description: str, content_type: str) -> List[str]:
        """Suggère des titres accrocheurs"""
        suggestions = []
        
        type_prefixes = {
            'programme': ['📚 Programme', '📖 Nouveau cours'],
            'echeance': ['📅 Échéance', '⏰ Date limite'],
            'difficulte': ['❓ Question', '🤔 Aide'],
            'ressource': ['📖 Ressource', '🔗 Document'],
            'annonce': ['📢 Annonce', '🔔 Important']
        }
        
        prefixes = type_prefixes.get(content_type, [''])
        first_sentence = description.split('.')[0][:50]
        
        if first_sentence:
            suggestions.append(f"{prefixes[0]}: {first_sentence}...")
        
        keywords = re.findall(r'\b[A-ZÀ-ÿ][a-zà-ÿ]+\b', description)
        if keywords:
            suggestions.append(f"{prefixes[0]}: {' '.join(keywords[:3])}")
        
        return suggestions[:3]
    
    def auto_correct_common_errors(self, text: str) -> Dict:
        """Correction automatique"""
        original = text
        corrections = []
        
        fixes = {
            r'\bsa\b': ('ça', 'Orthographe'),
            r'\bmalgres\b': ('malgré', 'Orthographe'),
            r'\bbiensur\b': ('bien sûr', 'Orthographe'),
        }
        
        corrected = text
        for pattern, (replacement, reason) in fixes.items():
            matches = list(re.finditer(pattern, corrected, re.IGNORECASE))
            if matches:
                corrected = re.sub(pattern, replacement, corrected, flags=re.IGNORECASE)
                corrections.append({
                    'original': matches[0].group(),
                    'correction': replacement,
                    'reason': reason
                })
        
        if '  ' in corrected:
            corrected = re.sub(r'\s+', ' ', corrected)
            corrections.append({
                'original': 'Espaces multiples',
                'correction': 'Espaces uniques',
                'reason': 'Formatage'
            })
        
        return {
            'original': original,
            'corrected': corrected,
            'has_changes': original != corrected,
            'corrections': corrections,
            'count': len(corrections)
        }


class AIContentEnricher:
    """Service d'enrichissement automatique"""
    
    def __init__(self):
        pass
    
    def extract_dates(self, text: str) -> List[Dict]:
        """Extrait les dates"""
        dates = []
        
        patterns = [
            (r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b', 'numeric'),
            (r'\b(\d{1,2})\s+(janvier|février|fevrier|mars|avril|mai|juin|juillet|août|aout|septembre|octobre|novembre|décembre|decembre)\s+(\d{4})\b', 'textual'),
        ]
        
        for pattern, pattern_type in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                parsed = self._parse_date(match.group())
                dates.append({
                    'text': match.group(),
                    'position': match.start(),
                    'parsed_date': parsed,
                    'type': pattern_type
                })
        
        return dates
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse une date"""
        months = {
            'janvier': 1, 'février': 2, 'fevrier': 2, 'mars': 3, 'avril': 4,
            'mai': 5, 'juin': 6, 'juillet': 7, 'août': 8, 'aout': 8,
            'septembre': 9, 'octobre': 10, 'novembre': 11, 'décembre': 12, 'decembre': 12
        }
        
        try:
            numeric_match = re.match(r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})', date_str)
            if numeric_match:
                day = int(numeric_match.group(1))
                month = int(numeric_match.group(2))
                year = int(numeric_match.group(3))
                if year < 100:
                    year += 2000
                if 1 <= month <= 12 and 1 <= day <= 31:
                    return datetime(year, month, day)
            
            for month_name, month_num in months.items():
                if month_name in date_str.lower():
                    numbers = re.findall(r'\d+', date_str)
                    if numbers:
                        day = int(numbers[0])
                        year = int(numbers[1]) if len(numbers) > 1 else datetime.now().year
                        if 1 <= day <= 31:
                            return datetime(year, month_num, day)
        except:
            pass
        
        return None
    
    def suggest_resources(self, text: str, content_type: str) -> List[str]:
        """Suggère des ressources"""
        suggestions = {
            'difficulte': [
                "💡 Rechercher des tutoriels YouTube",
                "📖 Consulter la documentation",
                "👥 Forums étudiants"
            ],
            'programme': [
                "📚 Préparer des supports",
                "📝 Créer des exercices",
                "🎥 Vidéos explicatives"
            ],
            'ressource': [
                "🔖 Sauvegarder en favoris",
                "📤 Partager avec le groupe"
            ],
            'echeance': [
                "⏰ Définir un rappel",
                "📅 Ajouter au calendrier"
            ],
            'annonce': [
                "📧 Envoyer par email",
                "📌 Épingler"
            ]
        }
        
        return suggestions.get(content_type, [])
    
    def extract_action_items(self, text: str) -> List[Dict]:
        """Extrait les actions à faire"""
        action_items = []
        
        patterns = [
            r'(?:il faut|faut|devez|devons)\s+([^.!?]+)',
            r'(?:rendre|soumettre|livrer)\s+([^.!?]+)',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                action = match.group(1).strip()
                priority = 'high' if any(w in action.lower() for w in ['urgent', 'vite']) else 'normal'
                action_items.append({
                    'action': action,
                    'priority': priority,
                    'type': 'extracted'
                })
        
        return action_items
    
    def suggest_tags(self, text: str, content_type: str, max_tags: int = 5) -> List[str]:
        """Suggère des tags"""
        default_tags = {
            'programme': ['cours', 'programme'],
            'echeance': ['deadline', 'échéance'],
            'difficulte': ['aide', 'question'],
            'ressource': ['ressource', 'document'],
            'annonce': ['annonce', 'info']
        }
        
        tags = set(default_tags.get(content_type, []))
        
        # Mots capitalisés
        capitalized = re.findall(r'\b[A-ZÀ-Ÿ][a-zà-ÿ]+\b', text)
        tags.update(word.lower() for word in capitalized[:3])
        
        return list(tags)[:max_tags]
    
    def detect_urgency_level(self, text: str, deadline: Optional[datetime]) -> Dict:
        """Détecte l'urgence"""
        urgency_score = 0
        reasons = []
        
        urgent_keywords = {
            'critique': 3, 'urgent': 3, 'immédiat': 3,
            'vite': 2, 'important': 1
        }
        
        for keyword, score in urgent_keywords.items():
            if keyword in text.lower():
                urgency_score += score
                reasons.append(f"Mot: '{keyword}'")
        
        if deadline:
            days_left = (deadline - datetime.utcnow()).days
            if days_left < 0:
                urgency_score += 5
                reasons.append("Dépassée!")
            elif days_left <= 1:
                urgency_score += 3
                reasons.append(f"{days_left}j")
            elif days_left <= 3:
                urgency_score += 2
                reasons.append(f"{days_left}j")
        
        if urgency_score >= 5:
            level, emoji, color = 'Critique', '🔴', 'danger'
        elif urgency_score >= 3:
            level, emoji, color = 'Élevé', '🟠', 'warning'
        elif urgency_score >= 1:
            level, emoji, color = 'Moyen', '🟡', 'info'
        else:
            level, emoji, color = 'Normal', '🟢', 'success'
        
        return {
            'level': level,
            'emoji': emoji,
            'color': color,
            'score': urgency_score,
            'reasons': reasons
        }


class AIRecurringContentGenerator:
    """Génération de contenu récurrent"""
    
    @staticmethod
    def generate_deadline_reminder(feed_item) -> Optional[Dict]:
        """Génère un rappel d'échéance"""
        if not feed_item.deadline:
            return None
        
        days_left = (feed_item.deadline - datetime.utcnow()).days
        
        if days_left <= 0:
            urgency = "⏰ URGENT - ÉCHÉANCE DÉPASSÉE"
            message = f"L'échéance '{feed_item.title}' est dépassée!"
        elif days_left == 1:
            urgency = "⚠️ DERNIER JOUR"
            message = f"Dernier jour pour '{feed_item.title}'!"
        elif days_left <= 3:
            urgency = "📌 RAPPEL"
            message = f"{days_left} jours pour '{feed_item.title}'."
        else:
            return None
        
        return {
            'title': f"{urgency} - {feed_item.title}",
            'description': f"{message}\n\n{feed_item.description}",
            'content_type': 'annonce',
            'deadline': feed_item.deadline,
            'is_ai_generated': True
        }
    
    @staticmethod
    def generate_weekly_summary(feed_items: List) -> Optional[Dict]:
        """Génère un résumé hebdo"""
        if not feed_items:
            return None
        
        total = len(feed_items)
        by_type = {}
        for item in feed_items:
            by_type[item.content_type] = by_type.get(item.content_type, 0) + 1
        
        summary = f"📊 **Résumé hebdomadaire**\n\nTotal: {total}\n\n"
        
        emojis = {'programme': '📚', 'echeance': '📅', 'difficulte': '🤔', 'ressource': '📖', 'annonce': '📢'}
        
        for ctype, count in by_type.items():
            emoji = emojis.get(ctype, '•')
            summary += f"{emoji} {ctype.capitalize()}: {count}\n"
        
        upcoming = [i for i in feed_items if i.deadline and i.deadline > datetime.utcnow()]
        if upcoming:
            summary += f"\n⏰ **Prochaines échéances:**\n"
            for item in sorted(upcoming, key=lambda x: x.deadline)[:5]:
                days = (item.deadline - datetime.utcnow()).days
                summary += f"• {item.title} - {days}j\n"
        
        return {
            'title': f"📊 Résumé - {datetime.now().strftime('%d/%m/%Y')}",
            'description': summary,
            'content_type': 'annonce',
            'is_ai_generated': True
        }
    
    @staticmethod
    def detect_missing_content(feed_items: List, days: int = 7) -> List[str]:
        """Détecte contenus manquants"""
        recent = datetime.utcnow() - timedelta(days=days)
        recent_items = [i for i in feed_items if i.created_at >= recent]
        
        existing = set(i.content_type for i in recent_items)
        all_types = {'programme', 'echeance', 'difficulte', 'ressource', 'annonce'}
        missing = all_types - existing
        
        messages = {
            'programme': "📚 Aucun programme publié cette semaine.",
            'echeance': "📅 Aucune échéance définie.",
            'ressource': "📖 Aucune ressource partagée.",
            'difficulte': "🤔 Aucune question signalée.",
            'annonce': "📢 Aucune annonce publiée."
        }

        return [messages.get(ctype, f"Manque: {ctype}") for ctype in missing]
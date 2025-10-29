import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')


class AIWritingAssistant:
    """Assistant d'écriture IA avec vérifications avancées"""
    
    def __init__(self):
        print("🧠 Assistant IA local initialisé (version améliorée).")
        
        # Dictionnaires étendus pour vérifications
        self.common_errors = {
            r'\bsa\b': 'ça',
            r'\bmalgres\b': 'malgré',
            r'\bparmis\b': 'parmi',
            r'\bbiensur\b': 'bien sûr',
            r'\bausitot\b': 'aussitôt',
            r'\bpeutetre\b': 'peut-être',
            r'\bquelquefois\b': 'quelquefois',
            r'\bparceque\b': 'parce que',
            r'\bquoique\b': 'quoi que',
        }
        
        self.redundant_phrases = [
            (r'\btrès très\b', 'très'),
            (r'\bbeaucoup beaucoup\b', 'beaucoup'),
            (r'\ben fait en fait\b', 'en fait'),
        ]

    # ================== Vérifications grammaticales avancées ==================
    
    def check_grammar(self, text: str) -> List[Dict]:
        """Vérifications grammaticales enrichies"""
        suggestions = []
        
        # 1. Espaces multiples
        if '  ' in text:
            suggestions.append({
                'type': 'grammar',
                'severity': 'low',
                'message': 'Espaces multiples détectés',
                'replacements': [text.replace('  ', ' ')],
                'context': 'Utilisez un seul espace entre les mots',
                'position': text.find('  ')
            })
        
        # 2. Ponctuation finale
        if len(text) > 20 and not text.rstrip().endswith(('.', '!', '?', '…')):
            suggestions.append({
                'type': 'grammar',
                'severity': 'medium',
                'message': 'Ponctuation finale manquante',
                'replacements': [text + '.'],
                'context': 'Ajoutez un point, point d\'exclamation ou d\'interrogation',
                'position': len(text)
            })
        
        # 3. Majuscule initiale
        if text and not text[0].isupper() and not text[0].isdigit() and text[0] not in ['(', '[', '"', '\'']:
            suggestions.append({
                'type': 'grammar',
                'severity': 'medium',
                'message': 'Majuscule initiale manquante',
                'replacements': [text[0].upper() + text[1:]],
                'context': 'Commencez par une majuscule',
                'position': 0
            })
        
        # 4. Erreurs orthographiques courantes
        for pattern, correction in self.common_errors.items():
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            for match in matches:
                suggestions.append({
                    'type': 'spelling',
                    'severity': 'high',
                    'message': f'Orthographe incorrecte: "{match.group()}"',
                    'replacements': [correction],
                    'context': f'Utilisez "{correction}" au lieu de "{match.group()}"',
                    'position': match.start()
                })
        
        # 5. Ponctuation avant espace
        if re.search(r'\s+[,;:!?]', text):
            suggestions.append({
                'type': 'grammar',
                'severity': 'low',
                'message': 'Espace avant ponctuation',
                'replacements': [],
                'context': 'Évitez les espaces avant , ; : ! ?',
                'position': -1
            })
        
        # 6. Espaces après ponctuation
        missing_spaces = re.finditer(r'[.!?,;:][a-zA-Z]', text)
        for match in missing_spaces:
            suggestions.append({
                'type': 'grammar',
                'severity': 'medium',
                'message': 'Espace manquant après ponctuation',
                'replacements': [],
                'context': 'Ajoutez un espace après la ponctuation',
                'position': match.start()
            })
        
        # 7. Répétitions de mots
        words = text.lower().split()
        for i in range(len(words) - 1):
            if words[i] == words[i + 1] and len(words[i]) > 2:
                suggestions.append({
                    'type': 'style',
                    'severity': 'low',
                    'message': f'Répétition détectée: "{words[i]}"',
                    'replacements': [],
                    'context': 'Évitez les répétitions consécutives',
                    'position': -1
                })
        
        # 8. Phrases trop longues (> 30 mots)
        sentences = re.split(r'[.!?]+', text)
        for sentence in sentences:
            word_count = len(sentence.split())
            if word_count > 30:
                suggestions.append({
                    'type': 'readability',
                    'severity': 'low',
                    'message': f'Phrase très longue ({word_count} mots)',
                    'replacements': [],
                    'context': 'Divisez en phrases plus courtes pour la lisibilité',
                    'position': -1
                })
        
        # 9. Redondances
        for pattern, replacement in self.redundant_phrases:
            if re.search(pattern, text, re.IGNORECASE):
                suggestions.append({
                    'type': 'style',
                    'severity': 'low',
                    'message': 'Expression redondante détectée',
                    'replacements': [replacement],
                    'context': 'Simplifiez l\'expression',
                    'position': -1
                })
        
        return suggestions[:10]  # Limiter à 10 suggestions
    
    def check_coherence(self, text: str) -> Dict:
        """Vérifie la cohérence du texte"""
        issues = []
        score = 10.0
        
        # 1. Transitions absentes
        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
        if len(sentences) > 3:
            transition_words = ['donc', 'ainsi', 'par conséquent', 'cependant', 
                              'néanmoins', 'en effet', 'd\'ailleurs', 'puis', 'ensuite']
            has_transitions = any(word in text.lower() for word in transition_words)
            if not has_transitions:
                issues.append("Manque de mots de transition entre les idées")
                score -= 2.0
        
        # 2. Équilibre des phrases
        sentence_lengths = [len(s.split()) for s in sentences]
        if sentence_lengths:
            avg_length = sum(sentence_lengths) / len(sentence_lengths)
            if avg_length < 5:
                issues.append("Phrases trop courtes (style haché)")
                score -= 1.5
            elif avg_length > 25:
                issues.append("Phrases trop longues (difficulté de lecture)")
                score -= 1.5
        
        # 3. Répétitions excessives
        words = [w.lower() for w in text.split() if len(w) > 4]
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        repeated = [w for w, c in word_freq.items() if c > 3]
        if repeated:
            issues.append(f"Mots répétés: {', '.join(repeated[:3])}")
            score -= 1.0
        
        # 4. Connecteurs logiques déséquilibrés
        positive_words = ['bien', 'bon', 'excellent', 'parfait']
        negative_words = ['mal', 'mauvais', 'problème', 'erreur']
        pos_count = sum(1 for w in positive_words if w in text.lower())
        neg_count = sum(1 for w in negative_words if w in text.lower())
        
        if pos_count > 0 and neg_count > 0 and abs(pos_count - neg_count) > 3:
            issues.append("Déséquilibre entre aspects positifs/négatifs")
            score -= 0.5
        
        return {
            'score': max(0, score),
            'issues': issues,
            'sentence_count': len(sentences),
            'avg_sentence_length': round(sum(sentence_lengths) / len(sentence_lengths), 1) if sentence_lengths else 0
        }
    
    def check_clarity(self, text: str) -> Dict:
        """Évalue la clarté du texte"""
        clarity_score = 10.0
        issues = []
        
        # 1. Jargon technique excessif
        complex_words = re.findall(r'\b\w{12,}\b', text)
        if len(complex_words) > 5:
            issues.append(f"{len(complex_words)} mots très longs détectés")
            clarity_score -= 2.0
        
        # 2. Phrases passives
        passive_indicators = ['été', 'était', 'seront', 'seraient']
        passive_count = sum(1 for ind in passive_indicators if ind in text.lower())
        if passive_count > 3:
            issues.append("Trop de constructions passives")
            clarity_score -= 1.5
        
        # 3. Négations multiples
        negations = ['ne pas', 'n\'a pas', 'ne jamais', 'ne rien']
        neg_count = sum(text.lower().count(neg) for neg in negations)
        if neg_count > 2:
            issues.append("Négations multiples (préférez l'affirmatif)")
            clarity_score -= 1.0
        
        # 4. Acronymes non définis
        acronyms = re.findall(r'\b[A-Z]{2,}\b', text)
        if len(acronyms) > 3:
            issues.append(f"{len(acronyms)} acronymes détectés - définissez-les")
            clarity_score -= 1.0
        
        # 5. Vocabulaire varié
        unique_words = len(set(text.lower().split()))
        total_words = len(text.split())
        lexical_diversity = unique_words / total_words if total_words > 0 else 0
        
        if lexical_diversity < 0.4:
            issues.append("Vocabulaire peu varié")
            clarity_score -= 1.5
        
        return {
            'score': max(0, clarity_score),
            'issues': issues,
            'lexical_diversity': round(lexical_diversity, 2),
            'complex_words_count': len(complex_words)
        }

    # ================== Analyse enrichie ==================
    
    def analyze_sentiment(self, text: str) -> Dict:
        """Analyse de sentiment enrichie avec nuances"""
        pos_words = {
            'excellent': 3, 'parfait': 3, 'génial': 3, 'super': 2, 
            'bien': 2, 'bon': 2, 'agréable': 2, 'intéressant': 1,
            'utile': 1, 'correct': 1
        }
        neg_words = {
            'horrible': -3, 'nul': -3, 'catastrophe': -3, 'mauvais': -2,
            'problème': -2, 'erreur': -2, 'difficile': -1, 'compliqué': -1,
            'inquiet': -1
        }
        
        score = 0
        text_lower = text.lower()
        
        # Comptage pondéré
        for word, weight in pos_words.items():
            score += text_lower.count(word) * weight
        for word, weight in neg_words.items():
            score += text_lower.count(word) * weight
        
        # Modificateurs d'intensité
        if 'très' in text_lower:
            score *= 1.2
        if 'vraiment' in text_lower:
            score *= 1.15
        
        # Négations inversent le sentiment
        if any(neg in text_lower for neg in ['ne pas', 'n\'est pas', 'pas du tout']):
            score *= -0.7
        
        # Classification
        if score >= 5:
            sentiment, emoji, confidence = 'très positif', '🤩', 0.9
        elif score >= 2:
            sentiment, emoji, confidence = 'positif', '😊', 0.85
        elif score >= -1:
            sentiment, emoji, confidence = 'neutre', '😐', 0.7
        elif score >= -4:
            sentiment, emoji, confidence = 'négatif', '😞', 0.85
        else:
            sentiment, emoji, confidence = 'très négatif', '😡', 0.9
        
        return {
            'sentiment': sentiment,
            'emoji': emoji,
            'confidence': confidence,
            'score': score,
            'method': 'advanced_lexical'
        }
    
    def detect_emotion(self, text: str) -> Dict:
        """Détection d'émotion avec plus de nuances"""
        text_lower = text.lower()
        
        # Patterns émotionnels
        emotions = {
            'joie': (['heureux', 'content', 'ravi', 'super', 'génial'], '😄', 0.8),
            'tristesse': (['triste', 'déçu', 'désolé', 'peine'], '😢', 0.85),
            'colère': (['énervé', 'furieux', 'inacceptable', 'scandaleux'], '😠', 0.9),
            'peur': (['inquiet', 'anxieux', 'stress', 'peur'], '😰', 0.8),
            'surprise': (['wow', 'incroyable', 'étonnant', '!'], '😲', 0.7),
            'curiosité': (['?', 'comment', 'pourquoi', 'intéressant'], '🤔', 0.75),
            'neutre': ([], '😐', 0.6)
        }
        
        detected_emotions = []
        for emotion_name, (keywords, emoji, conf) in emotions.items():
            match_count = sum(1 for keyword in keywords if keyword in text_lower)
            if match_count > 0:
                detected_emotions.append((emotion_name, emoji, conf, match_count))
        
        if detected_emotions:
            # Trier par nombre de correspondances
            detected_emotions.sort(key=lambda x: x[3], reverse=True)
            emotion, emoji, confidence, _ = detected_emotions[0]
        else:
            emotion, emoji, confidence = 'neutre', '😐', 0.6
        
        return {
            'emotion': emotion,
            'emoji': emoji,
            'confidence': confidence,
            'secondary_emotions': [e[0] for e in detected_emotions[1:3]],
            'method': 'pattern_matching'
        }

    def calculate_readability_score(self, text: str) -> Dict:
        """Calcule un score de lisibilité (style Flesch)"""
        sentences = [s for s in re.split(r'[.!?]+', text) if s.strip()]
        words = text.split()
        
        if not sentences or not words:
            return {'score': 0, 'level': 'N/A', 'issues': ['Texte trop court']}
        
        # Métriques de base
        total_sentences = len(sentences)
        total_words = len(words)
        total_syllables = sum(self._count_syllables(word) for word in words)
        
        avg_words_per_sentence = total_words / total_sentences
        avg_syllables_per_word = total_syllables / total_words
        
        # Score simplifié (0-100)
        readability = 206.835 - (1.015 * avg_words_per_sentence) - (84.6 * avg_syllables_per_word)
        readability = max(0, min(100, readability))
        
        # Classification
        if readability >= 80:
            level, color = 'Très facile', 'success'
        elif readability >= 60:
            level, color = 'Facile', 'info'
        elif readability >= 40:
            level, color = 'Moyen', 'warning'
        else:
            level, color = 'Difficile', 'danger'
        
        return {
            'score': round(readability, 1),
            'level': level,
            'color': color,
            'avg_words_per_sentence': round(avg_words_per_sentence, 1),
            'avg_syllables_per_word': round(avg_syllables_per_word, 2),
            'total_sentences': total_sentences,
            'total_words': total_words
        }
    
    def _count_syllables(self, word: str) -> int:
        """Compte approximatif des syllabes (français)"""
        word = word.lower()
        vowels = 'aeiouyéèêëàâäôöùûü'
        syllable_count = 0
        previous_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not previous_was_vowel:
                syllable_count += 1
            previous_was_vowel = is_vowel
        
        # Minimum 1 syllabe
        return max(1, syllable_count)

    def calculate_quality_score(self, text: str, content_type: str) -> float:
        """Score global de qualité enrichi"""
        score = 5.0
        
        # 1. Grammaire (20%)
        grammar_issues = len(self.check_grammar(text))
        if grammar_issues == 0:
            score += 2.0
        elif grammar_issues <= 2:
            score += 1.0
        
        # 2. Longueur optimale (15%)
        if 100 <= len(text) <= 1000:
            score += 1.5
        elif 50 <= len(text) < 100 or 1000 < len(text) <= 2000:
            score += 0.75
        
        # 3. Ponctuation (10%)
        if any(p in text for p in ['.', '!', '?']):
            score += 1.0
        
        # 4. Sentiment positif (15%)
        sentiment = self.analyze_sentiment(text)
        if sentiment['sentiment'] in ['positif', 'très positif']:
            score += 1.5
        elif sentiment['sentiment'] == 'neutre':
            score += 0.75
        
        # 5. Cohérence (20%)
        coherence = self.check_coherence(text)
        score += (coherence['score'] / 10) * 2.0
        
        # 6. Clarté (20%)
        clarity = self.check_clarity(text)
        score += (clarity['score'] / 10) * 2.0
        
        return round(min(score, 10), 1)

    # ================== Méthodes existantes améliorées ==================

    def suggest_improvements(self, text: str, content_type: str) -> List[str]:
        """Suggestions d'amélioration enrichies"""
        suggestions = []
        
        # Longueur
        if len(text) < 20:
            suggestions.append("📝 Texte trop court. Ajoutez plus de contexte et de détails.")
        elif len(text) > 2000:
            suggestions.append("✂️ Texte très long. Divisez en sections ou résumez les points clés.")
        
        # Structure
        if '.' not in text and len(text) > 50:
            suggestions.append("💬 Structurez avec de la ponctuation pour améliorer la lecture.")
        
        # Cohérence
        coherence = self.check_coherence(text)
        if coherence['score'] < 7:
            suggestions.extend([f"🔗 {issue}" for issue in coherence['issues'][:2]])
        
        # Clarté
        clarity = self.check_clarity(text)
        if clarity['score'] < 7:
            suggestions.extend([f"💡 {issue}" for issue in clarity['issues'][:2]])
        
        # Lisibilité
        readability = self.calculate_readability_score(text)
        if readability['score'] < 40:
            suggestions.append("📖 Simplifiez les phrases pour améliorer la lisibilité.")
        
        # Type spécifique
        type_hints = {
            'programme': ['chapitre', 'cours', 'module', 'semaine'],
            'echeance': ['date', 'rendu', 'deadline', 'soumission'],
            'difficulte': ['aide', 'problème', 'question', 'comprendre'],
            'ressource': ['lien', 'document', 'pdf', 'référence'],
            'annonce': ['important', 'note', 'attention', 'nouveau']
        }
        
        if content_type in type_hints:
            if not any(k in text.lower() for k in type_hints[content_type]):
                suggestions.append(f"📌 Ajoutez des mots-clés du type {content_type}: {', '.join(type_hints[content_type][:3])}")
        
        # Ton
        tone = self._check_tone(text, content_type)
        if tone:
            suggestions.append(tone)
        
        return suggestions[:7]  # Limiter à 7 suggestions max

    def adapt_tone(self, text: str, content_type: str) -> str:
        """Adapte le ton avec plus de sophistication"""
        adapted = text
        
        tone_prefixes = {
            'programme': '📚 Programme: ',
            'echeance': '📅 Échéance: ',
            'annonce': '📢 Annonce importante: ',
            'difficulte': '❓ Question: ',
            'ressource': '📖 Ressource utile: '
        }
        
        # Ajouter préfixe si absent
        prefix = tone_prefixes.get(content_type, '')
        if prefix and not any(adapted.startswith(p) for p in tone_prefixes.values()):
            adapted = prefix + adapted
        
        # Ajouter formules de politesse selon le type
        if content_type == 'echeance':
            if not any(word in adapted.lower() for word in ['merci', 'cordialement', 's\'il vous plaît']):
                adapted += "\n\n⏰ Merci de respecter cette échéance."
        
        elif content_type == 'annonce':
            if not adapted.endswith(('.', '!', '?')):
                adapted += "."
        
        elif content_type == 'difficulte':
            if '?' in adapted and not adapted.endswith('aide'):
                adapted += "\n\n💡 N'hésitez pas à demander de l'aide si besoin!"
        
        return adapted

    def _check_tone(self, text: str, content_type: str) -> str:
        """Vérifie l'adéquation du ton"""
        text_lower = text.lower()
        
        urgent_words = ['urgent', 'immédiat', 'vite', 'rapidement', 'asap']
        formal_words = ['veuillez', 'merci', 'cordialement', 's\'il vous plaît']
        casual_words = ['salut', 'coucou', 'hey', 'genre']
        
        has_urgent = any(w in text_lower for w in urgent_words)
        has_formal = any(w in text_lower for w in formal_words)
        has_casual = any(w in text_lower for w in casual_words)
        
        if content_type == 'programme' and has_urgent:
            return "⚠️ Ton urgent inapproprié pour un programme - utilisez un ton informatif."
        
        if content_type == 'echeance':
            if not has_formal:
                return "💼 Ajoutez une formule de politesse (merci, cordialement)."
            if has_casual:
                return "🎯 Évitez le ton trop familier pour une échéance."
        
        if content_type == 'annonce':
            if has_casual:
                return "📢 Ton trop familier - adoptez un ton professionnel."
            if not has_formal:
                return "✉️ Ajoutez une formule de politesse pour l'annonce."
        
        if content_type == 'ressource' and has_urgent:
            return "📚 Ton urgent inadapté pour une ressource - restez informatif."
        
        return ""

    # Méthodes utilitaires existantes conservées
    def detect_spam_likelihood(self, text: str) -> Dict:
        """Détection de spam enrichie"""
        spam_score = 0
        reasons = []
        
        # Majuscules excessives
        if text.isupper() and len(text) > 20:
            spam_score += 3
            reasons.append("Texte entièrement en MAJUSCULES")
        
        upper_ratio = sum(1 for c in text if c.isupper()) / len(text) if text else 0
        if upper_ratio > 0.5:
            spam_score += 2
            reasons.append("Trop de majuscules")
        
        # Ponctuation excessive
        exclamation_count = text.count('!')
        if exclamation_count > 5:
            spam_score += 2
            reasons.append(f"{exclamation_count} points d'exclamation")
        
        # Mots suspects
        spam_keywords = ['gratuit', 'argent facile', 'cliquez ici', 'promotion', 
                        'gagnez', 'offre limitée', 'urgent', 'maintenant']
        detected_spam = [w for w in spam_keywords if w in text.lower()]
        if detected_spam:
            spam_score += len(detected_spam) * 2
            reasons.append(f"Mots suspects: {', '.join(detected_spam[:3])}")
        
        # URLs suspectes multiples
        url_count = len(re.findall(r'https?://', text))
        if url_count > 3:
            spam_score += 2
            reasons.append(f"{url_count} URLs détectées")
        
        # Classification
        if spam_score >= 6:
            likelihood, color, is_spam = 'Très élevé', 'danger', True
        elif spam_score >= 4:
            likelihood, color, is_spam = 'Élevé', 'warning', True
        elif spam_score >= 2:
            likelihood, color, is_spam = 'Moyen', 'info', False
        else:
            likelihood, color, is_spam = 'Faible', 'success', False
        
        return {
            'is_spam': is_spam,
            'score': spam_score,
            'likelihood': likelihood,
            'color': color,
            'reasons': reasons
        }

    def auto_correct_common_errors(self, text: str) -> Dict:
        """Correction automatique enrichie"""
        original = text
        corrected = text
        corrections = []
        
        # Corrections orthographiques
        for pattern, replacement in self.common_errors.items():
            matches = list(re.finditer(pattern, corrected, re.IGNORECASE))
            for match in matches:
                corrected = corrected[:match.start()] + replacement + corrected[match.end():]
                corrections.append({
                    'original': match.group(),
                    'correction': replacement,
                    'reason': 'Orthographe',
                    'position': match.start()
                })
        
        # Espaces multiples
        if '  ' in corrected:
            corrected = re.sub(r'\s+', ' ', corrected)
            corrections.append({
                'original': 'Espaces multiples',
                'correction': 'Espace unique',
                'reason': 'Formatage'
            })
        
        # Espace avant ponctuation
        corrected = re.sub(r'\s+([,;:!?.])', r'\1', corrected)
        
        # Espace après ponctuation
        corrected = re.sub(r'([,;:!?.])([a-zA-Z])', r'\1 \2', corrected)
        
        return {
            'original': original,
            'corrected': corrected,
            'has_changes': original != corrected,
            'corrections': corrections,
            'count': len(corrections)
        }

    def suggest_title(self, description: str, content_type: str) -> List[str]:
        """Suggestions de titres enrichies"""
        suggestions = []
        
        type_prefixes = {
            'programme': ['📚 Programme', '📖 Cours', '🎓 Formation'],
            'echeance': ['📅 Échéance', '⏰ Deadline', '📆 À rendre'],
            'difficulte': ['❓ Question', '🤔 Aide', '🆘 Besoin d\'aide'],
            'ressource': ['📖 Ressource', '🔗 Document', '📚 Support'],
            'annonce': ['📢 Annonce', '🔔 Important', 'ℹ️ Information']
        }
        
        prefixes = type_prefixes.get(content_type, ['📝'])
        
        # Première phrase
        first_sentence = description.split('.')[0][:60].strip()
        if first_sentence:
            suggestions.append(f"{prefixes[0]}: {first_sentence}")
        
        # Mots-clés capitalisés
        keywords = re.findall(r'\b[A-ZÀ-Ÿ][a-zà-ÿ]+\b', description)
        if keywords:
            suggestions.append(f"{prefixes[1]}: {' '.join(keywords[:4])}")
        
        # Dates extraites
        dates = re.findall(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', description)
        if dates:
            suggestions.append(f"{prefixes[0]}: Échéance {dates[0]}")
        
        # Mots importants (> 6 caractères)
        important_words = [w for w in description.split() if len(w) > 6 and w[0].isupper()]
        if important_words:
            suggestions.append(f"{prefixes[2] if len(prefixes) > 2 else prefixes[0]}: {' '.join(important_words[:3])}")
        
        return suggestions[:4]

    def predict_engagement(self, text: str, content_type: str) -> Dict:
        """Prédit le niveau d'engagement potentiel basé sur des heuristiques."""
        engagement_score = 0.0
        
        # Facteur 1: Longueur du texte (plus long = plus engageant, jusqu'à un point)
        length = len(text)
        if length > 200:
            engagement_score += 2.0
        elif length > 100:
            engagement_score += 1.0
        
        # Facteur 2: Sentiment positif (encourage l'engagement)
        sentiment = self.analyze_sentiment(text)
        if sentiment['score'] > 0:
            engagement_score += 2.0
        elif sentiment['score'] < 0:
            engagement_score -= 1.0
        
        # Facteur 3: Lisibilité (texte facile à lire = plus engageant)
        readability = self.calculate_readability_score(text)['score']
        if readability > 60:
            engagement_score += 2.0
        elif readability > 40:
            engagement_score += 1.0
        
        # Facteur 4: Clarté (texte clair = plus engageant)
        clarity = self.check_clarity(text)['score']
        engagement_score += (clarity / 10) * 2.0  # Échelle à 0-2
        
        # Facteur 5: Cohérence (texte cohérent = plus engageant)
        coherence = self.check_coherence(text)['score']
        engagement_score += (coherence / 10) * 2.0  # Échelle à 0-2
        
        # Bonus pour certains types de contenu (ex: annonces ou questions attirent plus d'interactions)
        if content_type in ['annonce', 'difficulte']:
            engagement_score += 1.0
        
        # Normaliser le score (max 10)
        total_score = max(0.0, min(10.0, engagement_score))
        
        # Classification du niveau
        if total_score >= 7:
            level, emoji = 'Élevé', '🔥'
        elif total_score >= 4:
            level, emoji = 'Moyen', '👍'
        else:
            level, emoji = 'Faible', '😴'
        
        return {
            'level': level,
            'emoji': emoji,
            'score': round(total_score, 1),
            'factors': ['length', 'sentiment', 'readability', 'clarity', 'coherence', 'content_type'],
            'method': 'heuristic'
        }


class AIContentEnricher:
    """Service d'enrichissement automatique amélioré"""
    
    def __init__(self):
        self.french_months = {
            'janvier': 1, 'février': 2, 'fevrier': 2, 'mars': 3, 'avril': 4,
            'mai': 5, 'juin': 6, 'juillet': 7, 'août': 8, 'aout': 8,
            'septembre': 9, 'octobre': 10, 'novembre': 11, 'décembre': 12, 'decembre': 12
        }
    
    def extract_dates(self, text: str) -> List[Dict]:
        """Extraction de dates enrichie"""
        dates = []
        
        # Pattern 1: Format numérique (dd/mm/yyyy, dd-mm-yyyy)
        numeric_pattern = r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b'
        for match in re.finditer(numeric_pattern, text):
            parsed = self._parse_date(match.group())
            if parsed:
                dates.append({
                    'text': match.group(),
                    'position': match.start(),
                    'parsed_date': parsed,
                    'type': 'numeric',
                    'formatted': parsed.strftime('%d/%m/%Y'),
                    'relative': self._get_relative_time(parsed)
                })
        
        # Pattern 2: Format textuel (dd mois yyyy)
        textual_pattern = r'\b(\d{1,2})\s+(janvier|février|fevrier|mars|avril|mai|juin|juillet|août|aout|septembre|octobre|novembre|décembre|decembre)\s+(\d{4})\b'
        for match in re.finditer(textual_pattern, text, re.IGNORECASE):
            parsed = self._parse_date(match.group())
            if parsed:
                dates.append({
                    'text': match.group(),
                    'position': match.start(),
                    'parsed_date': parsed,
                    'type': 'textual',
                    'formatted': parsed.strftime('%d/%m/%Y'),
                    'relative': self._get_relative_time(parsed)
                })
        
        # Pattern 3: Dates relatives (aujourd'hui, demain, etc.)
        relative_dates = {
            r'\baujourd\'?hui\b': 0,
            r'\bdemain\b': 1,
            r'\baprès-demain\b': 2,
            r'\bhier\b': -1,
            r'\bavant-hier\b': -2,
        }
        
        for pattern, days_offset in relative_dates.items():
            if re.search(pattern, text, re.IGNORECASE):
                date_obj = datetime.utcnow() + timedelta(days=days_offset)
                dates.append({
                    'text': re.search(pattern, text, re.IGNORECASE).group(),
                    'position': re.search(pattern, text, re.IGNORECASE).start(),
                    'parsed_date': date_obj,
                    'type': 'relative',
                    'formatted': date_obj.strftime('%d/%m/%Y'),
                    'relative': self._get_relative_time(date_obj)
                })
        
        # Pattern 4: Dans X jours/semaines
        future_pattern = r'dans\s+(\d+)\s+(jour|jours|semaine|semaines|mois)'
        for match in re.finditer(future_pattern, text, re.IGNORECASE):
            amount = int(match.group(1))
            unit = match.group(2).lower()
            
            if 'jour' in unit:
                days = amount
            elif 'semaine' in unit:
                days = amount * 7
            elif 'mois' in unit:
                days = amount * 30
            else:
                days = 0
            
            date_obj = datetime.utcnow() + timedelta(days=days)
            dates.append({
                'text': match.group(),
                'position': match.start(),
                'parsed_date': date_obj,
                'type': 'future',
                'formatted': date_obj.strftime('%d/%m/%Y'),
                'relative': self._get_relative_time(date_obj)
            })
        
        return sorted(dates, key=lambda x: x['position'])
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse une date avec gestion d'erreurs"""
        try:
            # Format numérique
            numeric_match = re.match(r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})', date_str)
            if numeric_match:
                day = int(numeric_match.group(1))
                month = int(numeric_match.group(2))
                year = int(numeric_match.group(3))
                
                if year < 100:
                    year += 2000
                
                if 1 <= month <= 12 and 1 <= day <= 31:
                    return datetime(year, month, day)
            
            # Format textuel
            for month_name, month_num in self.french_months.items():
                if month_name in date_str.lower():
                    numbers = re.findall(r'\d+', date_str)
                    if len(numbers) >= 2:
                        day = int(numbers[0])
                        year = int(numbers[1])
                        if 1 <= day <= 31:
                            return datetime(year, month_num, day)
        except:
            pass
        
        return None
    
    def _get_relative_time(self, date: datetime) -> str:
        """Retourne le temps relatif (dans X jours)"""
        now = datetime.utcnow()
        delta = date - now
        days = delta.days
        
        if days < 0:
            return f"Il y a {abs(days)} jour(s)"
        elif days == 0:
            return "Aujourd'hui"
        elif days == 1:
            return "Demain"
        elif days == 2:
            return "Après-demain"
        elif days < 7:
            return f"Dans {days} jours"
        elif days < 30:
            weeks = days // 7
            return f"Dans {weeks} semaine(s)"
        else:
            months = days // 30
            return f"Dans {months} mois"
    
    def suggest_resources(self, text: str, content_type: str) -> List[str]:
        """Suggestions de ressources enrichies"""
        base_resources = {
            'difficulte': [
                "💡 Tutoriels YouTube sur le sujet",
                "📖 Documentation officielle",
                "👥 Forum d'entraide",
                "📧 Contacter un tuteur",
                "🎓 Cours en ligne (MOOC)"
            ],
            'programme': [
                "📚 Supports de cours",
                "📝 Exercices pratiques",
                "🎥 Vidéos explicatives",
                "📊 Fiches de révision",
                "🧪 Travaux pratiques"
            ],
            'ressource': [
                "🔖 Ajouter aux favoris",
                "📤 Partager avec d'autres",
                "💾 Télécharger le document",
                "📋 Créer une fiche résumé",
                "🔗 Lien vers ressources similaires"
            ],
            'echeance': [
                "⏰ Ajouter un rappel",
                "📅 Synchroniser le calendrier",
                "✅ Créer une checklist",
                "📧 Notification par email",
                "⏱️ Planifier des sessions de travail"
            ],
            'annonce': [
                "📧 Envoyer par email",
                "📌 Épingler l'annonce",
                "🔔 Activer les notifications",
                "💬 Ouvrir une discussion",
                "📱 Partager sur les réseaux"
            ]
        }
        
        # Ressources contextuelles basées sur les mots-clés
        contextual = []
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['code', 'programmation', 'développement']):
            contextual.append("💻 IDE en ligne (Replit, CodePen)")
        
        if any(word in text_lower for word in ['mathématiques', 'calcul', 'équation']):
            contextual.append("🔢 Calculatrice scientifique")
        
        if any(word in text_lower for word in ['présentation', 'exposé', 'diaporama']):
            contextual.append("🎨 Templates de présentation")
        
        if any(word in text_lower for word in ['rapport', 'mémoire', 'document']):
            contextual.append("📄 Modèles de documents")
        
        resources = base_resources.get(content_type, [])
        return (resources + contextual)[:6]
    
    def extract_action_items(self, text: str) -> List[Dict]:
        """Extraction d'actions enrichie"""
        action_items = []
        
        # Pattern 1: Verbes d'action explicites
        action_patterns = [
            (r'(?:il faut|faut|devez|devons|doit)\s+([^.!?]+)', 'high'),
            (r'(?:rendre|soumettre|livrer|envoyer)\s+([^.!?]+)', 'high'),
            (r'(?:préparer|réviser|étudier|lire)\s+([^.!?]+)', 'medium'),
            (r'(?:vérifier|consulter|regarder)\s+([^.!?]+)', 'low'),
            (r'(?:ne pas oublier|pensez à|n\'oubliez pas)\s+([^.!?]+)', 'high'),
        ]
        
        for pattern, priority in action_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                action = match.group(1).strip()
                
                # Ajuster la priorité selon les mots-clés
                if any(word in action.lower() for word in ['urgent', 'immédiat', 'vite']):
                    priority = 'high'
                
                action_items.append({
                    'action': action,
                    'priority': priority,
                    'type': 'extracted',
                    'position': match.start()
                })
        
        # Pattern 2: Points numérotés ou à puces
        list_pattern = r'(?:^|\n)\s*[\d\-•]\s*([^.\n]+)'
        for match in re.finditer(list_pattern, text):
            action_items.append({
                'action': match.group(1).strip(),
                'priority': 'normal',
                'type': 'list_item',
                'position': match.start()
            })
        
        # Dédupliquer et limiter
        unique_actions = []
        seen = set()
        for item in action_items:
            action_lower = item['action'].lower()
            if action_lower not in seen and len(action_lower) > 5:
                seen.add(action_lower)
                unique_actions.append(item)
        
        return sorted(unique_actions, key=lambda x: {'high': 0, 'medium': 1, 'normal': 2, 'low': 3}[x['priority']])[:8]
    
    def suggest_tags(self, text: str, content_type: str, max_tags: int = 5) -> List[str]:
        """Suggestions de tags enrichies"""
        tags = set()
        
        # Tags par défaut selon le type
        default_tags = {
            'programme': ['cours', 'programme', 'formation'],
            'echeance': ['deadline', 'échéance', 'rendu'],
            'difficulte': ['aide', 'question', 'support'],
            'ressource': ['ressource', 'document', 'référence'],
            'annonce': ['annonce', 'info', 'important']
        }
        tags.update(default_tags.get(content_type, []))
        
        # Mots capitalisés (noms propres, concepts)
        capitalized = re.findall(r'\b[A-ZÀ-Ÿ][a-zà-ÿ]{3,}\b', text)
        tags.update(word.lower() for word in capitalized[:3])
        
        # Mots fréquents (> 5 caractères, répétés)
        words = [w.lower() for w in re.findall(r'\b\w{5,}\b', text)]
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        frequent = [w for w, c in word_freq.items() if c >= 2]
        tags.update(frequent[:2])
        
        # Tags contextuels
        context_keywords = {
            'mathématiques': ['maths', 'calcul', 'équation'],
            'informatique': ['code', 'programmation', 'développement'],
            'langue': ['français', 'anglais', 'grammaire'],
            'sciences': ['physique', 'chimie', 'biologie'],
            'histoire': ['historique', 'date', 'événement'],
        }
        
        text_lower = text.lower()
        for tag, keywords in context_keywords.items():
            if any(kw in text_lower for kw in keywords):
                tags.add(tag)
        
        # Filtrer et limiter
        filtered_tags = [t for t in tags if 3 <= len(t) <= 20]
        return filtered_tags[:max_tags]
    
    def detect_urgency_level(self, text: str, deadline: Optional[datetime]) -> Dict:
        """Détection d'urgence enrichie"""
        urgency_score = 0
        reasons = []
        
        # Mots-clés d'urgence
        urgency_keywords = {
            'critique': 5, 'urgent': 4, 'immédiat': 4, 'asap': 4,
            'rapidement': 3, 'vite': 3, 'bientôt': 2,
            'important': 2, 'prioritaire': 3, 'essentiel': 2
        }
        
        text_lower = text.lower()
        for keyword, score in urgency_keywords.items():
            if keyword in text_lower:
                urgency_score += score
                reasons.append(f"Mot-clé: '{keyword}' (+{score})")
        
        # Ponctuation insistante
        exclamation_count = text.count('!')
        if exclamation_count >= 3:
            urgency_score += 2
            reasons.append(f"{exclamation_count} points d'exclamation")
        
        # Deadline proche
        if deadline:
            try:
                now = datetime.utcnow()
                delta = deadline - now
                days_left = delta.days
                hours_left = delta.seconds // 3600
                
                if days_left < 0:
                    urgency_score += 10
                    reasons.append("⚠️ Échéance dépassée!")
                elif days_left == 0:
                    urgency_score += 8
                    reasons.append(f"Aujourd'hui ({hours_left}h restantes)")
                elif days_left == 1:
                    urgency_score += 6
                    reasons.append("Demain")
                elif days_left <= 3:
                    urgency_score += 4
                    reasons.append(f"Dans {days_left} jours")
                elif days_left <= 7:
                    urgency_score += 2
                    reasons.append(f"Cette semaine ({days_left}j)")
            except:
                pass
        
        # Classification enrichie
        if urgency_score >= 10:
            level, emoji, color = 'Critique', '🔴', 'danger'
        elif urgency_score >= 6:
            level, emoji, color = 'Très élevé', '🟠', 'warning'
        elif urgency_score >= 4:
            level, emoji, color = 'Élevé', '🟡', 'warning'
        elif urgency_score >= 2:
            level, emoji, color = 'Moyen', '🔵', 'info'
        else:
            level, emoji, color = 'Normal', '🟢', 'success'
        
        return {
            'level': level,
            'emoji': emoji,
            'color': color,
            'score': urgency_score,
            'reasons': reasons,
            'percentage': min(100, urgency_score * 10)
        }


class AIRecurringContentGenerator:
    """Génération de contenu récurrent améliorée"""
    
    @staticmethod
    def generate_deadline_reminder(feed_item) -> Optional[Dict]:
        """Génère un rappel d'échéance enrichi"""
        if not feed_item.deadline:
            return None
        
        now = datetime.utcnow()
        delta = feed_item.deadline - now
        days_left = delta.days
        hours_left = delta.seconds // 3600
        
        # Messages personnalisés selon l'urgence
        if days_left < 0:
            urgency = "🚨 URGENT - ÉCHÉANCE DÉPASSÉE"
            message = f"⚠️ L'échéance '{feed_item.title}' était le {feed_item.deadline.strftime('%d/%m/%Y')}.\n\nAction immédiate requise !"
            priority = 'critical'
        elif days_left == 0:
            urgency = "⏰ AUJOURD'HUI"
            message = f"🔴 Dernier jour pour '{feed_item.title}'!\n\nIl reste environ {hours_left}h.\n\nDépêchez-vous de finaliser."
            priority = 'high'
        elif days_left == 1:
            urgency = "⚠️ DEMAIN"
            message = f"🟠 '{feed_item.title}' est à rendre demain.\n\nVérifiez que tout est prêt."
            priority = 'high'
        elif days_left <= 3:
            urgency = "📌 RAPPEL IMPORTANT"
            message = f"🟡 Plus que {days_left} jours pour '{feed_item.title}'.\n\nPlanifiez votre temps efficacement."
            priority = 'medium'
        elif days_left <= 7:
            urgency = "📅 RAPPEL"
            message = f"🔵 '{feed_item.title}' approche ({days_left} jours).\n\nCommencez à vous organiser."
            priority = 'low'
        else:
            return None  # Pas de rappel si > 7 jours
        
        return {
            'title': f"{urgency} - {feed_item.title}",
            'description': f"{message}\n\n📝 Description originale:\n{feed_item.description[:200]}...",
            'content_type': 'annonce',
            'deadline': feed_item.deadline,
            'is_ai_generated': True,
            'ai_tone': 'urgent',
            'ai_quality_score': 8.5,
            'priority': priority
        }
    
    @staticmethod
    def generate_weekly_summary(feed_items: List) -> Optional[Dict]:
        """Génère un résumé hebdomadaire enrichi"""
        if not feed_items:
            return None
        
        total = len(feed_items)
        by_type = {}
        by_author = {}
        
        for item in feed_items:
            # Par type
            by_type[item.content_type] = by_type.get(item.content_type, 0) + 1
            # Par auteur
            author_name = item.get_author_username()
            by_author[author_name] = by_author.get(author_name, 0) + 1
        
        # Construction du résumé
        summary = f"📊 **Résumé de la semaine du {datetime.now().strftime('%d/%m/%Y')}**\n\n"
        summary += f"📈 **Statistiques globales:**\n"
        summary += f"• Total de publications: **{total}**\n"
        summary += f"• Contributeurs actifs: **{len(by_author)}**\n\n"
        
        # Par type
        summary += f"📚 **Répartition par type:**\n"
        emojis = {
            'programme': '📚', 'echeance': '📅', 'difficulte': '🤔',
            'ressource': '📖', 'annonce': '📢'
        }
        for ctype, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total) * 100
            summary += f"{emojis.get(ctype, '•')} {ctype.capitalize()}: **{count}** ({percentage:.0f}%)\n"
        
        # Prochaines échéances
        upcoming = [i for i in feed_items if i.deadline and i.deadline > datetime.utcnow()]
        if upcoming:
            summary += f"\n⏰ **Prochaines échéances ({len(upcoming)}):**\n"
            for item in sorted(upcoming, key=lambda x: x.deadline)[:5]:
                days = (item.deadline - datetime.utcnow()).days
                summary += f"• **{item.title}** - {days}j\n"
        
        # Top contributeurs
        if len(by_author) > 1:
            summary += f"\n🏆 **Top contributeurs:**\n"
            for author, count in sorted(by_author.items(), key=lambda x: x[1], reverse=True)[:3]:
                summary += f"• {author}: {count} publication(s)\n"
        
        summary += f"\n✨ *Résumé généré automatiquement par l'IA*"
        
        return {
            'title': f"📊 Résumé hebdomadaire - {datetime.now().strftime('%d/%m/%Y')}",
            'description': summary,
            'content_type': 'annonce',
            'is_ai_generated': True,
            'ai_tone': 'informatif',
            'ai_quality_score': 9.0
        }
    
    @staticmethod
    def detect_missing_content(feed_items: List, days: int = 7) -> List[str]:
        """Détecte les contenus manquants avec suggestions"""
        recent = datetime.utcnow() - timedelta(days=days)
        recent_items = [i for i in feed_items if i.created_at >= recent]
        
        existing_types = set(i.content_type for i in recent_items)
        all_types = {'programme', 'echeance', 'difficulte', 'ressource', 'annonce'}
        missing_types = all_types - existing_types
        
        suggestions = {
            'programme': "📚 Aucun programme publié. Suggestion: Partagez le planning des prochains cours.",
            'echeance': "📅 Aucune échéance définie. Suggestion: Ajoutez les dates de rendus importants.",
            'ressource': "📖 Aucune ressource partagée. Suggestion: Partagez des documents utiles.",
            'difficulte': "🤔 Aucune question signalée. Suggestion: Encouragez les étudiants à poser leurs questions.",
            'annonce': "📢 Aucune annonce publiée. Suggestion: Communiquez les informations importantes."
        }
        
        messages = [suggestions.get(ctype, f"Contenu manquant: {ctype}") for ctype in missing_types]
        
        # Statistiques supplémentaires
        if recent_items:
            avg_per_day = len(recent_items) / days
            if avg_per_day < 1:
                messages.append(f"⚠️ Activité faible: {avg_per_day:.1f} publication(s)/jour en moyenne.")
        else:
            messages.append("⚠️ Aucune activité sur les 7 derniers jours!")
        
        return messages
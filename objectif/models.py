from mongoengine import (
    Document, StringField, DateTimeField, ListField,
    FloatField, IntField, BooleanField
)
from datetime import datetime
import os
import json
import requests
from django.utils import timezone

class Objective(Document):
    # 🔹 Relation avec l’utilisateur Django/Mongo
    user_id = StringField(required=True)

    # 🔹 Champs principaux
    titre = StringField(required=True)
    description = StringField()
    filiere = StringField(required=True)
    niveau = StringField(required=True)

    # 🔹 Gestion de l'état
    priorite = StringField(choices=['haute', 'moyenne', 'basse'], default='moyenne')
    etat = StringField(choices=['non commencé', 'en cours', 'terminé'], default='non commencé')

    # 🔹 Suivi du temps
    date_creation = DateTimeField(default=datetime.utcnow)
    date_debut = DateTimeField(default=None)
    date_echeance = DateTimeField(default=None)
    derniere_mise_a_jour = DateTimeField(default=datetime.utcnow)

    # 🔹 Données de progression
    progression = FloatField(default=0.0)
    nb_sessions = IntField(default=0)
    temps_total = FloatField(default=0.0)

    # 🔹 Liens et IA
    taches = ListField(StringField())
    ressources = ListField(StringField())
    tags = ListField(StringField())
    suggestion_ia = StringField()
    score_priorite_ia = FloatField(default=0.0)
    objectif_recommande = BooleanField(default=False)

    # 🔹 Nouveaux champs pour l'analyse IA détaillée
    analyse_ia = StringField()  # Analyse complète de l'IA
    points_forts = ListField(StringField())  # Points forts identifiés par l'IA
    points_amelioration = ListField(StringField())  
    risques = ListField(StringField())  # Risques identifiés
    recommendations = ListField(StringField())  # Recommandations spécifiques
    delai_realisme = StringField()  # Évaluation du réalisme des délais
    niveau_difficulte = StringField(choices=['facile', 'moyen', 'difficile', 'expert'])  # Niveau de difficulté estimé

    meta = {
        'collection': 'objectifs',
        'ordering': ['-date_creation'],
        'indexes': ['user_id', 'etat', 'priorite']
    }

    def generate_ia_suggestion(self):
        """Génère une suggestion IA basique"""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return

        prompt = f"""
        Tu es un assistant expert en gestion d'objectifs. 
        Voici les informations de l'objectif :
        Titre : {self.titre}
        Description : {self.description}
        Tags : {', '.join(self.tags)}
        Progression actuelle : {self.progression}%
        Priorité actuelle : {self.priorite}

        Propose :
        1. Une suggestion concrète pour l'utilisateur pour faire progresser cet objectif.
        2. Un score de priorité entre 0 et 1.
        3. Indique si cet objectif devrait être recommandé maintenant (true/false).
        
        Réponds au format JSON :
        {{
          "suggestion": "...",
          "score_priorite": 0.0,
          "recommande": true/false
        }}
        """

        endpoint = "https://api.generativelanguage.googleapis.com/v1/models/gemini-2.5-flash-lite:generateContent"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": api_key
        }
        data = {
            "prompt": {"text": prompt},
            "model": "gemini-2.0-flash-lite",
            "temperature": 0.7,
            "maxOutputTokens": 150
        }

        resp = requests.post(endpoint, json=data, headers=headers)
        if resp.status_code != 200:
            return

        resp_json = resp.json()
        text = resp_json.get("candidates", [{}])[0].get("output", "")
        try:
            result = json.loads(text)
            self.suggestion_ia = result.get("suggestion", "")
            self.score_priorite_ia = result.get("score_priorite", 0.0)
            self.objectif_recommande = result.get("recommande", False)
        except json.JSONDecodeError:
            self.suggestion_ia = text
            self.score_priorite_ia = 0.5
            self.objectif_recommande = False

        self.derniere_mise_a_jour = datetime.utcnow()
        self.save()

    def generate_complete_ia_analysis(self):
        """Génère une analyse IA complète et détaillée"""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return

        # Préparer les données pour l'analyse
        jours_restants = ""
        if self.date_echeance:
            aujourd_hui = timezone.now().date()
            if hasattr(self.date_echeance, 'date'):
                date_echeance = self.date_echeance.date()
            else:
                date_echeance = self.date_echeance
            jours_restants = (date_echeance - aujourd_hui).days

        prompt = f"""
        Tu es un expert en analyse d'objectifs académiques et professionnels.
        
        OBJECTIF À ANALYSER :
        - Titre : {self.titre}
        - Description : {self.description}
        - Filière : {self.filiere}
        - Niveau : {self.niveau}
        - Priorité : {self.priorite}
        - État : {self.etat}
        - Progression : {self.progression}%
        - Tags : {', '.join(self.tags)}
        - Tâches prévues : {', '.join(self.taches)}
        - Ressources : {', '.join(self.ressources)}
        - Jours restants : {jours_restants if jours_restants else 'Non défini'}

        EFFECTUE UNE ANALYSE COMPLÈTE ET RÉPONDS STRICTEMENT EN JSON :

        {{
            "analyse_ia": "Analyse textuelle complète de 3-4 phrases",
            "points_forts": ["point 1", "point 2", "point 3"],
            "points_amelioration": ["point 1", "point 2", "point 3"], 
            "risques": ["risque 1", "risque 2"],
            "recommendations": ["reco 1", "reco 2", "reco 3"],
            "delai_realisme": "Très réaliste|Réaliste|Peu réaliste|Irrealiste",
            "niveau_difficulte": "facile|moyen|difficile|expert",
            "suggestion_ia": "Suggestion concise pour l'utilisateur",
            "score_priorite_ia": 0.85,
            "objectif_recommande": true
        }}

        Sois honnête, constructif et précis dans ton analyse.
        """

        endpoint = "https://api.generativelanguage.googleapis.com/v1/models/gemini-2.5-flash-lite:generateContent"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": api_key
        }
        data = {
            "prompt": {"text": prompt},
            "model": "gemini-2.0-flash-lite", 
            "temperature": 0.3,
            "maxOutputTokens": 800
        }

        try:
            resp = requests.post(endpoint, json=data, headers=headers)
            if resp.status_code == 200:
                resp_json = resp.json()
                text = resp_json.get("candidates", [{}])[0].get("output", "")
                
                # Nettoyer la réponse
                text = text.strip()
                if text.startswith("```json"):
                    text = text[7:]
                if text.endswith("```"):
                    text = text[:-3]
                
                result = json.loads(text)
                
                # Mettre à jour tous les champs
                self.analyse_ia = result.get("analyse_ia", "")
                self.points_forts = result.get("points_forts", [])
                self.points_amelioration = result.get("points_amelioration", [])
                self.risques = result.get("risques", [])
                self.recommendations = result.get("recommendations", [])
                self.delai_realisme = result.get("delai_realisme", "")
                self.niveau_difficulte = result.get("niveau_difficulte", "moyen")
                self.suggestion_ia = result.get("suggestion_ia", "")
                self.score_priorite_ia = result.get("score_priorite_ia", 0.5)
                self.objectif_recommande = result.get("objectif_recommande", False)
                
                self.derniere_mise_a_jour = datetime.utcnow()
                self.save()
                
                return True
                
        except Exception as e:
            print(f"Erreur lors de l'analyse IA: {e}")
            return False

    def __str__(self):
        return f"{self.titre} ({self.etat})"    
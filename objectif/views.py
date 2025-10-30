from pyexpat.errors import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from objectif.utils import _get_mongo_user
from .models import Objective
from .forms import ObjectiveForm
import google.generativeai as genai
from django.http import HttpResponse, JsonResponse

import qrcode
import io
import json
import datetime

from django.utils import timezone
from bson import ObjectId
import os
import requests

# Import pour le PDF
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

genai.configure(api_key="AIzaSyBCutcN7kxoQ8frc9GHPGXlBMneulZCHzc")

# =============================================================================
# NOUVELLES FONCTIONS DE CALCUL DES ATTRIBUTS
# =============================================================================

def calculer_progression_par_dates(obj):
    """Calcule la progression basée sur les dates (début et échéance)"""
    if not getattr(obj, 'date_debut', None) or not getattr(obj, 'date_echeance', None):
        return 0
    
    aujourd_hui = timezone.now().date()
    
    # Convertir en date si c'est un datetime
    date_debut = obj.date_debut.date() if hasattr(obj.date_debut, 'date') else obj.date_debut
    date_echeance = obj.date_echeance.date() if hasattr(obj.date_echeance, 'date') else obj.date_echeance
    
    # Si pas encore commencé
    if aujourd_hui < date_debut:
        return 0
    
    # Si échéance dépassée
    if aujourd_hui > date_echeance:
        return 100
    
    # Calcul du pourcentage de temps écoulé
    duree_totale = (date_echeance - date_debut).days
    temps_ecoule = (aujourd_hui - date_debut).days
    
    if duree_totale > 0:
        progression_temporelle = int((temps_ecoule / duree_totale) * 100)
        return min(progression_temporelle, 100)
    
    return 0

def calculer_progression_par_etat(obj):
    """Calcule la progression basée sur l'état de l'objectif"""
    etat = getattr(obj, 'etat', 'en attente')
    
    if etat == 'terminé':
        return 100
    elif etat == 'en cours':
        return 50  # Valeur intermédiaire
    elif etat == 'en attente':
        return 10  # Juste commencé
    else:
        return 0

def calculer_progression_par_priorite(obj):
    """Calcule la progression basée sur la priorité et le temps écoulé"""
    priorite = getattr(obj, 'priorite', 'moyenne')
    facteur_priorite = {
        'haute': 1.3,   # Avance plus vite
        'moyenne': 1.0, # Vitesse normale
        'basse': 0.7    # Avance plus lentement
    }.get(priorite, 1.0)
    
    progression_base = calculer_progression_par_dates(obj)
    return min(int(progression_base * facteur_priorite), 100)

def calculer_progression_par_taches(obj):
    """Calcule la progression basée sur le nombre de tâches"""
    taches = getattr(obj, 'taches', [])
    if not taches:
        return 0
    
    # Plus de tâches = progression potentiellement plus lente
    facteur_complexite = min(len(taches) / 10, 2.0)
    
    progression_base = calculer_progression_par_dates(obj)
    if facteur_complexite > 0:
        progression_ajustee = progression_base / facteur_complexite
        return min(int(progression_ajustee), 100)
    
    return progression_base

def calculer_progression_intelligente(obj):
    """Calcule la progression en combinant plusieurs méthodes"""
    methodes = [
        calculer_progression_par_dates(obj),
        calculer_progression_par_etat(obj),
        calculer_progression_par_priorite(obj),
        calculer_progression_par_taches(obj)
    ]
    
    # Poids différents pour chaque méthode
    poids = [0.4, 0.3, 0.2, 0.1]  # Dates + État + Priorité + Tâches
    
    progression_ponderee = sum(methode * poids for methode, poids in zip(methodes, poids))
    
    # Ajustement basé sur la dernière mise à jour
    derniere_maj = getattr(obj, 'derniere_mise_a_jour', None)
    if derniere_maj:
        jours_depuis_maj = (timezone.now().date() - derniere_maj.date()).days
        if jours_depuis_maj > 7:  # Si pas de mise à jour depuis une semaine
            progression_ponderee *= 0.9  # Légère pénalité
    
    return min(int(progression_ponderee), 100)

def calculer_progression_automatique(obj):
    """Calcule la progression basée sur les données disponibles"""
    # Si progression manuelle existe, on l'utilise en priorité
    progression_manuelle = getattr(obj, 'progression', 0)
    if progression_manuelle > 0:
        return progression_manuelle
    
    # Sinon, calcul intelligent basé sur les données disponibles
    return calculer_progression_intelligente(obj)

def calculer_temps_total_automatique(obj):
    """Calcule le temps total basé sur la durée de l'objectif"""
    if not getattr(obj, 'date_debut', None) or not getattr(obj, 'date_echeance', None):
        return getattr(obj, 'temps_total', 0)
    
    # Convertir en date si c'est un datetime
    date_debut = obj.date_debut.date() if hasattr(obj.date_debut, 'date') else obj.date_debut
    date_echeance = obj.date_echeance.date() if hasattr(obj.date_echeance, 'date') else obj.date_echeance
    
    duree_jours = (date_echeance - date_debut).days
    
    # Estimation : 2 heures de travail par jour en moyenne
    temps_estime = round(duree_jours * 2, 1)
    return max(temps_estime, getattr(obj, 'temps_total', 0))

def calculer_nb_sessions_automatique(obj):
    """Estime le nombre de sessions basé sur la durée"""
    temps_total = calculer_temps_total_automatique(obj)
    
    # Estimation : sessions de 1.5 heures en moyenne
    if temps_total > 0:
        return max(int(temps_total / 1.5), getattr(obj, 'nb_sessions', 1))
    
    return getattr(obj, 'nb_sessions', 1)

def calculer_jours_restants(obj):
    """Calcule les jours restants jusqu'à l'échéance"""
    if not getattr(obj, 'date_echeance', None):
        return "-"
    
    aujourd_hui = timezone.now().date()
    date_echeance = obj.date_echeance
    
    # Convertir en date si c'est un datetime
    if hasattr(date_echeance, 'date'):
        date_echeance = date_echeance.date()
    
    if date_echeance < aujourd_hui:
        return "Dépassé"
    
    jours_restants = (date_echeance - aujourd_hui).days
    return jours_restants

def calculer_efficacite(obj, progression, temps_total):
    """Calcule l'efficacité (progression par heure)"""
    if temps_total == 0 or progression == 0:
        return "N/A"
    
    efficacite = progression / temps_total if temps_total > 0 else 0
    
    if efficacite > 3:
        return "🚀 Excellente"
    elif efficacite > 1.5:
        return "👍 Bonne"
    elif efficacite > 0.5:
        return "📊 Moyenne"
    else:
        return "🐌 Faible"

def calculer_tous_les_attributs(obj):
    """Calcule tous les attributs automatiques d'un objectif"""
    progression = calculer_progression_automatique(obj)
    temps_total = calculer_temps_total_automatique(obj)
    nb_sessions = calculer_nb_sessions_automatique(obj)
    jours_restants = calculer_jours_restants(obj)
    efficacite = calculer_efficacite(obj, progression, temps_total)
    
    return {
        'progression': progression,
        'temps_total': temps_total,
        'nb_sessions': nb_sessions,
        'jours_restants': jours_restants,
        'efficacite': efficacite
    }

# =============================================================================
# VUES EXISTANTES (AVEC NOUVELLES FONCTIONS DE CALCUL)
# =============================================================================

@login_required
def list_objectif(request):
    # 🔹 Filtrer par user connecté
    objectifs = Objective.objects(user_id=str(request.user.id))
    return render(request, "objectif/list.html", {"objectifs": objectifs})

@login_required
def create_objectif(request):
    if request.method == "POST":
        form = ObjectiveForm(request.POST)
        if form.is_valid():
            obj = Objective(
                user_id=str(request.user.id),
                **form.cleaned_data
            )
            obj.save()
            return redirect("objectif:list")
    else:
        form = ObjectiveForm()
    return render(request, "objectif/form.html", {"form": form, "title": "Créer un objectif"})

@login_required
def update_objectif(request, id):
    objectif = Objective.objects.get(id=id, user_id=str(request.user.id))
    if request.method == "POST":
        form = ObjectiveForm(request.POST)
        if form.is_valid():
            for key, value in form.cleaned_data.items():
                setattr(objectif, key, value)
            objectif.derniere_mise_a_jour = datetime.datetime.utcnow()
            objectif.save()
            return redirect("objectif:list")
    else:
        initial = {
            "titre": objectif.titre,
            "description": objectif.description,
            "filiere": objectif.filiere,
            "niveau": objectif.niveau,
            "priorite": objectif.priorite,
            "etat": objectif.etat,
            "date_debut": objectif.date_debut,
            "date_echeance": objectif.date_echeance,
        }
        form = ObjectiveForm(initial=initial)
    return render(request, "objectif/form.html", {"form": form, "title": "Modifier un objectif"})

@login_required
def delete_objectif(request, id):
    objectif = Objective.objects.get(id=id, user_id=str(request.user.id))
    if request.method == "POST":
        objectif.delete()
        return redirect("objectif:list")
    return render(request, "objectif/confirm_delete.html", {"objectif": objectif})

@login_required
def objective_details(request, obj_id):
    """Page de détails d'un objectif avec QR Code et Calendrier"""
    try:
        obj = Objective.objects.get(id=obj_id)
        
        # CALCUL DES ATTRIBUTS AUTOMATIQUES
        attributs_calcules = calculer_tous_les_attributs(obj)
        
        # Préparer les données pour l'affichage
        details = {
            'titre': getattr(obj, 'titre', 'Sans titre'),
            'description': getattr(obj, 'description', 'Aucune description'),
            'filiere': getattr(obj, 'filiere', 'Non spécifiée'),
            'niveau': getattr(obj, 'niveau', 'Non spécifié'),
            'priorite': getattr(obj, 'priorite', 'Non spécifié'),
            'etat': getattr(obj, 'etat', 'Non spécifié'),
            
            # ATTRIBUTS CALCULÉS AUTOMATIQUEMENT
            'progression': attributs_calcules['progression'],
            'nb_sessions': attributs_calcules['nb_sessions'],
            'temps_total': attributs_calcules['temps_total'],
            'jours_restants': attributs_calcules['jours_restants'],
            'efficacite': attributs_calcules['efficacite'],
            
            'date_creation': getattr(obj, 'date_creation', 'Non spécifiée'),
            'date_debut': getattr(obj, 'date_debut', 'Non spécifiée'),
            'date_echeance': getattr(obj, 'date_echeance', 'Non spécifiée'),
            'derniere_mise_a_jour': getattr(obj, 'derniere_mise_a_jour', 'Non spécifiée'),
            'taches': getattr(obj, 'taches', []),
            'ressources': getattr(obj, 'ressources', []),
            'tags': getattr(obj, 'tags', []),
            'suggestion_ia': getattr(obj, 'suggestion_ia', 'Aucune suggestion'),
            'score_priorite_ia': getattr(obj, 'score_priorite_ia', 0),
            'objectif_recommande': getattr(obj, 'objectif_recommande', False)
        }
        
        # Formater les dates
        for date_field in ['date_creation', 'date_debut', 'date_echeance', 'derniere_mise_a_jour']:
            if hasattr(obj, date_field) and getattr(obj, date_field):
                date_value = getattr(obj, date_field)
                if hasattr(date_value, 'strftime'):
                    details[date_field] = date_value.strftime("%d/%m/%Y %H:%M")
        
        # Données pour le calendrier
        calendar_data = generate_calendar_data(obj)
        
        context = {
            'objectif': obj,
            'details': details,
            'calendar_data': calendar_data,
            'today': timezone.now().date()
        }
        
        return render(request, 'objectif/details.html', context)
        
    except Objective.DoesNotExist:
        return HttpResponse("Objectif non trouvé", status=404)

def generate_calendar_data(obj):
    """Générer les données pour le calendrier avec gestion robuste des dates"""
    calendar_data = {
        'events': [],
        'timeline': [],
        'deadline_alert': None
    }
    
    # Date d'échéance
    if hasattr(obj, 'date_echeance') and obj.date_echeance:
        try:
            deadline = obj.date_echeance
            # Convertir en date si c'est un datetime
            if hasattr(deadline, 'date'):
                deadline_date = deadline.date()
            else:
                deadline_date = deadline
            
            calendar_data['events'].append({
                'date': deadline_date.isoformat(),
                'title': 'Échéance',
                'type': 'deadline',
                'description': f'Échéance: {obj.titre}'
            })
            
            # Alerte si échéance proche
            today = timezone.now().date()
            days_until_deadline = (deadline_date - today).days
            if days_until_deadline <= 7:
                calendar_data['deadline_alert'] = {
                    'days_left': days_until_deadline,
                    'is_urgent': days_until_deadline <= 3
                }
        except (TypeError, AttributeError) as e:
            print(f"Erreur traitement date échéance: {e}")
    
    # Date de début
    if hasattr(obj, 'date_debut') and obj.date_debut:
        try:
            start_date = obj.date_debut
            # Convertir en date si c'est un datetime
            if hasattr(start_date, 'date'):
                start_date_date = start_date.date()
            else:
                start_date_date = start_date
            
            calendar_data['events'].append({
                'date': start_date_date.isoformat(),
                'title': 'Début',
                'type': 'start',
                'description': f'Début: {obj.titre}'
            })
        except (TypeError, AttributeError) as e:
            print(f"Erreur traitement date début: {e}")
    
    # Générer une timeline basée sur la progression
    progression = getattr(obj, 'progression', 0)
    if progression > 0:
        calendar_data['timeline'].append({
            'date': timezone.now().date().isoformat(),
            'progress': progression,
            'description': f'Progression: {progression}%'
        })
    
    return calendar_data

@login_required
def objective_calendar(request):
    """Vue calendrier pour tous les objectifs"""
    all_objectifs = list(Objective.objects.all())
    
    calendar_events = []
    for obj in all_objectifs:
        # Échéance
        if hasattr(obj, 'date_echeance') and obj.date_echeance:
            deadline = obj.date_echeance
            if timezone.is_aware(deadline):
                deadline = deadline.date()
            
            calendar_events.append({
                'id': str(obj.id),
                'title': f'📅 {obj.titre}',
                'start': deadline.isoformat(),
                'end': deadline.isoformat(),
                'color': '#ff4444',
                'type': 'deadline',
                'url': f'/objectives/details/{obj.id}/'
            })
        
        # Date de début
        if hasattr(obj, 'date_debut') and obj.date_debut:
            start_date = obj.date_debut
            if timezone.is_aware(start_date):
                start_date = start_date.date()
            
            calendar_events.append({
                'id': str(obj.id) + '_start',
                'title': f'🚀 Début: {obj.titre}',
                'start': start_date.isoformat(),
                'end': start_date.isoformat(),
                'color': '#00aa00',
                'type': 'start',
                'url': f'/objectives/details/{obj.id}/'
            })
    
    context = {
        'calendar_events': json.dumps(calendar_events),
        'objectifs_count': len(all_objectifs)
    }
    
    return render(request, 'objectif/calendar.html', context)

@login_required
def calendar_events_api(request):
    """API pour les événements du calendrier"""
    all_objectifs = list(Objective.objects.all())
    
    events = []
    for obj in all_objectifs:
        # Échéance
        if hasattr(obj, 'date_echeance') and obj.date_echeance:
            deadline = obj.date_echeance
            if timezone.is_aware(deadline):
                deadline = deadline.date()
            
            events.append({
                'id': str(obj.id),
                'title': f'Échéance: {obj.titre}',
                'start': deadline.isoformat(),
                'end': deadline.isoformat(),
                'color': '#dc3545',
                'textColor': 'white',
                'url': f'/objectives/details/{obj.id}/'
            })
        
        # Date de début
        if hasattr(obj, 'date_debut') and obj.date_debut:
            start_date = obj.date_debut
            if timezone.is_aware(start_date):
                start_date = start_date.date()
            
            events.append({
                'id': str(obj.id) + '_start',
                'title': f'Début: {obj.titre}',
                'start': start_date.isoformat(),
                'end': start_date.isoformat(),
                'color': '#28a745',
                'textColor': 'white',
                'url': f'/objectives/details/{obj.id}/'
            })
    
    return JsonResponse(events, safe=False)

@login_required
def generate_qrcode(request, obj_id):
    """Générer un QR Code pour un objectif"""
    try:
        obj = Objective.objects.get(id=obj_id)
        
        # URL de détail de l'objectif
        detail_url = request.build_absolute_uri(f'/objectives/details/{obj_id}/')
        
        # Créer le QR Code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(detail_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Sauvegarder dans un buffer
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return HttpResponse(buffer.getvalue(), content_type='image/png')
        
    except Objective.DoesNotExist:
        return HttpResponse("Objectif non trouvé", status=404)

@login_required
def objective_details_ia(request, obj_id):
    """Page de détails d'un objectif avec analyse IA"""
    try:
        obj = Objective.objects.get(id=obj_id, user_id=str(request.user.id))
        
        # CALCUL DES ATTRIBUTS AUTOMATIQUES
        attributs_calcules = calculer_tous_les_attributs(obj)
        
        # Préparer les données pour l'affichage
        details = {
            'titre': getattr(obj, 'titre', 'Sans titre'),
            'description': getattr(obj, 'description', 'Aucune description'),
            'filiere': getattr(obj, 'filiere', 'Non spécifiée'),
            'niveau': getattr(obj, 'niveau', 'Non spécifié'),
            'priorite': getattr(obj, 'priorite', 'Non spécifié'),
            'etat': getattr(obj, 'etat', 'Non spécifié'),
            
            # ATTRIBUTS CALCULÉS AUTOMATIQUEMENT
            'progression': attributs_calcules['progression'],
            'nb_sessions': attributs_calcules['nb_sessions'],
            'temps_total': attributs_calcules['temps_total'],
            'jours_restants': attributs_calcules['jours_restants'],
            'efficacite': attributs_calcules['efficacite'],
            
            'date_creation': getattr(obj, 'date_creation', 'Non spécifiée'),
            'date_debut': getattr(obj, 'date_debut', 'Non spécifiée'),
            'date_echeance': getattr(obj, 'date_echeance', 'Non spécifiée'),
            'derniere_mise_a_jour': getattr(obj, 'derniere_mise_a_jour', 'Non spécifiée'),
            'taches': getattr(obj, 'taches', []),
            'ressources': getattr(obj, 'ressources', []),
            'tags': getattr(obj, 'tags', []),
            'suggestion_ia': getattr(obj, 'suggestion_ia', 'Aucune suggestion'),
            'score_priorite_ia': getattr(obj, 'score_priorite_ia', 0),
            'objectif_recommande': getattr(obj, 'objectif_recommande', False),
            # Nouveaux champs d'analyse IA
            'analyse_ia': getattr(obj, 'analyse_ia', ''),
            'points_forts': getattr(obj, 'points_forts', []),
            'points_amelioration': getattr(obj, 'points_amelioration', []),
            'risques': getattr(obj, 'risques', []),
            'recommendations': getattr(obj, 'recommendations', []),
            'delai_realisme': getattr(obj, 'delai_realisme', ''),
            'niveau_difficulte': getattr(obj, 'niveau_difficulte', 'moyen')
        }
        
        # Formater les dates
        for date_field in ['date_creation', 'date_debut', 'date_echeance', 'derniere_mise_a_jour']:
            if hasattr(obj, date_field) and getattr(obj, date_field):
                date_value = getattr(obj, date_field)
                if hasattr(date_value, 'strftime'):
                    details[date_field] = date_value.strftime("%d/%m/%Y %H:%M")
        
        # Données pour le calendrier
        calendar_data = generate_calendar_data(obj)
        
        context = {
            'objectif': obj,
            'details': details,
            'calendar_data': calendar_data,
            'today': timezone.now().date(),
            'has_ia_analysis': bool(getattr(obj, 'analyse_ia', ''))
        }
        
        return render(request, 'objectif/details.html', context)
        
    except Objective.DoesNotExist:
        return HttpResponse("Objectif non trouvé", status=404)

@login_required
def objective_json(request, obj_id):
    """API JSON des détails d'un objectif"""
    try:
        obj = Objective.objects.get(id=obj_id)
        
        # CALCUL DES ATTRIBUTS AUTOMATIQUES
        attributs_calcules = calculer_tous_les_attributs(obj)
        
        # Sérialiser l'objectif
        data = {
            'id': str(obj.id),
            'titre': getattr(obj, 'titre', ''),
            'description': getattr(obj, 'description', ''),
            'filiere': getattr(obj, 'filiere', ''),
            'niveau': getattr(obj, 'niveau', ''),
            'priorite': getattr(obj, 'priorite', ''),
            'etat': getattr(obj, 'etat', ''),
            'progression': attributs_calcules['progression'],
            'date_creation': getattr(obj, 'date_creation', '').isoformat() if hasattr(obj, 'date_creation') and obj.date_creation else '',
            'date_debut': getattr(obj, 'date_debut', '').isoformat() if hasattr(obj, 'date_debut') and obj.date_debut else '',
            'date_echeance': getattr(obj, 'date_echeance', '').isoformat() if hasattr(obj, 'date_echeance') and obj.date_echeance else '',
            'derniere_mise_a_jour': getattr(obj, 'derniere_mise_a_jour', '').isoformat() if hasattr(obj, 'derniere_mise_a_jour') and obj.derniere_mise_a_jour else '',
            'nb_sessions': attributs_calcules['nb_sessions'],
            'temps_total': attributs_calcules['temps_total'],
            'taches': getattr(obj, 'taches', []),
            'ressources': getattr(obj, 'ressources', []),
            'tags': getattr(obj, 'tags', []),
            'suggestion_ia': getattr(obj, 'suggestion_ia', ''),
            'score_priorite_ia': getattr(obj, 'score_priorite_ia', 0),
            'objectif_recommande': getattr(obj, 'objectif_recommande', False)
        }
        
        return JsonResponse(data)
        
    except Objective.DoesNotExist:
        return JsonResponse({'error': 'Objectif non trouvé'}, status=404)

@login_required
def chatbot_view(request):
    """Vue principale du chatbot"""
    try:
        # Récupérer le vrai user MongoDB
        mongo_user = _get_mongo_user(request.user)
        
        # CORRECTION : Utiliser user__id pour le filtrage
        objectifs = Objective.objects.filter(user__id=mongo_user.id)
        
        return render(request, "objectif/chatbot.html", {"objectifs": objectifs})
        
    except Exception as e:
        print(f"Erreur dans chatbot_view: {e}")
        # En cas d'erreur, retourner une liste vide
        return render(request, "objectif/chat.html", {"objectifs": []})

@login_required
def chatbot_api(request):
    """API pour le chatbot"""
    if request.method == "POST":
        try:
            user_message = request.POST.get("message", "").strip()
            
            if not user_message:
                return JsonResponse({"error": "Message vide"}, status=400)

            # Récupérer le vrai user MongoDB
            mongo_user = _get_mongo_user(request.user)
            
            # CORRECTION : Récupérer tous les objectifs et filtrer manuellement
            all_objectifs = Objective.objects.all()
            user_objectifs = []
            
            for obj in all_objectifs:
                try:
                    # Vérifier si l'objectif appartient à l'utilisateur
                    if hasattr(obj, 'user') and obj.user and str(obj.user.id) == str(mongo_user.id):
                        user_objectifs.append(obj)
                except Exception as e:
                    print(f"Erreur avec l'objectif {obj.id}: {e}")
                    continue

            # Construire le contexte
            context = "\n".join([
                f"- {obj.titre} (État: {obj.etat}, Priorité: {obj.priorite}, Progression: {getattr(obj, 'progression', 0)}%)"
                for obj in user_objectifs
            ]) or "Aucun objectif enregistré."

            # Prompt amélioré pour Gemini
            prompt = f"""
Tu es EduBot, un assistant éducatif intelligent et motivant qui aide les étudiants à progresser dans leurs objectifs académiques.

CONTEXTE DES OBJECTIFS DE L'UTILISATEUR :
{context}

QUESTION DE L'UTILISATEUR :
{user_message}

GUIDELINES POUR TA RÉPONSE :
- Sois encourageant, positif et constructif
- Propose des conseils pratiques et réalisables
- Si tu parles d'un objectif spécifique, référence-le clairement
- Garde tes réponses concises mais utiles (max 3-4 phrases)
- Adapte ton ton à la situation : motivant pour les défis, félicitations pour les progrès
- Si la question n'est pas liée aux objectifs, redirige gentiment vers le sujet

RÉPONSE :
"""

            # Appel à Gemini
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content(prompt)
            
            return JsonResponse({
                "reply": response.text,
                "status": "success",
                "objectifs_count": len(user_objectifs)
            })

        except Exception as e:
            print(f"Erreur dans chatbot_api: {e}")
            return JsonResponse({
                "error": f"Erreur du chatbot: {str(e)}",
                "status": "error"
            }, status=500)

    return JsonResponse({"error": "Méthode non autorisée"}, status=405)

@login_required
def trigger_ia_analysis(request, obj_id):
    """Déclenche une analyse IA complète pour un objectif"""
    try:
        # Utiliser get_object_or_404 pour une meilleure gestion
        obj = get_object_or_404(Objective, id=obj_id, user_id=str(request.user.id))
        
        # Générer l'analyse IA
        success = generate_complete_ia_analysis(obj)
        
        if success:
            # Utiliser la session comme fallback si messages pose problème
            try:
                messages.success(request, "✅ Analyse IA générée avec succès!")
            except:
                request.session['analysis_message'] = "success:✅ Analyse IA générée avec succès!"
        else:
            try:
                messages.error(request, "❌ Erreur lors de la génération de l'analyse IA")
            except:
                request.session['analysis_message'] = "error:❌ Erreur lors de la génération de l'analyse IA"
            
        return redirect('objectif:details', obj_id=obj_id)
        
    except Exception as e:
        print(f"Erreur dans trigger_ia_analysis: {e}")
        try:
            messages.error(request, f"❌ Erreur lors de l'analyse IA: {str(e)}")
        except:
            request.session['analysis_message'] = f"error:❌ Erreur lors de l'analyse IA: {str(e)}"
        return redirect('objectif:details', obj_id=obj_id)

@login_required
def get_ia_analysis(request, obj_id):
    """API pour récupérer l'analyse IA d'un objectif"""
    try:
        obj = get_object_or_404(Objective, id=obj_id, user_id=str(request.user.id))
        
        analysis_data = {
            'analyse_ia': getattr(obj, 'analyse_ia', ''),
            'points_forts': getattr(obj, 'points_forts', []),
            'points_amelioration': getattr(obj, 'points_amelioration', []),
            'risques': getattr(obj, 'risques', []),
            'recommendations': getattr(obj, 'recommendations', []),
            'delai_realisme': getattr(obj, 'delai_realisme', ''),
            'niveau_difficulte': getattr(obj, 'niveau_difficulte', 'moyen'),
            'suggestion_ia': getattr(obj, 'suggestion_ia', ''),
            'score_priorite_ia': getattr(obj, 'score_priorite_ia', 0),
            'objectif_recommande': getattr(obj, 'objectif_recommande', False)
        }
        
        return JsonResponse(analysis_data)
        
    except Exception as e:
        return JsonResponse({'error': 'Erreur lors de la récupération des données'}, status=500)

def generate_complete_ia_analysis(obj):
    """Génère une analyse IA complète et détaillée avec Gemini 2.5 Flash"""
    
    api_key = os.getenv("AIzaSyBCutcN7kxoQ8frc9GHPGXlBMneulZCHzc")
    if not api_key:
        print("❌ Clé API Gemini non trouvée")
        return False

    try:
        # Préparer les données pour l'analyse
        jours_restants = ""
        if obj.date_echeance:
            aujourd_hui = timezone.now().date()
            try:
                # Gérer différents types de dates
                if hasattr(obj.date_echeance, 'date'):
                    date_echeance = obj.date_echeance.date()
                else:
                    date_echeance = obj.date_echeance
                
                # Vérifier que les deux sont des date objects
                if isinstance(date_echeance, datetime.date) and isinstance(aujourd_hui, datetime.date):
                    jours_restants = (date_echeance - aujourd_hui).days
                else:
                    jours_restants = "Date non valide"
            except (TypeError, AttributeError) as e:
                print(f"Erreur calcul jours restants: {e}")
                jours_restants = "Erreur calcul"

        prompt = f"""
        Tu es un expert en analyse d'objectifs académiques et professionnels.
        
        OBJECTIF À ANALYSER :
        - Titre : {getattr(obj, 'titre', 'Non spécifié')}
        - Description : {getattr(obj, 'description', 'Non spécifiée')}
        - Filière : {getattr(obj, 'filiere', 'Non spécifiée')}
        - Niveau : {getattr(obj, 'niveau', 'Non spécifié')}
        - Priorité : {getattr(obj, 'priorite', 'Non spécifiée')}
        - État : {getattr(obj, 'etat', 'Non spécifié')}
        - Progression : {getattr(obj, 'progression', 0)}%
        - Tags : {', '.join(getattr(obj, 'tags', []))}
        - Tâches prévues : {', '.join(getattr(obj, 'taches', []))}
        - Ressources : {', '.join(getattr(obj, 'ressources', []))}
        - Jours restants : {jours_restants if jours_restants else 'Non défini'}

        EFFECTUE UNE ANALYSE COMPLÈTE ET RÉPONDS STRICTEMENT EN JSON :

        {{
            "analyse_ia": "Analyse textuelle complète de 3-4 phrases",
            "points_forts": ["point fort 1", "point fort 2", "point fort 3"],
            "points_amelioration": ["point amélioration 1", "point amélioration 2"], 
            "risques": ["risque 1", "risque 2"],
            "recommendations": ["recommandation 1", "recommandation 2", "recommandation 3"],
            "delai_realisme": "Très réaliste|Réaliste|Peu réaliste|Irrealiste",
            "niveau_difficulte": "facile|moyen|difficile|expert",
            "suggestion_ia": "Suggestion concise pour l'utilisateur",
            "score_priorite_ia": 0.85,
            "objectif_recommande": true
        }}

        Sois honnête, constructif et précis dans ton analyse.
        Réponds UNIQUEMENT avec le JSON, sans texte supplémentaire.
        """

        # Utilisation du modèle Gemini 2.5 Flash
        endpoint = "https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent"
        
        headers = {
            "Content-Type": "application/json",
        }
        
        data = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.3,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 1024,
            }
        }

        print("🔄 Appel à l'API Gemini 2.5 Flash...")
        
        # Deux méthodes d'appel possibles
        try:
            # Méthode 1 : avec le paramètre key dans l'URL
            resp = requests.post(f"{endpoint}?key={api_key}", json=data, headers=headers, timeout=30)
        except:
            # Méthode 2 : avec le header Authorization
            headers["Authorization"] = f"Bearer {api_key}"
            resp = requests.post(endpoint, json=data, headers=headers, timeout=30)
        
        if resp.status_code == 200:
            resp_json = resp.json()
            print("✅ Réponse reçue de l'API Gemini")
            
            # Extraction du texte de réponse (structure Gemini 2.5)
            text = ""
            try:
                if 'candidates' in resp_json and resp_json['candidates']:
                    candidate = resp_json['candidates'][0]
                    if 'content' in candidate and 'parts' in candidate['content']:
                        text = candidate['content']['parts'][0].get('text', '').strip()
                
                # Alternative pour différentes structures de réponse
                if not text and 'candidates' in resp_json and resp_json['candidates']:
                    text = resp_json['candidates'][0].get('content', {}).get('parts', [{}])[0].get('text', '').strip()
                    
            except Exception as extract_error:
                print(f"❌ Erreur extraction texte: {extract_error}")
                # Tentative d'extraction alternative
                text = str(resp_json).split('"text": "')[-1].split('"')[0] if '"text": "' in str(resp_json) else ""
            
            if not text:
                print("❌ Réponse vide de l'API Gemini")
                print(f"Réponse complète: {resp_json}")
                return False
            
            # Nettoyer la réponse
            text = text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
            
            print(f"📝 Texte reçu ({len(text)} caractères): {text[:200]}...")
            
            # Parsing JSON
            try:
                result = json.loads(text)
            except json.JSONDecodeError as e:
                print(f"❌ Erreur parsing JSON: {e}")
                print(f"Texte problématique: {text}")
                
                # Fallback: créer une analyse basique
                result = {
                    "analyse_ia": f"Analyse de l'objectif '{getattr(obj, 'titre', '')}'. Progression actuelle: {getattr(obj, 'progression', 0)}%. Priorité: {getattr(obj, 'priorite', 'Non définie')}.",
                    "points_forts": [
                        "Objectif bien défini et structuré",
                        f"Progression de {getattr(obj, 'progression', 0)}% déjà accomplie",
                        "Ressources et tâches identifiées"
                    ],
                    "points_amelioration": [
                        "Améliorer la planification des délais si nécessaire",
                        "Diversifier les méthodes d'apprentissage"
                    ],
                    "risques": [
                        "Risque de retard si non suivi régulièrement",
                        "Dépendance aux ressources identifiées"
                    ],
                    "recommendations": [
                        "Planifier des sessions régulières de travail",
                        "Suivre la progression hebdomadaire",
                        "Adapter les méthodes en fonction des résultats"
                    ],
                    "delai_realisme": "Réaliste",
                    "niveau_difficulte": "moyen",
                    "suggestion_ia": f"Pour l'objectif '{getattr(obj, 'titre', '')}', continuez vos efforts actuels et révisez régulièrement votre planning pour maintenir la progression.",
                    "score_priorite_ia": 0.7,
                    "objectif_recommande": True
                }
            
            # Mettre à jour tous les champs avec des valeurs par défaut
            obj.analyse_ia = result.get("analyse_ia", "Analyse générée par l'IA")
            obj.points_forts = result.get("points_forts", [])
            obj.points_amelioration = result.get("points_amelioration", [])
            obj.risques = result.get("risques", [])
            obj.recommendations = result.get("recommendations", [])
            obj.delai_realisme = result.get("delai_realisme", "Non évalué")
            obj.niveau_difficulte = result.get("niveau_difficulte", "moyen")
            obj.suggestion_ia = result.get("suggestion_ia", "Suggestion non disponible")
            obj.score_priorite_ia = float(result.get("score_priorite_ia", 0.5))
            obj.objectif_recommande = bool(result.get("objectif_recommande", False))
            
            obj.derniere_mise_a_jour = datetime.datetime.utcnow()
            obj.save()
            
            print("✅ Analyse IA sauvegardée avec succès")
            return True
            
        else:
            print(f"❌ Erreur API Gemini: {resp.status_code}")
            print(f"Réponse erreur: {resp.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse IA: {e}")
        import traceback
        traceback.print_exc()
        return False

@login_required
def generate_pdf_bilan(request, obj_id):
    """Génère un bilan PDF complet de l'objectif"""
    try:
        obj = Objective.objects.get(id=obj_id, user_id=str(request.user.id))
        
        # CALCUL DES ATTRIBUTS AUTOMATIQUES POUR LE PDF
        attributs_calcules = calculer_tous_les_attributs(obj)
        
        # Créer le buffer PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=50, bottomMargin=50)
        styles = getSampleStyleSheet()
        
        # Styles personnalisés
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1,  # Centré
            textColor=colors.HexColor('#2c3e50')
        )
        
        section_style = ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.HexColor('#3498db')
        )
        
        story = []
        
        # En-tête avec titre
        story.append(Paragraph(f"BILAN COMPLET - {obj.titre}", title_style))
        story.append(Spacer(1, 10))
        
        # Date de génération
        date_style = ParagraphStyle(
            'DateStyle',
            parent=styles['Normal'],
            fontSize=10,
            alignment=1,
            textColor=colors.gray
        )
        story.append(Paragraph(f"Généré le {datetime.datetime.now().strftime('%d/%m/%Y à %H:%M')}", date_style))
        story.append(Spacer(1, 20))
        
        # Section 1: Informations générales
        story.append(Paragraph("📊 INFORMATIONS GÉNÉRALES", section_style))
        
        info_data = [
            ['Titre', obj.titre],
            ['Description', obj.description or 'Non spécifiée'],
            ['Filière', getattr(obj, 'filiere', 'Non spécifiée')],
            ['Niveau', getattr(obj, 'niveau', 'Non spécifié')],
            ['Priorité', getattr(obj, 'priorite', 'Non spécifiée')],
            ['État', getattr(obj, 'etat', 'Non spécifié')],
            ['Progression', f"{attributs_calcules['progression']}%"],
            ['Sessions réalisées', str(attributs_calcules['nb_sessions'])],
            ['Temps total', f"{attributs_calcules['temps_total']} heures"],
            ['Date création', obj.date_creation.strftime("%d/%m/%Y %H:%M") if obj.date_creation else 'Non spécifiée'],
            ['Date début', obj.date_debut.strftime("%d/%m/%Y %H:%M") if obj.date_debut else 'Non spécifiée'],
            ['Date échéance', obj.date_echeance.strftime("%d/%m/%Y %H:%M") if obj.date_echeance else 'Non spécifiée'],
            ['Dernière mise à jour', obj.derniere_mise_a_jour.strftime("%d/%m/%Y %H:%M") if obj.derniere_mise_a_jour else 'Non spécifiée']
        ]
        
        info_table = Table(info_data, colWidths=[150, 350])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 25))
        
        # Section 2: Barre de progression visuelle
        story.append(Paragraph("📈 PROGRESSION", section_style))
        
        # Créer un diagramme de progression simple
        progression = attributs_calcules['progression']
        progression_data = [
            ['Progression actuelle', f"{progression}%"]
        ]
        
        progression_table = Table(progression_data, colWidths=[200, 300])
        progression_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e9ecef')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(progression_table)
        story.append(Spacer(1, 15))
        
        # Section 3: Analyse IA si disponible
        if hasattr(obj, 'analyse_ia') and obj.analyse_ia:
            story.append(Paragraph("🤖 ANALYSE INTELLIGENCE ARTIFICIELLE", section_style))
            
            # Score de priorité IA
            score = getattr(obj, 'score_priorite_ia', 0)
            score_data = [
                ['Score de priorité IA', f"{score*100:.1f}%"],
                ['Difficulté estimée', getattr(obj, 'niveau_difficulte', 'Non évalué').title()],
                ['Délai réaliste', getattr(obj, 'delai_realisme', 'Non évalué').replace('_', ' ').title()],
                ['Recommandé par IA', 'Oui' if getattr(obj, 'objectif_recommande', False) else 'Non']
            ]
            
            score_table = Table(score_data, colWidths=[150, 350])
            score_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#17a2b8')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#e8f4fd')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#b3e0ff')),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(score_table)
            story.append(Spacer(1, 15))
            
            # Analyse globale
            story.append(Paragraph("<b>Analyse globale:</b>", styles['Heading3']))
            story.append(Paragraph(obj.analyse_ia, styles['Normal']))
            story.append(Spacer(1, 12))
            
            # Points forts
            if hasattr(obj, 'points_forts') and obj.points_forts:
                story.append(Paragraph("<b>Points forts:</b>", styles['Heading3']))
                for point in obj.points_forts:
                    story.append(Paragraph(f"• {point}", styles['Normal']))
                story.append(Spacer(1, 12))
            
            # Recommandations
            if hasattr(obj, 'recommendations') and obj.recommendations:
                story.append(Paragraph("<b>Recommandations:</b>", styles['Heading3']))
                for reco in obj.recommendations:
                    story.append(Paragraph(f"• {reco}", styles['Normal']))
                story.append(Spacer(1, 12))
        
        # Section 4: Tâches à réaliser
        if hasattr(obj, 'taches') and obj.taches:
            story.append(Paragraph("✅ TÂCHES À RÉALISER", section_style))
            
            tasks_data = [['#', 'Tâche']]
            for i, tache in enumerate(obj.taches, 1):
                tasks_data.append([str(i), tache])
            
            tasks_table = Table(tasks_data, colWidths=[30, 470])
            tasks_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#28a745')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#d4edda')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#c3e6cb')),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(tasks_table)
            story.append(Spacer(1, 25))
        
        # Section 5: Ressources
        if hasattr(obj, 'ressources') and obj.ressources:
            story.append(Paragraph("📚 RESSOURCES DISPONIBLES", section_style))
            
            resources_data = [['#', 'Ressource']]
            for i, ressource in enumerate(obj.ressources, 1):
                resources_data.append([str(i), ressource])
            
            resources_table = Table(resources_data, colWidths=[30, 470])
            resources_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6f42c1')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#e8e2ff')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#d6cfff')),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(resources_table)
            story.append(Spacer(1, 25))
        
        # Section 6: Tags
        if hasattr(obj, 'tags') and obj.tags:
            story.append(Paragraph("🏷️ TAGS ET CATÉGORIES", section_style))
            
            tags_text = ", ".join([f"#{tag}" for tag in obj.tags])
            story.append(Paragraph(tags_text, styles['Normal']))
            story.append(Spacer(1, 25))
        
        # Pied de page
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            alignment=1,
            textColor=colors.gray,
            spaceBefore=20
        )
        story.append(Paragraph(f"Bilan généré automatiquement - ID: {obj.id}", footer_style))
        
        # Générer le PDF
        doc.build(story)
        buffer.seek(0)
        
        # Retourner le PDF
        response = HttpResponse(buffer, content_type='application/pdf')
        filename = f"bilan_{obj.titre.replace(' ', '_').lower()}_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
        
    except Exception as e:
        print(f"❌ Erreur génération PDF bilan: {e}")
        import traceback
        traceback.print_exc()
        return HttpResponse(f"Erreur lors de la génération du bilan PDF: {str(e)}", status=500)
# feed/ai_video_services.py
"""
Services IA pour génération vidéo - VERSION LÉGÈRE (APIs)
Aucun téléchargement de modèles requis
"""
import requests
import json
from pathlib import Path
from django.conf import settings

class AIVideoGenerator:
    """Service IA utilisant des APIs externes gratuites"""
    
    def __init__(self):
        pass
    
    def generate_tiktok_script(self, feed_item):
      
        # OPTION A: Google Gemini API (Gratuit)
        try:
            import google.generativeai as genai
            
            GEMINI_API_KEY = "AIzaSyAv4Kvswtjl0TSyZi4O7V8HxIyFRlQW33Q"  # À remplacer
            
            if GEMINI_API_KEY == "AIzaSyAv4Kvswtjl0TSyZi4O7V8HxIyFRlQW33Q":
                # Fallback: Script basique sans IA
                return self._generate_basic_script(feed_item)
            
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-pro')
            
            prompt = f"""
Transforme ce post éducatif en script TikTok viral (60 secondes MAX):

Titre: {feed_item.title}
Type: {feed_item.get_content_type_display()}
Description: {feed_item.description[:200]}

Format requis:
- Hook accrocheur (3 premières secondes)
- 3 points clés maximum
- Langage jeune et simple
- 2-3 émojis pertinents
- Call-to-action final
- 150-180 mots MAX

Script:
"""
            
            response = model.generate_content(prompt)
            script = response.text.strip()
            
            # Limiter longueur
            words = script.split()
            if len(words) > 180:
                script = ' '.join(words[:180])
            
            return {
                'success': True,
                'script': script,
                'model': 'gemini-pro',
                'word_count': len(script.split())
            }
            
        except Exception as e:
            print(f"⚠️ Gemini API error: {e}")
            # Fallback: script basique
            return self._generate_basic_script(feed_item)
    
    def _generate_basic_script(self, feed_item):
        """
        Génère un script basique SANS IA (fallback)
        Utilise juste des templates
        """
        templates = {
            'programme': f"""
🎓 NOUVEAU PROGRAMME

{feed_item.title}

📚 Ce que vous allez apprendre:
{feed_item.description[:150]}

💡 Astuce: Prenez des notes dès maintenant!

👉 À vous de jouer!
""",
            'echeance': f"""
⏰ ATTENTION DEADLINE!

{feed_item.title}

⚠️ Date limite: {feed_item.deadline.strftime('%d/%m/%Y') if feed_item.deadline else 'À définir'}

📋 Ne tardez pas!

🚀 Bon courage!
""",
            'difficulte': f"""
🤔 PROBLÈME À RÉSOUDRE

{feed_item.title}

❓ {feed_item.description[:100]}

💡 N'hésitez pas à demander de l'aide!

✅ Vous allez y arriver!
""",
            'ressource': f"""
📖 RESSOURCE UTILE

{feed_item.title}

🔍 {feed_item.description[:150]}

💾 Sauvegardez cette info!
""",
            'annonce': f"""
📢 ANNONCE IMPORTANTE

{feed_item.title}

ℹ️ {feed_item.description[:150]}

👀 À ne pas manquer!
"""
        }
        
        script = templates.get(feed_item.content_type, templates['programme'])
        
        return {
            'success': True,
            'script': script,
            'model': 'template-basic',
            'word_count': len(script.split())
        }
    
    def generate_audio(self, text, output_path):
        """
        Génère l'audio avec gTTS (GRATUIT, aucun téléchargement)
        """
        try:
            from gtts import gTTS
            
            print(f"🎙️ Génération audio avec gTTS...")
            
            # Générer avec Google TTS (gratuit), slow=True pour rallonger la durée
            tts = gTTS(text=text, lang='fr', slow=True)
            tts.save(output_path)
            
            print(f"✅ Audio généré: {output_path}")
            
            return {
                'success': True,
                'audio_path': output_path
            }
        except Exception as e:
            print(f"❌ Erreur audio: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_subtitles(self, audio_path, script_text):
        """
        Génère les sous-titres SANS Whisper
        Utilise le script directement avec timing estimé
        """
        try:
            print("📝 Génération sous-titres (sans Whisper)...")
            
            # Obtenir durée audio
            from pydub import AudioSegment
            audio = AudioSegment.from_file(audio_path)
            duration = len(audio) / 1000.0  # En secondes
            
            # Découper le script en segments
            sentences = self._split_into_sentences(script_text)
            
            # Calculer timing
            time_per_sentence = duration / len(sentences) if sentences else 1.0
            
            srt_content = []
            for i, sentence in enumerate(sentences):
                start_time = i * time_per_sentence
                end_time = (i + 1) * time_per_sentence
                
                srt_content.append(f"{i+1}")
                srt_content.append(f"{self._format_time(start_time)} --> {self._format_time(end_time)}")
                srt_content.append(sentence)
                srt_content.append("")
            
            srt_string = "\n".join(srt_content)
            
            print(f"✅ Sous-titres générés ({len(sentences)} segments)")
            
            return {
                'success': True,
                'srt': srt_string,
                'segments': [{'start': i*time_per_sentence, 'end': (i+1)*time_per_sentence, 'text': s} 
                           for i, s in enumerate(sentences)]
            }
            
        except Exception as e:
            print(f"❌ Erreur sous-titres: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _split_into_sentences(self, text):
        """Découpe le texte en phrases"""
        import re
        # Découper sur . ! ? ou retour à la ligne
        sentences = re.split(r'[.!?\n]+', text)
        # Nettoyer
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences
    
    def _format_time(self, seconds):
        """Format SRT time"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
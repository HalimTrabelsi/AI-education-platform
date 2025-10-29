from PIL import Image, ImageDraw, ImageFont
import requests
import time
import os
from pathlib import Path
from django.conf import settings

class TikTokVideoGenerator:
    """Génère des vidéos via API cloud Shotstack"""
    
    def __init__(self):
        self.width = 1080
        self.height = 1920
        self.shotstack_api_key = 'Sewtw6mPEEU33NlrZXoyIBfNQQ6h2NMLLSeu1LRZ'  # Remplacez par votre clé API Shotstack
        self.shotstack_base_url = 'https://api.shotstack.io/edit/v1'
    
    def generate_video(self, feed_item, script, audio_path, subtitles_path):
        """Génère la vidéo via API Shotstack"""
        try:
            print("🎬 Début génération vidéo via API cloud...")
            
            # 1. Créer l'image de fond localement
            print("🎨 Création de l'image...")
            image_path = self._create_main_image(feed_item, script)
            
            # 2. Uploader l'image et l'audio à litterbox.catbox.moe
            print("📤 Upload des fichiers...")
            image_url = self._upload_file(image_path)
            audio_url = self._upload_file(audio_path)
            
            # 3. Payload pour Shotstack
            print("🔗 Préparation du payload...")
            payload = {
                "timeline": {
                    "soundtrack": {
                        "src": audio_url,
                        "effect": "fadeIn"
                    },
                    "tracks": [
                        {
                            "clips": [
                                {
                                    "asset": {
                                        "type": "image",
                                        "src": image_url
                                    },
                                    "start": 0,
                                    "length": 60
                                }
                            ]
                        }
                    ]
                },
                "output": {
                    "format": "mp4",
                    "resolution": "hd"
                }
            }
            
            # 4. Envoyer à l'API
            headers = {
                'Content-Type': 'application/json',
                'x-api-key': self.shotstack_api_key
            }
            response = requests.post(f"{self.shotstack_base_url}/render", json=payload, headers=headers)
            
            if not response.ok:
                raise Exception(f"Erreur API: {response.text}")
            
            render_data = response.json()['response']
            render_id = render_data['id']
            
            # 5. Attente du rendu
            print("⏳ Attente du rendu (1-2 minutes)...")
            video_url = None
            for _ in range(30):
                status_response = requests.get(f"{self.shotstack_base_url}/render/{render_id}", headers=headers)
                if not status_response.ok:
                    raise Exception(f"Erreur status: {status_response.text}")
                status_data = status_response.json()['response']
                if status_data['status'] == 'done':
                    video_url = status_data['url']
                    break
                elif status_data['status'] in ['failed', 'cancelled']:
                    raise Exception(f"Rendu échoué: {status_data.get('error', 'Inconnu')}")
                time.sleep(10)
            
            if not video_url:
                raise Exception("Timeout rendu")
            
            # 6. Télécharger la vidéo
            output_path = self._get_output_path(feed_item)
            with open(output_path, 'wb') as f:
                f.write(requests.get(video_url).content)
            
            # Nettoyer fichiers locaux
            try:
                os.remove(image_path)
            except:
                pass
            
            print("✅ Vidéo générée!")
            
            return {
                'success': True,
                'video_path': output_path,
                'duration': status_data.get('duration', 30)
            }
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }
    
    def _upload_file(self, local_path):
        """Upload fichier vers litterbox.catbox.moe pour URL directe (temporaire 12h)"""
        with open(local_path, 'rb') as f:
            files = {'fileToUpload': f}
            data = {
                'reqtype': 'fileupload',
                'time': '12h'  # Durée : 1h, 12h, 24h, 72h
            }
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.post('https://litterbox.catbox.moe/resources/internals/api.php', files=files, data=data, headers=headers)
            if response.ok:
                return response.text.strip()
            raise Exception(f"Échec upload: {response.text}")
    
    def _create_main_image(self, feed_item, script):
        """Crée l'image principale"""
        colors = {
            'programme': ((100, 150, 255), (50, 50, 200)),
            'echeance': ((255, 100, 100), (200, 50, 50)),
            'difficulte': ((255, 200, 100), (200, 150, 50)),
            'ressource': ((100, 255, 150), (50, 200, 100)),
            'annonce': ((200, 100, 255), (150, 50, 200))
        }
        
        color_top, color_bottom = colors.get(feed_item.content_type, colors['programme'])
        
        img = Image.new('RGB', (self.width, self.height))
        draw = ImageDraw.Draw(img)
        
        for y in range(self.height):
            ratio = y / self.height
            r = int(color_top[0] * (1 - ratio) + color_bottom[0] * ratio)
            g = int(color_top[1] * (1 - ratio) + color_bottom[1] * ratio)
            b = int(color_top[2] * (1 - ratio) + color_bottom[2] * ratio)
            draw.line([(0, y), (self.width, y)], fill=(r, g, b))
        
        cx, cy = self.width // 2, 400
        radius = 150
        draw.ellipse(
            [cx - radius, cy - radius, cx + radius, cy + radius],
            fill=(255, 255, 255),
            outline=(100, 100, 255),
            width=5
        )
        
        emojis = {
            'programme': '📚',
            'echeance': '⏰',
            'difficulte': '🤔',
            'ressource': '📖',
            'annonce': '📢'
        }
        emoji = emojis.get(feed_item.content_type, '📝')
        
        try:
            font_emoji = ImageFont.truetype("seguiemj.ttf", 100)
        except:
            try:
                font_emoji = ImageFont.truetype("arial.ttf", 80)
            except:
                font_emoji = ImageFont.load_default()
        
        bbox = draw.textbbox((0, 0), emoji, font=font_emoji)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw.text((cx - tw//2, cy - th//2), emoji, font=font_emoji, fill=(50, 50, 50))
        
        title = feed_item.title
        if len(title) > 40:
            title = title[:37] + "..."
        
        try:
            font_title = ImageFont.truetype("arial.ttf", 50)
        except:
            font_title = ImageFont.load_default()
        
        lines = self._wrap_text(title, font_title, self.width - 100, draw)
        y_text = 700
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font_title)
            tw = bbox[2] - bbox[0]
            x_text = (self.width - tw) // 2
            for adj in range(-2, 3):
                for adj2 in range(-2, 3):
                    draw.text((x_text+adj, y_text+adj2), line, font=font_title, fill=(0, 0, 0))
            draw.text((x_text, y_text), line, font=font_title, fill=(255, 255, 255))
            y_text += 60
        
        temp_dir = Path(settings.MEDIA_ROOT) / 'temp_video'
        temp_dir.mkdir(parents=True, exist_ok=True)
        image_path = temp_dir / f"frame_{feed_item.pk}.png"
        img.save(image_path)
        
        return str(image_path)
    
    def _wrap_text(self, text, font, max_width, draw):
        """Découpe le texte en lignes"""
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            width = bbox[2] - bbox[0]
            
            if width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    def _get_output_path(self, feed_item):
        """Chemin de sortie"""
        media_root = Path(settings.MEDIA_ROOT)
        videos_dir = media_root / 'feed_videos'
        videos_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"tiktok_{feed_item.pk}_{feed_item.created_at.strftime('%Y%m%d_%H%M%S')}.mp4"
        return str(videos_dir / filename)
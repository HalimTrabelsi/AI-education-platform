
<p align="center">
  <a href="https://themeselection.com/item/sneat-dashboard-free-django/" target="_blank">
    <img src="https://cdn.themeselection.com/ts-assets/sneat/logo/logo.png" alt="sneat-logo" width="60px" height="auto">
  </a>
</p>

<h1 align="center">
  <a href="#" target="_blank">
    AI-Learning — Réseau social d’apprentissage & révision assistée par IA
  </a>
</h1>

<p align="center">
Plateforme éducative intelligente intégrant IA, modération, et ressources partagées — construite sur <strong>Django + MongoDB</strong> et propulsée par <strong>Sneat Admin Template</strong>.
</p>

<p align="center">
  <a href="https://github.com/themeselection/sneat-bootstrap-html-django-admin-template-free/releases">
    <img src="https://img.shields.io/github/release/themeselection/sneat-bootstrap-html-django-admin-template-free.svg" alt="GitHub release">
  </a>
  <a href="https://github.com/themeselection/sneat-bootstrap-html-django-admin-template-free/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/themeselection/sneat-bootstrap-html-django-admin-template-free" alt="license">
  </a>
  <a href="https://x.com/Theme_Selection" target="_blank">
    <img alt="Twitter Follow" src="https://img.shields.io/twitter/follow/Theme_Selection">
  </a>
</p>

<kbd>[![Sneat - Bootstrap 5 HTML Django Admin Template Demo Screenshot](https://cdn.themeselection.com/ts-assets/sneat/sneat-bootstrap-django-admin-template-free/banner/banner.png)](https://themeselection.com/item/sneat-dashboard-free-django/)</kbd>

## 🚀 Introduction

**AI-Learning** est une plateforme web intelligente permettant aux étudiants et enseignants de **partager, réviser et évaluer** leurs ressources pédagogiques dans un environnement social, assisté par IA.
Basée sur **Sneat (Django Admin Template)**, elle combine ergonomie professionnelle, puissance IA et collaboration académique.

---

## 🎯 Problème à résoudre

Les étudiants dispersent leurs cours, TD et annales entre WhatsApp, Google Drive et PDF.
Résultat : recherche lente, qualité variable, révision peu personnalisée.

---

## 💡 Proposition de valeur

Une **plateforme unique** pour partager, chercher et réviser avec IA :

* 🔍 Recherche sémantique sur polycopiés, vidéos et TD
* 🧠 Résumés “prêts à réviser”
* 🎯 Génération de QCM et quiz adaptatifs
* 📰 Fil d’actualité pédagogique personnalisé
* 🛡️ Détection du plagiat, triche et contenu NSFW

---

## 👥 Acteurs de la plateforme

| Rôle                         | Description                                   |
| ---------------------------- | --------------------------------------------- |
| 🎓 Étudiant                  | Consulte, révise et publie des ressources     |
| 🧑‍🏫 Enseignant/Tuteur      | Valide, corrige et publie des TD              |
| 🧑‍💼 Modérateur pédagogique | Gère la qualité et la conformité des contenus |
| 👨‍💻 Administrateur         | Supervise règles, filières et analytics       |

---

## 🧩 Modules (Apps Django)

| Module                      | Description                                         | IA Intégrée                           |
| --------------------------- | --------------------------------------------------- | ------------------------------------- |
| **Identité & Profils**      | Gestion des comptes, filières, niveaux et objectifs | Suggestion d’intérêts et modules      |
| **Ressources pédagogiques** | Upload PDF/vidéos, métadonnées, tags                | Résumé, extraction de formules, OCR   |
| **Fil d’actualité IA**      | Contenus recommandés selon profil et programme      | Ranking multi-facteurs                |
| **Quiz & Évaluation**       | QCM/QCU, questions ouvertes, parcours adaptatif     | Génération questions, feedback IA     |
| **Modération & Intégrité**  | Signalements, anti-plagiat, détection triche/NSFW   | Analyse sémantique, scoring de risque |
| **Recherche & Découverte**  | Recherche par concepts et similarité                | Embeddings vectoriels texte/vidéo     |

---

## ⚙️ Architecture technique

**Backend :**

* Django 5 + Django REST Framework
* MongoDB + Atlas Search / Vector Search
* Celery + Redis pour les tâches asynchrones
* MinIO / S3 pour le stockage des médias

**IA & NLP :**

* Embeddings (E5 / Instructor)
* Résumé de texte (LLM)
* OCR (Tesseract)
* Transcription audio (Whisper)
* Anti-plagiat (similarité vectorielle)

**Frontend :**

* Sneat Django Admin Template (Bootstrap 5)
* Responsive & modular UI

---

## 📊 KPIs Clés

* ✅ Taux de réussite aux quiz
* 🔁 Rétention à 7/30 jours
* ⏱️ Temps de révision utile
* 📘 Pourcentage de ressources validées
* 🔍 Recherches sémantiques abouties

---

## 🧪 Stack & Outils

| Domaine         | Outils                                 |
| --------------- | -------------------------------------- |
| Framework       | Django 5, Django REST Framework        |
| Base de données | MongoDB (Atlas), MySQL (optionnel)     |
| AI              | Transformers, Whisper, Instructor, OCR |
| Frontend        |       Bootstrap Django Template        |
| DevOps          | Docker, Jenkins, SonarQube, Nexus      |
| Auth            | JWT / Django AllAuth                   |

---

## 🏗️ Installation ⚒️

### 1️⃣ Cloner le dépôt

```bash
git clone https://github.com/votre-compte/ai-learning-platform.git
cd ai-learning-platform
```

### 2️⃣ Créer un environnement virtuel

**Linux / macOS :**

```bash
python -m venv venv
source venv/bin/activate
```

**Windows :**

```bash
python -m venv venv
venv\Scripts\activate
```

### 3️⃣ Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4️⃣ Configurer les variables d’environnement

```env
MONGO_URI=<votre_URI_MongoDB>
AWS_ACCESS_KEY=<votre_access_key>
AWS_SECRET_KEY=<votre_secret_key>
OPENAI_API_KEY=<votre_clef_IA>
REDIS_URL=redis://localhost:6379
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
DEBUG=True
```

### 5️⃣ Appliquer les migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6️⃣ Créer un superutilisateur Django

```bash
python manage.py createsuperuser
```

### 7️⃣ Lancer le serveur

```bash
python manage.py runserver
```

* Application : `http://127.0.0.1:8000/`
* Admin : `http://127.0.0.1:8000/admin/`

---

## 🤖 Exemple de fonctionnalité IA


##  Génération de QCM et quiz adaptatifs

```python
from ai_tools import summarize_pdf

summary = summarize_pdf("uploads/chapitre2.pdf")
print(summary)
# → "Ce chapitre présente la loi normale, ses propriétés et son application..."
```

##  Recherche sémantique dans les documents

```python
from ai_tools import semantic_search

results = semantic_search(
    query="Loi de probabilité",
    documents=["uploads/chapitre1.pdf", "uploads/chapitre2.pdf"]
)
for res in results:
    print(res['document'], res['score'], res['snippet'])

```
##  Détection de plagiat et contenu NSFW

```python
from ai_tools import detect_plagiarism, detect_nsfw

plagiarism_score = detect_plagiarism("uploads/td_etudiant.pdf")
nsfw_flag = detect_nsfw("uploads/video_cours.mp4")

print("Plagiat:", plagiarism_score, "NSFW:", nsfw_flag)

```
##  Transcription Vidéo

```python
from ai_tools import video

transcript = transcribe_audio("uploads/coursvideo.mp4")
print("Transcription:", transcript[:200])

```
##  Recommandation personnalisée de ressources

```python
from ai_tools import recommend_resources

recommendations = recommend_resources(user_id=5)
for r in recommendations:
    print(r['title'], r['type'], r['link'])

```

##  Résumé intelligent de vidéos
```python
from ai_tools import summarize_video

summary = summarize_video("uploads/cours_video.mp4")
print("Résumé vidéo:", summary)

```

---

## 🧰 Contribuer

1. Fork du dépôt
2. Créez une branche : `feature/ma-fonctionnalite`
3. Commit & push vos changements
4. Créez une Pull Request 🚀

---
## Browser Support 🖥️

![chrome](https://github.com/nuxt/nuxt/assets/47495003/bbb6d7b0-2db6-4af4-abdc-a73de71dd287)
&nbsp;&nbsp;![firefox](https://github.com/nuxt/nuxt/assets/47495003/bca1f2d0-d597-453b-8525-5c94e36bfc33)
&nbsp;&nbsp;![safari](https://github.com/nuxt/nuxt/assets/47495003/8ecbb395-78fb-40fb-bb59-7301bf8a7e5d)
&nbsp;&nbsp;![Microsoft Edge](https://github.com/nuxt/nuxt/assets/47495003/f945821b-0cbd-464d-8103-824d4d5c4e9a)

\*_It also supports other browser which implemented latest CSS standards_

## Contributing 🦸

Contribution are always welcome and recommended! Here is how:

- Fork the repository ([here is the guide](https://docs.github.com/en/get-started/quickstart/fork-a-repo)).
- Clone to your machine `git clone https://github.com/HalimTrabelsi/AI-education-platform` Make your changes
- Create a pull request

### Contribution Requirements 🧰

- When you contribute, you agree to give a non-exclusive license to ThemeSelection to use that contribution in any context as we (ThemeSelection) see appropriate.
- If you use content provided by another party, it must be appropriately licensed using an open source license.
- Contributions are only accepted through Github pull requests.
- Finally, contributed code must work in all supported browsers (see above for browser support).

## Changelog 📆

Please refer to the [CHANGELOG](CHANGELOG.md) file. We will add a detailed release notes to each new release.

## Support 🧑🏻‍💻

For free products, enjoy community support via GitHub issues. Upgrade to Premium for dedicated support from our expert team.

## License &copy;

- Copyright © [ThemeSelection](https://themeselection.com/)
- Licensed under [MIT](LICENSE)
- All our free items are Open Source and licensed under MIT. You can use our free items for personal as well as commercial purposes. We just need an attribution from your end. Copy the below link and paste it at the footer of your web application or project.
  ```html
  <a href="https://themeselection.com/">ThemeSelection</a>
  ```

## Also Available In

<p>
   <!-- Figma -->
   <a href="https://themeselection.com/item/sneat-figma-admin-dashboard-builder-ui-kit/" target="_blank"><picture><source width="auto" height="74px" media="(prefers-color-scheme: dark)" srcset="https://github.com/microsoft/vscode/assets/47495003/0318a6c8-4f9b-4cf6-af5e-d357f909ea2b"><source width="auto" height="74px" media="(prefers-color-scheme: light)" srcset="https://github.com/microsoft/vscode/assets/47495003/47f21dfe-c1fc-4a7d-859e-4d98f8cdded1"><img width="auto" height="74px" alt="html" src="https://github.com/microsoft/vscode/assets/47495003/47f21dfe-c1fc-4a7d-859e-4d98f8cdded1"></picture></img></a>&nbsp;&nbsp;
   <!-- HTML -->
   <a href="https://themeselection.com/item/sneat-bootstrap-html-admin-template/" target="_blank"><picture><source width="auto" height="74px" media="(prefers-color-scheme: dark)" srcset="https://github.com/microsoft/vscode/assets/47495003/5fe77c46-2e4c-475a-8dec-e30e2badddee"><source width="auto" height="74px" media="(prefers-color-scheme: light)" srcset="https://github.com/microsoft/vscode/assets/47495003/3f5decd8-cd99-4ed3-aa76-528ca061385b"><img width="auto" height="74px" alt="html" src="https://github.com/microsoft/vscode/assets/47495003/3f5decd8-cd99-4ed3-aa76-528ca061385b"></picture></img></a>&nbsp;&nbsp;
   <!-- HTML + Laravel -->
   <a href="https://themeselection.com/item/sneat-bootstrap-laravel-admin-template/" target="_blank"><picture><source width="auto" height="74px" media="(prefers-color-scheme: dark)" srcset="https://github.com/microsoft/vscode/assets/47495003/efe420e4-9863-41b7-9eda-47ea94f21a62"><source width="auto" height="74px" media="(prefers-color-scheme: light)" srcset="https://github.com/microsoft/vscode/assets/47495003/be3b86e0-4d5e-4736-bf89-4267fb4d6710"><img width="auto" height="74px" alt="html_laravel" src="https://github.com/microsoft/vscode/assets/47495003/be3b86e0-4d5e-4736-bf89-4267fb4d6710"></picture></img></a>&nbsp;&nbsp;
   <!-- HTML + Django -->
   <a href="https://themeselection.com/item/sneat-bootstrap-django-admin-template/" target="_blank"><picture><source width="auto" height="74px" media="(prefers-color-scheme: dark)" srcset="https://github.com/microsoft/vscode/assets/47495003/3c87d33b-1223-4aaa-a652-388dcb714c98"><source width="auto" height="74px" media="(prefers-color-scheme: light)" srcset="https://github.com/microsoft/vscode/assets/47495003/51db1947-eac1-466f-87fd-5a209010fe9c"><img width="auto" height="74px" alt="html_django" src="https://github.com/microsoft/vscode/assets/47495003/51db1947-eac1-466f-87fd-5a209010fe9c"></picture></img></a>&nbsp;&nbsp;
   <!-- .Net Core -->
   <a href="https://themeselection.com/item/sneat-aspnet-core-mvc-admin-template/" target="_blank"><picture><source width="auto" height="74px" media="(prefers-color-scheme: dark)" srcset="https://github.com/microsoft/vscode/assets/47495003/6327fd7b-9c54-4189-a852-28551ad0e002"><source width="auto" height="74px" media="(prefers-color-scheme: light)" srcset="https://github.com/microsoft/vscode/assets/47495003/9856e9d5-021f-4573-902a-702e80dd0102"><img width="auto" height="74px" alt="net_core" src="https://github.com/microsoft/vscode/assets/47495003/9856e9d5-021f-4573-902a-702e80dd0102"></picture></img></a>&nbsp;&nbsp;
   <!-- NextJS -->
   <a href="https://themeselection.com/item/sneat-mui-react-nextjs-admin-template/" target="_blank"><picture><source width="auto" height="74px" media="(prefers-color-scheme: dark)" srcset="https://github.com/microsoft/vscode/assets/47495003/66344629-6d21-4f92-9078-f479b39cb34e"><source width="auto" height="74px" media="(prefers-color-scheme: light)" srcset="https://github.com/microsoft/vscode/assets/47495003/e1daf4e1-3fa5-4a44-969a-6143ddd67310"><img width="auto" height="74px" alt="next.js" src="https://github.com/microsoft/vscode/assets/47495003/e1daf4e1-3fa5-4a44-969a-6143ddd67310"></picture></img></a>&nbsp;&nbsp;
   <!-- Vue -->
   <a href="https://themeselection.com/item/sneat-vuetify-vuejs-admin-template/" target="_blank"><picture><source width="auto" height="74px" media="(prefers-color-scheme: dark)" srcset="https://github.com/microsoft/vscode/assets/47495003/881bbbb8-d1c9-421c-9bce-4ea43dfa9e6e"><source width="auto" height="74px" media="(prefers-color-scheme: light)" srcset="https://github.com/microsoft/vscode/assets/47495003/b02d6473-0345-42c2-be58-e648806104fa"><img width="auto" height="74px" alt="vue" src="https://github.com/microsoft/vscode/assets/47495003/b02d6473-0345-42c2-be58-e648806104fa"></picture></img></a>&nbsp;&nbsp;
   <!-- Vue + Laravel -->
   <a href="https://themeselection.com/item/sneat-vuetify-vuejs-laravel-admin-template/" target="_blank"><picture><source width="auto" height="74px" media="(prefers-color-scheme: dark)" srcset="https://github.com/microsoft/vscode/assets/47495003/20b6428e-3fa5-4f80-a389-9e4cd732c2de"><source width="auto" height="74px" media="(prefers-color-scheme: light)" srcset="https://github.com/microsoft/vscode/assets/47495003/3008d3eb-7b5b-4d9c-8563-837744a901da"><img width="auto" height="74px" alt="vue_laravel" src="https://github.com/microsoft/vscode/assets/47495003/3008d3eb-7b5b-4d9c-8563-837744a901da"></picture></img></a>&nbsp;&nbsp;
</p>


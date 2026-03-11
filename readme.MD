#  AI Smart CV Analyzer

Interface web 3D pour analyser et optimiser vos CVs grâce à l'IA.

---

##  Structure du projet

```
AI Smart CV Analyzer/
├── Backend/
│   ├── main.py
│   ├── engine.py
│   ├── recommender.py
│   └── .env
└── frontend/
    └── cv-optimizer.html   ← ici
└── venv/                    # Environnement virtuel Python
```

---

##  Installation

### 1. Cloner / ouvrir le projet

```bash
cd "AI Smart CV Analyzer/Backend"
```

### 2. Activer l'environnement virtuel

```bash
# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate
```

### 3. Installer les dépendances

```bash
pip install fastapi uvicorn docling python-dotenv groq
```

### 4. Configurer la clé API Groq

Crée un fichier `.env` dans le dossier `Backend/` :

```env
GROQ_API_KEY=ta_clé_api_groq
```

Obtenir une clé gratuite : [console.groq.com](https://console.groq.com)

---

##  Lancer l'application

```bash
uvicorn main:app --reload
```

Puis ouvre dans ton navigateur :

```
http://localhost:8000
```

>  Ne pas ouvrir `cv-optimizer.html` directement — toujours passer par `http://localhost:8000`

---

##  Fonctionnalités

| Fonctionnalité | Description |
|---|---|
| **Analyser le CV** | Upload un PDF + offre d'emploi → score de matching + recommandations IA |
| **Générer CV** | Génère une version optimisée du CV en Markdown prête à copier |
| **Mode démo** | Si le backend est absent, un résultat de démonstration s'affiche |

---

## 🔌 Endpoints API

| Méthode | Route | Description |
|---|---|---|
| `GET` | `/` | Sert l'interface HTML |
| `POST` | `/analyze` | Analyse CV + retourne score et conseils |
| `POST` | `/generate-cv` | Génère un CV optimisé en Markdown |

### Exemple de réponse `/analyze`

```json
{
  "score": "73%",
  "recommendations": "Points forts : ...\nPoints à améliorer : ..."
}
```

### Exemple de réponse `/generate-cv`

```json
{
  "status": "success",
  "revised_cv_markdown": "# Jean Dupont\n..."
}
```

---

##  Modèles IA utilisés

Le projet utilise **Groq** comme provider LLM (gratuit) :

| Modèle | Usage | Limite gratuite |
|---|---|---|
| `llama-3.3-70b-versatile` | Analyse + génération | 100k tokens/jour |
| `llama-3.1-8b-instant` | Alternative économe | 100k tokens/jour |

> Si tu atteins la limite (`Error 429`), attends quelques minutes ou change de modèle dans `recommender.py`.

---

##  Stack technique

- **Backend** — Python, FastAPI, Docling (extraction PDF)
- **LLM** — Groq API (llama-3.3-70b)
- **Frontend** — HTML/CSS/JS vanilla, Three.js (background 3D)
- **Fonts** — Syne + DM Mono (Google Fonts)

---

##  Problèmes fréquents

**L'interface ne s'affiche pas / rien ne se passe**
→ Vérifier que uvicorn tourne et ouvrir `http://localhost:8000`

**Error 429 - Rate limit**
→ Limite Groq atteinte, attendre 2-3 minutes

**Error 404 sur `/`**
→ Vérifier que `cv-optimizer.html` est bien dans le même dossier que `main.py`

<<<<<<< HEAD
**Le score s'affiche mais les recommandations sont vides**
→ Vérifier la clé `GROQ_API_KEY` dans `.env`
=======
>>>>>>> 7ff0c5f (docs: sauvegarde avant synchronisation)

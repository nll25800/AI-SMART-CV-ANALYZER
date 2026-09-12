# AI Smart CV Analyzer

Interface web 3D pour analyser et optimiser vos CVs grâce à l'IA, avec recherche d'offres d'emploi intégrée. Déployé sur un cluster Kubernetes (k3s) en pré-production AWS.

🔗 **Application en ligne :** [cv-analyzer-na.duckdns.org](https://cv-analyzer-na.duckdns.org)

---

## Structure du projet

```
AI Smart CV Analyzer/
├── Backend/
│   ├── main.py                  # API FastAPI (routes /analyze, /generate-cv, /generate-cv-pdf, /search-jobs)
│   ├── engine.py                 # Scoring CV ↔ offre (sentence-transformers)
│   ├── recommender.py            # Analyse & génération de CV via LLM (Groq)
│   ├── scraper.py                # Recherche d'offres d'emploi (API Adzuna)
│   ├── cv_pdf_generator.py       # Génération du CV optimisé en PDF (ReportLab)
│   ├── database.py               # SQLAlchemy — engine, session, modèle Analysis
│   ├── alembic/                  # Migrations de schéma versionnées
│   
├── frontend/
│   └── cv-optimizer.html         # Interface unique (3 onglets : Analyser / Générer / Offres)
├── k8s/
│   └── cv-analyzer-deploy.yaml   # Deployment + Service + Ingress (k3s)
├── terraform/                    # Infra AWS (EC2, k3s, RDS, security groups)
└── .github/workflows/            # Pipelines CI/CD (en cours de mise en place)
```

---

## Architecture de déploiement (production actuelle)

| Composant | Détail |
|---|---|
| **Cluster** | k3s, 2 nœuds EC2 (`k3s-master`, `k3s-agent`), région AWS eu-west-3 (Paris) |
| **Ingress / HTTPS** | Traefik + cert-manager, certificat Let's Encrypt automatique |
| **Domaine** | `https://cv-analyzer-na.duckdns.org` |
| **Base de données** | RDS PostgreSQL (`db.t3.micro`), privée, accessible uniquement depuis le cluster |
| **Registre d'images** | Docker Hub (`nettorche/cv-analyzer`) |
| **Secrets** | Kubernetes Secret (`cv-analyzer-secrets`) injecté via `envFrom` — `GROQ_API_KEY`, `ADZUNA_APP_ID`, `ADZUNA_APP_KEY`, `DATABASE_URL` |

> Le déploiement se fait actuellement à la main (`docker build/push` + `kubectl apply`). Une CI/CD via GitHub Actions est en cours de mise en place (build + scan de vulnérabilités automatiques, déploiement soumis à approbation manuelle).

---

## Installation en local (développement)

### 1. Cloner le projet

```bash
git clone <url-du-repo>
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
pip install -r requirements.txt
```

### 4. Configurer les variables d'environnement

Un fichier `.env` (non versionné) est requis dans `Backend/`, contenant les clés d'accès aux services externes utilisés (LLM, recherche d'offres d'emploi, base de données). Se référer à la documentation interne du projet pour la liste exacte des variables attendues.

### 5. Appliquer les migrations de base de données

```bash
alembic upgrade head
```

---

## Lancer l'application en local

```bash
uvicorn main:app --reload
```

Puis ouvre :

```
http://localhost:8000
```

> Ne pas ouvrir `cv-optimizer.html` directement — toujours passer par le serveur FastAPI.

---

## Fonctionnalités

| Fonctionnalité | Description |
|---|---|
| **Analyser le CV** | Upload un PDF + offre d'emploi → score de matching + recommandations IA. L'analyse (score, offre, recommandations) est persistée en base — le contenu du CV lui-même n'est jamais stocké. |
| **Générer CV** | Génère une version optimisée du CV en Markdown, réécrite pour correspondre à l'offre ciblée |
| **Export PDF** | Met en page le CV optimisé en PDF (2 colonnes, auto-scaling A4), avec photo optionnelle |
| **Recherche d'offres** | Recherche d'offres d'emploi réelles via l'API Adzuna, utilisables directement comme base d'analyse |
| **Mode démo** | Si le backend est injoignable, un résultat de démonstration s'affiche côté frontend |

---

## Endpoints API

| Méthode | Route | Description |
|---|---|---|
| `GET` | `/` | Sert l'interface HTML |
| `POST` | `/analyze` | Analyse CV + retourne score et conseils (persisté en base) |
| `POST` | `/generate-cv` | Génère un CV optimisé en Markdown |
| `POST` | `/generate-cv-pdf` | Génère et retourne le CV optimisé au format PDF |
| `GET` | `/search-jobs` | Recherche d'offres d'emploi (paramètres : `domain`, `location`, `results`) |

### Exemple de réponse `/analyze`

```json
{
  "score": "73%",
  "recommendations": "🔑 Mots-clés manquants : ...\n💼 Expériences non couvertes : ..."
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

## Modèles IA utilisés

| Modèle | Usage | Limite gratuite |
|---|---|---|
| `llama-3.3-70b-versatile` (Groq) | Analyse + génération de CV | 100k tokens/jour |
| `all-MiniLM-L6-v2` (sentence-transformers) | Scoring de similarité CV ↔ offre | Local, gratuit, illimité |

> Si tu atteins la limite Groq (`Error 429`), attends quelques minutes ou change de modèle dans `recommender.py`.

---

## Stack technique

- **Backend** — Python, FastAPI, Docling (extraction PDF), SQLAlchemy + Alembic
- **NLP** — sentence-transformers (`all-MiniLM-L6-v2`)
- **LLM** — Groq API (llama-3.3-70b)
- **PDF** — ReportLab (génération), Docling (extraction)
- **Base de données** — PostgreSQL (AWS RDS)
- **Emploi** — API Adzuna
- **Frontend** — HTML/CSS/JS vanilla, Three.js (background 3D)
- **Infrastructure** — Docker, Kubernetes (k3s), Terraform, Traefik, cert-manager
- **CI/CD** — GitHub Actions (en cours de mise en place)
- **Fonts** — Syne + DM Mono (Google Fonts)

 
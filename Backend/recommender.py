import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("ERREUR : La clé GROQ_API_KEY n'est pas définie dans le fichier .env")

llm = ChatGroq(
    model_name="llama-3.3-70b-versatile",
    temperature=0.5,
    groq_api_key=api_key
)


# ── ANALYSE ───────────────────────────────────────────────────────────────────
def get_ai_advice(cv_text: str, job_desc: str, score: float) -> str:
    system_prompt = (
        "Tu es un expert en recrutement technique (RH Tech). "
        "Tu analyses en détail la correspondance entre un CV et une offre d'emploi. "
        "Tu es direct, précis et orienté action."
    )

    user_prompt = f"""
Mon CV (format Markdown) :
---
{cv_text}
---

Offre d'emploi :
---
{job_desc}
---

Mon score de matching actuel est de {score}%.

Fais une analyse structurée en 3 sections :

## 🔑 Mots-clés manquants
Liste tous les mots-clés importants présents dans l'offre mais ABSENTS de mon CV.
(technologies, outils, méthodologies, certifications, langages...)
Formate en liste avec des tirets.

## 💼 Expériences requises non couvertes
Identifie les expériences, missions ou responsabilités demandées dans l'offre
que mon CV ne mentionne pas ou mentionne insuffisamment.
Formate en liste avec des tirets.

## 🛠️ Compétences techniques à mettre en avant
Liste les compétences techniques de l'offre que je dois absolument faire apparaître
dans mon CV (même si je les possède mais ne les ai pas citées explicitement).
Formate en liste avec des tirets.
"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", user_prompt),
    ])

    chain = prompt | llm
    response = chain.invoke({})
    return response.content


# ── GÉNÉRATION ────────────────────────────────────────────────────────────────
def generate_revised_cv(cv_text: str, job_desc: str) -> str:
    system_prompt = (
        "Tu es un rédacteur de CV expert, spécialisé dans l'optimisation ATS. "
        "Tu réécris des CVs pour maximiser leur score de matching avec une offre d'emploi précise. "
        
    )

    user_prompt = f"""
Réécris ce CV en Markdown pour qu'il corresponde parfaitement à l'offre d'emploi.

CV ORIGINAL :
---
{cv_text}
---

OFFRE D'EMPLOI :
---
{job_desc}
---

INSTRUCTIONS STRICTES :

1. **PROFIL** (section en haut du CV)
   - Réécris entièrement le profil professionnel en te basant sur le "profil recherché" dans l'offre.
   - Le profil doit refléter exactement ce que l'employeur cherche, en utilisant ses propres mots.
   - 3 à 4 lignes maximum.

2. **COMPÉTENCES TECHNIQUES**
   - Extrais TOUS les mots-clés techniques de l'offre (langages, frameworks, outils, méthodologies...).
   - Intègre-les tous dans la section Compétences, en les organisant par catégorie.
   - Ne supprime pas les compétences existantes du candidat si elles sont pertinentes.

3. **EXPÉRIENCES PROFESSIONNELLES**
   - Réécris entièrements le contenu de chaque expérience a partir des missions qui opnt été cités dans l'offre.
   - Utilise les verbes d'action et le vocabulaire exact de l'offre d'emploi.

   

4. **STRUCTURE OBLIGATOIRE** (dans cet ordre) :
   # Prénom Nom
   ## Profil
   ## Compétences Techniques
   ## Expériences Professionnelles
   ## Formation
   ## (autres sections si présentes dans le CV original)

Génère uniquement le CV en Markdown, sans commentaire ni texte d'introduction.
"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", user_prompt),
    ])

    chain = prompt | llm
    response = chain.invoke({})
    return response.content
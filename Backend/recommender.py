import os
import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from pydantic import ValidationError

from cv_schema import CVData

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("ERREUR : La clé GROQ_API_KEY n'est pas définie dans le fichier .env")

llm = ChatGroq(
    model_name="llama-3.3-70b-versatile",
    temperature=0.5,
    groq_api_key=api_key
)

# LLM configuré pour forcer une sortie JSON valide (json_object mode).
# Rappel : ça garantit un JSON syntaxiquement valide, PAS la conformité
# à notre schéma précis -> d'où la validation Pydantic juste après.
llm_json = ChatGroq(
    model_name="llama-3.3-70b-versatile",
    temperature=0.3,  # un peu plus bas : on veut de la précision structurelle, pas de la créativité
    groq_api_key=api_key,
    model_kwargs={"response_format": {"type": "json_object"}}
)

MAX_RETRIES = 3


# ── ANALYSE (inchangé) ────────────────────────────────────────────────────────
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


# ── GÉNÉRATION STRUCTURÉE (JSON + Pydantic + retry) ───────────────────────────
def _build_system_prompt() -> str:
    """
    Construit le prompt système en injectant le JSON Schema généré automatiquement
    par Pydantic. Ça évite de dupliquer la définition du schéma à la main dans le
    prompt : si on modifie cv_schema.py, le prompt suit automatiquement.
    """
    schema_json = json.dumps(CVData.model_json_schema(), ensure_ascii=False, indent=2)

    return f"""Tu es un rédacteur de CV expert, spécialisé dans l'optimisation ATS.
Tu réécris des CVs pour maximiser leur score de matching avec une offre d'emploi précise.

Tu dois répondre UNIQUEMENT avec un objet JSON valide, sans aucun texte avant ou après,
qui respecte EXACTEMENT ce JSON Schema :

{schema_json}

Règles strictes :
- N'ajoute AUCUN champ qui n'est pas dans le schéma.
- Respecte les noms de champs exactement (ex: "poste", pas "titre_poste").
- Les champs optionnels peuvent être null s'ils sont inconnus, mais préfère une chaîne vide
  plutôt que null quand c'est raisonnable.
- Réponds uniquement avec le JSON, rien d'autre.
"""


def _build_user_prompt(cv_text: str, job_desc: str) -> str:
    return f"""Réécris ce CV pour qu'il corresponde parfaitement à l'offre d'emploi.

CV ORIGINAL :
---
{cv_text}
---

OFFRE D'EMPLOI :
---
{job_desc}
---

INSTRUCTIONS DE CONTENU :

1. PROFIL : réécris-le en te basant sur le profil recherché dans l'offre, 3-4 lignes max,
   dans les mots de l'employeur.

2. COMPÉTENCES : extrais tous les mots-clés techniques de l'offre (langages, frameworks,
   outils, méthodologies) et regroupe-les par catégorie cohérente. Ne supprime pas les
   compétences existantes du candidat si elles sont pertinentes.

3. EXPÉRIENCES : réécris le contenu de chaque expérience en te basant sur les missions
   citées dans l'offre, avec les verbes d'action et le vocabulaire exact de l'offre.

Réponds uniquement avec le JSON structuré conforme au schéma fourni dans le message système.
"""


def generate_revised_cv_structured(cv_text: str, job_desc: str) -> CVData:
    """
    Génère un CV optimisé sous forme d'objet CVData validé.

    Pattern generate -> validate -> retry :
    1. On demande au LLM un JSON (mode json_object = garantit un JSON syntaxiquement valide).
    2. On valide ce JSON contre notre schéma Pydantic strict (extra=forbid).
    3. Si la validation échoue, on renvoie l'erreur Pydantic EXACTE au LLM pour qu'il
       se corrige, plutôt qu'un vague "corrige le format".
    4. On abandonne après MAX_RETRIES tentatives avec une erreur claire.
    """
    system_prompt = _build_system_prompt()
    user_prompt = _build_user_prompt(cv_text, job_desc)

    messages = [
        ("system", system_prompt),
        ("user", user_prompt),
    ]

    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        prompt = ChatPromptTemplate.from_messages(messages)
        chain = prompt | llm_json
        response = chain.invoke({})
        raw_content = response.content

        try:
            raw_json = json.loads(raw_content)
        except json.JSONDecodeError as e:
            last_error = f"Réponse non-JSON malgré le mode json_object : {e}"
            messages.append(("assistant", raw_content))
            messages.append(("user", f"Ta réponse n'était pas un JSON valide ({e}). "
                                      f"Réponds à nouveau, UNIQUEMENT avec le JSON, sans texte autour."))
            continue

        try:
            cv_data = CVData.model_validate(raw_json)
            return cv_data  # succès -> on sort immédiatement
        except ValidationError as e:
            last_error = str(e)
            # On renvoie l'erreur Pydantic exacte au LLM pour qu'il corrige précisément
            # les champs fautifs, plutôt que de tout regénérer à l'aveugle.
            messages.append(("assistant", raw_content))
            messages.append(("user", f"Ton JSON ne respecte pas le schéma attendu. "
                                      f"Voici l'erreur de validation exacte :\n{e}\n\n"
                                      f"Corrige UNIQUEMENT les champs en erreur et renvoie "
                                      f"le JSON complet corrigé, toujours conforme au schéma."))

    raise ValueError(
        f"Impossible de générer un CV structuré valide après {MAX_RETRIES} tentatives. "
        f"Dernière erreur : {last_error}"
    )


# ── Ancienne fonction Markdown, gardée pour compat le temps de la transition ──
def generate_revised_cv(cv_text: str, job_desc: str) -> str:
    """
    DEPRECATED : ancienne version qui renvoyait du Markdown libre.
    À supprimer une fois que main.py et le frontend sont migrés vers
    generate_revised_cv_structured().
    """
    system_prompt = (
        "Tu es un rédacteur de CV expert, spécialisé dans l'optimisation ATS. "
        "Tu réécris des CVs pour maximiser leur score de matching avec une offre d'emploi précise."
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

Génère uniquement le CV en Markdown, sans commentaire ni texte d'introduction.
"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", user_prompt),
    ])

    chain = prompt | llm
    response = chain.invoke({})
    return response.content

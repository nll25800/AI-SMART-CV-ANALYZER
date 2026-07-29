"""
test_recommender.py - Script de test manuel pour generate_revised_cv_structured()
À lancer avec : python test_recommender.py
"""
import traceback
from recommender import generate_revised_cv_structured

cv_text = """
# Jean Dupont

## Profil
Développeur avec 3 ans d'expérience en développement web.

## Expériences
Développeur Backend - Acme Corp - 2022 - Présent
- Développement d'APIs REST en Python
- Maintenance de bases de données PostgreSQL

## Formation
Licence Informatique - Université de Lyon - 2021

## Compétences
Python, Django, PostgreSQL, Git
"""

job_desc = """
Nous recherchons un Data Scientist spécialisé en Machine Learning et IA Générative (LLM, RAG).
Compétences requises : Python, TensorFlow, AWS, Docker, MLOps.
Expérience en conception de pipelines ETL et déploiement de modèles en production.
"""

if __name__ == "__main__":
    try:
        result = generate_revised_cv_structured(cv_text, job_desc)
        print("=== SUCCÈS ===")
        print(result.model_dump_json(indent=2))
    except ValueError as e:
        print("=== ÉCHEC APRÈS RETRIES ===")
        print(str(e))
        print("\n--- TRACE COMPLÈTE ---")
        traceback.print_exc()
    except Exception as e:
        print(f"=== ERREUR INATTENDUE ({type(e).__name__}) ===")
        print(str(e))
        print("\n--- TRACE COMPLÈTE ---")
        traceback.print_exc()
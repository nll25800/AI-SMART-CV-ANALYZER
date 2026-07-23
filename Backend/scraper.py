import os
import httpx
from dotenv import load_dotenv

load_dotenv()

ADZUNA_APP_ID  = os.getenv("ADZUNA_APP_ID")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY")

COUNTRY_CODES = {
    "france": "fr",
    "belgique": "be",
    "suisse": "ch",
    "canada": "ca",
    "royaume-uni": "gb",
    "etats-unis": "us",
}

def search_jobs(domain: str, location: str, results: int = 10) -> list[dict]:
    """
    Recherche des offres d'emploi via l'API Adzuna.
    Retourne une liste de dicts avec les infos clés de chaque offre.
    """
    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        raise ValueError("ADZUNA_APP_ID ou ADZUNA_APP_KEY manquant dans .env")

    # Déterminer le pays selon la ville saisie (défaut: France)
    country = "fr"
    location_lower = location.lower()
    for key, code in COUNTRY_CODES.items():
        if key in location_lower:
            country = code
            break

    url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"

    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "results_per_page": results,
        "what": domain,
        "where": location,
        "content-type": "application/json",
        "sort_by": "date",           # offres les plus récentes en premier
    }

    response = httpx.get(url, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()

    jobs = []
    for job in data.get("results", []):
        jobs.append({
            "title":       job.get("title", "N/A"),
            "company":     job.get("company", {}).get("display_name", "N/A"),
            "location":    job.get("location", {}).get("display_name", "N/A"),
            "description": job.get("description", ""),
            "salary_min":  job.get("salary_min"),
            "salary_max":  job.get("salary_max"),
            "url":         job.get("redirect_url", "#"),
            "created":     job.get("created", ""),
        })

    return jobs
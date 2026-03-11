import trafilatura

def extract_job_from_url(url: str):
    downloaded = trafilatura.fetch_url(url)
    if downloaded is None:
        return None
    
    # On extrait le texte principal en format texte brut ou markdown
    result = trafilatura.extract(downloaded, include_formatting=True)
    return result
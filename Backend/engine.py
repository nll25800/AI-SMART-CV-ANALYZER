from sentence_transformers import SentenceTransformer, util
import numpy as np

# On charge un modèle performant et léger d'Hugging Face
# 'all-MiniLM-L6-v2' est parfait pour commencer

# je peux utiliser paraphrase-multilingual-MiniLM-L12-v2 aussi 
model = SentenceTransformer('all-MiniLM-L6-v2')

def get_matching_score(cv_text: str, job_description: str):
    # 1. On transforme les textes en vecteurs (Embeddings)
    # L'IA "lit" et convertit le sens en chiffres
    embeddings = model.encode([cv_text, job_description])
    
    cv_vector = embeddings[0]
    jd_vector = embeddings[1]
    
    # 2. On calcule la similarité cosinus (le score de proximité)
    # Plus l'angle entre les deux vecteurs est petit, plus le score est haut
    cosine_sim = util.cos_sim(cv_vector, jd_vector)
    
    # On transforme le score en pourcentage propre
    score_percentage = round(float(cosine_sim) * 100, 2)
    
    return score_percentage
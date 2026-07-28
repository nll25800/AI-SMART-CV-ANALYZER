import resource

def mem_mb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024

print(f"[1] Python nu : {mem_mb():.1f} MB")

from fastapi import FastAPI
print(f"[2] + fastapi : {mem_mb():.1f} MB")

from docling.document_converter import DocumentConverter
print(f"[3] + import docling : {mem_mb():.1f} MB")

converter = DocumentConverter()
print(f"[4] + DocumentConverter() : {mem_mb():.1f} MB")

from engine import get_matching_score
print(f"[5] + engine (sentence_transformers + modèle) : {mem_mb():.1f} MB")

from recommender import get_ai_advice, generate_revised_cv
print(f"[6] + recommender (langchain_groq) : {mem_mb():.1f} MB")

from scraper import search_jobs
print(f"[7] + scraper (httpx) : {mem_mb():.1f} MB")

from cv_pdf_generator import generate_pdf
print(f"[8] + cv_pdf_generator (reportlab) : {mem_mb():.1f} MB")
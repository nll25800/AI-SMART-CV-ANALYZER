from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse          # ← ajout
from docling.document_converter import DocumentConverter
import shutil
import os

# Import des fonctions de nos modules personnalisés
from engine import get_matching_score
from recommender import get_ai_advice, generate_revised_cv

app = FastAPI(title="AI CV Expert & Optimizer")

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialisation du convertisseur Docling
converter = DocumentConverter()

# ── Frontend ──────────────────────────────────────────────────────────────────
@app.get("/")                                        # ← ajout
async def serve_frontend():
    return FileResponse("../frontend/cv-optimizer.html")         # ← ajout


# ── API ───────────────────────────────────────────────────────────────────────
@app.post("/analyze")
async def analyze_cv(file: UploadFile = File(...), job_description: str = Form(...)):
    """Analyse le CV, donne un score et des conseils."""
    temp_path = f"temp_{file.filename}"

    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        result = converter.convert(temp_path)
        cv_text = result.document.export_to_markdown()
        score = get_matching_score(cv_text, job_description)
        advice = get_ai_advice(cv_text, job_description, score)
        return {
            "score": f"{score}%",
            "recommendations": advice
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@app.post("/generate-cv")
async def rewrite_cv(file: UploadFile = File(...), job_description: str = Form(...)):
    """Génère une version optimisée du CV en Markdown."""
    temp_path = f"temp_gen_{file.filename}"

    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        result = converter.convert(temp_path)
        cv_text = result.document.export_to_markdown()
        new_cv_markdown = generate_revised_cv(cv_text, job_description)
        return {
            "status": "success",
            "revised_cv_markdown": new_cv_markdown
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from docling.document_converter import DocumentConverter
import shutil, os, traceback

from engine import get_matching_score
from recommender import get_ai_advice, generate_revised_cv
from scraper import search_jobs
from cv_pdf_generator import generate_pdf

app = FastAPI(title="AI CV Expert & Optimizer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

converter = DocumentConverter()

# ── Frontend ──────────────────────────────────────────────────────────────────
@app.get("/")
async def serve_frontend():
    return FileResponse("../frontend/cv-optimizer.html")

# ── Search jobs ───────────────────────────────────────────────────────────────
@app.get("/search-jobs")
async def search_jobs_endpoint(domain: str, location: str, results: int = 10):
    try:
        jobs = search_jobs(domain, location, results)
        return {"jobs": jobs}
    except Exception as e:
        return {"error": str(e)}

# ── Analyze ───────────────────────────────────────────────────────────────────
@app.post("/analyze")
async def analyze_cv(file: UploadFile = File(...), job_description: str = Form(...)):
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    try:
        result  = converter.convert(temp_path)
        cv_text = result.document.export_to_markdown()
        score   = get_matching_score(cv_text, job_description)
        advice  = get_ai_advice(cv_text, job_description, score)
        return {"score": f"{score}%", "recommendations": advice}
    except Exception as e:
        return {"error": str(e)}
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

# ── Generate CV (Markdown) ────────────────────────────────────────────────────
@app.post("/generate-cv")
async def rewrite_cv(file: UploadFile = File(...), job_description: str = Form(...)):
    temp_path = f"temp_gen_{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    try:
        result         = converter.convert(temp_path)
        cv_text        = result.document.export_to_markdown()
        new_cv_markdown = generate_revised_cv(cv_text, job_description)
        return {"status": "success", "revised_cv_markdown": new_cv_markdown}
    except Exception as e:
        return {"error": str(e)}
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

# ── Generate CV (PDF) ─────────────────────────────────────────────────────────
@app.post("/generate-cv-pdf")
async def generate_cv_pdf(
    cv_markdown: str = Form(...),
    photo: UploadFile = File(None)
):
    """
    Reçoit le markdown du CV + photo optionnelle.
    Retourne un PDF téléchargeable.
    """
    try:
        photo_bytes = None
        if photo and photo.filename:
            photo_bytes = await photo.read()

        print(f"[PDF] Génération pour {len(cv_markdown)} chars de markdown")
        pdf_bytes = generate_pdf(cv_markdown, photo_bytes)
        print(f"[PDF] Généré : {len(pdf_bytes)} bytes")

        if not pdf_bytes:
            raise ValueError("Le PDF généré est vide")

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=cv-optimise.pdf",
                "Content-Length": str(len(pdf_bytes))
            }
        )
    except Exception as e:
        print(f"[PDF ERROR] {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
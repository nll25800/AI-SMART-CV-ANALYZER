from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from docling.document_converter import DocumentConverter
import shutil, os, traceback

from engine import get_matching_score
from recommender import get_ai_advice, generate_revised_cv_structured
from scraper import search_jobs
from cv_pdf_generator import generate_pdf
from cv_schema import CVData
from pydantic import ValidationError

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

@app.get("/mentions-legales")
async def serve_legal_page():
    return FileResponse("../frontend/mentions-legales.html")

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

# ── Generate CV (JSON structuré) ──────────────────────────────────────────────
@app.post("/generate-cv")
async def rewrite_cv(file: UploadFile = File(...), job_description: str = Form(...)):
    temp_path = f"temp_gen_{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    try:
        result   = converter.convert(temp_path)
        cv_text  = result.document.export_to_markdown()
        cv_data  = generate_revised_cv_structured(cv_text, job_description)
        return {"status": "success", "revised_cv_data": cv_data.model_dump()}
    except ValueError as e:
        # Échec après les tentatives de retry dans generate_revised_cv_structured
        return {"error": str(e)}
    except Exception as e:
        return {"error": str(e)}
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

# ── Generate CV (PDF) ─────────────────────────────────────────────────────────
@app.post("/generate-cv-pdf")
async def generate_cv_pdf(
    cv_data: str = Form(...),
    photo: UploadFile = File(None)
):
    """
    Reçoit le CV structuré (JSON, conforme à CVData) en string + photo optionnelle.
    Retourne un PDF téléchargeable.
    """
    try:
        # On valide le JSON reçu contre le schéma avant de le passer au générateur PDF.
        # Ça évite qu'un JSON malformé (venant d'un bug frontend, ou d'une manip
        # directe de l'API) fasse planter reportlab avec une erreur obscure.
        try:
            cv_data_obj = CVData.model_validate_json(cv_data)
        except ValidationError as e:
            raise HTTPException(status_code=422, detail=f"cv_data invalide : {e}")

        # Logs de diagnostic explicites : on veut savoir précisément si une
        # photo a été reçue, avec quel nom/taille, pour identifier si le
        # problème vient du frontend (rien n'est envoyé) ou d'ailleurs.
        if photo is None:
            print("[PDF] Aucun champ 'photo' reçu dans la requête (photo=None)")
        elif not photo.filename:
            print(f"[PDF] Champ 'photo' reçu mais vide (filename={photo.filename!r})")
        else:
            print(f"[PDF] Photo reçue : filename={photo.filename!r}, content_type={photo.content_type!r}")

        photo_bytes = None
        if photo and photo.filename:
            photo_bytes = await photo.read()
            print(f"[PDF] Photo lue : {len(photo_bytes)} bytes")

        print(f"[PDF] Génération pour le CV de {cv_data_obj.name}")
        pdf_bytes = generate_pdf(cv_data_obj.model_dump(), photo_bytes)
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
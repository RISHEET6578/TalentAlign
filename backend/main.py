import os
import io
import re
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pypdf import PdfReader
import docx
from google.genai import Client

app = FastAPI(title="TalentAlign API Engine", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    ai_client = Client()
except Exception:
    ai_client = None

def extract_text_from_docx(file_bytes: bytes) -> str:
    doc = docx.Document(io.BytesIO(file_bytes))
    return "\n".join([para.text for para in doc.paragraphs])

def extract_links(text: str) -> list:
    found_links = []
    for word in text.split():
        if any(k in word for k in ["github.com", "linkedin.com", "http", "www."]):
            found_links.append(word.strip(",;|()[]{}"))
    lower_text = text.lower()
    if "linkedin" in lower_text and not any("linkedin" in l for l in found_links):
        found_links.append("linkedin.com (Profile Detected)")
    if "portfolio" in lower_text and not any("portfolio" in l or "github" in l for l in found_links):
        found_links.append("External Portfolio (Detected)")
    return list(set(found_links))

@app.post("/api/v1/evaluate")
async def evaluate_resume(resume: UploadFile = File(...), job_description: str = Form(...)):
    filename_lower = resume.filename.lower()
    if not (filename_lower.endswith('.pdf') or filename_lower.endswith('.docx')):
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported.")
    
    try:
        file_content = await resume.read()
        extracted_text = ""
        
        if filename_lower.endswith('.pdf'):
            pdf_reader = PdfReader(io.BytesIO(file_content))
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    extracted_text += page_text + "\n"
        elif filename_lower.endswith('.docx'):
            extracted_text = extract_text_from_docx(file_content)
                
        if not extracted_text.strip():
            raise HTTPException(status_code=400, detail="The file contains no readable text.")
            
        # Hardcoded skill parsing matching your original design rules
        jd_words = set(re.findall(r'\b\w+\b', job_description.lower()))
        resume_words = set(re.findall(r'\b\w+\b', extracted_text.lower()))
        
        # Simple extraction strategy for core keywords
        common_tech = {"python", "java", "c++", "javascript", "react", "sql", "aws", "docker", "kubernetes", "machine learning", "deep learning", "git"}
        jd_skills = jd_words.intersection(common_tech)
        resume_skills = resume_words.intersection(common_tech)
        
        detected_links = extract_links(extracted_text)
        links_score = 100.0 if len(detected_links) > 0 else 0.0

        if not jd_skills:
            keyword_score = 100.0
            matched_skills = set()
            missing_skills = []
        else:
            matched_skills = resume_skills.intersection(jd_skills)
            missing_skills = list(jd_skills.difference(resume_skills))
            keyword_score = (len(matched_skills) / len(jd_skills)) * 100

        semantic_score = 50.0 
        if ai_client:
            prompt = f"Rate structural match between Resume and JD from 0.0 to 1.0. Output numbers only.\nRESUME:\n{extracted_text[:3000]}\nJD:\n{job_description[:1500]}"
            try:
                response = ai_client.models.generate_content(model='gemini-3.1-flash-lite', contents=prompt)
                match = re.search(r"0\.\d+|1\.0|\d+", response.text.strip())
                if match:
                    semantic_score = min(float(match.group()) * 100, 100.0)
            except Exception:
                pass

        final_score = round((semantic_score * 0.50) + (keyword_score * 0.40) + (links_score * 0.10), 2)
        rating = "STRONG MATCH" if final_score >= 70 else "AVERAGE MATCH" if final_score >= 40 else "WEAK MATCH"

        return {
            "final_match_rating": rating,
            "overall_score": final_score,
            "breakdown": {
                "semantic_context_score": round(semantic_score, 2),
                "hard_skills_coverage_score": round(keyword_score, 2),
                "online_presence_score": links_score
            },
            "extracted_assets": {
                "detected_links": detected_links,
                "matched_skills": list(matched_skills),
                "missing_skills_in_demand": missing_skills
            },
            "raw_resume_text": extracted_text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/coaching")
async def generate_coaching_feedback(resume_text: str = Form(...), job_description: str = Form(...), overall_score: float = Form(...)):
    if not ai_client:
        return {"coaching_report": "⚠️ AI Coaching unavailable."}
    prompt = f"Provide career advice matching Markdown requirements for score {overall_score}%.\nResume: {resume_text[:2000]}\nJD: {job_description[:1000]}"
    try:
        response = ai_client.models.generate_content(model='gemini-3.1-flash-lite', contents=prompt)
        return {"coaching_report": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

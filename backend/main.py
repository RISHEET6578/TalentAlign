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

        matched_skills = []
        missing_skills = []
        semantic_score = 65.0

        if ai_client:
            prompt = f"""
            Analyze this resume and job description to extract core competencies.
            
            RESUME:
            {extracted_text[:3000]}
            
            JOB DESCRIPTION:
            {job_description[:1500]}
            
            Return the output strictly in this pattern:
            SCORE: [Insert match score between 0 and 100]
            MATCHED_SKILLS: [Comma-separated skills present in the resume that align with the job description requirements]
            MISSING_SKILLS: [Comma-separated skills missing or required by the job description but weak in the resume]
            """
            try:
                response = ai_client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                res_text = str(response.text)
                
                normalized_text = re.sub(r'[\*_]', '', res_text)
                
                score_match = re.search(r"SCORE:\s*(\d+)", normalized_text, re.IGNORECASE)
                if score_match:
                    semantic_score = float(score_match.group(1))
                    
                matched_match = re.search(r"MATCHED_SKILLS:\s*(.*?)(?=MISSING_SKILLS:|$)", normalized_text, re.IGNORECASE | re.DOTALL)
                if matched_match:
                    content = matched_match.group(1).strip()
                    if content and content.lower() != "none":
                        matched_skills = [s.strip() for s in content.split(",") if s.strip()]
                        
                missing_match = re.search(r"MISSING_SKILLS:\s*(.*)", normalized_text, re.IGNORECASE | re.DOTALL)
                if missing_match:
                    content = missing_match.group(1).strip()
                    if content and content.lower() != "none":
                        missing_skills = [s.strip() for s in content.split(",") if s.strip()]
            except Exception:
                pass

        detected_links = extract_links(extracted_text)
        links_score = 100.0 if len(detected_links) > 0 else 0.0

        final_score = round((semantic_score * 0.90) + (links_score * 0.10), 2)
        rating = "STRONG MATCH" if final_score >= 70 else "AVERAGE MATCH" if final_score >= 40 else "WEAK MATCH"

        return {
            "final_match_rating": rating,
            "overall_score": final_score,
            "breakdown": {
                "semantic_context_score": round(semantic_score, 2),
                "hard_skills_coverage_score": round(semantic_score, 2),
                "online_presence_score": links_score
            },
            "extracted_assets": {
                "detected_links": detected_links,
                "matched_skills": matched_skills,
                "missing_skills_in_demand": missing_skills
            },
            "raw_resume_text": extracted_text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/coaching")
async def generate_coaching_feedback(resume_text: str = Form(...), job_description: str = Form(...), overall_score: float = Form(...)):
    if not ai_client:
        return {"coaching_report": "⚠️ AI Coaching system is currently offline."}
        
    prompt = f"""
    You are an expert career coach. Analyze the candidate's resume and target job description to create an operational optimization action plan.
    Provide constructive, markdown-formatted professional advice including structured action bullets on how they can bridge their gaps for this position.
    
    Current Match Score: {overall_score}%
    
    Candidate Resume Background: 
    {resume_text[:2500]}
    
    Target Job Description: 
    {job_description[:1500]}
    """
    try:
        response = ai_client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
        return {"coaching_report": response.text.strip()}
    except Exception as e:
        return {"coaching_report": f"⚠️ Error generating feedback: {str(e)}"}

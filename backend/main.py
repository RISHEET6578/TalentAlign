import os
import io
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pypdf import PdfReader
import docx

# Import your native local dictionary logic
from backend.parser import extract_skills_from_text
from backend.matcher import calculate_match_matrix, ai_client

app = FastAPI(title="TalentAlign API Engine", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def extract_text_from_docx(file_bytes: bytes) -> str:
    doc = docx.Document(io.BytesIO(file_bytes))
    return "\n".join([para.text for para in doc.paragraphs])

@app.get("/")
def home():
    return {"status": "TalentAlign API Engine is running smoothly!"}

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

        # Run your precise local keyword array extractions
        resume_skills = extract_skills_from_text(extracted_text)
        jd_skills = extract_skills_from_text(job_description)

        # Run your matrix calculations
        report_data = calculate_match_matrix(extracted_text, job_description, resume_skills, jd_skills)
        
        # 🛡️ Safety Check: Ensure report_data is valid and has expected keys
        if not report_data or not isinstance(report_data, dict):
            # Fallback structure if calculation returns None or fails
            report_data = {
                "final_match_rating": "AVERAGE MATCH",
                "overall_score": 50.0,
                "breakdown": {
                    "semantic_context_score": 50.0,
                    "hard_skills_coverage_score": 50.0,
                    "online_presence_score": 0.0
                },
                "extracted_assets": {
                    "detected_links": [],
                    "matched_skills": list(resume_skills.intersection(jd_skills)) if jd_skills else [],
                    "missing_skills_in_demand": list(jd_skills.difference(resume_skills)) if jd_skills else []
                }
            }
        
        # Keep raw text available for the follow-up coaching script call
        report_data["raw_resume_text"] = extracted_text
        return report_data

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
        response = ai_client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        return {"coaching_report": response.text.strip()}
    except Exception as e:
        return {"coaching_report": f"⚠️ Error generating feedback: {str(e)}"}

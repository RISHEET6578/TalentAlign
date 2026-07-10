import os
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pypdf import PdfReader
import docx  # Import python-docx
import io

from backend.parser import extract_skills_from_text
from backend.matcher import calculate_match_matrix
from google.genai import Client

app = FastAPI(title="AI Candidate Screening Engine API", version="1.2.0")

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
    """Helper function to extract clean text from a DOCX file stream."""
    doc = docx.Document(io.BytesIO(file_bytes))
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return "\n".join(full_text)

@app.post("/api/v1/evaluate")
async def evaluate_resume(resume: UploadFile = File(...), job_description: str = Form(...)):
    filename_lower = resume.filename.lower()
    
    # Supported format guard rails
    if not (filename_lower.endswith('.pdf') or filename_lower.endswith('.docx')):
        raise HTTPException(status_code=400, detail="Invalid format. Only PDF and DOCX files are supported.")
    
    try:
        file_content = await resume.read()
        extracted_text = ""
        
        # Route processing based on file extension type
        if filename_lower.endswith('.pdf'):
            pdf_reader = PdfReader(io.BytesIO(file_content))
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    extracted_text += page_text + "\n"
        elif filename_lower.endswith('.docx'):
            extracted_text = extract_text_from_docx(file_content)
                
        if not extracted_text.strip():
            raise HTTPException(status_code=400, detail="The uploaded file contains no readable text contents.")
            
        resume_skills = extract_skills_from_text(extracted_text)
        jd_skills = extract_skills_from_text(job_description)
        
        report = calculate_match_matrix(extracted_text, job_description, resume_skills, jd_skills)
        report["raw_resume_text"] = extracted_text
        return report
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal processing failure: {str(e)}")


@app.post("/api/v1/coaching")
async def generate_coaching_feedback(
    resume_text: str = Form(...), 
    job_description: str = Form(...),
    overall_score: float = Form(...)
):
    if not ai_client:
        return {"coaching_report": "⚠️ AI Coaching is currently unavailable. Please verify your GEMINI_API_KEY environment variable setup."}

    prompt = f"""
    You are an elite Tech Career Coach and Senior Technical Recruiter. 
    Analyze this candidate's Resume against the Target Job Description (JD). The current system assigned them an overall score of {overall_score}%.
    
    Provide a highly constructive, friendly, and structured "Bridge the Gap" guide in Markdown format with these exact headings:
    
    ### 🕵️‍♂️ Why is the Score at this Level?
    (Give a brief 2-3 sentence high-level summary explaining the structural alignment or identity gap between their resume projects and the job description expectations.)
    
    ### 🛠️ Critical Missing Proficiencies
    (Look at the technical stack requirements and list the specific frameworks, architectures, or concepts they missed. Suggest what they should learn next.)
    
    ### 📝 Resume Adjustment Strategies
    (Give 2 actionable bullet points on how they can reword, emphasize, or reframe their existing experience, projects, or certifications to show stronger alignment with what the company asks for.)
    
    ---
    **Resume Text:**
    {resume_text}
    
    **Job Description Text:**
    {job_description}
    """

    try:
        response = ai_client.models.generate_content(
            model='gemini-3.1-flash-lite',
            contents=prompt,
        )
        return {"coaching_report": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini API failure: {str(e)}")
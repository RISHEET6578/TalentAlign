import os
import re
from google.genai import Client

# Pull the key from Render's environment setup
api_key_env = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

try:
    if api_key_env:
        ai_client = Client(api_key=api_key_env)
    else:
        ai_client = Client()
except Exception:
    ai_client = None

def extract_links(text: str) -> list:
    """Scans the raw text string to extract portfolio link metrics."""
    found_links = []
    for word in text.split():
        if "github.com" in word or "linkedin.com" in word or "http" in word or "www." in word:
            cleaned_link = word.strip(",;|()[]{}")
            found_links.append(cleaned_link)
            
    lower_text = text.lower()
    if "linkedin" in lower_text and not any("linkedin" in l for l in found_links):
        found_links.append("linkedin.com (Profile Detected)")
    if "portfolio" in lower_text and not any("portfolio" in l or "github" in l for l in found_links):
        found_links.append("External Portfolio (Detected)")
            
    return list(set(found_links))


def calculate_match_matrix(resume_text: str, jd_text: str, resume_skills: set, jd_skills: set) -> dict:
    """Evaluates universal candidate eligibility by mapping hard skill metrics,
    online presence validations, and deep semantic project embeddings via Gemini."""
    detected_links = extract_links(resume_text)
    links_score = 100.0 if len(detected_links) > 0 else 0.0

    if not jd_skills:
        keyword_score = 100.0
        matched_skills = set()
        missing_skills = []
    else:
        matched_skills = resume_skills.intersection(jd_skills)
        missing_skills = list(jd_skills.difference(resume_skills))
        keyword_score = (len(matched_skills) / len(jd_skills)) * 100

    # Fallback default score if API is down
    semantic_score = 50.0 
    
    if ai_client:
        prompt = f"""
        You are an API endpoint that outputs only a raw number.
        Rate the structural and contextual match between this Resume and Job Description on a scale from 0.0 to 1.0.
        Consider project alignment, experience level, and domain context.
        Respond with ONLY a decimal number between 0.0 and 1.0 (e.g., 0.78). Do not write code, markdown, or text.

        RESUME:
        {resume_text[:4000]}

        JOB DESCRIPTION:
        {jd_text[:2000]}
        """
        try:
            response = ai_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            match = re.search(r"0\.\d+|1\.0|\d+", response.text.strip())
            if match:
                parsed_val = float(match.group())
                if parsed_val > 1.0:
                    semantic_score = min(parsed_val, 100.0)
                else:
                    semantic_score = parsed_val * 100
        except Exception:
            pass 

    final_score = (semantic_score * 0.50) + (keyword_score * 0.40) + (links_score * 0.10)
    final_score = round(final_score, 2)

    if final_score >= 70:
        rating = "STRONG MATCH"
    elif final_score >= 40:
        rating = "AVERAGE MATCH"
    else:
        rating = "WEAK MATCH"

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
        }
    }

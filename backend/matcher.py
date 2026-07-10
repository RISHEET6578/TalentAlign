import re
import os
import numpy as np
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Initialize the local AI embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

def extract_links(text: str) -> list:
    """
    Scans the raw text string to extract portfolio link metrics.
    Includes explicit keyword fallback scanning for clean text representations.
    """
    # 1. Standard URL pattern match
    url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+|[a-zA-Z0-9.-]+\.(?:com|io|me|net)(/[^\s<>"]*)?'
    links = re.findall(url_pattern, text)
    
    found_links = []
    for word in text.split():
        if "github.com" in word or "linkedin.com" in word or "http" in word or "www." in word:
            cleaned_link = word.strip(",;|()[]{}")
            found_links.append(cleaned_link)
            
    # 2. Contextual Fallback: If text labels exist but raw URLs were stripped by the parser
    lower_text = text.lower()
    if "linkedin" in lower_text and not any("linkedin" in l for l in found_links):
        found_links.append("linkedin.com (Profile Detected)")
    if "portfolio" in lower_text and not any("portfolio" in l or "github" in l for l in found_links):
        found_links.append("External Portfolio (Detected)")
            
    return list(set(found_links))


def calculate_match_matrix(resume_text: str, jd_text: str, resume_skills: set, jd_skills: set) -> dict:
    """
    Evaluates universal candidate eligibility by mapping hard skill metrics,
    online presence validations, and deep semantic project embeddings.
    """
    detected_links = extract_links(resume_text)
    links_score = 100.0 if len(detected_links) > 0 else 0.0

    if not jd_skills:
        keyword_score = 100.0
        missing_skills = []
    else:
        matched_skills = resume_skills.intersection(jd_skills)
        missing_skills = list(jd_skills.difference(resume_skills))
        keyword_score = (len(matched_skills) / len(jd_skills)) * 100

    embeddings = embedding_model.encode([resume_text, jd_text])
    semantic_sim = cosine_similarity(
        embeddings[0].reshape(1, -1), 
        embeddings[1].reshape(1, -1)
    )[0][0]
    
    semantic_score = max(0.0, float(semantic_sim)) * 100

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

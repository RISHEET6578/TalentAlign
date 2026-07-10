import re

# A massive, comprehensive skills dictionary for modern tech ecosystems
SKILL_KEYWORDS = {
    # --- Advanced AI & Data Science ---
    "python", "machine learning", "ml", "deep learning", "dl", "tensorflow", "pytorch", 
    "nlp", "natural language processing", "genai", "generative ai", "llm", "large language models", 
    "rag", "agentic ai", "prompt engineering", "langchain", "scikit-learn", "pandas", "numpy",
    
    # --- Modern Web & App Development ---
    "html", "css", "javascript", "typescript", "react", "react native", "node.js", "next.js", 
    "angular", "vue", "fastapi", "django", "flask", "android", "ios", "xml",
    
    # --- Enterprise Backend Languages & Ecosystems ---
    "java", "c", "c++", "c#", "csharp", ".net", "dotnet", "asp.net", "go", "golang", "ruby", "php",
    
    # --- Cloud, DevOps & Data Platforms ---
    "aws", "amazon web services", "azure", "gcp", "google cloud", "docker", "kubernetes", 
    "sql", "nosql", "mongodb", "postgresql", "mysql", "redis", "git", "github",
    
    # --- System Engineering & Core Concepts ---
    "data structures", "algorithms", "dsa", "oops", "computer networks", "operating systems", 
    "dbms", "sdlc", "cybersecurity", "linux", "windows", "wireshark", "mininet", "ryu",
    
    # --- Management, Experience Tracking & Agile ---
    "agile", "scrum", "kanban", "jira", "ci/cd", "devops", "system design", "microservices"
}

def extract_skills_from_text(text: str) -> set:
    """
    Cleanses the text corpus and extracts recognizable technical skill signatures.
    Handles shorthand punctuation mappings natively (like .net or c#).
    """
    if not text:
        return set()
        
    # Convert text to lowercase
    lower_text = text.lower()
    
    # Clean text but preserve characters like '+' and '#' and '.' for c++, c#, and .net
    cleaned_text = re.sub(r'[^a-zA-Z0-9+#\.\s]', ' ', lower_text)
    
    found_skills = set()
    
    for skill in SKILL_KEYWORDS:
        # Protect specific shortcuts using rigid regex boundaries
        if skill in ["c#", "csharp", ".net", "dotnet", "c++", "ml", "dl", "nlp", "aws"]:
            if skill in lower_text:
                found_skills.add(skill)
        else:
            if re.search(r'\b' + re.escape(skill) + r'\b', cleaned_text):
                found_skills.add(skill)
                
    # Normalize synonyms so matching works perfectly even if phrasing is different
    normalized_skills = set()
    for s in found_skills:
        if s == "csharp": normalized_skills.add("c#")
        elif s == "dotnet": normalized_skills.add(".net")
        elif s == "natural language processing": normalized_skills.add("nlp")
        elif s == "deep learning": normalized_skills.add("dl")
        elif s == "amazon web services": normalized_skills.add("aws")
        else:
            normalized_skills.add(s)
            
    return normalized_skills
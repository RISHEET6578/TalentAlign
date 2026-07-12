# TalentAlign AI 🎯👔

### Decoupled Intelligent Talent Acquisition Architecture with Modular Competency Matrix Integration

**TalentAlign AI** is a production-grade, decoupled applicant tracking and automated resume-to-JD evaluation engine. It leverages a high-performance local technical dictionary alongside advanced semantic analysis to parse, match, score, and deliver operational career optimization plans for candidates in real time with zero structural drift.

---

## 🏛️ Architecture Overview

The system is engineered using a decoupled microservices-style architecture to ensure complete isolation of concerns, secure environment abstraction, and flawless scalability.
```text
+-----------------------------------+                +-----------------------------------+
|        Streamlit Frontend         |   REST API     |          FastAPI Backend          |
|  (Hosted on Streamlit Community)  | -------------> |        (Hosted on Render)         |
+-----------------------------------+   (HTTP POST)  +-----------------------------------+
                                                                       |
                                                        +--------------+--------------+
                                                        |                             |
                                                        v                             v
                                                +---------------+             +---------------+
                                                | Local Parser  |             |  Gemini 2.5   |
                                                | (Regex Engine)|             |     Flash     |
                                                +---------------+             +---------------+
```
* **Frontend (UI Layer):** Built with **Streamlit**, providing a clean, multi-column dashboard workspace that safely manages view states, layout rendering, and color-coded badge populations completely isolated from backend analytics.
* **Backend (Engine Layer):** Built with **FastAPI**, strictly abstracting private environment authorizations (`GEMINI_API_KEY`), running custom rule-based dictionary lookups, and orchestration routines.

---

## 🛠️ Engineering Highlight: Hybrid Match Matrix & Defensive API Integration

### The Problem (Silent Failures & Parsing Blindspots)
Early iterations relied strictly on prompting an LLM to read both files and spit out an unstructured text string, trying to parse lists using fragile text splits. This caused two major production bottlenecks:
1. **Silent Drops:** When the LLM structure drifted or safety filters triggered, the system hit unexpected errors, resulting in empty keyword blocks or complete data drops.
2. **Context Loss:** Pure text extractions frequently misread specific developer shorthands (like `C++`, `C#`, or `.NET`), stripping out essential punctuation and generating inaccurate gap evaluations.

### The Solution (Modular Parsing & Defensive Interception)
The architecture was refactored into a high-performance **Hybrid Matrix Execution Pipeline** combining rule-based deterministic parsing with semantic validation:
* **Deterministic Processing:** A robust local parser (`backend/parser.py`) cleans and processes tech assets natively using specialized boundary expressions to protect characters like `+` and `#`.
* **Architectural Isolation:** The matching core (`backend/matcher.py`) correlates exact overlaps natively (`intersection` and `difference`), keeping keyword scores predictable while reserving the live AI endpoint strictly for high-level semantic scoring.
* **Defensive Interception:** Guardrails were implemented across both endpoints to gracefully intercept `NoneType` responses and prevent crashing under traffic spikes, ensuring uninterrupted frontend operations.

---

## 🧰 Tech Stack & Pillars

* **LLM Engine:** Google Gemini 2.5 Flash *(Optimized for lightning-fast reasoning, strict instructions, and high-velocity feedback orchestration)*
* **Parsing & Evaluation Core:** Custom Python Regex Engines + PyPDF *(Structured text stream extractor)* + Python-Docx
* **Backend Framework:** FastAPI + Uvicorn ASGI Server
* **Frontend Interface:** Streamlit *(Session state-tracked with embedded custom CSS skill-tag badge rendering)*
* **Deployment Infrastructure:** GitHub *(CI/CD versioning)* + Render Cloud Services *(Backend Environment)*

---

## 🚀 Local Setup & Installation

To spin up this architecture locally inside an explicit development environment (e.g., Anaconda), follow these steps:

### 1. Clone and Navigate

git clone [https://github.com/RISHEET6578/TalentAlign-AI.git](https://github.com/RISHEET6578/TalentAlign-AI.git)
cd TalentAlign-AI

### 2. Install Dependencies

pip install -r requirements.txt

### 3. Environment Configuration
Create a local .env file in your root workspace configuration:

GEMINI_API_KEY="your_actual_gemini_api_key_here"

### 4. Fire up the Microservices Concurrently
Open two terminal instances to activate the decoupled layers cleanly:

Terminal 1 (Backend Engine Layer):

uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
Terminal 2 (Frontend App Layer):

streamlit run frontend/app.py
## 📊 Structured Response Demonstration
The engine splits incoming raw asset files into an identical, highly organized structured JSON schema before parsing it out to the client workspace layouts:

JSON
{
  "final_match_rating": "STRONG MATCH",
  "overall_score": 85.5,
  "breakdown": {
    "semantic_context_score": 80.0,
    "hard_skills_coverage_score": 90.0,
    "online_presence_score": 100.0
  },
  "extracted_assets": {
    "detected_links": ["github.com", "linkedin.com"],
    "matched_skills": ["python", "c++", "fastapi", "docker"],
    "missing_skills_in_demand": ["kubernetes", "aws"]
  }
}

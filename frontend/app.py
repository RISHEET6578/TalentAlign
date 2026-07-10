import streamlit as st
import requests

st.set_page_config(page_title="TalentAlign", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .skill-tag { display: inline-block; background-color: #E1F5FE; color: #0288D1; padding: 4px 10px; margin: 3px; border-radius: 15px; font-weight: 500; font-size: 13px; }
    .missing-tag { display: inline-block; background-color: #FFEBEE; color: #C62828; padding: 4px 10px; margin: 3px; border-radius: 15px; font-weight: 500; font-size: 13px; }
    </style>
""", unsafe_allow_html=True)

st.title("🎯 TalentAlign: Smart Matcher Desk")
st.markdown("---")

# 🚨 BACKEND ENDPOINT SPECIFICATION
BACKEND_URL = "https://talentalign-uc88.onrender.com" 

col1, col2 = st.columns([1, 1], gap="large")
with col1:
    st.subheader("✨ Your Story (Resume)")
    uploaded_file = st.file_uploader("Drop resume", type=["pdf", "docx"], label_visibility="collapsed")
with col2:
    st.subheader("📝 Their Ask (JD)")
    jd_text = st.text_area("Paste role criteria", height=150, label_visibility="collapsed")

if st.button("🚀 Bridge the Gap", type="primary", use_container_width=True):
    if uploaded_file and jd_text.strip():
        if "coaching_report" in st.session_state:
            del st.session_state["coaching_report"]
        with st.spinner("Analyzing..."):
            try:
                files = {"resume": (uploaded_file.name, uploaded_file.getvalue(), "application/octet-stream")}
                response = requests.post(f"{BACKEND_URL}/api/v1/evaluate", files=files, data={"job_description": jd_text})
                if response.status_code == 200:
                    st.session_state["report"] = response.json()
                    st.session_state["jd_text_saved"] = jd_text
                else:
                    st.error(f"Backend 404/Error Path: {response.status_code}")
            except Exception as e:
                st.error(f"Cannot contact engine: {e}")

if "report" in st.session_state:
    report = st.session_state["report"]
    st.markdown(f"### Scorecard: {report['final_match_rating']} ({report['overall_score']}%)")
    st.progress(int(report['overall_score']))
    
    assets = report["extracted_assets"]
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### 🟢 Matched Competencies")
        if assets.get("matched_skills"):
            st.markdown("".join([f"<span class='skill-tag'>{s}</span>" for s in assets["matched_skills"]]), unsafe_allow_html=True)
        else:
            st.caption("No specific keyword tags matched from the standard checklist.")
            
    with c2:
        st.markdown("##### 💡 Missing Skills")
        if assets.get("missing_skills_in_demand"):
            st.markdown("".join([f"<span class='missing-tag'>{s}</span>" for s in assets["missing_skills_in_demand"]]), unsafe_allow_html=True)
        else:
            st.caption("No clear missing tech stack gaps detected!")

    st.markdown("---")
    if st.button("🧠 Generate AI Optimization Plan"):
        with st.spinner("Running AI Coach..."):
            try:
                coaching_data = {"resume_text": report["raw_resume_text"], "job_description": st.session_state["jd_text_saved"], "overall_score": report['overall_score']}
                coach_response = requests.post(f"{BACKEND_URL}/api/v1/coaching", data=coaching_data)
                if coach_response.status_code == 200:
                    st.session_state["coaching_report"] = coach_response.json()["coaching_report"]
            except Exception as e:
                st.error(f"Coach connection error: {e}")

    if "coaching_report" in st.session_state:
        st.markdown(st.session_state["coaching_report"])

    # 🔍 Live Data Stream Inspector Window
    st.markdown("---")
    with st.expander("👀 Debug Inspection: Raw Backend Response Data"):
        st.json(report)

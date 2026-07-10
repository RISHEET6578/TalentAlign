import streamlit as st
import requests

st.set_page_config(page_title="AI Matcher", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .metric-card { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 5px solid #4A90E2; }
    .skill-tag { display: inline-block; background-color: #E1F5FE; color: #0288D1; padding: 4px 10px; margin: 3px; border-radius: 15px; font-weight: 500; font-size: 13px; }
    .missing-tag { display: inline-block; background-color: #FFEBEE; color: #C62828; padding: 4px 10px; margin: 3px; border-radius: 15px; font-weight: 500; font-size: 13px; }
    </style>
""", unsafe_allow_html=True)

st.title("🎯 TalentAlign: Smart Matcher Desk")
st.caption("Let's see how well this candidate matches the target role rules!")
st.markdown("---")

# 🌐 PRODUCTION CONFIGURATION: Put your live Render URL here!
# Replace this string with your exact live Render backend service URL.
BACKEND_URL = "https://talentalign.onrender.com" 

col1, col2 = st.columns([1, 1], gap="large")
with col1:
    st.subheader("✨ Your Story (Resume)")
    uploaded_file = st.file_uploader("Drop candidate resume here", type=["pdf", "docx"], label_visibility="collapsed")
with col2:
    st.subheader("📝 Their Ask (JD)")
    jd_text = st.text_area("Paste the role criteria, responsibilities, or skills here:", height=150, placeholder="E.g., Looking for a Python developer who knows SQL...", label_visibility="collapsed")

st.markdown("<br>", unsafe_allow_html=True)

if st.button("🚀 Bridge the Gap", type="primary", use_container_width=True):
    if uploaded_file and jd_text.strip():
        # Clear out any stale coach logs on a fresh submission click
        if "coaching_report" in st.session_state:
            del st.session_state["coaching_report"]
            
        with st.spinner("Analyzing data and matching skills..."):
            try:
                files = {"resume": (uploaded_file.name, uploaded_file.getvalue(), "application/octet-stream")}
                # Updated to use live cloud backend destination
                response = requests.post(f"{BACKEND_URL}/api/v1/evaluate", files=files, data={"job_description": jd_text})
                
                if response.status_code == 200:
                    st.session_state["report"] = response.json()
                    st.session_state["jd_text_saved"] = jd_text
                else:
                    st.error(f"Backend returned an error status code: {response.status_code}")
            except Exception as e:
                st.error(f"Could not connect to the online server engine: {e}")
    else:
        st.error("Please ensure you've uploaded a resume PDF/DOCX and pasted a job description first!")

# Check if an analysis report is active in memory state to render views
if "report" in st.session_state:
    report = st.session_state["report"]
    jd_text_saved = st.session_state["jd_text_saved"]
    
    st.markdown("### 📊 Your Match Scorecard")
    rating = report["final_match_rating"]
    score = report["overall_score"]
    
    m1, m2 = st.columns([1, 2])
    with m1:
        if rating == "STRONG MATCH":
            st.success(f"🏆 **{rating}**")
        elif rating == "AVERAGE MATCH":
            st.warning(f"⚠️ **{rating}**")
        else:
            st.error(f"🛑 **{rating}**")
    with m2:
        st.progress(int(score))
        st.markdown(f"**Overall Eligibility Standing:** `{score}%`")
    
    st.markdown("#### Score Breakdown")
    b1, b2, b3 = st.columns(3)
    breakdown = report["breakdown"]
    b1.metric("Project & Experience Match", f"{breakdown['semantic_context_score']}%")
    b2.metric("Core Technical Skills Match", f"{breakdown['hard_skills_coverage_score']}%")
    b3.metric("Online Profile Links Found", f"{breakdown['online_presence_score']}%")
    
    st.markdown("---")
    
    assets = report["extracted_assets"]
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### 🟢 Matched Competencies")
        if assets["matched_skills"]:
            html_tags = "".join([f"<span class='skill-tag'>{s}</span>" for s in assets["matched_skills"]])
            st.markdown(html_tags, unsafe_allow_html=True)
        else:
            st.info("No matching tech keywords found yet.")
        
        st.markdown("##### 🔗 Discovered Online Profiles")
        if assets["detected_links"]:
            for link in assets["detected_links"]:
                display_name = link.split(" ")[0] if " " in link else link
                url_target = display_name if display_name.startswith("http") else "https://" + display_name
                st.markdown(f"🔗 [{link}]({url_target})")
        else:
            st.caption("No portfolio or platform profile links found on this resume.")
            
    with c2:
        st.markdown("##### 💡 Key Skills to Add")
        if assets["missing_skills_in_demand"]:
            html_missing = "".join([f"<span class='missing-tag'>{s}</span>" for s in assets["missing_skills_in_demand"]])
            st.markdown(html_missing, unsafe_allow_html=True)
        else:
            st.success("Awesome! The candidate has every single skill requested in the job description!")

    st.markdown("---")
    
    # --- ENTERPRISE AI COACHING INTERFACE BLOCK ---
    st.markdown("### 💡 Strategic Upskilling & Coaching Advisor")
    st.write("Want to know exactly how to adjust your projects or what specific proficiencies to learn next to dominate this role?")
    
    if st.button("🧠 Generate AI Optimization Plan", type="secondary"):
        with st.spinner("Analyzing skill gaps and structural context metrics..."):
            try:
                coaching_data = {
                    "resume_text": report["raw_resume_text"],
                    "job_description": jd_text_saved,
                    "overall_score": score
                }
                # Updated to use live cloud backend destination
                coach_response = requests.post(f"{BACKEND_URL}/api/v1/coaching", data=coaching_data)
                if coach_response.status_code == 200:
                    st.session_state["coaching_report"] = coach_response.json()["coaching_report"]
                else:
                    st.error(f"Coach API backend error response code: {coach_response.status_code}")
            except Exception as e:
                st.error(f"Failed to generate coaching strategy data: {e}")

    # --- FIXED NATIVE STREAMLIT AI COACHING INTERFACE BLOCK ---
    if "coaching_report" in st.session_state:
        with st.container():
            st.markdown(st.session_state["coaching_report"])

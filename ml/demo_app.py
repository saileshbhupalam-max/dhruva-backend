"""
DHRUVA ML Demo - Streamlit App
==============================
- Clarifying questions asked to CITIZEN (not officer)
- Officer provides feedback/reasoning for decisions
- High contrast: black text, light backgrounds only

Run with: streamlit run demo_app.py
"""

import sys
from pathlib import Path
from datetime import datetime
import streamlit.components.v1 as components

sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
from grievance_processor import GrievanceProcessor
from clarifying_questions import get_clarifying_questions
from knowledge_graph import (
    GrievanceKnowledgeGraph,
    check_pyvis_available,
    DISTRICT_DATA,
    DEPARTMENT_DATA,
    KEY_STATS,
)

# Page config
st.set_page_config(
    page_title="DHRUVA Demo",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================================
# CSS - Matching Frontend Design System (tailwind.config.js)
# Colors: primary=#1E40AF, success=#10B981, warning=#F59E0B, danger=#EF4444
# ============================================================================
st.markdown("""
<style>
    /* ===== DESIGN SYSTEM TOKENS ===== */
    :root {
        /* Primary Blue - matches frontend */
        --primary: #1E40AF;
        --primary-50: #EFF6FF;
        --primary-100: #DBEAFE;
        --primary-200: #BFDBFE;
        --primary-700: #1E40AF;
        --primary-800: #1E3A8A;

        /* Success Green */
        --success: #10B981;
        --success-50: #ECFDF5;
        --success-100: #D1FAE5;
        --success-700: #047857;

        /* Warning Amber */
        --warning: #F59E0B;
        --warning-50: #FFFBEB;
        --warning-100: #FEF3C7;
        --warning-600: #D97706;

        /* Danger Red */
        --danger: #EF4444;
        --danger-50: #FEF2F2;
        --danger-100: #FEE2E2;
        --danger-600: #DC2626;

        /* Neutrals */
        --gray-50: #F9FAFB;
        --gray-100: #F3F4F6;
        --gray-200: #E5E7EB;
        --gray-300: #D1D5DB;
        --gray-500: #6B7280;
        --gray-600: #4B5563;
        --gray-700: #374151;
        --gray-900: #111827;
        --white: #FFFFFF;
    }

    /* ===== GLOBAL STYLES ===== */
    .main .block-container {
        padding: 1rem;
        max-width: 100%;
        background: var(--white) !important;
    }

    /* Force readable text - gray-900 on light backgrounds */
    .main, .main p, .main div, .main span, .main label,
    .main h1, .main h2, .main h3, .main h4, .main h5, .main h6 {
        color: var(--gray-900) !important;
    }

    /* ===== HEADER ===== */
    .demo-header {
        text-align: center;
        padding: 1rem 0;
        background: var(--gray-100) !important;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .demo-title {
        font-size: 2rem;
        font-weight: 800;
        color: var(--gray-900) !important;
        margin: 0;
    }
    .demo-subtitle {
        font-size: 1rem;
        color: var(--gray-600) !important;
        margin: 0;
    }

    /* ===== PROGRESS STEPPER (matches Stepper.tsx) ===== */
    .progress-container {
        display: flex;
        justify-content: center;
        gap: 0.5rem;
        margin: 1rem 0;
        flex-wrap: wrap;
    }
    .progress-pill {
        padding: 0.625rem 1rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 500;
        color: var(--gray-600) !important;
        background: var(--gray-200) !important;
    }
    .progress-active {
        background: var(--primary-100) !important;
        color: var(--primary-700) !important;
        box-shadow: 0 0 0 4px var(--primary-50);
    }
    .progress-done {
        background: var(--success-100) !important;
        color: var(--success-700) !important;
    }

    /* ===== CARDS (matches Card.tsx) ===== */
    .card {
        background: var(--white) !important;
        border-radius: 0.5rem;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
        padding: 1.5rem;
        margin: 0.75rem 0;
    }
    .card-success {
        background: var(--success-50) !important;
        border-left: 4px solid var(--success) !important;
    }
    .card-warning {
        background: var(--warning-50) !important;
        border-left: 4px solid var(--warning) !important;
    }
    .card-info {
        background: var(--primary-50) !important;
        border-left: 4px solid var(--primary) !important;
    }
    .card-label {
        font-size: 0.875rem;
        color: var(--gray-500) !important;
        margin-bottom: 0.25rem;
    }
    .card-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--gray-900) !important;
    }
    .card-sub {
        font-size: 0.75rem;
        color: var(--gray-600) !important;
        margin-top: 0.25rem;
    }

    /* ===== TIMELINE ===== */
    .timeline-entry {
        display: flex;
        gap: 0.75rem;
        margin: 0.75rem 0;
        padding: 1rem;
        background: var(--white) !important;
        border: 1px solid var(--gray-200) !important;
        border-left: 4px solid var(--primary) !important;
        border-radius: 0.5rem;
    }
    .timeline-icon {
        font-size: 1.3rem;
        flex-shrink: 0;
    }
    .timeline-text {
        flex: 1;
    }
    .timeline-title {
        font-weight: 600;
        color: var(--gray-900) !important;
        font-size: 1rem;
    }
    .timeline-desc {
        color: var(--gray-700) !important;
        font-size: 0.875rem;
        margin-top: 0.2rem;
    }
    .timeline-time {
        color: var(--gray-500) !important;
        font-size: 0.75rem;
        margin-top: 0.2rem;
    }

    /* ===== CLARIFYING QUESTIONS BOX ===== */
    .clarify-box {
        background: var(--warning-50) !important;
        border: 2px solid var(--warning) !important;
        border-radius: 0.5rem;
        padding: 1.25rem;
        margin: 1rem 0;
    }
    .clarify-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: var(--gray-900) !important;
        margin-bottom: 0.5rem;
    }
    .clarify-desc {
        font-size: 0.875rem;
        color: var(--gray-700) !important;
    }

    /* ===== BUTTONS (matches Button.tsx) ===== */
    .stButton > button {
        font-size: 1rem !important;
        padding: 0.75rem 1.5rem !important;
        min-height: 44px !important;
        border-radius: 0.5rem !important;
        font-weight: 500 !important;
        width: 100% !important;
        background: var(--gray-200) !important;
        color: var(--gray-900) !important;
        border: none !important;
        transition: background-color 0.15s ease;
    }
    .stButton > button[kind="primary"] {
        background: var(--primary) !important;
        color: var(--white) !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: var(--primary-800) !important;
    }
    .stButton > button:hover {
        background: var(--gray-300) !important;
    }
    .stButton > button:disabled {
        opacity: 0.5;
        cursor: not-allowed;
    }

    /* ===== TEXT INPUTS ===== */
    .stTextArea textarea, .stTextInput input {
        font-size: 1rem !important;
        padding: 0.75rem !important;
        border-radius: 0.5rem !important;
        border: 1px solid var(--gray-300) !important;
        color: var(--gray-900) !important;
        background: var(--white) !important;
    }
    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 3px var(--primary-100) !important;
    }

    /* ===== SELECTBOX ===== */
    .stSelectbox > div > div {
        color: var(--gray-900) !important;
        background: var(--white) !important;
    }

    /* ===== TABS ===== */
    .stTabs [data-baseweb="tab-list"] {
        background: var(--gray-100) !important;
        border-radius: 0.5rem;
        padding: 0.25rem;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 1rem !important;
        padding: 0.6rem 1rem !important;
        font-weight: 500 !important;
        color: var(--gray-600) !important;
        background: transparent !important;
    }
    .stTabs [aria-selected="true"] {
        background: var(--white) !important;
        color: var(--gray-900) !important;
        border-radius: 0.375rem;
    }

    /* ===== METRICS ===== */
    [data-testid="stMetricValue"] {
        color: var(--gray-900) !important;
        font-size: 1.5rem !important;
    }
    [data-testid="stMetricLabel"] {
        color: var(--gray-600) !important;
    }

    /* ===== SIDEBAR ===== */
    [data-testid="stSidebar"] {
        background: var(--gray-50) !important;
    }
    [data-testid="stSidebar"] * {
        color: var(--gray-900) !important;
    }
    .sidebar-box {
        background: var(--white) !important;
        border: 1px solid var(--gray-200) !important;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.75rem 0;
    }
    .sidebar-heading {
        font-size: 0.875rem;
        font-weight: 700;
        color: var(--gray-900) !important;
        margin-bottom: 0.5rem;
    }
    .sidebar-content {
        font-size: 0.875rem;
        color: var(--gray-600) !important;
        line-height: 1.5;
    }

    /* ===== ALERTS ===== */
    .stAlert {
        border-radius: 0.5rem !important;
    }
    .stAlert * {
        color: var(--gray-900) !important;
    }
    div[data-testid="stAlert"] {
        background: var(--primary-50) !important;
        border-left: 4px solid var(--primary) !important;
    }

    /* ===== RADIO BUTTONS ===== */
    .stRadio label {
        color: var(--gray-900) !important;
        background: var(--gray-50) !important;
        padding: 0.5rem 0.75rem !important;
        border-radius: 0.375rem !important;
    }

    /* ===== EXPANDER ===== */
    .streamlit-expanderHeader {
        font-weight: 500 !important;
        color: var(--gray-900) !important;
        background: var(--gray-50) !important;
    }

    /* ===== BLOCK DIAGRAM ===== */
    .diagram-container {
        background: var(--gray-50) !important;
        border: 1px solid var(--gray-200) !important;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    .diagram-title {
        font-size: 1.125rem;
        font-weight: 700;
        color: var(--gray-900) !important;
        text-align: center;
        margin-bottom: 0.25rem;
    }
    .diagram-subtitle {
        font-size: 0.875rem;
        color: var(--gray-600) !important;
        text-align: center;
        margin-bottom: 1rem;
    }
    .diagram-feedback {
        margin-top: 1rem;
        padding: 0.75rem;
        background: var(--warning-50) !important;
        border: 1px dashed var(--warning) !important;
        border-radius: 0.375rem;
        text-align: center;
        font-size: 0.875rem;
        color: var(--gray-700) !important;
    }
    .feedback-label {
        font-weight: 600;
        color: var(--warning-600) !important;
    }
    .diagram-flow {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        align-items: center;
        gap: 0.5rem;
    }
    .diagram-box {
        background: var(--white) !important;
        border: 2px solid var(--primary) !important;
        border-radius: 0.5rem;
        padding: 0.75rem 1rem;
        text-align: center;
        min-width: 100px;
    }
    .diagram-box-title {
        font-weight: 600;
        font-size: 0.875rem;
        color: var(--gray-900) !important;
    }
    .diagram-box-sub {
        font-size: 0.75rem;
        color: var(--gray-600) !important;
        margin-top: 0.25rem;
    }
    .diagram-arrow {
        font-size: 1.25rem;
        color: var(--primary) !important;
    }
    .diagram-model {
        background: var(--primary-50) !important;
        border-color: var(--primary) !important;
    }
    .diagram-human {
        background: var(--success-50) !important;
        border-color: var(--success) !important;
    }

    /* ===== SENTIMENT/BADGE CARDS (matches Badge.tsx variants) ===== */
    .sentiment-card {
        background: var(--white) !important;
        border: 1px solid var(--gray-200) !important;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .sentiment-critical {
        background: var(--danger-50) !important;
        border-color: var(--danger) !important;
    }
    .sentiment-critical .card-value {
        color: var(--danger-600) !important;
    }
    .sentiment-high {
        background: var(--warning-50) !important;
        border-color: var(--warning) !important;
    }
    .sentiment-high .card-value {
        color: var(--warning-600) !important;
    }
    .sentiment-medium {
        background: var(--warning-50) !important;
        border-color: var(--warning) !important;
    }
    .sentiment-medium .card-value {
        color: var(--warning-600) !important;
    }
    .sentiment-normal {
        background: var(--success-50) !important;
        border-color: var(--success) !important;
    }
    .sentiment-normal .card-value {
        color: var(--success-700) !important;
    }

    /* ===== BADGES (matches Badge.tsx) ===== */
    .badge {
        display: inline-flex;
        align-items: center;
        padding: 0.25rem 0.625rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 500;
    }
    .badge-primary {
        background: var(--primary-100) !important;
        color: var(--primary-700) !important;
    }
    .badge-success {
        background: var(--success-100) !important;
        color: var(--success-700) !important;
    }
    .badge-warning {
        background: var(--warning-100) !important;
        color: var(--warning-600) !important;
    }
    .badge-danger {
        background: var(--danger-100) !important;
        color: var(--danger-600) !important;
    }

    /* ===== MOBILE RESPONSIVE ===== */
    @media (max-width: 768px) {
        .progress-container {
            flex-direction: column;
            align-items: center;
        }
        .stButton > button {
            min-height: 48px !important;
        }
        .diagram-flow {
            flex-direction: column;
        }
        .diagram-arrow {
            transform: rotate(90deg);
        }
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# INITIALIZE
# ============================================================================
@st.cache_resource(ttl=60)
def load_processor():
    return GrievanceProcessor()

try:
    processor = load_processor()
except Exception as e:
    st.error(f"Failed to load AI models: {e}")
    st.stop()

ALL_DEPARTMENTS = [
    "Revenue", "Social Welfare", "Municipal Administration", "Civil Supplies",
    "Agriculture", "Health", "Education", "Energy", "Police", "Water Resources",
    "Housing", "Transport", "Panchayat Raj", "Animal Husbandry", "Women & Child Welfare"
]

# Session state
defaults = {
    "analysis_result": None,
    "case_id": None,
    "audit_trail": [],
    "current_dept": None,
    "grievance_text": "",
    "clarification_given": False,
    "citizen_answered": False,
    "current_step": 1,
    "officer_feedback": "",
}
for key, default in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = default

LOW_CONFIDENCE_THRESHOLD = 0.70

# ============================================================================
# SIDEBAR
# ============================================================================
with st.sidebar:
    st.markdown("## Guide")

    st.markdown("""
    <div class="sidebar-box">
        <div class="sidebar-heading">What is DHRUVA?</div>
        <div class="sidebar-content">
            AI system that routes citizen grievances to the correct government department in Andhra Pradesh.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="sidebar-box">
        <div class="sidebar-heading">Demo Flow</div>
        <div class="sidebar-content">
            1. Citizen submits grievance<br>
            2. AI asks clarifying questions if needed<br>
            3. Officer reviews and provides feedback<br>
            4. Case is assigned with full audit trail
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    if st.button("Reset Demo", use_container_width=True):
        for key in defaults:
            st.session_state[key] = defaults[key]
        st.cache_resource.clear()
        st.rerun()

    with st.expander("Share (QR Code)"):
        try:
            import qrcode
            from io import BytesIO
            import socket
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            demo_url = f"http://{local_ip}:8501"
            qr = qrcode.QRCode(version=1, box_size=6, border=3)
            qr.add_data(demo_url)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white")
            buf = BytesIO()
            qr_img.save(buf, format="PNG")
            buf.seek(0)
            st.image(buf, width=150)
            st.caption(demo_url)
        except:
            st.info("QR unavailable")

    with st.expander("All 15 Departments"):
        for d in ALL_DEPARTMENTS:
            st.caption(f"- {d}")

# ============================================================================
# HEADER
# ============================================================================
st.markdown("""
<div class="demo-header">
    <div class="demo-title">DHRUVA</div>
    <div class="demo-subtitle">A Source of Truth for Government | A Companion for Citizens | A North Star for Policy</div>
</div>
""", unsafe_allow_html=True)

# Progress bar
def render_progress():
    steps = [("Submit", 1), ("Clarify", 1), ("Officer Review", 2), ("Done", 3)]
    html = '<div class="progress-container">'
    for label, step_group in steps:
        if step_group < st.session_state.current_step:
            css = "progress-pill progress-done"
        elif step_group == st.session_state.current_step:
            css = "progress-pill progress-active"
        else:
            css = "progress-pill"
        html += f'<span class="{css}">{label}</span>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

render_progress()

# Tabs
tabs = st.tabs(["Citizen View", "Officer View", "Auditor View", "Policymaker View"])

# ============================================================================
# TAB 1: CITIZEN
# ============================================================================
with tabs[0]:

    # PHASE 1: No submission yet
    if st.session_state.analysis_result is None:
        st.markdown("### Submit Your Grievance")
        st.markdown("Describe your problem in English, Telugu, or mixed language.")

        examples = [
            "My pension has not been received for 6 months",
            "Road in our area has many potholes",
            "Ration shop not giving rice",
            "School lo teacher ledu 2 months ga",
            "Theft in my house, police not registering FIR",
        ]

        selected = st.selectbox(
            "Select example or type your own:",
            ["Type your own..."] + examples,
            key="example_select"
        )

        if selected == "Type your own...":
            grievance_text = st.text_area(
                "Your grievance:",
                value="",
                height=120,
                placeholder="Describe your problem here...",
                key="grievance_input"
            )
        else:
            grievance_text = st.text_area(
                "Your grievance:",
                value=selected,
                height=120,
                key="grievance_input_example"
            )

        can_submit = len(grievance_text.strip()) >= 10

        if st.button("SUBMIT GRIEVANCE", type="primary", use_container_width=True, disabled=not can_submit):
            with st.spinner("AI analyzing..."):
                try:
                    result = processor.process(grievance_text=grievance_text)
                    st.session_state.analysis_result = result
                    st.session_state.grievance_text = grievance_text
                    st.session_state.case_id = f"PGRS-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    st.session_state.current_dept = result["classification"]["department"]
                    st.session_state.audit_trail = [{
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "action": "SUBMITTED",
                        "actor": "Citizen",
                        "icon": "📝",
                        "details": f"Grievance submitted"
                    }]
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

        if not can_submit and len(grievance_text.strip()) > 0:
            st.warning("Please add more detail (at least 10 characters)")

    # PHASE 2: Submitted - check if clarification needed
    elif not st.session_state.citizen_answered:
        result = st.session_state.analysis_result
        conf = result["classification"]["confidence"]
        dept = st.session_state.current_dept

        st.success(f"Submitted! Case ID: **{st.session_state.case_id}**")

        # Show initial AI result - 4 columns for dept, sentiment, lapse risk, SLA
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
            <div class="card card-info">
                <div class="card-label">AI Suggested Department</div>
                <div class="card-value">{dept}</div>
                <div class="card-sub">Confidence: {conf:.0%}</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            distress = result["sentiment"]["distress_level"]
            sentiment_class = f"sentiment-{distress.lower()}"
            sentiment_icons = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "NORMAL": "🟢"}
            st.markdown(f"""
            <div class="sentiment-card {sentiment_class}">
                <div class="card-label">Sentiment Analysis</div>
                <div class="card-value">{sentiment_icons.get(distress, "⚪")} {distress}</div>
                <div class="card-sub">Distress level detected</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            # Lapse prediction
            lapse = result.get("lapse_prediction", {})
            lapse_risk = lapse.get("risk_score", 0)
            lapse_level = "HIGH" if lapse_risk > 0.6 else "MEDIUM" if lapse_risk > 0.3 else "LOW"
            lapse_class = "sentiment-high" if lapse_risk > 0.6 else "sentiment-medium" if lapse_risk > 0.3 else "sentiment-normal"
            st.markdown(f"""
            <div class="sentiment-card {lapse_class}">
                <div class="card-label">Lapse Risk Prediction</div>
                <div class="card-value">{lapse_level}</div>
                <div class="card-sub">Risk of improper redressal</div>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            st.markdown(f"""
            <div class="card">
                <div class="card-label">Response SLA</div>
                <div class="card-value">{result["sla"]["hours"]}h</div>
                <div class="card-sub">Based on priority</div>
            </div>
            """, unsafe_allow_html=True)

        # LOW CONFIDENCE: Ask citizen clarifying questions
        if conf < LOW_CONFIDENCE_THRESHOLD:
            st.markdown("""
            <div class="clarify-box">
                <div class="clarify-title">Help us understand better</div>
                <div class="clarify-desc">AI confidence is {:.0%}. Please answer one question to improve routing accuracy:</div>
            </div>
            """.format(conf), unsafe_allow_html=True)

            questions = get_clarifying_questions(
                grievance_text=st.session_state.grievance_text,
                predicted_dept=result["classification"]["department"],
                top_3_depts=result["classification"]["top_3"],
                confidence=conf
            )

            for i, q in enumerate(questions[:3]):
                q_text = q.get("question", "")
                q_telugu = q.get("question_telugu", "")
                target = q.get("target_dept", dept)
                boost = q.get("confidence_boost", 0.15)

                btn_label = f"Yes: {q_text}"
                if q_telugu:
                    btn_label += f" ({q_telugu})"

                if st.button(btn_label, key=f"citizen_clarify_{i}", use_container_width=True):
                    new_conf = min(conf + boost, 0.88)
                    st.session_state.analysis_result["classification"]["confidence"] = new_conf
                    st.session_state.current_dept = target
                    st.session_state.citizen_answered = True
                    st.session_state.current_step = 2
                    st.session_state.audit_trail.append({
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "action": "CLARIFIED",
                        "actor": "Citizen",
                        "icon": "💬",
                        "details": f"Answered: '{q_text}' -> Routed to {target} ({new_conf:.0%})"
                    })
                    st.rerun()

            st.markdown("---")
            if st.button("Skip clarification - proceed as is", use_container_width=True):
                st.session_state.citizen_answered = True
                st.session_state.current_step = 2
                st.session_state.audit_trail.append({
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "action": "AI_ROUTED",
                    "actor": "System",
                    "icon": "🤖",
                    "details": f"Auto-routed to {dept} ({conf:.0%} confidence)"
                })
                st.rerun()

        else:
            # HIGH CONFIDENCE: Auto proceed
            st.session_state.citizen_answered = True
            st.session_state.current_step = 2
            st.session_state.audit_trail.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "action": "AI_ROUTED",
                "actor": "System",
                "icon": "🤖",
                "details": f"Auto-routed to {dept} ({conf:.0%} confidence)"
            })
            st.rerun()

    # PHASE 3: Citizen has answered - show final status
    else:
        result = st.session_state.analysis_result
        dept = st.session_state.current_dept
        conf = result["classification"]["confidence"]
        distress = result["sentiment"]["distress_level"]

        st.success(f"Your grievance has been submitted! Case ID: **{st.session_state.case_id}**")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
            <div class="card card-success">
                <div class="card-label">Assigned Department</div>
                <div class="card-value">{dept}</div>
                <div class="card-sub">Confidence: {conf:.0%}</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            sentiment_class = f"sentiment-{distress.lower()}"
            sentiment_icons = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "NORMAL": "🟢"}
            st.markdown(f"""
            <div class="sentiment-card {sentiment_class}">
                <div class="card-label">Sentiment/Priority</div>
                <div class="card-value">{sentiment_icons.get(distress, "⚪")} {distress}</div>
                <div class="card-sub">Urgency level</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            lapse = result.get("lapse_prediction", {})
            lapse_risk = lapse.get("risk_score", 0)
            lapse_level = "HIGH" if lapse_risk > 0.6 else "MEDIUM" if lapse_risk > 0.3 else "LOW"
            lapse_class = "sentiment-high" if lapse_risk > 0.6 else "sentiment-medium" if lapse_risk > 0.3 else "sentiment-normal"
            st.markdown(f"""
            <div class="sentiment-card {lapse_class}">
                <div class="card-label">Lapse Risk</div>
                <div class="card-value">{lapse_level}</div>
                <div class="card-sub">Improper redressal risk</div>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            st.markdown(f"""
            <div class="card card-info">
                <div class="card-label">Response SLA</div>
                <div class="card-value">{result["sla"]["hours"]}h</div>
                <div class="card-sub">Expected response time</div>
            </div>
            """, unsafe_allow_html=True)

        st.info("Your grievance is now pending officer review. Go to the **Officer tab** to see the review process.")

        if st.button("Submit Another Grievance", use_container_width=True):
            for key in defaults:
                st.session_state[key] = defaults[key]
            st.rerun()

# ============================================================================
# TAB 2: OFFICER
# ============================================================================
with tabs[1]:

    if st.session_state.analysis_result is None:
        st.info("No grievances to review. Submit one in the Citizen tab first.")

    elif not st.session_state.citizen_answered:
        st.info("Citizen is still providing clarification. Please wait.")

    else:
        result = st.session_state.analysis_result
        conf = result["classification"]["confidence"]
        dept = st.session_state.current_dept

        st.markdown(f"### Case: {st.session_state.case_id}")

        # Show grievance
        st.markdown("**Citizen's Grievance:**")
        st.markdown(f"""
        <div class="card">
            {st.session_state.grievance_text}
        </div>
        """, unsafe_allow_html=True)

        # AI recommendation
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("AI Recommendation", dept)
        with col2:
            st.metric("Confidence", f"{conf:.0%}")
        with col3:
            st.metric("Priority", result["sentiment"]["distress_level"])

        st.markdown("---")
        st.markdown("### Your Decision")

        # Officer feedback - REQUIRED
        officer_feedback = st.text_input(
            "Your feedback/reasoning (required):",
            value=st.session_state.officer_feedback,
            placeholder="e.g., 'Classification correct' or 'Reassigning because...'"
        )
        st.session_state.officer_feedback = officer_feedback

        has_feedback = len(officer_feedback.strip()) >= 5

        # Accept button
        if st.button(
            f"ACCEPT: Assign to {dept}",
            type="primary",
            use_container_width=True,
            disabled=not has_feedback
        ):
            st.session_state.current_step = 3
            st.session_state.audit_trail.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "action": "ACCEPTED",
                "actor": "Officer",
                "icon": "✅",
                "details": f"Assigned to {dept}. Feedback: {officer_feedback}"
            })
            st.balloons()
            st.success(f"Case assigned to **{dept}**!")

        if not has_feedback:
            st.warning("Please provide feedback (at least 5 characters) before accepting.")

        st.markdown("---")
        st.markdown("**Or reassign to a different department:**")

        # Quick reassign buttons for top alternatives
        top_3 = result["classification"]["top_3"]
        cols = st.columns(3)
        for i, item in enumerate(top_3):
            d = item["department"]
            c = item["confidence"]
            if d != st.session_state.current_dept:
                with cols[i % 3]:
                    if st.button(f"{d} ({c:.0%})", key=f"reassign_{i}", use_container_width=True, disabled=not has_feedback):
                        old = st.session_state.current_dept
                        st.session_state.current_dept = d
                        st.session_state.current_step = 3
                        st.session_state.audit_trail.append({
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "action": "REASSIGNED",
                            "actor": "Officer",
                            "icon": "🔄",
                            "details": f"Changed from {old} to {d}. Feedback: {officer_feedback}"
                        })
                        st.rerun()

        # All departments dropdown
        with st.expander("Choose from all 15 departments"):
            other_depts = [d for d in ALL_DEPARTMENTS if d not in [x["department"] for x in top_3]]
            selected_dept = st.selectbox("Select department:", other_depts, key="other_dept_select")

            if st.button("Reassign to selected department", disabled=not has_feedback):
                old = st.session_state.current_dept
                st.session_state.current_dept = selected_dept
                st.session_state.current_step = 3
                st.session_state.audit_trail.append({
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "action": "REASSIGNED",
                    "actor": "Officer",
                    "icon": "🔄",
                    "details": f"Changed from {old} to {selected_dept}. Feedback: {officer_feedback}"
                })
                st.rerun()

# ============================================================================
# TAB 3: AUDIT TRAIL
# ============================================================================
with tabs[2]:
    st.markdown("### Audit Trail")

    if not st.session_state.audit_trail:
        st.info("No activity yet. Submit a grievance to see the audit trail.")
    else:
        st.markdown(f"**Case:** {st.session_state.case_id}")
        st.markdown(f"**Current Status:** Assigned to **{st.session_state.current_dept}**")

        st.markdown("---")

        for entry in st.session_state.audit_trail:
            st.markdown(f"""
            <div class="timeline-entry">
                <div class="timeline-icon">{entry.get("icon", "📌")}</div>
                <div class="timeline-text">
                    <div class="timeline-title">{entry["action"]} by {entry["actor"]}</div>
                    <div class="timeline-desc">{entry["details"]}</div>
                    <div class="timeline-time">{entry["timestamp"]}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("""
        **Feedback Collection (for future model improvement):**
        - ✅ Officer feedback is **logged** for batch retraining
        - ✅ Citizen clarifications are **recorded** in audit trail
        - ✅ Reassignment patterns are **tracked** for analysis
        - ⚠️ **Note:** Live reinforcement learning is NOT active - feedback is stored for periodic offline retraining
        """)

# ============================================================================
# TAB 4: POLICY INSIGHTS (Knowledge Graph)
# ============================================================================
with tabs[3]:
    st.markdown("### Policy Insights - Knowledge Graph View")
    st.markdown("Visual analysis of AP PGRS data for policymakers. **Interactive**: Drag nodes, zoom, hover for details.")

    if not check_pyvis_available():
        st.error("Knowledge graph visualization requires pyvis. Run: `pip install pyvis`")
    else:
        kg = GrievanceKnowledgeGraph()
        stats = kg.get_summary_stats()

        # Key stats row
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
            <div class="card card-warning">
                <div class="card-label">2018 Dissatisfaction</div>
                <div class="card-value">{KEY_STATS['dissatisfaction_2018']}%</div>
                <div class="card-sub">Sparked current reforms</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="card">
                <div class="card-label">Feedback Calls Analyzed</div>
                <div class="card-value">{KEY_STATS['total_feedback_calls']:,}</div>
                <div class="card-sub">State Call Center 1100</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="sentiment-card sentiment-high">
                <div class="card-label">False Closures Found</div>
                <div class="card-value">{KEY_STATS['false_closures']:,}</div>
                <div class="card-sub">2025 investigation</div>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            st.markdown(f"""
            <div class="card card-info">
                <div class="card-label">Best/Worst Variance</div>
                <div class="card-value">{KEY_STATS['variance_best_worst']}%</div>
                <div class="card-sub">Between districts</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # Graph type selector with descriptions
        graph_options = {
            "District-Department Network": "See how 14 districts and 10 departments perform",
            "Officer Lapse Patterns": "12 government-classified officer failure types",
            "Issue Category Flow": "How citizen complaints flow to departments",
            "Officer Performance Heatmap": "Officers flagged in pre-audit reports"
        }

        graph_type = st.selectbox(
            "Select Knowledge Graph View:",
            list(graph_options.keys()),
            format_func=lambda x: f"{x} - {graph_options[x]}",
            key="kg_graph_type"
        )

        # Generate and display the selected graph
        with st.spinner("Generating knowledge graph..."):
            if graph_type == "District-Department Network":
                st.markdown("""
                <div style="background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%); padding: 15px; border-radius: 8px; margin-bottom: 15px; border-left: 4px solid #2563EB;">
                <h4 style="margin: 0 0 10px 0; color: #1E40AF;">District-Department Performance Overview</h4>
                <p style="margin: 0; color: #374151;"><strong>DATA SOURCE:</strong> State Call Center 1100 - 93,892 feedback calls analyzed</p>
                </div>
                """, unsafe_allow_html=True)

                # Visual Legend with shapes, colors, sizes
                st.markdown("""
                <div style="background: #F9FAFB; padding: 12px; border-radius: 8px; margin-bottom: 15px; border: 1px solid #E5E7EB;">
                <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                <tr style="border-bottom: 1px solid #E5E7EB;">
                    <th style="text-align: left; padding: 8px; width: 25%;">Element</th>
                    <th style="text-align: left; padding: 8px; width: 25%;">Shape</th>
                    <th style="text-align: left; padding: 8px; width: 25%;">Size Meaning</th>
                    <th style="text-align: left; padding: 8px; width: 25%;">Color Meaning</th>
                </tr>
                <tr>
                    <td style="padding: 8px;"><strong>Districts</strong></td>
                    <td style="padding: 8px;"><span style="display: inline-block; width: 16px; height: 16px; border-radius: 50%; background: #6B7280; vertical-align: middle;"></span> Circle</td>
                    <td style="padding: 8px;"><strong>BIGGER = MORE PROBLEMS</strong><br/>(higher dissatisfaction)</td>
                    <td style="padding: 8px;">
                        <span style="color: #059669;">&#9679;</span> Green = Good |
                        <span style="color: #F59E0B;">&#9679;</span> Orange = Poor |
                        <span style="color: #DC2626;">&#9679;</span> Red = Critical
                    </td>
                </tr>
                <tr style="background: #F3F4F6;">
                    <td style="padding: 8px;"><strong>Departments</strong></td>
                    <td style="padding: 8px;"><span style="display: inline-block; width: 14px; height: 14px; background: #6B7280; vertical-align: middle;"></span> Square</td>
                    <td style="padding: 8px;"><strong>BIGGER = MORE GRIEVANCES</strong><br/>(higher volume)</td>
                    <td style="padding: 8px;">
                        <span style="color: #DC2626;">&#9632;</span> Red = >70% dissatisfied |
                        <span style="color: #F97316;">&#9632;</span> Orange = 50-70%
                    </td>
                </tr>
                <tr>
                    <td style="padding: 8px;"><strong>Connections</strong></td>
                    <td style="padding: 8px;">Lines</td>
                    <td style="padding: 8px;"><strong>THICKER = MORE PROBLEMS</strong></td>
                    <td style="padding: 8px;">
                        <span style="color: #DC2626;">- - -</span> Dashed Red = Known problem hotspots
                    </td>
                </tr>
                </table>
                </div>
                """, unsafe_allow_html=True)

                html = kg.create_district_department_graph()

                # Key takeaway
                st.info("**KEY INSIGHT:** Look for the BIGGEST RED circles - those are districts with the worst citizen dissatisfaction needing immediate attention. Ananthapur is the largest problem area.")

            elif graph_type == "Officer Lapse Patterns":
                st.markdown("""
                <div style="background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%); padding: 15px; border-radius: 8px; margin-bottom: 15px; border-left: 4px solid #D97706;">
                <h4 style="margin: 0 0 10px 0; color: #92400E;">12 Government-Classified Officer Lapses</h4>
                <p style="margin: 0; color: #374151;"><strong>SOURCE:</strong> AP PGRS Audit Framework - Official lapse classification system</p>
                </div>
                """, unsafe_allow_html=True)

                # Visual Legend for Lapse Types
                st.markdown("""
                <div style="background: #F9FAFB; padding: 12px; border-radius: 8px; margin-bottom: 15px; border: 1px solid #E5E7EB;">
                <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                <tr style="border-bottom: 1px solid #E5E7EB;">
                    <th style="text-align: left; padding: 8px; width: 20%;">Category</th>
                    <th style="text-align: left; padding: 8px; width: 30%;">Description</th>
                    <th style="text-align: left; padding: 8px; width: 25%;">Size Meaning</th>
                    <th style="text-align: left; padding: 8px; width: 25%;">Color = Severity</th>
                </tr>
                <tr>
                    <td style="padding: 8px;"><strong>Behavioral (5)</strong><br/><span style="color: #DC2626;">&#9679;</span> Red branch</td>
                    <td style="padding: 8px;">Human misconduct: abuse, threats, bribery, political interference</td>
                    <td style="padding: 8px;"><strong>BIGGER = MORE SEVERE</strong></td>
                    <td style="padding: 8px;">
                        <span style="color: #DC2626;">&#9679;</span> CRITICAL |
                        <span style="color: #F59E0B;">&#9679;</span> HIGH
                    </td>
                </tr>
                <tr style="background: #F3F4F6;">
                    <td style="padding: 8px;"><strong>Procedural (7)</strong><br/><span style="color: #F59E0B;">&#9679;</span> Orange branch</td>
                    <td style="padding: 8px;">Process failures: wrong endorsements, no follow-up, improper forwarding</td>
                    <td style="padding: 8px;"><strong>BIGGER = MORE SEVERE</strong></td>
                    <td style="padding: 8px;">
                        <span style="color: #F59E0B;">&#9679;</span> HIGH |
                        <span style="color: #EAB308;">&#9679;</span> MEDIUM |
                        <span style="color: #34D399;">&#9679;</span> LOW
                    </td>
                </tr>
                </table>
                </div>
                """, unsafe_allow_html=True)

                html = kg.create_lapse_pattern_graph()

                st.warning("**KEY INSIGHT:** Look for BIGGEST RED nodes - 'BRIBE DEMANDED' is CRITICAL. Biggest orange nodes like 'Wrong/Blank Endorsement' and 'False Jurisdiction' are the most common audit findings requiring training.")

            elif graph_type == "Issue Category Flow":
                st.markdown("""
                <div style="background: linear-gradient(135deg, #ECFDF5 0%, #D1FAE5 100%); padding: 15px; border-radius: 8px; margin-bottom: 15px; border-left: 4px solid #059669;">
                <h4 style="margin: 0 0 10px 0; color: #065F46;">Grievance Flow: Citizens to Departments</h4>
                <p style="margin: 0; color: #374151;"><strong>Shows:</strong> How different issue types are routed to departments</p>
                </div>
                """, unsafe_allow_html=True)

                # Visual Legend for Issue Flow
                st.markdown("""
                <div style="background: #F9FAFB; padding: 12px; border-radius: 8px; margin-bottom: 15px; border: 1px solid #E5E7EB;">
                <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                <tr style="border-bottom: 1px solid #E5E7EB;">
                    <th style="text-align: left; padding: 8px; width: 20%;">Element</th>
                    <th style="text-align: left; padding: 8px; width: 20%;">Shape</th>
                    <th style="text-align: left; padding: 8px; width: 30%;">Size Meaning</th>
                    <th style="text-align: left; padding: 8px; width: 30%;">Color Meaning</th>
                </tr>
                <tr>
                    <td style="padding: 8px;"><strong>Issue Categories</strong></td>
                    <td style="padding: 8px;"><span style="display: inline-block; width: 16px; height: 16px; border-radius: 50%; background: #6B7280; vertical-align: middle;"></span> Circle</td>
                    <td style="padding: 8px;"><strong>BIGGER = MORE COMPLAINTS</strong><br/>(+++ HIGH, ++ MEDIUM, + LOW)</td>
                    <td style="padding: 8px;">
                        <span style="color: #EF4444;">&#9679;</span> Red = LOW satisfaction |
                        <span style="color: #F59E0B;">&#9679;</span> Orange = MEDIUM
                    </td>
                </tr>
                <tr style="background: #F3F4F6;">
                    <td style="padding: 8px;"><strong>Departments</strong></td>
                    <td style="padding: 8px;"><span style="display: inline-block; width: 14px; height: 14px; background: #6B7280; vertical-align: middle;"></span> Square</td>
                    <td style="padding: 8px;">All same size</td>
                    <td style="padding: 8px;">
                        <span style="color: #DC2626;">&#9632;</span> Red = >70% unhappy |
                        <span style="color: #F97316;">&#9632;</span> Orange = 50-70% |
                        <span style="color: #3B82F6;">&#9632;</span> Blue = <50%
                    </td>
                </tr>
                </table>
                <p style="margin: 8px 0 0 0; font-size: 13px; color: #6B7280;"><strong>Flow:</strong> Citizens (left) file issues (middle) handled by Departments (right). Follow the lines to see which departments handle what.</p>
                </div>
                """, unsafe_allow_html=True)

                html = kg.create_issue_flow_graph()

                st.error("**KEY INSIGHT:** Look for BIG RED circles connecting to RED squares - Land & Revenue (HIGH volume + LOW satisfaction) routes to Revenue Dept (77% unhappy). This is the #1 pain point.")

            else:  # Officer Performance Heatmap
                st.markdown("""
                <div style="background: linear-gradient(135deg, #FEE2E2 0%, #FECACA 100%); padding: 15px; border-radius: 8px; margin-bottom: 15px; border-left: 4px solid #DC2626;">
                <h4 style="margin: 0 0 10px 0; color: #991B1B;">Officer Audit Performance</h4>
                <p style="margin: 0; color: #374151;"><strong>SOURCE:</strong> West Godavari & Ananthapur Pre-Audit Reports (2025)</p>
                </div>
                """, unsafe_allow_html=True)

                # Visual Legend for Officer Performance
                st.markdown("""
                <div style="background: #F9FAFB; padding: 12px; border-radius: 8px; margin-bottom: 15px; border: 1px solid #E5E7EB;">
                <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                <tr style="border-bottom: 1px solid #E5E7EB;">
                    <th style="text-align: left; padding: 8px; width: 20%;">Element</th>
                    <th style="text-align: left; padding: 8px; width: 20%;">Shape</th>
                    <th style="text-align: left; padding: 8px; width: 30%;">Size Meaning</th>
                    <th style="text-align: left; padding: 8px; width: 30%;">Color = Problem Level</th>
                </tr>
                <tr>
                    <td style="padding: 8px;"><strong>Districts</strong></td>
                    <td style="padding: 8px;"><span style="display: inline-block; width: 16px; height: 16px; border-radius: 50%; background: #6366F1; vertical-align: middle;"></span> Blue Circle</td>
                    <td style="padding: 8px;">Fixed size (grouping)</td>
                    <td style="padding: 8px;">Indigo = District identifier</td>
                </tr>
                <tr style="background: #F3F4F6;">
                    <td style="padding: 8px;"><strong>Officers</strong></td>
                    <td style="padding: 8px;"><span style="display: inline-block; width: 14px; height: 14px; background: #6B7280; vertical-align: middle;"></span> Square</td>
                    <td style="padding: 8px;"><strong>BIGGER = WORSE PERFORMANCE</strong><br/>(higher % improper handling)</td>
                    <td style="padding: 8px;">
                        <span style="color: #DC2626;">&#9632;</span> Red = >70% CRITICAL |
                        <span style="color: #F97316;">&#9632;</span> Orange = 50-70% |
                        <span style="color: #EAB308;">&#9632;</span> Yellow = <50%
                    </td>
                </tr>
                </table>
                <p style="margin: 8px 0 0 0; font-size: 13px; color: #6B7280;"><strong>"Improper Rate"</strong> = % of grievances this officer handled incorrectly (found during surprise audits using 12 lapse classifications)</p>
                </div>
                """, unsafe_allow_html=True)

                html = kg.create_performance_heatmap_graph()

                st.error("**KEY INSIGHT:** Look for BIGGEST RED squares - Joint Director of Fisheries (76.7%) and District Fisheries Officer (72.4%) in West Godavari. Two officers in same department = systemic issue needing department-wide training.")

            # Render the graph with instructions
            st.markdown("**Interact with the graph:** Drag nodes to rearrange | Hover for details | Scroll to zoom")
            components.html(html, height=700, scrolling=True)

        st.markdown("---")

        # Data tables
        with st.expander("District Satisfaction Rankings (from 93,892 feedback calls)"):
            # Create a simple table
            table_data = []
            for district, data in sorted(DISTRICT_DATA.items(), key=lambda x: x[1]['rank']):
                table_data.append({
                    "Rank": data['rank'],
                    "District": district,
                    "Satisfaction (0-5)": f"{data['satisfaction']:.2f}",
                    "Status": data['category'].replace('_', ' ').title()
                })
            st.table(table_data)

        with st.expander("Department Performance (dissatisfaction & reopen rates)"):
            dept_data = []
            for dept, data in sorted(DEPARTMENT_DATA.items(), key=lambda x: -x[1]['dissatisfaction']):
                dept_data.append({
                    "Department": dept,
                    "Dissatisfaction %": f"{data['dissatisfaction']:.1f}%",
                    "Reopen Rate": f"{data['reopen_rate']:.1f}%",
                    "Grievances": data['grievances'],
                    "Status": data['category'].upper()
                })
            st.table(dept_data)

        st.markdown("""
        **Data Sources:**
        - State Call Center 1100 Feedback Report (93,892 calls)
        - West Godavari Pre-Audit Report (Aug-Oct 2025)
        - Ananthapur District Audit Performance Report
        - PGRS Department-HOD Wise Report (Nov 21, 2025)
        - Improper Redressal Lapses Classification (12 types)
        """)

# ============================================================================
# BLOCK DIAGRAM - Always visible at bottom
# ============================================================================
st.markdown("---")
st.markdown("""
<div class="diagram-container">
    <div class="diagram-title">How DHRUVA Works - System Architecture</div>
    <div class="diagram-subtitle">4 ML Models + Human-in-the-Loop</div>
    <div class="diagram-flow">
        <div class="diagram-box">
            <div class="diagram-box-title">📝 Citizen Input</div>
            <div class="diagram-box-sub">English / Telugu / Mixed</div>
        </div>
        <span class="diagram-arrow">→</span>
        <div class="diagram-box diagram-model">
            <div class="diagram-box-title">🔤 TF-IDF</div>
            <div class="diagram-box-sub">Text Vectorization</div>
        </div>
        <span class="diagram-arrow">→</span>
        <div class="diagram-box diagram-model">
            <div class="diagram-box-title">🏢 Model 1</div>
            <div class="diagram-box-sub">Dept Classification</div>
        </div>
        <span class="diagram-arrow">→</span>
        <div class="diagram-box diagram-model">
            <div class="diagram-box-title">😊 Model 2</div>
            <div class="diagram-box-sub">Sentiment/Distress</div>
        </div>
        <span class="diagram-arrow">→</span>
        <div class="diagram-box diagram-model">
            <div class="diagram-box-title">⚠️ Model 3</div>
            <div class="diagram-box-sub">Lapse Prediction</div>
        </div>
        <span class="diagram-arrow">→</span>
        <div class="diagram-box">
            <div class="diagram-box-title">❓ Clarify</div>
            <div class="diagram-box-sub">If confidence < 70%</div>
        </div>
        <span class="diagram-arrow">→</span>
        <div class="diagram-box diagram-human">
            <div class="diagram-box-title">👮 Officer</div>
            <div class="diagram-box-sub">Accept / Reassign</div>
        </div>
        <span class="diagram-arrow">→</span>
        <div class="diagram-box diagram-human">
            <div class="diagram-box-title">✅ Assigned</div>
            <div class="diagram-box-sub">To Department</div>
        </div>
    </div>
    <div class="diagram-feedback">
        <span class="feedback-label">📊 Feedback Loop:</span>
        Officer decisions logged for periodic batch retraining (not live RL)
    </div>
</div>
""", unsafe_allow_html=True)

# Model details
with st.expander("Technical Details - All 4 Models"):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **Model 1: Department Classification**
        - Ensemble Voting Classifier (LR + RF + SVM)
        - TF-IDF vectorization (5000 features)
        - 15 AP government departments
        - **95.5% accuracy** on held-out test data
        - Bilingual: English + Telugu + Mixed

        **Model 2: Sentiment/Distress Detection**
        - 4 levels: CRITICAL, HIGH, MEDIUM, NORMAL
        - Drives SLA assignment (24h to 168h)
        - Detects emotional urgency patterns
        """)
    with col2:
        st.markdown("""
        **Model 3: Lapse Prediction**
        - Predicts risk of improper redressal
        - Based on historical complaint patterns
        - Alerts officers to high-risk cases

        **Model 4: Classification Fallback**
        - Keyword-based backup classifier
        - Used when main model has low confidence
        - Ensures graceful degradation

        **Clarifying Questions Engine:**
        - Knowledge-base driven (no external LLM API)
        - Triggered when confidence < 70%
        """)

    st.markdown("---")
    st.markdown("""
    **Feedback & Retraining:**
    Officer reassignments and feedback are logged in the audit trail for future batch retraining.
    **Note:** This is NOT live reinforcement learning - models are retrained periodically offline.
    """)

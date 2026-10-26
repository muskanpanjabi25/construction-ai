"""Multimodal Construction Intelligence Platform - Skill Wallet Capstone Project 1."""
from __future__ import annotations

import json
import random
import re
from urllib.parse import quote

import streamlit as st
from PIL import Image

st.set_page_config(page_title="Construction Intelligence Platform", page_icon="🏗️", layout="wide")

st.markdown(
    """
<style>
.metric-card{background:#0f172a;color:#fff;padding:16px;border-radius:12px;text-align:center}
.metric-card h2{margin:0;font-size:2rem;color:#38bdf8}
.pill{display:inline-block;padding:4px 12px;border-radius:999px;font-weight:600;color:#fff}
.ok{background:#16a34a}.warn{background:#f59e0b}.bad{background:#dc2626}
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------- Sidebar
with st.sidebar:
    st.title("🏗️ Site Intelligence")
    api_key = st.text_input("Google Gemini API key", type="password",
                            help="Leave empty to run in demonstration mode.")
    model_name = st.text_input("Gemini model", value="gemini-2.0-flash")
    st.caption("Mode: " + ("🟢 Live Gemini" if api_key else "🟡 Demo (no key)"))
    st.markdown("---")
    st.markdown(
        "**Architecture**\n\n"
        "1. Image / text input\n2. Multimodal LLM (Gemini)\n"
        "3. Strict JSON contract\n4. Streamlit UI rendering"
    )


# ---------------------------------------------------------------- Helpers
def parse_json(text: str) -> dict:
    """Extract a JSON object from an LLM response."""
    text = re.sub(r"```(?:json)?", "", text).strip()
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        raise ValueError("No JSON found in model response")
    return json.loads(match.group(0))


def ask_gemini(prompt: str, image: Image.Image | None = None) -> dict:
    import google.generativeai as genai

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)
    parts = [prompt + "\nRespond ONLY with valid JSON, no markdown."]
    if image is not None:
        parts.append(image)
    return parse_json(model.generate_content(parts).text)


def analyse(prompt: str, image, demo: dict) -> dict:
    """Run live analysis when a key exists; otherwise (or on error) use demo data."""
    if not api_key:
        return demo
    try:
        return ask_gemini(prompt, image)
    except Exception as exc:  # noqa: BLE001
        st.warning(f"Live analysis failed ({exc}). Showing demo output instead.")
        return demo


def pill(text: str, level: str) -> str:
    cls = {"low": "ok", "medium": "warn", "high": "bad", "critical": "bad"}.get(level.lower(), "warn")
    return f'<span class="pill {cls}">{text}</span>'


def load_image(file):
    try:
        return Image.open(file).convert("RGB")
    except Exception:  # noqa: BLE001
        st.error("Could not read that image. Please upload a valid JPG/PNG.")
        return None


def inr(amount: float) -> str:
    if amount >= 1e7:
        return f"₹{amount / 1e7:.2f} Cr"
    return f"₹{amount / 1e5:.2f} Lakhs"


# ---------------------------------------------------------------- Demo data
DEMO_SAFETY = {
    "safety_score": 62, "overall_status": "Needs Improvement",
    "ppe_detection": {"helmet": True, "high_vis_vest": True, "steel_toe_boots": False, "safety_harness": False},
    "hazards": [
        {"hazard": "Worker at height without harness", "severity": "Critical",
         "remedy": "Stop work; provide full-body harness anchored to a rated point."},
        {"hazard": "Unprotected open edge", "severity": "High",
         "remedy": "Install guardrails and toe boards per OSHA 1926.502."},
        {"hazard": "Loose material on walkway", "severity": "Medium",
         "remedy": "Clear walkways and designate material storage."},
    ],
}
DEMO_CRACK = {
    "defect_type": "Settlement", "crack_width_mm": 3.2, "severity_score": 6,
    "urgency": "High",
    "probable_causes": ["Differential foundation settlement", "Poor soil compaction", "Moisture variation"],
    "recommended_repairs": ["Epoxy injection", "Structural re-grouting", "Geotechnical survey of foundation"],
}

# ---------------------------------------------------------------- Tabs
st.title("Multimodal Construction Intelligence Platform")
t1, t2, t3, t4 = st.tabs(["🦺 Safety & PPE Audit", "🧱 Crack Diagnostics",
                          "📐 Planning & Valuation", "🌦️ Site Assistant"])

# ---- Tab 1
with t1:
    st.subheader("Site Safety & PPE Audit")
    up = st.file_uploader("Upload a construction site photo", type=["jpg", "jpeg", "png"], key="safety")
    desc = st.text_area("Optional site description", key="safety_desc")
    if up and st.button("Run safety audit", type="primary"):
        img = load_image(up)
        if img:
            st.image(img)
            prompt = (
                "You are a construction safety auditor (OSHA, IS 456). Analyse the image. Return JSON with keys: "
                "safety_score (0-100), overall_status, ppe_detection {helmet, high_vis_vest, steel_toe_boots, "
                "safety_harness as booleans}, hazards [list of {hazard, severity (Low|Medium|High|Critical), remedy}]. "
                f"Context: {desc}"
            )
            with st.spinner("Analysing..."):
                res = analyse(prompt, img, DEMO_SAFETY)
            st.session_state["safety"] = res
    res = st.session_state.get("safety")
    if res:
        c1, c2 = st.columns(2)
        c1.markdown(f'<div class="metric-card"><h2>{res.get("safety_score", "-")}/100</h2>Safety Score</div>',
                    unsafe_allow_html=True)
        c2.markdown(f'<div class="metric-card"><h2>{res.get("overall_status", "-")}</h2>Overall Status</div>',
                    unsafe_allow_html=True)
        st.markdown("#### PPE Checklist")
        for k, v in res.get("ppe_detection", {}).items():
            st.write(("✅ " if v else "❌ ") + k.replace("_", " ").title())
        st.markdown("#### Hazards")
        for h in res.get("hazards", []):
            st.markdown(f"{pill(h.get('severity', 'Medium'), h.get('severity', 'Medium'))} "
                        f"**{h.get('hazard')}** — {h.get('remedy')}", unsafe_allow_html=True)
        st.download_button("⬇️ Download JSON report", json.dumps(res, indent=2),
                           "safety_report.json", "application/json")

# ---- Tab 2
with t2:
    st.subheader("Crack Diagnostics & Structural Integrity")
    up = st.file_uploader("Upload a concrete / wall surface photo", type=["jpg", "jpeg", "png"], key="crack")
    if up and st.button("Diagnose crack", type="primary"):
        img = load_image(up)
        if img:
            st.image(img)
            prompt = (
                "You are a structural engineer. Classify the defect. Return JSON with keys: defect_type "
                "(Hairline|Settlement|Structural Shear|Thermal Expansion|Spalling), crack_width_mm (number), "
                "severity_score (1-10), urgency (Low|Medium|High|Critical), probable_causes [list], "
                "recommended_repairs [list, e.g. epoxy injection, structural re-grouting]."
            )
            with st.spinner("Analysing..."):
                st.session_state["crack"] = analyse(prompt, img, DEMO_CRACK)
    r = st.session_state.get("crack")
    if r:
        a, b, c = st.columns(3)
        a.metric("Defect type", r.get("defect_type"))
        b.metric("Crack width", f"{r.get('crack_width_mm')} mm")
        c.metric("Severity", f"{r.get('severity_score')}/10")
        st.markdown(f"Urgency: {pill(r.get('urgency', 'Medium'), r.get('urgency', 'Medium'))}", unsafe_allow_html=True)
        st.markdown("**Probable causes**")
        for x in r.get("probable_causes", []):
            st.write("• " + x)
        st.markdown("**Recommended repairs**")
        for x in r.get("recommended_repairs", []):
            st.write("🔧 " + x)
        st.download_button("⬇️ Download JSON report", json.dumps(r, indent=2),
                           "crack_report.json", "application/json")

# ---- Tab 3
with t3:
    st.subheader("Planning & Real Estate Valuation (INR)")
    c1, c2 = st.columns(2)
    stype = c1.selectbox("Structure type", ["Residential", "Commercial", "Industrial", "Villa"])
    sqft = c1.number_input("Built-up area (sq ft)", 200, 500000, 2000, step=100)
    tier = c2.selectbox("Location tier", ["Tier 1", "Tier 2", "Tier 3"])
    pct = c2.slider("Completion %", 0, 100, 40)

    cost_rate = {"Residential": 1800, "Commercial": 2400, "Industrial": 1500, "Villa": 3000}[stype]
    tier_mult = {"Tier 1": 1.3, "Tier 2": 1.0, "Tier 3": 0.8}[tier]
    market_rate = {"Tier 1": 12000, "Tier 2": 6500, "Tier 3": 3500}[tier] * (1.25 if stype == "Commercial" else 1)

    budget = sqft * cost_rate * tier_mult
    spent = budget * pct / 100
    valuation = sqft * market_rate * (0.35 + 0.65 * pct / 100)
    cement_bags = sqft * 0.4 * (1 - pct / 100)
    steel_kg = sqft * 4 * (1 - pct / 100)

    m1, m2, m3 = st.columns(3)
    m1.metric("Total project budget", inr(budget))
    m2.metric("Capex incurred", inr(spent))
    m3.metric("Current asset valuation", inr(valuation))
    m4, m5 = st.columns(2)
    m4.metric("Cement still required", f"{cement_bags:,.0f} bags")
    m5.metric("Steel still required", f"{steel_kg / 1000:,.1f} tonnes")
    st.progress(pct / 100, text=f"Milestone progress: {pct}%")

    st.markdown("#### Conceptual architectural rendering")
    style = st.text_input("Rendering style", "modern minimalist, glass facade, sunset")
    if st.button("Generate rendering"):
        p = quote(f"3D architectural render of a {stype.lower()} building, {style}, photorealistic")
        st.image(f"https://image.pollinations.ai/prompt/{p}?width=768&height=512", caption="Pollinations AI concept")

# ---- Tab 4
with t4:
    st.subheader("Daily Site Assistant & Weather Advisory")
    weather = st.selectbox("Today's weather", ["Normal", "High Wind", "Heavy Rain", "Extreme Heat"])
    advisory = {
        "Normal": ("success", "Normal operations. Hold the daily toolbox talk and inspect scaffolds."),
        "High Wind": ("error", "Suspend crane and lifting operations above 30 km/h. Secure loose sheets and scaffolding."),
        "Heavy Rain": ("error", "Switch off temporary electrics near water, cover fresh concrete, and pause excavation."),
        "Extreme Heat": ("warning", "Enforce hydration breaks, restrict heavy work 12–3 PM, and wet-cure concrete twice daily."),
    }[weather]
    getattr(st, advisory[0])(advisory[1])

    st.markdown("#### Construction Engineering Assistant")
    if "chat" not in st.session_state:
        st.session_state.chat = []
    for m in st.session_state.chat:
        st.chat_message(m["role"]).write(m["content"])
    q = st.chat_input("Ask about concrete, safety, scheduling, costs...")
    if q:
        st.session_state.chat.append({"role": "user", "content": q})
        st.chat_message("user").write(q)
        reply = None
        if api_key:
            try:
                import google.generativeai as genai

                genai.configure(api_key=api_key)
                history = "\n".join(f"{m['role']}: {m['content']}" for m in st.session_state.chat[-8:])
                reply = genai.GenerativeModel(model_name).generate_content(
                    f"You are a concise construction engineering assistant. Weather today: {weather}.\n{history}"
                ).text
            except Exception as exc:  # noqa: BLE001
                reply = f"(Live assistant error: {exc})"
        if reply is None:
            tips = {
                "concrete": "Keep concrete moist for at least 7 days (14 for blended cement) and avoid pouring above 38°C.",
                "safety": "Mandatory PPE: helmet, vest, boots, and harness above 2 m. Run daily toolbox talks.",
                "cost": "Use the Planning tab for a budget estimate; add 10% contingency.",
                "crack": "Measure width; over 0.3 mm or growing cracks need an engineer's inspection.",
            }
            reply = next((v for k, v in tips.items() if k in q.lower()),
                         "Demo mode: add a Gemini key in the sidebar for full answers. Try asking about concrete, safety, cost or cracks.")
        st.session_state.chat.append({"role": "assistant", "content": reply})
        st.chat_message("assistant").write(reply)

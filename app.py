import streamlit as st
import os
from assistant.assistant import AssistantAssistant
from tools.ocr_tool import OCRTool
from tools.calculator_tool import CalculatorTool
from tools.tool_registry import get_registry
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

# Page Config
st.set_page_config(
    page_title="Smart Expense Assistant Assistant",
    page_icon="🤖",
    layout="wide"
)

# Initialize Tools and Registry
@st.cache_resource
def init_assistant():
    registry = get_registry()
    # Register tools
    if "ocr_extractor" not in registry.list_tools():
        registry.register(OCRTool())
    if "calculator" not in registry.list_tools():
        registry.register(CalculatorTool())
    
    return AssistantAssistant()

assistant = init_assistant()

# UI Header
st.title("📘 Smart Expense Assistant Assistant")
st.markdown("### OpenClaw Assistanthon 2026 — Autonomous AI Auditor")
st.divider()

# Sidebar
with st.sidebar:
    st.header("Settings")
    use_gpu = st.checkbox("Use GPU (EasyOCR)", value=False)
    max_loops = st.slider("Max Autonomous Loops", 1, 5, 3)
    assistant.max_loops = max_loops
    st.divider()
    st.info("Assistant ini akan memproses struk secara otonom, mendeteksi mismatch, dan memberikan rekomendasi berdasarkan Personal Budget Rules.")

# Main Layout
col1, col2 = st.columns([1, 1])

with col1:
    st.header("📤 Upload Receipt")
    uploaded_file = st.file_uploader("Pilih gambar struk (JPG/PNG)...", type=["jpg", "jpeg", "png"])
    
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Receipt", use_column_width=True)
        
        # Save temp file for processing
        temp_path = f"temp_{uploaded_file.name}"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        if st.button("🚀 Analyze with Assistant"):
            with st.spinner("Assistant sedang berpikir..."):
                result = assistant.run(temp_path)
                st.session_state['analysis_result'] = result
            
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)

with col2:
    st.header("🧠 Assistant Thinking Process")
    
    if 'analysis_result' in st.session_state:
        result = st.session_state['analysis_result']
        
        # DISPLAY THINKING LOG (The Wow Factor)
        for log in result.get('thinking_log', []):
            with st.expander(f"📌 {log['step']}: {log['thought']}"):
                st.write(f"**Action:** {log['action']}")
                if log['result']:
                    st.success(f"**Result:** {log['result']}")
        
        st.divider()
        st.header("📊 Final Analysis Result")
        
        # Status Badge
        status = result.get('status', 'REVIEW')
        if status == 'APPROVED':
            st.success(f"### Status: {status} ✅")
        elif status == 'ATTENTION':
            st.error(f"### Status: {status} ⚠️")
        else:
            st.warning(f"### Status: {status} 🔍")
            
        if result.get('attention_reason'):
            st.error(f"**Reason:** {result['attention_reason']}")
            
        # Display Data
        st.subheader(f"Merchant: {result.get('merchant', 'Unknown')}")
        st.write(f"Date: {result.get('date', 'Unknown')}")
        
        st.markdown(f"**Insight Score:** {result.get('insight_score', 0)}/100")
        st.progress(result.get('insight_score', 0) / 100)
        
        # Items Table
        if result.get('items'):
            import pandas as pd
            df = pd.DataFrame(result['items'])
            st.table(df[['name', 'category', 'price', 'flag', 'budget_reason']])
        
        st.metric("Total Match", "YES" if result.get('total_match') else "NO", delta=f"Rp {result.get('stated_total', 0) - result.get('calculated_total', 0):,}")
        
        if result.get('insights'):
            st.subheader("💡 Insights")
            for insight in result['insights']:
                st.info(insight)
    else:
        st.info("Upload struk dan klik 'Analyze' untuk melihat proses berpikir Assistant.")

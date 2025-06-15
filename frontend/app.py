import streamlit as st
import requests
import json
import time

st.set_page_config(
    page_title="FAQ Bot",
    page_icon="🤖",
    layout="wide"
)

# Rate limiting protection
if 'last_request_time' not in st.session_state:
    st.session_state.last_request_time = 0

def can_make_request():
    """Check if we can make a request (rate limiting)"""
    current_time = time.time()
    time_since_last = current_time - st.session_state.last_request_time
    return time_since_last > 2  # Wait 2 seconds between requests

def get_faq_response(question: str):
    """Get response with rate limiting"""
    if not can_make_request():
        return {"error": "Please wait a moment before asking another question"}

    try:
        st.session_state.last_request_time = time.time()
        response = requests.post(
            "http://localhost:8000/ask",
            json={"question": question},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API Error: {response.status_code}"}
    except Exception as e:
        return {"error": f"Connection Error: {str(e)}"}

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Sidebar
with st.sidebar:
    st.header("About")
    st.write("This FAQ bot uses:")
    st.write("• ChromaDB for vector search")
    st.write("• Google Gemini for AI responses")
    st.write("• FastAPI backend")
    st.write("• Streamlit interface")

    # API Status check (with rate limiting)
    if st.button("Check API Status"):
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                st.success("✅ API Connected")
                st.info(f"Database entries: {data.get('database_entries', 'Unknown')}")
            else:
                st.error("❌ API Error")
        except:
            st.error("❌ API Disconnected")

    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# Main content
st.title("🤖 FAQ Bot")
st.write("Ask me anything about our services!")

# Input form to prevent auto-submission
with st.form("question_form", clear_on_submit=True):
    question = st.text_input("Type your question here:")
    submitted = st.form_submit_button("Ask Question", type="primary")

    if submitted and question:
        with st.spinner("Getting answer..."):
            result = get_faq_response(question)

            if "error" in result:
                st.error(result["error"])
            else:
                # Add to chat history
                st.session_state.messages.append({
                    "question": question,
                    "answer": result.get("answer", "No answer available"),
                    "ai_provider": result.get("ai_provider", "unknown"),
                    "confidence": result.get("confidence", "unknown")
                })
                st.rerun()

# Quick action buttons (with rate limiting protection)
st.subheader("🚀 Quick Actions")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Return Policy") and can_make_request():
        result = get_faq_response("What is your return policy?")
        if "error" not in result:
            st.session_state.messages.append({
                "question": "What is your return policy?",
                "answer": result.get("answer", "No answer available"),
                "ai_provider": result.get("ai_provider", "unknown"),
                "confidence": result.get("confidence", "unknown")
            })
            st.rerun()

with col2:
    if st.button("Shipping Info") and can_make_request():
        result = get_faq_response("How long does shipping take?")
        if "error" not in result:
            st.session_state.messages.append({
                "question": "How long does shipping take?",
                "answer": result.get("answer", "No answer available"),
                "ai_provider": result.get("ai_provider", "unknown"),
                "confidence": result.get("confidence", "unknown")
            })
            st.rerun()

with col3:
    if st.button("Support Contact") and can_make_request():
        result = get_faq_response("How can I contact support?")
        if "error" not in result:
            st.session_state.messages.append({
                "question": "How can I contact support?",
                "answer": result.get("answer", "No answer available"),
                "ai_provider": result.get("ai_provider", "unknown"),
                "confidence": result.get("confidence", "unknown")
            })
            st.rerun()

# Display chat history
if st.session_state.messages:
    st.subheader("💬 Conversation History")

    for i, msg in enumerate(reversed(st.session_state.messages[-5:])):
        with st.container():
            st.write(f"**❓ You:** {msg['question']}")
            st.write(f"**🤖 Bot:** {msg['answer']}")

            col_meta1, col_meta2 = st.columns(2)
            with col_meta1:
                st.caption(f"Confidence: {msg['confidence']}")
            with col_meta2:
                st.caption(f"AI: {msg['ai_provider']}")

            st.divider()

# Rate limiting notice
if not can_make_request():
    st.warning("⏳ Please wait a moment before asking another question (rate limiting)")

st.markdown("---")
st.markdown("Made with ❤️ using Streamlit, FastAPI, ChromaDB, and AI")
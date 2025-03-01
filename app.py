# app.py
import streamlit as st
from retriever import generate_response, policy_links


# Set page config
st.set_page_config(
    page_title="UDST Policy Chatbot",
    page_icon="📚",
    layout="centered"
)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Custom CSS styling
st.markdown("""
<style>
    /* Global Title Styling */
    .global-title {
        color: #2B3A8C;
        font-size: 2.5em !important;
        font-weight: 700;
        text-align: center;
        padding: 20px 0;
        border-bottom: 3px solid #2B3A8C;
        margin-bottom: 25px;
    }
    
    /* Chat container */
    .chat-history {
        max-height: 60vh;
        overflow-y: auto;
        padding-right: 10px;
        margin-bottom: 20px;
    }
    
    /* Input container */
    .input-container {
        position: fixed;
        bottom: 80px;
        width: 85%;
        display: flex;
        gap: 10px;
        z-index: 999;
    }
    
    /* Clear button styling */
    .clear-btn {
        background-color: #f8f9fa;
        border: 1px solid #ced4da;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar with numbered policies
# In the sidebar section:
with st.sidebar:
    st.header("📜 UDST Policies")
    # Numbered list with hyperlinks
    for i, policy_name in enumerate(policy_links.keys(), start=1):
        url = policy_links[policy_name]  # Get URL from your dictionary
        st.markdown(
            f"{i}. [{policy_name}]({url})", 
            unsafe_allow_html=True
        )
    st.markdown("---")
    st.caption("UDST Policy Chatbot")

# Main interface
st.markdown('<h1 class="global-title">📚 UDST POLICY ASSISTANT</h1>', unsafe_allow_html=True)

# Chat history container
with st.container():
    st.markdown('<div class="chat-history">', unsafe_allow_html=True)
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    st.markdown('</div>', unsafe_allow_html=True)

# Sample questions section
if not st.session_state.messages:
    st.subheader("💬 FAQ:")
    cols = st.columns(2)
    sample_questions = [
        "What is the attendance policy?",
        "What are course Registration Policies?",
        "What are the library rules?",
        "Explain scholarship requirements",
        "International student policies?",
        "Student conduct guidelines?"
    ]
    
    for i, question in enumerate(sample_questions):
        if cols[i%2].button(
            question,
            use_container_width=True,
            key=f"sample_{i}"
        ):
            st.session_state.messages.append({"role": "user", "content": question})
            with st.spinner("Searching policies..."):
                response = generate_response(question)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"{response}"
                })
            st.rerun()

# Input section with clear button
input_container = st.container()
with input_container:
    cols = st.columns([5, 1])
    with cols[0]:
        prompt = st.chat_input("Enter your question about UDST policies:")
    with cols[1]:
        if st.button("Clear Chat", 
                   key="clear_chat",
                   use_container_width=True,
                   help="Clear conversation history"):
            st.session_state.messages = []
            st.rerun()

# Process query
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.spinner("🔍 Searching university policies..."):
        response = generate_response(prompt)
    st.session_state.messages.append({
        "role": "assistant",
        "content": f"{response}"
    })
    st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: grey;">
    <p>Note: Responses are based on official UDST policies.</p>
</div>
""", unsafe_allow_html=True)
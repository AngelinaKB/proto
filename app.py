import streamlit as st
from backend.llm import generate_sql, LLMError

# -------------------------------------------------------
# Page config — must be first Streamlit call in the file
# -------------------------------------------------------
st.set_page_config(
    page_title="Optic",
    page_icon="🔍",
    layout="centered",
)

# -------------------------------------------------------
# Minimal style tweaks
# -------------------------------------------------------
st.markdown("""
<style>
    /* Tighten up the top padding */
    .block-container { padding-top: 2rem; }
    /* Style the SQL code block */
    .sql-box {
        background: #0e1117;
        border: 1px solid #2d2d3f;
        border-radius: 8px;
        padding: 1rem;
        font-family: monospace;
        font-size: 0.85rem;
        white-space: pre-wrap;
        color: #a9b1d6;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------
# Header
# -------------------------------------------------------
st.title("🔍 Optic")
st.caption("Ask questions about your workforce data in plain English.")
st.divider()

# -------------------------------------------------------
# Example questions (clickable chips)
# -------------------------------------------------------
EXAMPLES = [
    "How many active employees are in each division?",
    "How many employees were hired last month?",
    "Which countries have the most employees?",
    "What are the most common termination reasons this year?",
]

st.markdown("**Try asking:**")
cols = st.columns(len(EXAMPLES))
for i, example in enumerate(EXAMPLES):
    if cols[i].button(example, use_container_width=True, key=f"ex_{i}"):
        st.session_state["prefill"] = example
        st.rerun()

st.divider()

# -------------------------------------------------------
# Question input
# -------------------------------------------------------
prefill = st.session_state.pop("prefill", "")
question = st.text_input(
    label="Your question",
    value=prefill,
    placeholder="e.g. How many employees were hired last month?",
    label_visibility="collapsed",
)

run = st.button("Ask", type="primary", use_container_width=True)

# -------------------------------------------------------
# Run the pipeline
# -------------------------------------------------------
if run and question.strip():
    st.divider()

    with st.spinner("Generating SQL..."):
        try:
            sql = generate_sql(question.strip())

            # ── Phase 1: show the SQL, no execution yet ──
            st.markdown("**Generated SQL**")
            st.code(sql, language="sql")

            st.info(
                "✅ Phase 1 complete — SQL generated successfully. "
                "Snowflake execution will be added in Phase 2.",
                icon="ℹ️",
            )

        except LLMError as e:
            st.error(f"**Could not generate SQL**\n\n{e}")

elif run and not question.strip():
    st.warning("Please enter a question first.")


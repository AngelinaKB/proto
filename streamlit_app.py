import streamlit as st
import requests
import json
from app.config import settings

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Data Flow Insight",
    page_icon="🔍",
    layout="wide",
)

# ── Config ────────────────────────────────────────────────────────────────────
API_URL = "http://localhost:8000/ask"

EXAMPLE_QUESTIONS = [
    "What failed last night?",
    "Which services haven't run in the last 7 days?",
    "What are the most common errors this week?",
    "Which jobs are running right now?",
    "Compare failures this week versus last week by report.",
    "Show SQL for service X.",
]

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🔍 Data Flow Insight")
st.caption("Natural language queries over service configuration and execution logs.")
st.divider()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Settings")
    show_sql = st.toggle("Show generated SQL", value=True)
    show_raw = st.toggle("Show raw JSON response", value=False)

    st.divider()
    st.header("💡 Example questions")
    for example in EXAMPLE_QUESTIONS:
        if st.button(example, use_container_width=True):
            st.session_state["question_input"] = example

# ── Input ─────────────────────────────────────────────────────────────────────
question = st.text_area(
    "Ask a question",
    key="question_input",
    placeholder="e.g. What failed last night?",
    height=80,
)

submit = st.button("Run", type="primary", use_container_width=False)

# ── Query & results ───────────────────────────────────────────────────────────
if submit and question.strip():
    with st.spinner("Generating SQL and querying..."):
        try:
            resp = requests.post(
                API_URL,
                json={"question": question.strip()},
                timeout=30,
            )
            data = resp.json()
        except requests.exceptions.ConnectionError:
            st.error("❌ Could not connect to the API. Is the server running on localhost:8000?")
            st.stop()
        except Exception as e:
            st.error(f"❌ Unexpected error: {e}")
            st.stop()

    # ── Error response ─────────────────────────────────────────────────────
    if data.get("status") == "error":
        st.error(f"❌ {data.get('error', 'Unknown error')}")

    # ── Success response ───────────────────────────────────────────────────
    else:
        rows = data.get("rows", [])
        sql = data.get("sql")
        summary = data.get("summary")
        result_type = data.get("result_type")

        # Summary (available from Phase 5)
        if summary:
            st.info(f"📝 {summary}")

        # Metrics strip
        col1, col2, col3 = st.columns(3)
        col1.metric("Rows returned", len(rows))
        if result_type:
            col2.metric("Result type", result_type)

        st.divider()

        # SQL panel
        if show_sql and sql:
            with st.expander("🧠 Generated SQL", expanded=True):
                st.code(sql, language="sql")

        # Results table
        if rows:
            st.subheader("Results")
            st.dataframe(rows, use_container_width=True)
        else:
            st.info("Query returned no rows.")

        # Raw JSON
        if show_raw:
            with st.expander("📦 Raw JSON response"):
                st.json(data)

elif submit and not question.strip():
    st.warning("Please enter a question.")

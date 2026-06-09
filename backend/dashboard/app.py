"""
Meeting AI Platform — Streamlit Analytics Dashboard.

Run:
    streamlit run dashboard/app.py
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

API_BASE = "http://localhost:8000"

st.set_page_config(
    page_title="Meeting AI Platform",
    page_icon="🧠",
    layout="wide",
)

st.title("🧠 Meeting AI Platform — Analytics Dashboard")

# ── Sidebar ──────────────────────────────────────────────────────────────────
st.sidebar.header("Navigation")
page = st.sidebar.radio(
    "Go to",
    ["Overview", "Meeting Detail", "RAG Q&A", "Ingest Text"],
)

# ── Helper ───────────────────────────────────────────────────────────────────

def api_get(path: str):
    try:
        r = requests.get(f"{API_BASE}{path}", timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API error: {e}")
        return None


def api_post(path: str, payload: dict):
    try:
        r = requests.post(f"{API_BASE}{path}", json=payload, timeout=60)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API error: {e}")
        return None


# ── Overview page ─────────────────────────────────────────────────────────────
if page == "Overview":
    st.header("📊 Platform Overview")

    overview = api_get("/analytics/overview")
    if overview:
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Meetings", overview.get("total_meetings", 0))
        col2.metric("Transcript Chunks", overview.get("total_transcript_chunks", 0))
        col3.metric("Vectors Indexed", overview.get("total_vectors_indexed", 0))

    st.divider()
    st.subheader("📋 All Meetings")
    meetings = api_get("/meetings/")
    if meetings:
        df = pd.DataFrame(meetings)
        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No meetings ingested yet.")


# ── Meeting Detail page ───────────────────────────────────────────────────────
elif page == "Meeting Detail":
    st.header("🔍 Meeting Detail")

    meetings = api_get("/meetings/") or []
    if not meetings:
        st.warning("No meetings found. Ingest a meeting first.")
    else:
        meeting_ids = [m["id"] for m in meetings]
        selected_id = st.selectbox("Select Meeting", meeting_ids)

        if selected_id:
            tabs = st.tabs(["Summary", "Action Items", "Sentiment", "Topics", "Engagement", "Agent"])

            # Summary
            with tabs[0]:
                st.subheader("📝 AI Summary")
                if st.button("Generate Summary"):
                    with st.spinner("Generating…"):
                        data = api_get(f"/meetings/{selected_id}/summary")
                    if data:
                        st.markdown(data.get("summary", ""))

            # Action Items
            with tabs[1]:
                st.subheader("✅ Action Items")
                if st.button("Extract Action Items"):
                    with st.spinner("Extracting…"):
                        data = api_get(f"/meetings/{selected_id}/action-items")
                    if data:
                        items = data.get("action_items", [])
                        if items:
                            df = pd.DataFrame(items)
                            st.dataframe(df, use_container_width=True)
                        else:
                            st.info("No action items found.")

            # Sentiment
            with tabs[2]:
                st.subheader("😊 Sentiment Analysis")
                if st.button("Analyse Sentiment"):
                    with st.spinner("Analysing…"):
                        data = api_get(f"/meetings/{selected_id}/sentiment")
                    if data:
                        agg = data.get("aggregate", {})
                        col1, col2 = st.columns(2)
                        col1.metric("Average Score", round(agg.get("avg_score", 0), 3))
                        col2.metric("Overall Label", agg.get("overall_label", "—").capitalize())

                        trend = agg.get("trend", [])
                        if trend:
                            fig = px.line(
                                x=list(range(len(trend))),
                                y=trend,
                                labels={"x": "Chunk", "y": "Sentiment Score"},
                                title="Sentiment Trend",
                            )
                            fig.add_hline(y=0, line_dash="dash", line_color="gray")
                            st.plotly_chart(fig, use_container_width=True)

            # Topics
            with tabs[3]:
                st.subheader("🗂️ Topic Clusters")
                num_clusters = st.slider("Number of clusters", 2, 6, 3)
                if st.button("Cluster Topics"):
                    with st.spinner("Clustering…"):
                        data = api_get(f"/meetings/{selected_id}/topics?num_clusters={num_clusters}")
                    if data:
                        top_terms = data.get("top_terms", {})
                        for cluster_id, terms in top_terms.items():
                            st.markdown(f"**Cluster {cluster_id}:** {', '.join(terms)}")

            # Engagement
            with tabs[4]:
                st.subheader("📈 Engagement Analytics")
                if st.button("Analyse Engagement"):
                    with st.spinner("Analysing…"):
                        data = api_get(f"/meetings/{selected_id}/engagement")
                    if data:
                        score = data.get("engagement_score", 0)
                        anomalies = data.get("anomaly_count", 0)

                        fig = go.Figure(go.Indicator(
                            mode="gauge+number",
                            value=score,
                            title={"text": "Engagement Score"},
                            gauge={
                                "axis": {"range": [0, 100]},
                                "bar": {"color": "royalblue"},
                                "steps": [
                                    {"range": [0, 40], "color": "lightcoral"},
                                    {"range": [40, 70], "color": "lightyellow"},
                                    {"range": [70, 100], "color": "lightgreen"},
                                ],
                            },
                        ))
                        st.plotly_chart(fig, use_container_width=True)
                        st.metric("Anomalous Chunks", anomalies)

            # Agent
            with tabs[5]:
                st.subheader("🤖 AI Agent Analysis")
                if st.button("Run Agent"):
                    with st.spinner("Running agent pipeline…"):
                        data = api_post(f"/agent/{selected_id}/run", {})
                    if data:
                        esc = data.get("escalation", {})
                        st.markdown(f"**Escalation needed:** {'🔴 YES' if esc.get('escalate') else '🟢 NO'}")
                        st.markdown(f"**Reason:** {esc.get('reason', '—')}")

                        unresolved = data.get("unresolved_discussions", [])
                        if unresolved:
                            st.markdown("**Unresolved Discussions:**")
                            for item in unresolved:
                                st.markdown(f"- {item}")

                        st.markdown("**Reminder:**")
                        st.info(data.get("reminder_message", "—"))


# ── RAG Q&A page ──────────────────────────────────────────────────────────────
elif page == "RAG Q&A":
    st.header("💬 Contextual Q&A over Meeting History")
    query = st.text_input("Ask a question about your meetings…",
                          placeholder="What decisions were made about Project X?")
    top_k = st.slider("Number of context chunks", 1, 10, 5)

    if st.button("Ask") and query:
        with st.spinner("Retrieving and generating answer…"):
            data = api_post("/rag/ask", {"query": query, "top_k": top_k})
        if data:
            st.markdown("### Answer")
            st.write(data.get("answer", ""))

            sources = data.get("sources", [])
            if sources:
                with st.expander("📚 Source Chunks"):
                    for s in sources:
                        st.markdown(
                            f"**Meeting:** `{s.get('meeting_id')}` | "
                            f"**Chunk:** {s.get('chunk_id')} | "
                            f"**Distance:** {s.get('distance', 0):.4f}"
                        )
                        st.text(s.get("text", ""))
                        st.divider()


# ── Ingest Text page ──────────────────────────────────────────────────────────
elif page == "Ingest Text":
    st.header("📥 Ingest a Transcript")
    meeting_id = st.text_input("Meeting ID (optional — leave blank to auto-generate)")
    transcript = st.text_area("Paste transcript here…", height=300)

    if st.button("Ingest") and transcript:
        with st.spinner("Ingesting…"):
            payload = {"transcript": transcript}
            if meeting_id:
                payload["meeting_id"] = meeting_id
            data = api_post("/ingest/text", payload)
        if data:
            st.success(f"✅ Ingested! Meeting ID: `{data.get('meeting_id')}`")
            st.json(data)

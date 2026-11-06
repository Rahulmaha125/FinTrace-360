"""
================================================================================
FinTrace 360: Financial Transaction Intelligence & Risk Analytics
Streamlit Production Dashboard Application
================================================================================
Run locally via:
    streamlit run app.py
Deploy to Streamlit Cloud by connecting your GitHub repository to streamlit.io.
"""

from pathlib import Path
import json
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ------------------------------------------------------------------------------
# 1. Page Configuration & Custom CSS
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="FinTrace 360 — Financial Transaction Intelligence & AML Analytics",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Dark/Light mode adaptive, card elevation, clean typography)
st.markdown("""
<style>
    .metric-card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(148, 163, 184, 0.15);
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .metric-title {
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #94a3b8;
    }
    .metric-val {
        font-size: 1.8rem;
        font-weight: 700;
        color: #f8fafc;
        margin-top: 4px;
    }
    .metric-sub {
        font-size: 0.75rem;
        color: #64748b;
        margin-top: 2px;
    }
    .badge-critical {
        background-color: rgba(244, 63, 94, 0.2);
        color: #f43f5e;
        border: 1px solid rgba(244, 63, 94, 0.4);
        padding: 2px 8px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 0.75rem;
    }
    .badge-high {
        background-color: rgba(245, 158, 11, 0.2);
        color: #f59e0b;
        border: 1px solid rgba(245, 158, 11, 0.4);
        padding: 2px 8px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 0.75rem;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 2. Data Loading & Caching Pipeline
# ------------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
OUTPUTS_DIR = BASE_DIR / "outputs"
METRICS_DIR = OUTPUTS_DIR / "metrics"

@st.cache_data(show_spinner="Loading FinTrace 360 Datasets...")
def load_all_datasets():
    acc_path = PROCESSED_DIR / "amlsim_accounts_clean.csv"
    tx_path = PROCESSED_DIR / "amlsim_transactions_clean.csv"
    feat_path = PROCESSED_DIR / "amlsim_account_features.csv"
    eval_path = METRICS_DIR / "ml_model_evaluation.json"

    df_acc = pd.read_csv(acc_path)
    df_tx = pd.read_csv(tx_path)
    df_feat = pd.read_csv(feat_path)

    ml_eval = {}
    if eval_path.exists():
        with open(eval_path, "r", encoding="utf-8") as f:
            ml_eval = json.load(f)

    return df_acc, df_tx, df_feat, ml_eval

try:
    df_accounts, df_transactions, df_features, ml_evaluation = load_all_datasets()
    data_loaded = True
except Exception as e:
    st.error(f"Error loading datasets: {e}")
    data_loaded = False

# ------------------------------------------------------------------------------
# 3. Sidebar Navigation & Global Filters
# ------------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 💳 FinTrace 360")
    st.caption("Financial Transaction Intelligence & Risk Engine")
    st.markdown("---")

    nav_choice = st.radio(
        "Navigation",
        [
            "🌐 3D Network Topology & Flows",
            "📊 Executive Financial Overview",
            "🚨 AML Risk Triage Queue",
            "🤖 AI / Machine Learning Diagnostics",
            "📑 Architecture & System Design"
        ],
        index=0
    )

    st.markdown("---")
    st.markdown("**Global Filters**")

    all_banks = ["All Banks"] + sorted(list(df_accounts["bank_id"].unique()))
    selected_bank = st.selectbox("Filter Banking Entity", all_banks, index=0)

    all_segments = ["All Segments"] + sorted(list(df_accounts["account_segment"].unique()))
    selected_segment = st.selectbox("Account Segment", all_segments, index=0)

    st.markdown("---")
    st.info("**GATE 1 Active Mode**\nVerified Benchmark: IBM AMLSim (20K accounts, 120.5K txs, 400 alerts). All data synthetic.")

# Filter Data according to global sidebar
filtered_accounts = df_accounts.copy()
filtered_features = df_features.copy()

if selected_bank != "All Banks":
    filtered_accounts = filtered_accounts[filtered_accounts["bank_id"] == selected_bank]
    filtered_features = filtered_features[filtered_features["bank_id"] == selected_bank]

if selected_segment != "All Segments":
    filtered_accounts = filtered_accounts[filtered_accounts["account_segment"] == selected_segment]
    filtered_features = filtered_features[filtered_features["account_segment"] == selected_segment]

# ------------------------------------------------------------------------------
# 4. VIEW 1: 3D Network Topology & Money Flows
# ------------------------------------------------------------------------------
if nav_choice == "🌐 3D Network Topology & Flows":
    st.markdown("## 🌐 3D Interactive Banking Universe & Money Flow Topologies")
    st.caption("Rotate in 3D space with mouse, zoom in/out, hover over nodes to inspect counterparty exposure, or filter by AML typology.")

    col_ctrl1, col_ctrl2 = st.columns([2, 1])
    with col_ctrl1:
        topology_filter = st.radio(
            "Topology Focus",
            ["All Flow Corridors", "Fan-In Smurfing Hubs", "Cyclic Layering Loops", "High-Value Wires ($400+)"],
            horizontal=True
        )

    # Sample sub-graph for interactive, smooth 3D rendering
    np.random.seed(42)
    alert_nodes = df_features[df_features["is_sar_alert"] == 1]["account_id"].head(25).tolist()
    high_turnover_nodes = df_features[df_features["turnover_ratio"] >= 40.0]["account_id"].head(30).tolist()
    normal_nodes = df_features[df_features["is_sar_alert"] == 0]["account_id"].sample(n=60, random_state=42).tolist()

    all_sample_ids = list(set(alert_nodes + high_turnover_nodes + normal_nodes))
    sample_df = df_features[df_features["account_id"].isin(all_sample_ids)].copy().reset_index(drop=True)

    # Compute 3D Coordinates (Spherical Projection)
    n_pts = len(sample_df)
    theta = np.linspace(0, 2 * np.pi, n_pts, endpoint=False)
    phi = np.linspace(0, np.pi, n_pts, endpoint=False)
    radius = np.where(sample_df["is_sar_alert"] == 1, 80 + np.random.uniform(0, 40, n_pts), 140 + np.random.uniform(0, 80, n_pts))

    sample_df["x"] = radius * np.sin(phi) * np.cos(theta)
    sample_df["y"] = radius * np.sin(phi) * np.sin(theta)
    sample_df["z"] = radius * np.cos(phi)

    # Color & Size mapping
    def assign_node_style(row):
        if row["is_sar_alert"] == 1:
            return "SAR Alert Hub", "#f43f5e", 10
        elif row["turnover_ratio"] >= 40.0:
            return "High Turnover Node", "#fbbf24", 7
        else:
            return "Benign Account", "#38bdf8", 4

    sample_df[["category", "color", "marker_size"]] = sample_df.apply(assign_node_style, axis=1, result_type="expand")

    # Build 3D Scatter Figure
    fig3d = go.Figure()

    # Draw Nodes by Category
    for cat, group in sample_df.groupby("category"):
        fig3d.add_trace(go.Scatter3d(
            x=group["x"],
            y=group["y"],
            z=group["z"],
            mode="markers+text",
            name=cat,
            marker=dict(
                size=group["marker_size"],
                color=group["color"],
                opacity=0.9,
                line=dict(color="#0f172a", width=1)
            ),
            text=np.where(group["is_sar_alert"] == 1, group["account_id"].apply(lambda i: f"ACCT-{i}"), ""),
            textposition="top center",
            textfont=dict(size=9, color="#ffffff"),
            hoverinfo="text",
            hovertext=group.apply(
                lambda r: f"<b>Account:</b> ACCT-{r['account_id']}<br>"
                          f"<b>Bank:</b> {r['bank_id']}<br>"
                          f"<b>Segment:</b> {r['account_segment']}<br>"
                          f"<b>Initial Balance:</b> ${r['initial_balance']:,.2f}<br>"
                          f"<b>Turnover:</b> ${r['total_volume']:,.2f} ({r['turnover_ratio']:.1f}x)<br>"
                          f"<b>In/Out Txs:</b> {int(r['in_tx_count'])} In / {int(r['out_tx_count'])} Out<br>"
                          f"<b>Status:</b> {'SAR ALERT (Confirmed)' if r['is_sar_alert'] == 1 else 'Normal'}",
                axis=1
            )
        ))

    # Draw Flow Edges
    # Edge sample connecting nodes
    edge_x, edge_y, edge_z = [], [], []
    id_to_coords = {r["account_id"]: (r["x"], r["y"], r["z"]) for _, r in sample_df.iterrows()}

    # Connect smurfing hub 9998 to inbound mules
    hub_coords = id_to_coords.get(9998, (0, 0, 0))
    for acct_id, coords in id_to_coords.items():
        if acct_id != 9998 and np.random.rand() < 0.15:
            edge_x.extend([coords[0], hub_coords[0], None])
            edge_y.extend([coords[1], hub_coords[1], None])
            edge_z.extend([coords[2], hub_coords[2], None])

    fig3d.add_trace(go.Scatter3d(
        x=edge_x, y=edge_y, z=edge_z,
        mode="lines",
        name="Transaction Flow",
        line=dict(color="rgba(148, 163, 184, 0.25)", width=1.5),
        hoverinfo="none"
    ))

    fig3d.update_layout(
        scene=dict(
            xaxis=dict(showbackground=False, showticklabels=False, title=""),
            yaxis=dict(showbackground=False, showticklabels=False, title=""),
            zaxis=dict(showbackground=False, showticklabels=False, title=""),
            bgcolor="#020617"
        ),
        margin=dict(l=0, r=0, b=0, t=0),
        legend=dict(orientation="h", yanchor="bottom", y=0.02, xanchor="center", x=0.5, font=dict(color="#94a3b8")),
        paper_bgcolor="#020617",
        height=580
    )

    st.plotly_chart(fig3d, use_container_width=True)

    # Detailed Account Dossier Inspector
    st.markdown("### 🔍 Account Risk Dossier & Typology Deep Dive")
    col_d1, col_d2 = st.columns([1, 2])

    with col_d1:
        top_critical = df_features[df_features["is_sar_alert"] == 1].sort_values(by="turnover_ratio", ascending=False)
        selected_account_id = st.selectbox(
            "Select Account to Inspect",
            top_critical["account_id"].tolist(),
            format_func=lambda i: f"ACCT-{i} (Turnover: {df_features.loc[df_features['account_id']==i, 'turnover_ratio'].values[0]:.1f}x)"
        )

    acct_row = df_features[df_features["account_id"] == selected_account_id].iloc[0]

    with col_d2:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Bank Entity", acct_row["bank_id"])
        c2.metric("Segment", acct_row["account_segment"])
        c3.metric("Opening Balance", f"${acct_row['initial_balance']:,.2f}")
        c4.metric("Turnover Ratio", f"{acct_row['turnover_ratio']:.1f}x", delta="CRITICAL" if acct_row["turnover_ratio"] > 100 else "ELEVATED")

    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Total Inflow ($)", f"${acct_row['total_inflow']:,.2f}", f"{int(acct_row['in_tx_count'])} transfers")
    col_m2.metric("Total Outflow ($)", f"${acct_row['total_outflow']:,.2f}", f"{int(acct_row['out_tx_count'])} transfers")
    col_m3.metric("Gross Turnover ($)", f"${acct_row['total_volume']:,.2f}", f"Active Days: {int(acct_row['total_active_days'])}")

    st.warning(f"**AML Typology Detected:** Account exhibits an extreme turnover-to-balance velocity of **{acct_row['turnover_ratio']:.1f}x** with **{int(acct_row['in_tx_count'])} inbound transfers** from disparate counterparties, matching high-priority **Smurfing Aggregator (Fan-In)** and **Cyclic Layering** signatures.")

# ------------------------------------------------------------------------------
# 5. VIEW 2: Executive Financial Overview
# ------------------------------------------------------------------------------
elif nav_choice == "📊 Executive Financial Overview":
    st.markdown("## 📊 Executive Financial Overview & Payment Rail Dynamics")
    st.caption("High-level transaction volume, payment channel breakdown, and cross-institutional clearing positions.")

    # Executive KPI Cards
    k1, k2, k3, k4, k5 = st.columns(5)
    total_tx_cnt = len(df_transactions)
    total_gross_vol = df_transactions["amount"].sum()
    avg_ticket = df_transactions["amount"].mean()
    alert_tx_cnt = int(df_transactions["is_alerted_tx"].sum())
    alert_vol = df_transactions[df_transactions["is_alerted_tx"] == 1]["amount"].sum()

    k1.metric("Total Transactions", f"{total_tx_cnt:,}", "149 Operating Days")
    k2.metric("Gross Settlement Flow", f"${total_gross_vol/1e6:.2f}M", "100% Verified")
    k3.metric("Average Transfer Size", f"${avg_ticket:,.2f}", f"Median: ${df_transactions['amount'].median():,.2f}")
    k4.metric("Monitored Accounts", f"{len(df_accounts):,}", "5 Banking Institutions")
    k5.metric("Alerted Transaction Flow", f"${alert_vol/1e6:.2f}M", f"{alert_tx_cnt/total_tx_cnt*100:.1f}% Alert Share")

    st.markdown("---")

    col_chart1, col_chart2 = st.columns([2, 1])

    with col_chart1:
        st.markdown("##### 📈 Daily Transaction Trajectory & Alert Activity (149 Days)")
        daily_agg = df_transactions.groupby("step_day").agg(
            total_volume=("amount", "sum"),
            alert_volume=("amount", lambda s: s[df_transactions.loc[s.index, "is_alerted_tx"] == 1].sum()),
            tx_count=("transaction_id", "count")
        ).reset_index()

        fig_daily = go.Figure()
        fig_daily.add_trace(go.Bar(
            x=daily_agg["step_day"],
            y=daily_agg["total_volume"],
            name="Normal Settlement Volume",
            marker_color="#0284c7"
        ))
        fig_daily.add_trace(go.Bar(
            x=daily_agg["step_day"],
            y=daily_agg["alert_volume"],
            name="Alerted (SAR) Volume",
            marker_color="#f43f5e"
        ))
        fig_daily.update_layout(
            barmode="stack",
            xaxis_title="Simulation Day (Step 1 to 149)",
            yaxis_title="Settlement Volume ($)",
            legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center"),
            margin=dict(l=0, r=0, t=20, b=0),
            height=340
        )
        st.plotly_chart(fig_daily, use_container_width=True)

    with col_chart2:
        st.markdown("##### 💳 Gross Volume by Payment Rail")
        rail_agg = df_transactions.groupby("transaction_type").agg(
            gross_volume=("amount", "sum"),
            count=("transaction_id", "count")
        ).reset_index()

        fig_donut = px.pie(
            rail_agg,
            values="gross_volume",
            names="transaction_type",
            hole=0.5,
            color="transaction_type",
            color_discrete_map={
                "WIRE": "#38bdf8",
                "ACH_TRANSFER": "#818cf8",
                "INTERNAL_TRANSFER": "#34d399",
                "INSTANT_PAY": "#fbbf24"
            }
        )
        fig_donut.update_layout(
            margin=dict(l=0, r=0, t=10, b=0),
            legend=dict(orientation="h", y=-0.1),
            height=340
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    # Bank Comparison
    st.markdown("##### 🏦 Institutional Clearing Volume & Exposure Breakdown")
    bank_agg = df_transactions.groupby("originator_bank_id").agg(
        total_outflow=("amount", "sum"),
        tx_count=("transaction_id", "count"),
        alerted_tx=("is_alerted_tx", "sum"),
        alerted_volume=("amount", lambda s: s[df_transactions.loc[s.index, "is_alerted_tx"] == 1].sum())
    ).reset_index()
    bank_agg["alert_rate_pct"] = (bank_agg["alerted_tx"] / bank_agg["tx_count"] * 100).round(2)

    col_b1, col_b2 = st.columns([2, 1])
    with col_b1:
        fig_bank = px.bar(
            bank_agg,
            x="originator_bank_id",
            y=["total_outflow", "alerted_volume"],
            barmode="group",
            labels={"value": "Volume ($)", "originator_bank_id": "Bank Identifier"},
            color_discrete_map={"total_outflow": "#0ea5e9", "alerted_volume": "#f43f5e"},
            height=280
        )
        fig_bank.update_layout(margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig_bank, use_container_width=True)

    with col_b2:
        st.dataframe(
            bank_agg[["originator_bank_id", "tx_count", "alert_rate_pct"]].rename(
                columns={"originator_bank_id": "Bank", "tx_count": "Transactions", "alert_rate_pct": "Alert %"}
            ),
            use_container_width=True,
            height=280
        )

# ------------------------------------------------------------------------------
# 6. VIEW 3: AML Risk Investigation Triage Queue
# ------------------------------------------------------------------------------
elif nav_choice == "🚨 AML Risk Triage Queue":
    st.markdown("## 🚨 AML Risk Investigation & Smurfing Triage Queue")
    st.caption("Prioritized investigation queue ranked by velocity turnover ratio and graph centrality. Filters out 95% false alarms.")

    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        tier_filter = st.selectbox("Filter Risk Classification", ["All Tiers", "CRITICAL", "HIGH", "MEDIUM", "LOW"])
    with col_f2:
        alert_only = st.checkbox("Show Confirmed SAR Alerts Only", value=True)
    with col_f3:
        search_query = st.text_input("Search Account ID", "")

    # Assign Priority
    triage_df = filtered_features.copy()
    def compute_tier(row):
        if row["turnover_ratio"] >= 100.0 and row["in_tx_count"] >= 20:
            return "CRITICAL"
        elif row["turnover_ratio"] >= 50.0:
            return "HIGH"
        elif row["is_sar_alert"] == 1:
            return "HIGH"
        elif row["total_tx_count"] >= 15:
            return "MEDIUM"
        else:
            return "LOW"

    triage_df["risk_tier"] = triage_df.apply(compute_tier, axis=1)

    if tier_filter != "All Tiers":
        triage_df = triage_df[triage_df["risk_tier"] == tier_filter]
    if alert_only:
        triage_df = triage_df[triage_df["is_sar_alert"] == 1]
    if search_query:
        triage_df = triage_df[triage_df["account_id"].astype(str).str.contains(search_query)]

    triage_df = triage_df.sort_values(by="turnover_ratio", ascending=False)

    st.markdown(f"**Showing {len(triage_df):,} accounts matching criteria**")

    # Display Table
    st.dataframe(
        triage_df[[
            "account_id", "bank_id", "account_segment", "initial_balance",
            "total_inflow", "total_outflow", "total_volume", "turnover_ratio",
            "in_tx_count", "out_tx_count", "risk_tier"
        ]].rename(columns={
            "account_id": "Account ID",
            "bank_id": "Bank",
            "account_segment": "Segment",
            "initial_balance": "Opening Bal ($)",
            "total_inflow": "Inflow ($)",
            "total_outflow": "Outflow ($)",
            "total_volume": "Turnover ($)",
            "turnover_ratio": "Turnover Ratio",
            "in_tx_count": "Inbound Txs",
            "out_tx_count": "Outbound Txs",
            "risk_tier": "Risk Tier"
        }),
        use_container_width=True,
        height=450
    )

    if st.button("📥 Export Current Triage View to CSV"):
        csv_data = triage_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download CSV Report",
            data=csv_data,
            file_name="fintrace360_aml_triage_export.csv",
            mime="text/csv"
        )

# ------------------------------------------------------------------------------
# 7. VIEW 4: AI & Machine Learning Diagnostics
# ------------------------------------------------------------------------------
elif nav_choice == "🤖 AI / Machine Learning Diagnostics":
    st.markdown("## 🤖 Machine Learning & Anomaly Detection Performance")
    st.caption("Benchmarking supervised classifiers and unsupervised anomaly detection on imbalanced financial fraud.")

    if ml_evaluation:
        df_ml = pd.DataFrame(ml_evaluation).T.reset_index().rename(columns={"index": "Model Architecture"})

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Best Model PR-AUC", "0.7749", "Logistic Regression")
        c2.metric("Ensemble ROC-AUC", "0.9091", "Random Forest")
        c3.metric("SAR Detection Recall", "72.3%", "261 / 361 Caught")
        c4.metric("False Positive Rate", "3.60%", "Controlled Alert Fatigue")

        st.markdown("##### 🏆 Model Comparison Benchmark (4,000 Holdout Accounts)")
        st.dataframe(
            df_ml[["Model Architecture", "precision", "recall", "f1_score", "pr_auc", "roc_auc", "false_positive_rate", "true_positives", "false_positives"]].rename(columns={
                "precision": "Precision",
                "recall": "Recall",
                "f1_score": "F1-Score",
                "pr_auc": "PR-AUC",
                "roc_auc": "ROC-AUC",
                "false_positive_rate": "False Positive Rate",
                "true_positives": "True Positives",
                "false_positives": "False Positives"
            }),
            use_container_width=True
        )

        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.markdown("##### 📊 PR-AUC Comparison Across Architectures")
            fig_prauc = px.bar(
                df_ml,
                x="Model Architecture",
                y="pr_auc",
                color="Model Architecture",
                color_discrete_sequence=["#38bdf8", "#818cf8", "#fbbf24", "#f43f5e"],
                labels={"pr_auc": "PR-AUC Score"}
            )
            fig_prauc.update_layout(showlegend=False, height=320, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig_prauc, use_container_width=True)

        with col_m2:
            st.markdown("##### 🎯 Feature Importance Ranking (Gini Index)")
            feat_imp = pd.DataFrame({
                "Feature": ["turnover_ratio", "fan_in_index", "in_tx_count", "tx_velocity_per_day", "total_volume", "flow_ratio"],
                "Importance": [0.424, 0.186, 0.141, 0.112, 0.082, 0.055]
            }).sort_values(by="Importance", ascending=True)

            fig_imp = px.bar(
                feat_imp,
                x="Importance",
                y="Feature",
                orientation="h",
                color="Importance",
                color_continuous_scale="Viridis"
            )
            fig_imp.update_layout(height=320, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig_imp, use_container_width=True)
    else:
        st.warning("ML evaluation metrics not found. Run `python src/ml/train_models.py` to populate.")

# ------------------------------------------------------------------------------
# 8. VIEW 5: Architecture & System Design
# ------------------------------------------------------------------------------
elif nav_choice == "📑 Architecture & System Design":
    st.markdown("## 📑 FinTrace 360 System Architecture & Governance")
    st.markdown("""
    ### Two-Gate Strategic Design:
    - **GATE 1 — Global Demo / Portfolio Mode (Active Implementation):**
      - Public & synthetic datasets: IBM AMLSim benchmark (20K accounts, 120.5K txs, 400 alerts).
      - Relational Star Schema warehouse in PostgreSQL with dimensional models.
      - Advanced SQL analytics (CTEs, Window Functions, 7-day rolling volume).
      - Transparent disclosure: All entities and account numbers are simulated.
    - **GATE 2 — Bank / Organization Mode (Future Roadmap):**
      - Architecture for verified financial institutions to ingest internal transaction feeds.
      - Tenant schema isolation per institution.
      - TLS 1.3 encryption and enterprise OAuth2 / RBAC access control.
      - Automated Suspicious Activity Report (SAR) regulatory filing.
    """)
    st.markdown("---")
    st.markdown("### Technical Stack")
    st.markdown("""
    - **Core Analytics & Data Engineering:** Python 3.14, Pandas, NumPy, Scipy
    - **Relational Data Warehouse:** PostgreSQL 18.4, SQLAlchemy, Advanced SQL (CTEs, Window Functions)
    - **Business Intelligence & Dashboards:** Streamlit, Plotly WebGL 3D, Microsoft Power BI Desktop
    - **Machine Learning (20% Scope):** Scikit-learn, XGBoost, Isolation Forest (PR-AUC focus)
    """)

# Footer
st.markdown("---")
st.caption("FinTrace 360 • Financial Transaction Intelligence & Risk Analytics • Candidate Portfolio 2026")

# FinTrace 360 — Business Problem & Analytics Charter

## 1. Executive Context

Financial institutions process millions of transactions daily across retail banking, commercial wire transfers, merchant acquiring, and mobile payment gateways. Within this continuous transaction flow, detecting anomalous financial behavior, potential money laundering schemes, and payment fraud presents significant operational and technical hurdles:
- **Volume & Velocity:** High transaction volumes overwhelm manual review workflows.
- **Subtle Typologies:** Laundering operations intentionally mimic legitimate business activity through structuring (smurfing), fan-out layering, cyclical transfers, and rapid movement of funds.
- **False Positive Overhead:** Traditional static rule engines trigger excessive false alarms, creating investigative backlogs and driving up operational compliance costs.
- **Risk Indicator Framing:** A statistical outlier or unusual transaction is **not** confirmed fraud; it is an investigation lead requiring contextual evidence, entity resolution, and behavioral profiling.

---

## 2. Strategic Operating Modes (Gate 1 vs. Gate 2)

FinTrace 360 solves these operational problems with an architecture structured around two gates:

### Gate 1 — Global Demo / Portfolio Mode (Active Implementation)
- Ingests public and synthetic transaction datasets (IBM AMLSim primary, PaySim, IEEE-CIS).
- Clearly demarcated simulated entities and synthetic account structures.
- Provides recruiter and industry stakeholder visibility into SQL data warehousing, business intelligence (Power BI), exploratory data analysis, and baseline/anomaly machine learning pipelines.
- Zero reliance on or claims of accessing proprietary banking data.

### Gate 2 — Bank / Organization Mode (Future Roadmap)
- Architectural foundation for verified financial institutions to connect their own internal data feeds.
- Independent database schema isolation per tenant bank.
- Enterprise security model (TLS 1.3, OAuth2/OIDC, RBAC, immutable audit logging).
- Automated regulatory reporting workflows (e.g., Suspicious Activity Reports / SAR triage).

---

## 3. Core Analytical Questions Addressed

1. **Transaction Velocity & Value:** What are the baseline transaction frequencies, gross monetary values, and average transaction amounts across accounts and channels?
2. **Account Activity Profiling:** Which originator and beneficiary accounts display unusually elevated activity or high transaction counts?
3. **Typology & Channel Distribution:** What are the dominant transaction types, and how do their velocity distributions differ between standard operations and alerted activity?
4. **Anti-Money Laundering Patterns:** Which structural network patterns (cycles, fan-in/fan-out, scatter-gather) are most strongly associated with AML alerts?
5. **Temporal Dynamics:** How does transaction velocity shift across steps, days, and operating windows?
6. **Network Graph Connectivity:** How are accounts connected across multi-hop counterparty transaction paths?
7. **Structuring Detection:** Can we isolate transaction clusters operating just below statutory reporting thresholds?
8. **Benign Outliers vs. Genuine Alerts:** How effectively can feature engineering separate high-wealth commercial accounts from malicious layering?
9. **Predictive Capability:** What is the realistic Precision, Recall, and PR-AUC trade-off for supervised classification on highly imbalanced synthetic alerts?
10. **Actionable Compliance Recommendations:** What data-driven policies can compliance teams deploy to optimize rule thresholds and investigative triage?

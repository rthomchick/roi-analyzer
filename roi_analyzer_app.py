import streamlit as st
import os
import sys

# Add current directory to path so imports work
sys.path.insert(0, os.path.dirname(__file__))

from roi_analyzer_production import ProductionROIAnalyzer

# ── Page Config ───────────────────────────────────────────────────────

st.set_page_config(
    page_title="ROI Analyzer",
    page_icon="📊",
    layout="wide"
)

# ── UI ────────────────────────────────────────────────────────────────

st.title("📊 Personalization ROI Analyzer")
st.caption("Quantify the business case for personalization investments")

# Input form
st.subheader("Investment Parameters")

col1, col2, col3 = st.columns(3)

with col1:
    investment = st.number_input(
        "Investment Amount ($)",
        min_value=10000,
        max_value=10000000,
        value=500000,
        step=50000,
        help="Total investment including development, licensing, and implementation"
    )

with col2:
    lift_pct = st.number_input(
        "Expected Conversion Lift (%)",
        min_value=0.1,
        max_value=5.0,
        value=0.6,
        step=0.1,
        help="Absolute percentage point increase in conversion rate (0.6% is a realistic target)"
    )

with col3:
    annual_traffic = st.number_input(
        "Annual Site Traffic",
        min_value=100000,
        max_value=100000000,
        value=1000000,
        step=100000,
        help="Total annual visitors to your site"
    )

scenario = st.text_input(
    "Scenario Description (optional)",
    placeholder="e.g. AI personalization improvements for product pages"
)

st.divider()

# Run analysis
if st.button("Run ROI Analysis", type="primary"):

    # Convert lift from percentage to decimal
    lift_decimal = lift_pct / 100

    with st.spinner("Running analysis... (this may take 30-60 seconds)"):
        try:
            analyzer = ProductionROIAnalyzer(
                annual_traffic=int(annual_traffic),
                token_budget=30000
            )

            results = analyzer.analyze(
                investment_amount=float(investment),
                expected_conversion_lift=lift_decimal,
                scenario_description=scenario or None
            )

        except Exception as e:
            st.error(f"Analysis failed: {e}")
            st.stop()

    # ── Display Results ───────────────────────────────────────────────

    if results['status'] == 'validation_failed':
        st.error("Input validation failed")
        for error in results.get('errors', []):
            st.warning(error)
        st.stop()

    if results['status'] == 'partial_failure':
        st.warning(f"Analysis partially failed at step: {results.get('failed_step')}")
        st.info(f"Error ID: {results.get('error_id')}")
        st.stop()

    # Success — display results
    fi = results['financial_impact']
    cd = results['current_data']
    validation = results['validation']

    simple_roi = (fi['additional_revenue'] / investment - 1) * 100
    payback = investment / fi['additional_revenue']

    # Assessment banner
    assessment = validation['assessment']
    if assessment == 'requires_scrutiny':
        st.error("🔴 HIGH-RISK SCENARIO — Requires executive scrutiny")
    elif assessment == 'needs_validation':
        st.warning("🟡 MODERATE-RISK — Validate assumptions before proceeding")
    else:
        st.success("✅ LOW-RISK SCENARIO — Assumptions appear realistic")

    # Key metrics
    st.subheader("Key Metrics")
    m1, m2, m3, m4 = st.columns(4)

    with m1:
        st.metric(
            "Additional Revenue",
            f"${fi['additional_revenue']:,.0f}",
            help="Projected incremental annual revenue"
        )
    with m2:
        st.metric(
            "Simple ROI",
            f"{simple_roi:.0f}%",
            help="(Additional Revenue / Investment - 1) × 100"
        )
    with m3:
        st.metric(
            "Payback Period",
            f"{payback:.1f} years",
            help="Investment / Additional Annual Revenue"
        )
    with m4:
        st.metric(
            "Relative Lift",
            f"{fi['relative_lift']:.1%}",
            help="Percentage improvement over current conversion rate"
        )

    # Conversion economics
    st.subheader("Conversion Economics")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Current State**")
        st.markdown(f"- Conversion Rate: {cd['conversion_rate']:.2%}")
        st.markdown(f"- Annual Transactions: {fi['current_transactions']:,.0f}")
        st.markdown(f"- Average Order Value: ${fi['average_order_value']:,.2f}")
        st.markdown(f"- Annual Revenue: ${cd['revenue']:,.0f}")

    with col2:
        st.markdown("**Projected State**")
        st.markdown(f"- Conversion Rate: {fi['new_conversion_rate']:.2%}")
        st.markdown(f"- Annual Transactions: {fi['new_transactions']:,.0f}")
        st.markdown(f"- Additional Transactions: {fi['additional_transactions']:,.0f}")
        st.markdown(f"- Additional Revenue: ${fi['additional_revenue']:,.0f}")

    # Assumption warnings
    warnings = validation.get('warnings', [])
    if warnings:
        st.subheader("Assumption Flags")
        for w in warnings:
            severity_map = {
                "high": st.error,
                "medium": st.warning,
                "low": st.info,
                "info": st.info
            }
            display_fn = severity_map.get(w['severity'], st.info)
            display_fn(f"**{w['severity'].upper()}:** {w['message']}")

    # Recommendation
    st.subheader("Recommendation")
    st.markdown(results['recommendation'])

    # Cost info
    metadata = results.get('metadata', {})
    budget = metadata.get('budget_summary', {})
    st.divider()
    st.caption(
        f"Tokens used: {budget.get('usage', 0):,} / {budget.get('budget_limit', 0):,} | "
        f"Tool calls: {metadata.get('tool_calls', 0)}"
    )

    # Download report
    report = analyzer.generate_report()
    st.download_button(
        label="📥 Download Full Report",
        data=report,
        file_name="roi_analysis.txt",
        mime="text/plain"
    )
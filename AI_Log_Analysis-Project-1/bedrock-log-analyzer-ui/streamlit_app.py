"""
Streamlit UI for Bedrock Log Analyzer
Pull logs from CloudWatch and analyze with AI enhancement.

Single-group mode: analyze one log group per run for cleaner AI results.
"""
import streamlit as st
import sys
import os
from datetime import datetime, timedelta, date, time
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from cloudwatch_client import CloudWatchClient
from log_parser import LogParser
from pattern_analyzer import PatternAnalyzer
from rule_detector import RuleBasedDetector
from bedrock_enhancer import BedrockEnhancer
from log_preprocessor import LogPreprocessor
from models import Metadata, AIInfo, AnalysisResult

# Page config
st.set_page_config(
    page_title="Bedrock Log Analyzer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .solution-card {
        background-color: #e8f4f8;
        padding: 15px;
        border-left: 4px solid #0066cc;
        margin: 10px 0;
        border-radius: 5px;
    }
    .ai-badge {
        background-color: #ffd700;
        color: #000;
        padding: 5px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None
if 'is_analyzing' not in st.session_state:
    st.session_state.is_analyzing = False

# ============================================================
# SIDEBAR — Configuration
# ============================================================
st.sidebar.title("⚙️ Configuration")

# --- AWS Settings ---
st.sidebar.subheader("AWS Settings")
aws_region = st.sidebar.text_input("AWS Region", value="ap-southeast-1")
aws_profile = st.sidebar.text_input("AWS Profile", value="")

# --- Log Group Selection (single group) ---
st.sidebar.subheader("Log Source")

LOG_GROUP_OPTIONS = [
    "/aws/vpc/flowlogs",
    "/aws/cloudtrail/logs",
    "/aws/ec2/web-tier/system",
    "/aws/ec2/web-tier/httpd",
    "/aws/ec2/web-tier/application",
    "/aws/ec2/app-tier/system",
    "/aws/ec2/app-tier/streamlit",
    "/aws/rds/mysql/error",
    "/aws/rds/mysql/slowquery",
]

selected_log_group = st.sidebar.selectbox(
    "Log Group (chọn 1 nguồn mỗi lần phân tích)",
    options=LOG_GROUP_OPTIONS,
    help="Chọn đúng 1 log group để AI phân tích tập trung."
)

# Source-specific search term hints
_SEARCH_HINTS = {
    "/aws/vpc/flowlogs": "Ví dụ: REJECT, 22, 3389, ACCEPT",
    "/aws/cloudtrail/logs": "Ví dụ: AccessDenied, DeleteVpc, errorCode, root",
    "/aws/ec2/web-tier/system": "Ví dụ: Failed password, kernel, error",
    "/aws/ec2/web-tier/httpd": "Ví dụ: 404, 500, POST, GET",
    "/aws/ec2/web-tier/application": "Ví dụ: ERROR, SQL Injection, timeout, failed",
    "/aws/ec2/app-tier/system": "Ví dụ: Failed password, kernel, error",
    "/aws/ec2/app-tier/streamlit": "Ví dụ: ERROR, exception, streamlit",
    "/aws/rds/mysql/error": "Ví dụ: Access denied, connection, error",
    "/aws/rds/mysql/slowquery": "Ví dụ: Query_time, Lock_time, SELECT",
}
search_hint = _SEARCH_HINTS.get(selected_log_group, "Nhập từ khóa tìm kiếm")

# --- Search Term (required) ---
st.sidebar.subheader("Search Settings")
search_term = st.sidebar.text_input(
    "Search Term (bắt buộc)",
    value="",
    help=search_hint,
    placeholder=search_hint
)

# Internal limit for retrieval
max_matches = 10000

# --- Time Range (replaces "hours back") ---
st.sidebar.subheader("⏰ Time Range")

# Default: last 1 hour
default_end = datetime.now()
default_start = default_end - timedelta(hours=1)

col_date1, col_date2 = st.sidebar.columns(2)
with col_date1:
    start_date = st.date_input("Start Date", value=default_start.date())
with col_date2:
    start_time_input = st.time_input("Start Time", value=default_start.time().replace(second=0, microsecond=0))

col_date3, col_date4 = st.sidebar.columns(2)
with col_date3:
    end_date = st.date_input("End Date", value=default_end.date())
with col_date4:
    end_time_input = st.time_input("End Time", value=default_end.time().replace(second=0, microsecond=0))

# Combine date + time into datetime
start_dt = datetime.combine(start_date, start_time_input)
end_dt = datetime.combine(end_date, end_time_input)

# --- AI Configuration ---
st.sidebar.subheader("AI Enhancement")
enable_ai = st.sidebar.checkbox("Enable AI Enhancement", value=True)
bedrock_model = st.sidebar.selectbox(
    "Bedrock Model",
    [
        "anthropic.claude-3-haiku-20240307-v1:0", 
        "apac.anthropic.claude-3-5-sonnet-20240620-v1:0",
        "apac.anthropic.claude-3-sonnet-20240229-v1:0",
        "us.anthropic.claude-3-5-sonnet-20240620-v1:0"
    ],
    help="Dùng 'apac.' cho khu vực Singapore (ap-southeast-1) hoặc 'anthropic.claude-3-haiku' bản gốc. Haiku thường luôn chạy ổn trên on-demand."
)

# ============================================================
# MAIN CONTENT
# ============================================================
st.title("📊 Log Analysis System")
st.markdown("Single-source AI analysis — one log group per run for focused, reliable results.")

# ============================================================
# VALIDATION + ANALYZE
# ============================================================
if st.sidebar.button("🚀 Analyze Logs", use_container_width=True, type="primary"):

    # --- Input validation ---
    validation_errors = []

    if not selected_log_group:
        validation_errors.append("⚠️ Vui lòng chọn một Log Group.")

    if not search_term or not search_term.strip():
        validation_errors.append("⚠️ Search Term là bắt buộc. Vui lòng nhập từ khóa tìm kiếm.")

    if start_dt >= end_dt:
        validation_errors.append("⚠️ Start Time phải trước End Time. Kiểm tra lại khoảng thời gian.")

    if validation_errors:
        for err in validation_errors:
            st.error(err)
    else:
        # --- All inputs valid → run analysis ---
        st.session_state.is_analyzing = True

        with st.spinner("Analyzing logs..."):
            try:
                # Step 1: Pull logs from CloudWatch (single group)
                st.info(f"📥 Pulling logs from **{selected_log_group}**...")
                cw_client = CloudWatchClient(region=aws_region, profile=aws_profile)

                raw_logs = cw_client.get_logs(
                    log_group=selected_log_group,
                    start_time=start_dt,
                    end_time=end_dt,
                    search_term=search_term.strip(),
                    max_matches=max_matches
                )

                if not raw_logs:
                    st.warning(f"⚠️ No logs found in {selected_log_group} matching '{search_term}' in the selected time range.")
                    st.session_state.is_analyzing = False
                else:
                    st.success(f"✅ Found {len(raw_logs)} matching logs from {selected_log_group}")

                    # Step 2: Parse logs
                    st.info("🔍 Parsing logs...")
                    parser = LogParser()
                    matches = [parser.parse_log_entry(log) for log in raw_logs]
                    matches = [m for m in matches if m]  # Filter None values
                    st.success(f"✅ Parsed {len(matches)} log entries")

                    # Step 3: Analyze patterns
                    st.info("📊 Analyzing patterns...")
                    analyzer = PatternAnalyzer()
                    analysis = analyzer.analyze_log_entries(matches)
                    st.success(f"✅ Found {len(analysis.error_patterns)} error patterns")

                    # Step 4: Detect issues (rule-based)
                    st.info("🎯 Detecting issues...")
                    detector = RuleBasedDetector()
                    issues = detector.detect_issues(analysis)
                    solutions = detector.generate_basic_solutions(issues)
                    st.success(f"✅ Detected {len(issues)} issues")

                    # Step 4.5: Build AI context (NEW — preprocessing)
                    st.info("🧠 Building AI context...")
                    preprocessor = LogPreprocessor()
                    ai_context = preprocessor.prepare_ai_context(
                        entries=matches,
                        analysis=analysis,
                        log_group_name=selected_log_group,
                        search_term=search_term.strip(),
                        time_range_str=f"{start_dt.strftime('%H:%M %d/%m')} to {end_dt.strftime('%H:%M %d/%m')}"
                    )
                    st.success(
                        f"✅ AI context ready — source: {ai_context.source_type}, "
                        f"high-relevance logs: {ai_context.total_logs_after_scoring}, "
                        f"suspicious IPs: {len(ai_context.suspicious_ips)}"
                    )

                    # Step 5: AI Enhancement
                    enhanced_solutions = solutions
                    ai_info = None

                    if enable_ai:
                        st.info("🤖 Enhancing with AI...")
                        enhancer = BedrockEnhancer(region=aws_region, model=bedrock_model)

                        if enhancer.is_available():
                            enhanced_solutions, usage_stats = enhancer.enhance_solutions(
                                solutions,
                                ai_context=ai_context
                            )

                            if "error" in usage_stats:
                                st.error(f"❌ {usage_stats['error']}")
                                st.warning("⚠️ Đã chuyển về chế độ hiển thị Basic Solutions do lỗi Bedrock.")
                                ai_info = AIInfo(ai_enhancement_used=False)
                            else:
                                ai_info = AIInfo(
                                    ai_enhancement_used=usage_stats.get("ai_enhancement_used", False),
                                    bedrock_model_used=usage_stats.get("bedrock_model_used"),
                                    total_tokens_used=usage_stats.get("total_tokens_used"),
                                    estimated_total_cost=usage_stats.get("estimated_total_cost"),
                                    api_calls_made=usage_stats.get("api_calls_made")
                                )
                                st.success(f"✅ AI enhancement completed (Cost: ${ai_info.estimated_total_cost:.4f})")
                        else:
                            st.warning("⚠️ AWS Bedrock not available, using basic solutions")
                            ai_info = AIInfo(ai_enhancement_used=False)
                    else:
                        ai_info = AIInfo(ai_enhancement_used=False)

                    # Step 6: Create results
                    metadata = Metadata(
                        timestamp=datetime.now().isoformat(),
                        search_term=search_term.strip(),
                        log_directory=selected_log_group,
                        total_files_searched=1,
                        total_matches=len(matches)
                    )

                    results = AnalysisResult(
                        metadata=metadata,
                        matches=matches,
                        analysis=analysis,
                        solutions=enhanced_solutions,
                        ai_info=ai_info
                    )

                    st.session_state.analysis_result = results
                    st.success("✅ Analysis complete!")

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                import traceback
                st.error(traceback.format_exc())
            finally:
                st.session_state.is_analyzing = False

# ============================================================
# RESULTS TABS (unchanged structure)
# ============================================================
tab1, tab2, tab3 = st.tabs(["📋 Summary", "📊 Analysis", "🔧 Solutions"])

if st.session_state.analysis_result is None:
    st.info("👈 Configure settings and click 'Analyze Logs' in the sidebar to see results")
else:
    result = st.session_state.analysis_result
    
    with tab1:
        st.subheader("Analysis Summary")
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Logs", result.metadata.total_matches)
        with col2:
            st.metric("Issues Found", len(result.solutions))
        with col3:
            if result.ai_info and result.ai_info.ai_enhancement_used:
                st.metric("AI Enhanced", "✅ Yes")
            else:
                st.metric("AI Enhanced", "❌ No")
        with col4:
            if result.ai_info and result.ai_info.estimated_total_cost:
                st.metric("Cost", f"${result.ai_info.estimated_total_cost:.4f}")
            else:
                st.metric("Cost", "$0.00")
        
        st.divider()
        
        # Component Error Summary Table
        st.subheader("🎯 Component Error Summary")
        if result.analysis.components:
            total_errors = sum(result.analysis.components.values())
            table_data = []
            for comp, count in result.analysis.components.items():
                ratio = f"{(count / total_errors) * 100:.1f}%" if total_errors > 0 else "0%"
                table_data.append({
                    "Nguồn Log (Component)": comp,
                    "Số lượng Lỗi": count,
                    "Tỉ trọng (%)": ratio
                })
            
            # Remove index when rendering the dataframe to make it cleaner
            st.dataframe(table_data, use_container_width=True, hide_index=True)
        else:
            st.info("Chưa có dữ liệu Component nào được tìm thấy.")
            
        st.divider()
        
        # Export results
        st.subheader("📥 Export Results")
        col1, col2 = st.columns(2)
        
        with col1:
            json_str = result.to_json()
            st.download_button(
                label="📄 Download JSON",
                data=json_str,
                file_name=f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        
        with col2:
            # CSV export
            csv_data = "Problem,Issue Type,Components,AI Enhanced,Solution\n"
            for sol in result.solutions:
                # Ép kiểu an toàn vì Bedrock thỉnh thoảng trả về dict/json object
                safe_solution = str(sol.solution).replace('"', '""')
                csv_data += f'"{sol.problem}","{sol.issue_type.value}","{", ".join(sol.affected_components)}",{sol.ai_enhanced},"{safe_solution[:100]}..."\n'
            
            st.download_button(
                label="📊 Download CSV",
                data=csv_data,
                file_name=f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

    with tab2:
        st.subheader("Detailed Analysis")
        
        # Severity distribution
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Severity Distribution")
            severity_data = result.analysis.severity_distribution
            if severity_data:
                st.bar_chart(severity_data)
        
        with col2:
            st.subheader("🏗️ Component Distribution")
            component_data = result.analysis.components
            if component_data:
                st.bar_chart(component_data)
        
        st.divider()
        
        # Error patterns
        st.subheader("🔴 Error Patterns")
        if result.analysis.error_patterns:
            for i, pattern in enumerate(result.analysis.error_patterns[:10], 1):
                with st.expander(f"{i}. {pattern.pattern[:60]}... (Count: {pattern.count})"):
                    st.write(f"**Component:** {pattern.component}")
                    st.write(f"**Count:** {pattern.count}")
                    st.write(f"**Pattern:** {pattern.pattern}")
        else:
            st.info("No error patterns found")

    with tab3:
        st.subheader("Suggested Solutions")
        if result.solutions:
            for i, solution in enumerate(result.solutions, 1):
                # If we have structural JSON from the new Bedrock prompt, render it layered
                if solution.structured_solution:
                    s_data = solution.structured_solution
                    attack_class = s_data.get("attack_classification", {})
                    summary = s_data.get("summary", {})
                    investigation = s_data.get("investigation", {})
                    action_plan = s_data.get("action_plan", {})
                    
                    with st.expander(f"🚨 {solution.problem}", expanded=True):
                        st.markdown(f'<span class="ai-badge">✨ AI Enhanced</span>', unsafe_allow_html=True)
                        st.write(f"**Components:** {', '.join(solution.affected_components)}")
                        
                        # NEW: Attack Classification
                        if attack_class:
                            st.markdown("### 🎯 Attack Classification")
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("MITRE Technique", attack_class.get("mitre_technique", "N/A"))
                            with col2:
                                st.metric("Threat Actor", attack_class.get("threat_actor_profile", "N/A"))
                            with col3:
                                st.metric("Attack Stage", attack_class.get("attack_stage", "N/A"))
                            st.divider()
                        
                        # Tier 1: Summary Box
                        severity = summary.get("severity", "Unknown")
                        impact = summary.get("impact", "Unknown")
                        confidence = summary.get("confidence", "Unknown")
                        
                        # Color-code severity
                        severity_color = {
                            "Critical": "🔴",
                            "High": "🟠",
                            "Medium": "🟡",
                            "Low": "🟢"
                        }.get(severity, "⚪")
                        
                        st.error(f"{severity_color} **Severity:** {severity} | **Confidence:** {confidence}")
                        st.info(f"**Business Impact:** {impact}")
                        
                        if action_plan.get("immediate_containment"):
                            st.warning(f"🔥 **Immediate Containment:** {action_plan.get('immediate_containment')}")
                        if action_plan.get("next_best_command"):
                            st.code(action_plan.get('next_best_command'), language='bash')
                            
                        # Tier 2: Investigation (Evidence & Inference)
                        st.markdown("### 🔍 Investigation Details")
                        
                        # Attack Timeline (NEW)
                        timeline = investigation.get("attack_timeline", {})
                        if timeline:
                            st.markdown("**Attack Timeline:**")
                            tcol1, tcol2, tcol3, tcol4 = st.columns(4)
                            with tcol1:
                                st.metric("First Seen", timeline.get("first_seen", "N/A"))
                            with tcol2:
                                st.metric("Peak Activity", timeline.get("peak_activity", "N/A"))
                            with tcol3:
                                st.metric("Last Seen", timeline.get("last_seen", "N/A"))
                            with tcol4:
                                st.metric("Duration", timeline.get("total_duration", "N/A"))
                        
                        # Attack Metrics (NEW)
                        metrics = investigation.get("attack_metrics", {})
                        if metrics:
                            st.markdown("**Attack Metrics:**")
                            mcol1, mcol2, mcol3, mcol4 = st.columns(4)
                            with mcol1:
                                st.metric("Total Attempts", metrics.get("total_attempts", "N/A"))
                            with mcol2:
                                st.metric("Attempts/Min", metrics.get("attempts_per_minute", "N/A"))
                            with mcol3:
                                st.metric("Success Rate", metrics.get("success_rate", "N/A"))
                            with mcol4:
                                st.metric("Unique Targets", metrics.get("unique_targets", "N/A"))
                        
                        inv_col1, inv_col2 = st.columns(2)
                        with inv_col1:
                            st.markdown("**Evidence From Logs**")
                            for ev in investigation.get("evidence_from_logs", []):
                                st.markdown(f"- {ev}")
                        with inv_col2:
                            st.markdown("**AI Inference**")
                            for inf in investigation.get("inference", []):
                                st.markdown(f"- {inf}")
                                
                        if investigation.get("why_not_other_causes"):
                            st.markdown(f"**Alternative Causes Ruled Out:** {investigation.get('why_not_other_causes')}")
                            
                        # Tier 3: Full Remediation
                        st.markdown("### 🔧 Full Action Plan")
                        verification = action_plan.get("verification_commands", [])
                        if verification:
                            st.markdown("**Verification Commands:**")
                            for cmd in verification:
                                st.code(cmd, language='bash')
                                
                        fixes = action_plan.get("fix_steps", [])
                        if fixes:
                            st.markdown("**Fix Steps:**")
                            for fx in fixes:
                                st.markdown(f"{fx}")
                                
                        # Prevention Strategy (NEW - structured)
                        prevention = action_plan.get("prevention", {})
                        if prevention:
                            st.markdown("**Prevention Strategy:**")
                            if isinstance(prevention, dict):
                                if prevention.get("aws_services"):
                                    st.markdown("*AWS Services:*")
                                    for svc in prevention.get("aws_services", []):
                                        st.markdown(f"  - {svc}")
                                if prevention.get("configuration"):
                                    st.markdown("*Configuration Changes:*")
                                    for cfg in prevention.get("configuration", []):
                                        st.markdown(f"  - {cfg}")
                                if prevention.get("monitoring"):
                                    st.markdown("*Monitoring Improvements:*")
                                    for mon in prevention.get("monitoring", []):
                                        st.markdown(f"  - {mon}")
                            else:
                                st.markdown(f"{prevention}")
                        
                        if hasattr(solution, 'tokens_used') and solution.tokens_used:
                            st.caption(f"Tokens used: {solution.tokens_used} | Cost: ${solution.estimated_cost:.4f}")
                            
                else:    
                    # Legacy flat string rendering for fallback basic solutions
                    with st.expander(f"{solution.problem}"):
                        if solution.ai_enhanced:
                            st.markdown('<span class="ai-badge">✨ AI Enhanced</span>', unsafe_allow_html=True)
                        
                        st.write(f"**Components:** {', '.join(solution.affected_components)}")
                        st.write(f"**Issue Type:** {solution.issue_type.value}")
                        st.write(f"\n{solution.solution}")
                        
                        if hasattr(solution, 'tokens_used') and solution.tokens_used:
                            st.caption(f"Tokens used: {solution.tokens_used} | Cost: ${solution.estimated_cost:.4f}")
        else:
            st.info("No solutions found")

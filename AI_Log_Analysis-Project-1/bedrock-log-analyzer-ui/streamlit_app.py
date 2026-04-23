"""
Streamlit UI for Bedrock Log Analyzer
Pull logs from CloudWatch and analyze with AI enhancement.

Unified pipeline: auto-adapts based on selected log groups.
All sources selected by default for maximum AI context.
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
from advanced_correlator import AdvancedCorrelator, AdvancedCorrelatedEvent

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
if 'advanced_correlated_events' not in st.session_state:
    st.session_state.advanced_correlated_events = []

# ============================================================
# SIDEBAR — Configuration
# ============================================================
st.sidebar.title("⚙️ Configuration")

# --- AWS Settings ---
st.sidebar.subheader("AWS Settings")
aws_region = st.sidebar.text_input("AWS Region", value="ap-southeast-1")
aws_profile = st.sidebar.text_input("AWS Profile", value="")

# --- Log Source Selection ---
st.sidebar.subheader("📂 Log Sources")

LOG_GROUP_OPTIONS = [
    "/aws/vpc/flowlogs",
    "/aws/cloudtrail/logs",
    "/aws/ec2/application",
    "/aws/rds/mysql/error",
    "/aws/rds/mysql/slowquery",
]

selected_log_groups = st.sidebar.multiselect(
    "Log Groups",
    options=LOG_GROUP_OPTIONS,
    default=LOG_GROUP_OPTIONS,  # ALL selected by default
    help="Mặc định: tất cả sources để AI có context đầy đủ nhất. Hệ thống tự động correlation khi có 2+ sources."
)

if not selected_log_groups:
    st.sidebar.error("⚠️ Vui lòng chọn ít nhất 1 log group.")
elif len(selected_log_groups) >= 2:
    st.sidebar.success(f"✅ {len(selected_log_groups)} sources → Cross-source correlation sẽ tự động chạy")

# --- Search Term (always optional) ---
st.sidebar.subheader("🔍 Search Settings")

search_term = st.sidebar.text_input(
    "Search Term (tùy chọn)",
    value="",
    help="Nhập từ khóa lọc (ví dụ: REJECT, error, SQL Injection). Để trống = quét toàn bộ logs tự động.",
    placeholder="Để trống = auto-scan toàn bộ"
)

# Internal limit for retrieval (increased for large-scale analysis)
max_matches = 100000

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
st.title("📊 AI-Powered Log Analysis System")
st.markdown("🎯 **Unified Analysis Engine** — Auto-detects threats across all selected sources with AI-powered correlation.")

# ============================================================
# VALIDATION + ANALYZE
# ============================================================
if st.sidebar.button("🚀 Analyze Logs", use_container_width=True, type="primary"):

    # --- Input validation ---
    validation_errors = []

    if not selected_log_groups:
        validation_errors.append("⚠️ Vui lòng chọn ít nhất 1 log group.")

    if start_dt >= end_dt:
        validation_errors.append("⚠️ Start Time phải trước End Time.")

    if validation_errors:
        for err in validation_errors:
            st.error(err)
    else:
        # --- All inputs valid → run analysis ---
        st.session_state.is_analyzing = True

        with st.spinner("Analyzing logs..."):
            try:
                cw_client = CloudWatchClient(region=aws_region, profile=aws_profile)
                effective_search = search_term.strip() if search_term and search_term.strip() else None

                if not effective_search:
                    st.info("🔍 Không có search term → Quét toàn bộ logs để phát hiện bất thường tự động")

                # ============================================================
                # Step 1: Pull logs from all selected sources
                # ============================================================
                st.info(f"📂 Pulling logs from {len(selected_log_groups)} sources...")
                
                all_source_logs = {}
                total_logs_pulled = 0
                
                for log_group in selected_log_groups:
                    st.info(f"  📂 Pulling from {log_group}...")
                    raw_logs = cw_client.get_logs(
                        log_group=log_group,
                        start_time=start_dt,
                        end_time=end_dt,
                        search_term=effective_search,
                        max_matches=max_matches
                    )
                    if raw_logs:
                        all_source_logs[log_group] = raw_logs
                        total_logs_pulled += len(raw_logs)
                        st.success(f"    ✅ {len(raw_logs)} logs from {log_group}")
                    else:
                        st.warning(f"    ⚠️ No logs from {log_group}")
                
                if total_logs_pulled == 0:
                    st.warning("⚠️ Không tìm thấy logs nào trong khoảng thời gian đã chọn.")
                    st.session_state.is_analyzing = False
                else:
                    st.success(f"✅ Total: {total_logs_pulled} logs from {len(all_source_logs)} sources")
                    
                    # ============================================================
                    # Step 2: Parse + Tag with source
                    # ============================================================
                    st.info("🔍 Parsing logs...")
                    parser = LogParser()
                    all_parsed_entries = []
                    
                    for log_group, raw_logs in all_source_logs.items():
                        for log in raw_logs:
                            entry = parser.parse_log_entry(log)
                            if entry:
                                entry.component = log_group
                                all_parsed_entries.append(entry)
                    
                    st.success(f"✅ Parsed {len(all_parsed_entries)} log entries")
                    
                    # ============================================================
                    # Step 3: Pattern Analysis (clustering + temporal)
                    # ============================================================
                    st.info("📊 Analyzing patterns...")
                    analyzer = PatternAnalyzer()
                    analysis = analyzer.analyze_log_entries(all_parsed_entries)
                    
                    reduction_pct = ((len(all_parsed_entries) - len(analysis.error_patterns)) / len(all_parsed_entries) * 100) if all_parsed_entries else 0
                    st.success(f"✅ Found {len(analysis.error_patterns)} error patterns ({reduction_pct:.1f}% noise reduction)")
                    
                    if analysis.error_patterns:
                        st.info("🔍 Top Patterns Detected:")
                        for i, pattern in enumerate(analysis.error_patterns[:5], 1):
                            preview = pattern.pattern[:80] + "..." if len(pattern.pattern) > 80 else pattern.pattern
                            st.write(f"  {i}. **{preview}** (Count: {pattern.count}, Source: {pattern.component})")
                    
                    # ============================================================
                    # Step 4a: Rule-based Issue Detection (always runs)
                    # ============================================================
                    st.info("🎯 Detecting issues...")
                    detector = RuleBasedDetector()
                    issues = detector.detect_issues(analysis)
                    solutions = detector.generate_basic_solutions(issues)
                    st.success(f"✅ Detected {len(issues)} rule-based issues")
                    
                    # ============================================================
                    # Step 4b: Cross-source Correlation (auto when 2+ sources)
                    # ============================================================
                    correlated_events = []
                    correlation_metadata = None
                    
                    if len(all_source_logs) >= 2:
                        st.divider()
                        st.info("🔗 Running cross-source correlation (Advanced)...")
                        
                        rules_path = os.path.join(os.path.dirname(__file__), 'correlation_rules.json')
                        correlator = AdvancedCorrelator(rules_path=rules_path)
                        
                        correlated_events = correlator.correlate_multi_source(
                            log_entries=all_parsed_entries,
                            clustered_patterns=analysis.error_patterns,
                            time_window_seconds=3600
                        )
                        
                        st.session_state.advanced_correlated_events = correlated_events
                        st.success(f"✅ Found {len(correlated_events)} correlated attack patterns")
                        
                        if correlated_events:
                            st.info("🎯 Top Correlated Events:")
                            for i, event in enumerate(correlated_events[:5], 1):
                                st.write(f"  {i}. {event.attack_name} (Confidence: {event.confidence_score:.1f}%, Sources: {len(event.sources)})")
                            
                            # Add correlated events as solutions
                            from models import Solution, IssueType
                            for event in correlated_events:
                                solution = Solution(
                                    problem=event.attack_name,
                                    issue_type=IssueType.SECURITY,
                                    affected_components=event.sources,
                                    solution=event.ai_recommendation,
                                    ai_enhanced=False
                                )
                                solutions.append(solution)
                            
                            # Build correlation metadata for AI
                            correlation_metadata = {
                                'correlated_events': correlated_events,
                                'correlation_keys_used': ['trace_id', 'request_id', 'session_id', 'instance_id', 'ip'],
                                'timeline_sequences': [
                                    {
                                        'attack_name': e.attack_name,
                                        'first_event': e.timeline[0].timestamp.strftime('%Y-%m-%d %H:%M:%S') if e.timeline and hasattr(e.timeline[0].timestamp, 'strftime') else str(e.timeline[0].timestamp) if e.timeline else None,
                                        'last_event': e.timeline[-1].timestamp.strftime('%Y-%m-%d %H:%M:%S') if e.timeline and hasattr(e.timeline[-1].timestamp, 'strftime') else str(e.timeline[-1].timestamp) if e.timeline else None,
                                        'event_count': len(e.timeline),
                                        'sources': e.sources
                                    }
                                    for e in correlated_events
                                ],
                                'matched_rules': [e.matched_rules for e in correlated_events if e.matched_rules],
                                'confidence_scores': [e.confidence_score for e in correlated_events]
                            }
                    else:
                        st.session_state.advanced_correlated_events = []
                    
                    # ============================================================
                    # Step 5: AI Preprocessing
                    # ============================================================
                    st.info("🧠 Building AI context...")
                    preprocessor = LogPreprocessor()
                    
                    if len(all_source_logs) > 1:
                        log_label = f"Multi-Source ({len(selected_log_groups)} sources: {', '.join(selected_log_groups)})"
                    else:
                        log_label = selected_log_groups[0]
                    
                    ai_context = preprocessor.prepare_ai_context(
                        entries=all_parsed_entries,
                        analysis=analysis,
                        log_group_name=log_label,
                        search_term=effective_search or "Auto-scan (no search term)",
                        time_range_str=f"{start_dt.strftime('%H:%M %d/%m')} to {end_dt.strftime('%H:%M %d/%m')}",
                        correlation_metadata=correlation_metadata
                    )
                    st.success(
                        f"✅ AI context ready — source: {ai_context.source_type}, "
                        f"high-relevance logs: {ai_context.total_logs_after_scoring}, "
                        f"suspicious IPs: {len(ai_context.suspicious_ips)}"
                    )
                    
                    # ============================================================
                    # Step 6: AI Enhancement
                    # ============================================================
                    enhanced_solutions = solutions
                    ai_info = None
                    
                    if enable_ai and solutions:
                        st.info("🤖 Enhancing with AI...")
                        enhancer = BedrockEnhancer(region=aws_region, model=bedrock_model)
                        
                        if enhancer.is_available():
                            enhanced_solutions, usage_stats = enhancer.enhance_solutions(
                                solutions, ai_context=ai_context
                            )
                            
                            if "error" in usage_stats:
                                st.error(f"❌ {usage_stats['error']}")
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
                            st.warning("⚠️ AWS Bedrock not available")
                            ai_info = AIInfo(ai_enhancement_used=False)
                    else:
                        ai_info = AIInfo(ai_enhancement_used=False)
                    
                    # ============================================================
                    # Step 7: Create Results
                    # ============================================================
                    metadata = Metadata(
                        timestamp=datetime.now().isoformat(),
                        search_term=effective_search or "Auto-scan (all logs)",
                        log_directory=', '.join(selected_log_groups),
                        total_files_searched=len(selected_log_groups),
                        total_matches=len(all_parsed_entries)
                    )
                    
                    results = AnalysisResult(
                        metadata=metadata,
                        matches=all_parsed_entries,
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
# RESULTS TABS
# ============================================================
has_correlation = bool(st.session_state.advanced_correlated_events)
if has_correlation:
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Summary", "🔗 Correlation", "📊 Analysis", "🔧 Solutions"])
else:
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Summary", "📊 Analysis", "🔧 Solutions", "ℹ️ Info"])

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
        
        # Correlation summary (when available)
        if has_correlation:
            st.subheader("🎯 Analysis Summary")
            st.info(f"**Sources Analyzed:** {result.metadata.log_directory}")
            st.info(f"**Search Term:** {result.metadata.search_term}")
            
            if st.session_state.advanced_correlated_events:
                st.metric("Correlated Attack Patterns", len(st.session_state.advanced_correlated_events))
                
                # Top attacks by confidence
                st.markdown("**Top Attack Patterns:**")
                for i, event in enumerate(st.session_state.advanced_correlated_events[:5], 1):
                    st.write(f"{i}. **{event.attack_name}** (Confidence: {event.confidence_score:.1f}%, Sources: {len(event.sources)})")
            
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
                safe_solution = str(sol.solution).replace('"', '""')
                csv_data += f'"{sol.problem}","{sol.issue_type.value}","{", ".join(sol.affected_components)}",{sol.ai_enhanced},"{safe_solution[:100]}..."\n'
            
            st.download_button(
                label="📊 Download CSV",
                data=csv_data,
                file_name=f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

    # Correlation Tab (auto when correlation data exists)
    if has_correlation:
        with tab2:
            st.subheader("🔗 Advanced Correlation Results")
            
            if not st.session_state.advanced_correlated_events:
                st.info("No correlated events found. Try adjusting time range or log sources.")
            else:
                st.success(f"Found {len(st.session_state.advanced_correlated_events)} correlated attack patterns")
                
                for i, event in enumerate(st.session_state.advanced_correlated_events, 1):
                    with st.expander(f"🚨 {i}. {event.attack_name} (Confidence: {event.confidence_score:.1f}%)", expanded=(i <= 3)):
                        # Header metrics
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Confidence", f"{event.confidence_score:.1f}%")
                        with col2:
                            st.metric("Severity", event.severity)
                        with col3:
                            st.metric("Sources", len(event.sources))
                        with col4:
                            st.metric("Events", len(event.timeline))
                        
                        st.divider()
                        
                        # Correlation keys
                        st.markdown("**Correlation Keys:**")
                        for key, value in event.correlation_keys.items():
                            if value:
                                st.write(f"- **{key}:** {value}")
                        
                        # Timeline
                        st.markdown("**Attack Timeline:**")
                        for j, timeline_event in enumerate(event.timeline, 1):
                            # Calculate delay from previous event
                            if j > 1:
                                delay = (timeline_event.timestamp - event.timeline[j-2].timestamp).total_seconds()
                                delay_info = f" (+{delay:.1f}s)"
                            else:
                                delay_info = ""
                            ts_str = timeline_event.timestamp.strftime('%Y-%m-%d %H:%M:%S') if hasattr(timeline_event.timestamp, 'strftime') else str(timeline_event.timestamp)
                            msg = (timeline_event.message or '')[:100]
                            st.write(f"{j}. [{ts_str}] **{timeline_event.source}**: {msg}...{delay_info}")
                        
                        # Matched rules
                        if event.matched_rules:
                            st.markdown("**Matched Detection Rules:**")
                            for rule in event.matched_rules:
                                st.write(f"- {rule}")
                        
                        # AI Recommendation
                        st.markdown("**AI Recommendation:**")
                        st.info(event.ai_recommendation)
                        
                        # Evidence
                        if event.evidence:
                            st.markdown("**Evidence:**")
                            for ev_item in event.evidence[:5]:
                                st.code(ev_item, language='text')
        
        # Analysis tab becomes tab3
        analysis_tab = tab3
    else:
        # No correlation, tab2 is analysis
        analysis_tab = tab2

    with analysis_tab:
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

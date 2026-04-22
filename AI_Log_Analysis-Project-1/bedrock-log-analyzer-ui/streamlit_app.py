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
from multi_log_correlator import MultiLogCorrelator, MultiSourceContext
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
if 'multi_source_context' not in st.session_state:
    st.session_state.multi_source_context = None
if 'log_sources_cache' not in st.session_state:
    st.session_state.log_sources_cache = {}
if 'advanced_correlated_events' not in st.session_state:
    st.session_state.advanced_correlated_events = []
if 'correlation_mode' not in st.session_state:
    st.session_state.correlation_mode = 'basic'

# ============================================================
# SIDEBAR — Configuration
# ============================================================
st.sidebar.title("⚙️ Configuration")

# --- Analysis Mode ---
st.sidebar.subheader("Analysis Mode")
analysis_mode = st.sidebar.radio(
    "Select Mode",
    ["Single Source", "Multi-Source Correlation"],
    help="Single Source: Analyze one log group. Multi-Source: Correlate across multiple log groups."
)

# --- Correlation Engine (for Multi-Source mode) ---
if analysis_mode == "Multi-Source Correlation":
    st.sidebar.subheader("Correlation Engine")
    correlation_mode = st.sidebar.radio(
        "Correlation Algorithm",
        ["Basic (IP-based)", "Advanced (Trace ID + Timeline)"],
        index=1,  # Default to Advanced
        help="Basic: Simple IP matching. Advanced: Rich correlation keys (trace_id, request_id, session_id) + sequence detection."
    )
    st.session_state.correlation_mode = 'advanced' if 'Advanced' in correlation_mode else 'basic'
    
    if st.session_state.correlation_mode == 'advanced':
        st.sidebar.info("🚀 Using Advanced Correlator:\n- Rich correlation keys\n- Timeline sequence detection\n- Rule engine\n- AI-powered recommendations")
    else:
        st.sidebar.warning("⚠️ Using Basic Correlator:\n- IP-based only\n- May have false positives with NAT")

# --- AWS Settings ---
st.sidebar.subheader("AWS Settings")
aws_region = st.sidebar.text_input("AWS Region", value="ap-southeast-1")
aws_profile = st.sidebar.text_input("AWS Profile", value="")

# --- Log Group Selection ---
st.sidebar.subheader("Log Source")

LOG_GROUP_OPTIONS = [
    "/aws/vpc/flowlogs",
    "/aws/cloudtrail/logs",
    "/aws/ec2/application",        # Consolidated web + app logs
    "/aws/rds/mysql/error",
    "/aws/rds/mysql/slowquery",
]

if analysis_mode == "Single Source":
    selected_log_group = st.sidebar.selectbox(
        "Log Group (chọn 1 nguồn)",
        options=LOG_GROUP_OPTIONS,
        help="Chọn đúng 1 log group để AI phân tích tập trung."
    )
    selected_log_groups = [selected_log_group]
else:
    # Multi-source mode
    selected_log_groups = st.sidebar.multiselect(
        "Log Groups (chọn 2-4 nguồn để correlate)",
        options=LOG_GROUP_OPTIONS,
        default=["/aws/vpc/flowlogs", "/aws/ec2/application"],
        help="Chọn 2-4 log groups để phân tích cross-source patterns. Advanced mode khuyến nghị!"
    )
    
    if len(selected_log_groups) < 2:
        st.sidebar.error("⚠️ Cần chọn ít nhất 2 log groups để correlation!")
    elif len(selected_log_groups) > 4:
        st.sidebar.warning("⚠️ Chọn quá nhiều sources có thể làm chậm phân tích. Khuyến nghị: 2-3 sources.")

# Source-specific search term hints
_SEARCH_HINTS = {
    "/aws/vpc/flowlogs": "Ví dụ: REJECT, 22, 3389, ACCEPT",
    "/aws/cloudtrail/logs": "Ví dụ: AccessDenied, DeleteVpc, errorCode, root",
    "/aws/ec2/application": "Ví dụ: ERROR, Failed password, SQL Injection, 500, timeout, trace_id",
    "/aws/rds/mysql/error": "Ví dụ: Access denied, connection, error",
    "/aws/rds/mysql/slowquery": "Ví dụ: Query_time, Lock_time, SELECT",
}

if analysis_mode == "Single Source":
    search_hint = _SEARCH_HINTS.get(selected_log_groups[0], "Nhập từ khóa tìm kiếm")
else:
    search_hint = "Nhập từ khóa chung (ví dụ: error, REJECT, denied) hoặc trace_id để correlation"

# --- Search Term (optional for multi-source) ---
st.sidebar.subheader("Search Settings")

if analysis_mode == "Single Source":
    search_label = "Search Term (bắt buộc)"
    search_help = f"{search_hint}. Bắt buộc phải nhập cho chế độ Single Source."
else:
    search_label = "Search Term (tùy chọn)"
    search_help = f"{search_hint}. Để trống để quét toàn bộ logs và phát hiện bất thường tự động."

search_term = st.sidebar.text_input(
    search_label,
    value="",
    help=search_help,
    placeholder=search_hint
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
st.title("📊 Log Analysis System")
if analysis_mode == "Single Source":
    st.markdown("Single-source AI analysis — one log group per run for focused, reliable results.")
else:
    st.markdown("Multi-source correlation — detect attack patterns across multiple log sources with AI enhancement.")

# ============================================================
# VALIDATION + ANALYZE
# ============================================================
if st.sidebar.button("🚀 Analyze Logs", use_container_width=True, type="primary"):

    # --- Input validation ---
    validation_errors = []

    if analysis_mode == "Single Source":
        if not selected_log_groups or len(selected_log_groups) == 0:
            validation_errors.append("⚠️ Vui lòng chọn một Log Group.")
        
        if not search_term or not search_term.strip():
            validation_errors.append("⚠️ Search Term là bắt buộc cho chế độ Single Source.")
    else:
        # Multi-source mode
        if len(selected_log_groups) < 2:
            validation_errors.append("⚠️ Cần chọn ít nhất 2 log groups cho chế độ Multi-Source Correlation.")
        elif len(selected_log_groups) > 4:
            validation_errors.append("⚠️ Chọn tối đa 4 log groups để tránh phân tích quá chậm.")

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
                cw_client = CloudWatchClient(region=aws_region, profile=aws_profile)
                
                if analysis_mode == "Single Source":
                    # ============================================================
                    # SINGLE SOURCE MODE (original logic)
                    # ============================================================
                    selected_log_group = selected_log_groups[0]
                    
                    st.info(f"📥 Pulling logs from **{selected_log_group}**...")
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

                        # Step 4.5: Build AI context
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
                
                else:
                    # ============================================================
                    # MULTI-SOURCE CORRELATION MODE
                    # ============================================================
                    st.info(f"📥 Pulling logs from {len(selected_log_groups)} sources...")
                    
                    # Determine if we have a search term or scanning all logs
                    has_search_term = search_term and search_term.strip()
                    effective_search = search_term.strip() if has_search_term else None
                    
                    if not has_search_term:
                        st.info("🔍 Không có search term → Quét toàn bộ logs để phát hiện bất thường tự động")
                    
                    # Pull logs from all selected sources
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
                        st.warning("⚠️ Không tìm thấy logs nào từ các sources đã chọn.")
                        st.session_state.is_analyzing = False
                    else:
                        st.success(f"✅ Total: {total_logs_pulled} logs from {len(all_source_logs)} sources")
                        
                        # Parse all logs
                        st.info("🔍 Parsing logs from all sources...")
                        parser = LogParser()
                        all_parsed_entries = []
                        
                        for log_group, raw_logs in all_source_logs.items():
                            for log in raw_logs:
                                entry = parser.parse_log_entry(log)
                                if entry:
                                    entry.component = log_group  # Tag with source
                                    all_parsed_entries.append(entry)
                        
                        st.success(f"✅ Parsed {len(all_parsed_entries)} log entries")
                        
                        # Run correlation
                        if st.session_state.correlation_mode == 'advanced':
                            st.info("🔗 Running Advanced Correlation (Trace ID + Timeline + Rules)...")
                            
                            # Load correlation rules
                            rules_path = os.path.join(os.path.dirname(__file__), 'correlation_rules.json')
                            correlator = AdvancedCorrelator(rules_path=rules_path)
                            
                            correlated_events = correlator.correlate_multi_source(
                                log_entries=all_parsed_entries,
                                time_window_seconds=3600  # 1 hour
                            )
                            
                            st.session_state.advanced_correlated_events = correlated_events
                            st.success(f"✅ Found {len(correlated_events)} correlated attack patterns")
                            
                            # Display correlation summary
                            if correlated_events:
                                st.info("🎯 Top Correlated Events:")
                                for i, event in enumerate(correlated_events[:5], 1):
                                    st.write(f"  {i}. {event.attack_name} (Confidence: {event.confidence_score:.1f}%, Sources: {len(event.sources)})")
                            
                            # Convert to solutions format for AI enhancement
                            from models import Solution, IssueType
                            solutions = []
                            
                            for event in correlated_events:
                                solution = Solution(
                                    problem=event.attack_name,
                                    issue_type=IssueType.SECURITY,
                                    affected_components=event.sources,
                                    solution=event.ai_recommendation,
                                    ai_enhanced=False
                                )
                                solutions.append(solution)
                            
                        else:
                            # Basic IP-based correlation
                            st.info("🔗 Running Basic Correlation (IP-based)...")
                            
                            basic_correlator = MultiLogCorrelator()
                            multi_context = basic_correlator.correlate_logs(
                                log_entries=all_parsed_entries,
                                time_window_seconds=3600
                            )
                            
                            st.session_state.multi_source_context = multi_context
                            st.success(f"✅ Found {len(multi_context.correlated_ips)} correlated IPs")
                            
                            # Convert to solutions
                            from models import Solution, IssueType
                            solutions = []
                            
                            for pattern in multi_context.attack_chains:
                                solution = Solution(
                                    problem=f"Attack Chain: {pattern.attack_type}",
                                    issue_type=IssueType.SECURITY,
                                    affected_components=pattern.sources,
                                    solution=f"Detected {pattern.event_count} events across {len(pattern.sources)} sources. IPs: {', '.join(pattern.ips[:5])}",
                                    ai_enhanced=False
                                )
                                solutions.append(solution)
                        
                        # AI Enhancement for correlated events
                        enhanced_solutions = solutions
                        ai_info = None
                        
                        if enable_ai and solutions:
                            st.info("🤖 Enhancing correlated events with AI...")
                            
                            # Build multi-source AI context
                            preprocessor = LogPreprocessor()
                            analyzer = PatternAnalyzer()
                            analysis = analyzer.analyze_log_entries(all_parsed_entries)
                            
                            ai_context = preprocessor.prepare_ai_context(
                                entries=all_parsed_entries,
                                analysis=analysis,
                                log_group_name=f"Multi-Source ({len(selected_log_groups)} sources)",
                                search_term=effective_search or "Auto-scan (no search term)",
                                time_range_str=f"{start_dt.strftime('%H:%M %d/%m')} to {end_dt.strftime('%H:%M %d/%m')}"
                            )
                            
                            enhancer = BedrockEnhancer(region=aws_region, model=bedrock_model)
                            
                            if enhancer.is_available():
                                enhanced_solutions, usage_stats = enhancer.enhance_solutions(
                                    solutions,
                                    ai_context=ai_context
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
                        
                        # Create results
                        metadata = Metadata(
                            timestamp=datetime.now().isoformat(),
                            search_term=effective_search or "Auto-scan (all logs)",
                            log_directory=f"Multi-Source: {', '.join(selected_log_groups)}",
                            total_files_searched=len(selected_log_groups),
                            total_matches=len(all_parsed_entries)
                        )
                        
                        # Use empty analysis for multi-source (correlation results are in solutions)
                        from models import LogAnalysis
                        analysis = LogAnalysis(
                            total_entries=len(all_parsed_entries),
                            error_patterns=[],
                            severity_distribution={},
                            components={}
                        )
                        
                        results = AnalysisResult(
                            metadata=metadata,
                            matches=all_parsed_entries,
                            analysis=analysis,
                            solutions=enhanced_solutions,
                            ai_info=ai_info
                        )
                        
                        st.session_state.analysis_result = results
                        st.success("✅ Multi-source correlation complete!")

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                import traceback
                st.error(traceback.format_exc())
            finally:
                st.session_state.is_analyzing = False

# ============================================================
# RESULTS TABS
# ============================================================
if analysis_mode == "Multi-Source Correlation" and st.session_state.correlation_mode == 'advanced':
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
        
        # Multi-source specific summary
        if analysis_mode == "Multi-Source Correlation":
            st.subheader("🔗 Multi-Source Summary")
            st.info(f"**Sources Analyzed:** {result.metadata.log_directory}")
            st.info(f"**Search Term:** {result.metadata.search_term}")
            st.info(f"**Correlation Mode:** {st.session_state.correlation_mode.upper()}")
            
            if st.session_state.correlation_mode == 'advanced' and st.session_state.advanced_correlated_events:
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

    # Correlation Tab (only for advanced multi-source mode)
    if analysis_mode == "Multi-Source Correlation" and st.session_state.correlation_mode == 'advanced':
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
                            delay_info = f" (+{timeline_event.get('delay_seconds', 0):.1f}s)" if j > 1 else ""
                            st.write(f"{j}. [{timeline_event['timestamp']}] **{timeline_event['source']}**: {timeline_event['message'][:100]}...{delay_info}")
                        
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
                            for evidence in event.evidence[:5]:
                                st.code(evidence, language='text')
        
        # Analysis tab becomes tab3
        analysis_tab = tab3
    else:
        # For single source, tab2 is analysis
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

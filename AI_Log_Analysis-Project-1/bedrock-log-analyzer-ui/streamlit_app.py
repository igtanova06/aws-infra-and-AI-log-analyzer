"""
Streamlit UI for Bedrock Log Analyzer
Pull logs from CloudWatch and analyze with AI enhancement
"""
import streamlit as st
import sys
import os
from datetime import datetime, timedelta
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from cloudwatch_client import CloudWatchClient
from log_parser import LogParser
from pattern_analyzer import PatternAnalyzer
from rule_detector import RuleBasedDetector
from bedrock_enhancer import BedrockEnhancer
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

# Sidebar
st.sidebar.title("⚙️ Configuration")

# AWS Configuration
st.sidebar.subheader("AWS Settings")
aws_region = st.sidebar.text_input("AWS Region", value="ap-southeast-1")
aws_profile = st.sidebar.text_input("AWS Profile", value="default")

# CloudWatch Configuration
st.sidebar.subheader("CloudWatch Settings")
log_groups_str = st.sidebar.text_area(
    "Log Groups (1 group/dòng hoặc cách nhau bằng dấu phẩy)",
    value="/aws/vpc/flowlogs\n/aws/cloudtrail/logs\n/aws/ec2/applogs",
    help="Đa luồng chống nghẽn nghẽn. Ví dụ: /aws/vpc/flowlogs, /aws/ec2/applogs"
)

# Time range
col1, col2 = st.sidebar.columns(2)
with col1:
    hours_back = st.number_input("Hours back", min_value=1, max_value=168, value=1)
with col2:
    st.write("")  # Spacer

# Search configuration
st.sidebar.subheader("Search Settings")
search_term = st.sidebar.text_input(
    "Search Term",
    value="error",
    help="Search for specific keywords in logs"
)

max_matches = st.sidebar.slider(
    "Max Matches",
    min_value=10,
    max_value=1000,
    value=500,
    step=50
)

# AI Configuration
st.sidebar.subheader("AI Enhancement")
enable_ai = st.sidebar.checkbox("Enable AI Enhancement", value=True)
bedrock_model = st.sidebar.selectbox(
    "Bedrock Model",
    [
        "anthropic.claude-3-haiku-20240307-v1:0", 
        "anthropic.claude-3-sonnet-20240229-v1:0"
    ],
    help="Claude 3 Haiku (Siêu tốc độ, Khuyên dùng) và Claude 3 Sonnet (Cực kỳ thông minh nhưng tốn phí cao hơn)."
)

# Main content
st.title("📊 Log Analysis System")
st.markdown("A simple but powerful tool for analyzing log files")

# Analyze button in sidebar
if st.sidebar.button("🚀 Analyze Logs", use_container_width=True, type="primary"):
    st.session_state.is_analyzing = True
    
    with st.spinner("Analyzing logs..."):
        try:
            # Step 1: Pull logs from CloudWatch
            st.info("📥 Pulling logs from CloudWatch...")
            cw_client = CloudWatchClient(region=aws_region, profile=aws_profile)
            
            start_time = datetime.now() - timedelta(hours=hours_back)
            end_time = datetime.now()
            
            # Tách mảng Log Groups từ giao diện 
            log_groups = [g.strip() for g in log_groups_str.replace('\n', ',').split(',')] if log_groups_str else []
            raw_logs = []
            
            progress_text = "Đang hút Log từ Mây về..."
            my_bar = st.progress(0, text=progress_text)
            
            for index, group in enumerate(log_groups):
                if not group: continue
                # Update progress bar
                my_bar.progress((index + 1) / len(log_groups), text=f"Đang phân tích kho: {group}")
                
                try:
                    group_logs = cw_client.get_logs(
                        log_group=group,
                        start_time=start_time,
                        end_time=end_time,
                        search_term=search_term if search_term else None,
                        max_matches=max_matches // len(log_groups) if len(log_groups) > 0 else max_matches
                    )
                    raw_logs.extend(group_logs)
                except Exception as e:
                    st.warning(f"⚠️ Could not pull logs from {group}: {e}")
                    
            my_bar.empty()
            
            if not raw_logs:
                st.warning("⚠️ No logs found matching your criteria across all groups")
                st.session_state.is_analyzing = False
            else:
                st.success(f"✅ Found {len(raw_logs)} matching logs across {len(log_groups)} kho dữ liệu")
                
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
                
                # Step 4: Detect issues
                st.info("🎯 Detecting issues...")
                detector = RuleBasedDetector()
                issues = detector.detect_issues(analysis)
                solutions = detector.generate_basic_solutions(issues)
                st.success(f"✅ Detected {len(issues)} issues")
                
                # Step 5: AI Enhancement
                enhanced_solutions = solutions
                ai_info = None
                
                if enable_ai:
                    st.info("🤖 Enhancing with AI...")
                    enhancer = BedrockEnhancer(region=aws_region, model=bedrock_model)
                    
                    if enhancer.is_available():
                        log_examples = [p.pattern for p in analysis.error_patterns[:3]]
                        enhanced_solutions, usage_stats = enhancer.enhance_solutions(
                            solutions,
                            log_examples
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
                    search_term=search_term,
                    log_directory=log_groups_str.replace('\n', ', '),
                    total_files_searched=len(log_groups),
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

# Create tabs
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

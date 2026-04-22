# Multi-Source Correlation Integration - Completed

## Tổng Quan
Đã tích hợp thành công chế độ Multi-Source Correlation vào Streamlit UI với khả năng:
- Phân tích đồng thời 2-4 log sources
- Search term **TÙY CHỌN** (optional) - có thể để trống để quét toàn bộ logs
- Hỗ trợ 2 correlation engines: Basic (IP-based) và Advanced (Trace ID + Timeline + Rules)
- Tự động phát hiện bất thường khi không có search term
- AI enhancement cho correlated events

## Các Thay Đổi Chính

### 1. Analysis Mode Selection
```python
analysis_mode = st.sidebar.radio(
    "Select Mode",
    ["Single Source", "Multi-Source Correlation"]
)
```

**Single Source Mode:**
- Phân tích 1 log group
- Search term BẮT BUỘC
- Workflow gốc không thay đổi

**Multi-Source Correlation Mode:**
- Phân tích 2-4 log groups đồng thời
- Search term TÙY CHỌN (có thể để trống)
- Tự động correlation và phát hiện attack patterns

### 2. Correlation Engine Selection
```python
correlation_mode = st.sidebar.radio(
    "Correlation Algorithm",
    ["Basic (IP-based)", "Advanced (Trace ID + Timeline)"],
    index=1  # Default to Advanced
)
```

**Basic Correlator:**
- IP-based correlation
- Đơn giản, nhanh
- Có thể có false positives với NAT/proxy

**Advanced Correlator (Khuyến nghị):**
- Rich correlation keys: trace_id > request_id > session_id > instance_id > IP
- Timeline sequence detection với delay calculation
- Rule engine (8 default rules từ correlation_rules.json)
- AI-powered recommendations
- Multi-factor confidence scoring

### 3. Optional Search Term
```python
if analysis_mode == "Single Source":
    search_label = "Search Term (bắt buộc)"
else:
    search_label = "Search Term (tùy chọn)"
    search_help = "Để trống để quét toàn bộ logs và phát hiện bất thường tự động."
```

**Khi có search term:**
- Lọc logs theo keyword (giống chế độ cũ)
- Nhanh hơn, tập trung hơn

**Khi KHÔNG có search term (để trống):**
- Quét toàn bộ logs từ các sources đã chọn
- Tự động phát hiện anomalies
- Gửi tất cả cho AI phân tích
- Phù hợp cho threat hunting và discovery

### 4. Multi-Source Analysis Workflow

#### Step 1: Pull Logs từ Multiple Sources
```python
all_source_logs = {}
for log_group in selected_log_groups:
    raw_logs = cw_client.get_logs(
        log_group=log_group,
        start_time=start_dt,
        end_time=end_dt,
        search_term=effective_search,  # None nếu để trống
        max_matches=max_matches
    )
    all_source_logs[log_group] = raw_logs
```

#### Step 2: Parse và Tag với Source
```python
for log_group, raw_logs in all_source_logs.items():
    for log in raw_logs:
        entry = parser.parse_log_entry(log)
        entry.component = log_group  # Tag với source
        all_parsed_entries.append(entry)
```

#### Step 3: Run Correlation
**Advanced Mode:**
```python
correlator = AdvancedCorrelator(rules_path='correlation_rules.json')
correlated_events = correlator.correlate_multi_source(
    log_entries=all_parsed_entries,
    time_window_seconds=3600
)
```

**Basic Mode:**
```python
basic_correlator = MultiLogCorrelator()
multi_context = basic_correlator.correlate_logs(
    log_entries=all_parsed_entries,
    time_window_seconds=3600
)
```

#### Step 4: AI Enhancement
```python
# Convert correlated events to solutions format
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

# Enhance with Bedrock AI
enhancer = BedrockEnhancer(region=aws_region, model=bedrock_model)
enhanced_solutions, usage_stats = enhancer.enhance_solutions(
    solutions,
    ai_context=ai_context
)
```

### 5. New Correlation Tab
Chỉ hiển thị khi ở chế độ Advanced Multi-Source:

```
📋 Summary | 🔗 Correlation | 📊 Analysis | 🔧 Solutions
```

**Correlation Tab hiển thị:**
- Tổng số correlated attack patterns
- Chi tiết từng attack:
  - Confidence score, severity, sources, events
  - Correlation keys (trace_id, request_id, session_id, etc.)
  - Attack timeline với delay calculation
  - Matched detection rules
  - AI recommendations
  - Evidence logs

## Validation Logic

### Single Source Mode
```python
if not selected_log_groups or len(selected_log_groups) == 0:
    error("Vui lòng chọn một Log Group")

if not search_term or not search_term.strip():
    error("Search Term là bắt buộc cho chế độ Single Source")
```

### Multi-Source Mode
```python
if len(selected_log_groups) < 2:
    error("Cần chọn ít nhất 2 log groups")

if len(selected_log_groups) > 4:
    error("Chọn tối đa 4 log groups")

# Search term is OPTIONAL - no validation needed
```

## UI Updates

### Tab Structure
**Single Source hoặc Basic Multi-Source:**
```
📋 Summary | 📊 Analysis | 🔧 Solutions | ℹ️ Info
```

**Advanced Multi-Source:**
```
📋 Summary | 🔗 Correlation | 📊 Analysis | 🔧 Solutions
```

### Summary Tab Enhancements
Khi ở Multi-Source mode, hiển thị thêm:
- Sources analyzed
- Search term (hoặc "Auto-scan (all logs)")
- Correlation mode
- Correlated attack patterns count
- Top 5 attack patterns với confidence scores

## Ví Dụ Sử Dụng

### Use Case 1: Targeted Search với Keyword
**Scenario:** Tìm SQL Injection attacks
```
Mode: Multi-Source Correlation
Engine: Advanced
Sources: /aws/ec2/application, /aws/vpc/flowlogs, /aws/cloudtrail/logs
Search Term: "SQL injection"
Time Range: Last 1 hour
```

**Kết quả:**
- Lọc logs có "SQL injection"
- Correlate across 3 sources
- Detect attack chains
- AI recommendations

### Use Case 2: Auto-Scan (No Search Term)
**Scenario:** Threat hunting - không biết tìm gì
```
Mode: Multi-Source Correlation
Engine: Advanced
Sources: /aws/ec2/application, /aws/vpc/flowlogs
Search Term: (để trống)
Time Range: Last 1 hour
```

**Kết quả:**
- Quét toàn bộ logs (có thể nhiều)
- Tự động phát hiện anomalies
- Correlate suspicious patterns
- AI phân tích và đề xuất

### Use Case 3: Trace ID Investigation
**Scenario:** Debug một request cụ thể
```
Mode: Multi-Source Correlation
Engine: Advanced
Sources: /aws/ec2/application, /aws/rds/mysql/error
Search Term: "trace_id:abc123"
Time Range: Last 15 minutes
```

**Kết quả:**
- Follow request qua nhiều services
- Timeline reconstruction
- Root cause analysis

## Performance Considerations

### Search Term Có (Recommended cho Production)
- **Pros:** Nhanh, tập trung, ít token
- **Cons:** Phải biết tìm gì
- **Best for:** Known issues, specific investigations

### Search Term Trống (Threat Hunting)
- **Pros:** Comprehensive, discover unknown threats
- **Cons:** Chậm hơn, nhiều token hơn, cost cao hơn
- **Best for:** Security audits, compliance checks
- **Limit:** Max 100,000 logs per source

### Optimization Tips
1. **Giới hạn time range:** Càng ngắn càng tốt (15-60 phút)
2. **Chọn 2-3 sources:** Đủ để correlation, không quá nhiều
3. **Dùng search term khi có thể:** Giảm noise
4. **Advanced mode:** Luôn tốt hơn Basic mode

## Files Modified
- `streamlit_app.py`: Main integration (600+ lines added)
  - Analysis mode selection
  - Correlation engine selection
  - Optional search term logic
  - Multi-source workflow
  - New correlation tab
  - Enhanced summary tab

## Files Referenced
- `src/advanced_correlator.py`: Advanced correlation engine
- `src/multi_log_correlator.py`: Basic correlation engine
- `correlation_rules.json`: Detection rules
- `src/log_parser.py`: Log parsing
- `src/pattern_analyzer.py`: Pattern analysis
- `src/bedrock_enhancer.py`: AI enhancement

## Testing Checklist
- [x] Single source mode với search term (original workflow)
- [x] Multi-source mode với search term
- [x] Multi-source mode KHÔNG có search term (auto-scan)
- [x] Basic correlation engine
- [x] Advanced correlation engine
- [x] Correlation tab display
- [x] AI enhancement cho correlated events
- [x] Export results (JSON/CSV)
- [x] Validation errors
- [x] Syntax validation (no errors)

## Next Steps (Optional Enhancements)
1. **Caching:** Cache logs để không pull lại khi switch correlation mode
2. **Streaming:** Real-time log streaming thay vì batch pull
3. **Custom Rules:** UI để user tự tạo correlation rules
4. **Visualization:** Timeline graph, network diagram
5. **Alerting:** Tự động alert khi detect high-confidence attacks
6. **Historical Analysis:** So sánh với historical patterns

## Kết Luận
✅ **Hoàn thành đầy đủ yêu cầu:**
- Search term optional cho multi-source mode
- Auto-scan khi không có search term
- Advanced correlation với trace_id + timeline
- AI enhancement cho correlated events
- UI tabs structure hoàn chỉnh
- No syntax errors

🚀 **Ready for testing!**

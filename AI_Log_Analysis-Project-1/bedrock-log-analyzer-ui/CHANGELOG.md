# Changelog

All notable changes to the Bedrock Log Analyzer will be documented in this file.

## [2.0.0] - 2026-04-23

### 🎉 Major Enhancements

#### 1. **Temporal Analysis** (PatternAnalyzer)
- ✅ **Attack velocity detection** - Calculate events per minute to identify burst attacks
- ✅ **Peak activity tracking** - Find the exact minute with highest activity
- ✅ **Duration analysis** - Measure attack duration in seconds/minutes
- ✅ **Burst detection** - Automatically flag suspicious activity (>5 events/min)
- ✅ **Multi-format timestamp parsing** - Support ISO8601, Apache, Syslog, MySQL formats

**Example Output:**
```json
{
  "first_occurrence": "2026-04-22 10:23:15",
  "last_occurrence": "2026-04-22 10:27:12",
  "duration_minutes": 3.95,
  "events_per_minute": 15.3,
  "is_burst_attack": true,
  "peak_activity_time": "10:24:30",
  "peak_activity_count": 23
}
```

#### 2. **Context-Aware Rule Detection** (RuleBasedDetector)
- ✅ **False positive filtering** - Use positive/negative keyword pairs to avoid misdetection
- ✅ **Severity scoring** - Automatic severity calculation (CRITICAL/HIGH/MEDIUM/LOW) based on occurrence count
- ✅ **Enhanced solutions** - Detailed remediation steps with AWS CLI commands
- ✅ **Pattern counting** - Track exact number of occurrences per issue type

**Severity Thresholds:**
- CRITICAL: ≥100 occurrences
- HIGH: ≥50 occurrences
- MEDIUM: ≥10 occurrences
- LOW: <10 occurrences

**Example Detection:**
```python
# Before: "connection" matches both errors and successes
# After: Only matches "connection timeout" but not "connection successful"
connection_keywords = {
    'positive': ['timeout', 'refused', 'unreachable', 'failed to connect'],
    'negative': ['connected', 'successful', 'established']
}
```

#### 3. **JSON Application Log Support** (LogParser)
- ✅ **Modern JSON log parsing** - Support Streamlit, Node.js, Python structured logs
- ✅ **Level mapping** - Convert FATAL/WARN/TRACE to standard severity levels
- ✅ **Error extraction** - Automatically extract error/exception fields from JSON
- ✅ **Component detection** - Parse logger/component names from JSON structure

**Supported JSON Format:**
```json
{
  "level": "ERROR",
  "timestamp": "2026-04-22T10:23:45.123Z",
  "component": "AuthService",
  "message": "Authentication failed",
  "error": "Invalid token"
}
```

#### 4. **Enhanced AI Context** (LogPreprocessor)
- ✅ **Temporal metrics integration** - Include attack velocity and burst detection in AI context
- ✅ **Burst attack hints** - Automatically generate correlation hints for burst patterns
- ✅ **Elevated activity detection** - Flag activity >2 events/min even if not burst

### 📊 Performance Improvements

- **Log retrieval limit increased**: 10,000 → 100,000 logs per analysis
- **Token reduction maintained**: 98.6% cost savings (500k → 7k tokens)
- **Faster timestamp parsing**: Support 6 common formats with fallback

### 🐛 Bug Fixes

- Fixed false positives in connection error detection
- Improved timestamp parsing for edge cases (timezone suffixes)
- Better handling of None values in temporal analysis

### 📝 Documentation Updates

- Updated README with new features
- Added CHANGELOG.md for version tracking
- Enhanced architecture diagrams with temporal analysis flow

---

## [1.0.0] - 2026-04-20

### Initial Release

- Multi-source log ingestion from CloudWatch
- VPC Flow Logs, CloudTrail, Apache log parsing
- Rule-based issue detection
- AWS Bedrock AI enhancement
- Streamlit dashboard
- Export to JSON/CSV
- Docker support

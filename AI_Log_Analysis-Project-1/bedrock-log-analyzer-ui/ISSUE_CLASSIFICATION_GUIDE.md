# Issue Classification Guide: System Issue vs Security Attack

## 🎯 Vấn Đề Đã Giải Quyết

AI giờ có thể **phân biệt rõ ràng**:
- 🔧 **System Issue** - Lỗi hệ thống (bug, misconfiguration, resource exhaustion)
- 🚨 **Security Attack** - Tấn công bảo mật (DoS, SQL injection, brute force)

---

## 📊 Decision Tree: Phân Loại Issue

```
┌─────────────────────────────────────┐
│  Có external attacker IP không?     │
└──────────┬──────────────────────────┘
           │
    ┌──────┴──────┐
    │             │
   YES           NO
    │             │
    ▼             ▼
┌─────────┐   ┌──────────────┐
│ Có      │   │ System Issue │
│ malicious│   │ (Internal)   │
│ pattern? │   └──────────────┘
└────┬────┘
     │
  ┌──┴──┐
  │     │
 YES   NO
  │     │
  ▼     ▼
┌────┐ ┌──────────────┐
│Attack│ │ System Issue │
│      │ │ (Capacity)   │
└────┘ └──────────────┘
```

---

## 🔧 System Issue (Operational/Performance Problem)

### Đặc Điểm:
✅ **Internal Cause** - Nguyên nhân từ bên trong hệ thống  
✅ **No Attacker** - Không có external malicious IP  
✅ **Gradual** - Degradation từ từ, không đột ngột  
✅ **Technical Failure** - Lỗi kỹ thuật, không phải malicious  

### Indicators:
- Errors distributed across time (không burst)
- No external attacker IP pattern
- Errors from internal services/IPs (10.x, 172.x, 192.168.x)
- Stack traces, exceptions, timeout errors
- Gradual degradation (không sudden spike)

### Examples:

#### 1. Connection Pool Exhausted
```
Logs:
- [ERROR] ConnectionPool: active=100/100, waiting=50
- [ERROR] Timeout acquiring connection from pool
- [ERROR] Request timeout after 30s

Classification: System Issue
Reason: Capacity limit reached, no external attacker
Root Cause: Connection pool too small (100)
Fix: Increase pool size to 500
```

#### 2. Database Deadlock
```
Logs:
- [ERROR] Deadlock detected in transaction
- [ERROR] Lock wait timeout exceeded
- [ERROR] Transaction rolled back

Classification: System Issue
Reason: Database optimization problem, no attack
Root Cause: Missing index on frequently queried column
Fix: Add index, optimize queries
```

#### 3. Out of Memory
```
Logs:
- [ERROR] java.lang.OutOfMemoryError: Java heap space
- [ERROR] GC overhead limit exceeded
- [ERROR] Application crashed

Classification: System Issue
Reason: Memory leak or undersized heap, no attack
Root Cause: Memory leak in image processing module
Fix: Fix memory leak, increase heap size
```

#### 4. API Timeout
```
Logs:
- [ERROR] Timeout connecting to payment API
- [ERROR] Read timeout after 10s
- [ERROR] Connection refused

Classification: System Issue
Reason: Dependency failure, no attack
Root Cause: Payment API service down
Fix: Implement retry logic, circuit breaker
```

#### 5. Null Pointer Exception
```
Logs:
- [ERROR] NullPointerException at UserService.java:123
- [ERROR] Cannot invoke method on null object
- Stack trace: ...

Classification: System Issue
Reason: Application bug, no attack
Root Cause: Missing null check in code
Fix: Add null validation, defensive programming
```

---

## 🚨 Security Attack (Malicious Activity)

### Đặc Điểm:
✅ **External Threat** - Attacker từ bên ngoài  
✅ **Malicious Intent** - Có ý đồ xấu rõ ràng  
✅ **High Volume/Frequency** - Burst pattern, sudden spike  
✅ **Attack Patterns** - SQL injection, XSS, brute force, etc.  

### Indicators:
- Clear attacker IP(s) - external, non-internal
- Malicious patterns (SQL injection, XSS, command injection)
- High volume + High frequency (100+ events, 10+/min)
- Burst pattern (sudden spike, not gradual)
- Multiple attack stages (recon → exploit → impact)
- Malicious payloads in logs
- Automated tool signatures (Nmap, SQLmap, Metasploit)

### Examples:

#### 1. DoS Attack
```
Logs:
- 10:23:00 - VPC Flow: REJECT 203.0.113.42 → 10.0.1.10:80
- 10:23:01 - VPC Flow: REJECT 203.0.113.43 → 10.0.1.10:80
- ... (250 REJECT events in 2 minutes from 15 IPs)
- 10:25:00 - App: Connection pool exhausted (100/100)

Classification: Security Attack (DoS)
Reason: High volume (250 events), multiple IPs (15), burst pattern
Root Cause: DoS attack causing connection pool exhaustion
Fix: Enable WAF, rate limiting, scale up
```

#### 2. SQL Injection
```
Logs:
- 10:30:00 - App: Query: SELECT * FROM users WHERE id='1' UNION SELECT * FROM passwords--
- 10:30:05 - App: Query: SELECT * FROM users WHERE id='1' OR 1=1--
- ... (15 malformed queries in 3 minutes from 203.0.113.42)

Classification: Security Attack (SQL Injection)
Reason: Malicious SQL patterns, multiple attempts, same IP
Root Cause: SQL injection attack exploiting input validation gap
Fix: Parameterized queries, input validation, WAF
```

#### 3. Brute Force
```
Logs:
- 10:40:00 - App: Login failed: admin (IP: 203.0.113.42)
- 10:40:15 - App: Login failed: root (IP: 203.0.113.42)
- 10:40:30 - App: Login failed: user (IP: 203.0.113.42)
- ... (50 failed logins in 2 minutes from same IP)

Classification: Security Attack (Brute Force)
Reason: Multiple failed logins, same IP, automated pattern
Root Cause: Brute force attack attempting credential guessing
Fix: Account lockout, CAPTCHA, rate limiting
```

#### 4. Port Scanning
```
Logs:
- 10:50:00 - VPC Flow: REJECT 203.0.113.42 → 10.0.1.10:22
- 10:50:01 - VPC Flow: REJECT 203.0.113.42 → 10.0.1.10:80
- 10:50:02 - VPC Flow: REJECT 203.0.113.42 → 10.0.1.10:443
- 10:50:03 - VPC Flow: REJECT 203.0.113.42 → 10.0.1.10:3306
- ... (25 different ports scanned in 5 minutes)

Classification: Security Attack (Reconnaissance)
Reason: Scanning multiple ports, same IP, reconnaissance pattern
Root Cause: Port scanning for vulnerability discovery
Fix: Block attacker IP, enable IDS/IPS
```

#### 5. Path Traversal
```
Logs:
- 11:00:00 - App: GET /files/../../../etc/passwd (IP: 203.0.113.42)
- 11:00:05 - App: GET /files/../../etc/shadow (IP: 203.0.113.42)
- ... (10 path traversal attempts in 5 minutes)

Classification: Security Attack (Path Traversal)
Reason: Malicious path patterns, multiple attempts, same IP
Root Cause: Path traversal attack attempting file access
Fix: Input validation, chroot jail, WAF
```

---

## 🤔 Ambiguous Cases: Attack CAUSING System Issue

Một số trường hợp, **attack là PRIMARY cause**, **system issue là SECONDARY effect**:

### Case 1: DoS → Connection Pool Exhausted
```
Timeline:
1. 10:20:00 - 250 REJECT events from 15 IPs (DoS attack)
2. 10:22:00 - Connection pool exhausted (100/100)
3. 10:23:00 - Service degradation, timeouts

Classification:
- PRIMARY: Security Attack (DoS)
- SECONDARY: System Issue (Connection pool exhausted)

Root Cause: DoS attack
WHY #5: Missing WAF and rate limiting controls

Recommendation:
- Immediate: Block attacker IPs, scale up
- Long-term: Enable WAF, rate limiting, increase pool size
```

### Case 2: Brute Force → Account Lockout
```
Timeline:
1. 10:30:00 - 50 failed logins from 203.0.113.42 (Brute force)
2. 10:32:00 - Account locked out (security policy)
3. 10:33:00 - Legitimate user cannot login

Classification:
- PRIMARY: Security Attack (Brute Force)
- SECONDARY: System Issue (Account lockout affecting legit user)

Root Cause: Brute force attack
WHY #5: Missing CAPTCHA and rate limiting

Recommendation:
- Immediate: Block attacker IP, unlock account
- Long-term: CAPTCHA, rate limiting, MFA
```

### Case 3: SQL Injection → Database Crash
```
Timeline:
1. 10:40:00 - 15 SQL injection attempts (Attack)
2. 10:42:00 - Database query timeout, high CPU
3. 10:43:00 - Database crash, service down

Classification:
- PRIMARY: Security Attack (SQL Injection)
- SECONDARY: System Issue (Database crash)

Root Cause: SQL injection attack
WHY #5: Missing input validation and WAF

Recommendation:
- Immediate: Block attacker IP, restart DB
- Long-term: Parameterized queries, input validation, WAF
```

---

## 📊 Classification Matrix

| Symptom | External IP? | Malicious Pattern? | High Volume? | Classification | Root Cause |
|---------|--------------|-------------------|--------------|----------------|------------|
| Connection pool full | ❌ No | ❌ No | ❌ No | System Issue | Capacity limit |
| Connection pool full | ✅ Yes | ✅ Yes (flood) | ✅ Yes (100+) | Attack (DoS) | DoS attack |
| Failed login | ❌ No | ❌ No | ❌ No | System Issue | User error |
| Failed login | ✅ Yes | ✅ Yes (brute) | ✅ Yes (50+) | Attack (Brute Force) | Brute force |
| SQL error | ❌ No | ❌ No | ❌ No | System Issue | Application bug |
| SQL error | ✅ Yes | ✅ Yes (injection) | ✅ Yes (10+) | Attack (SQL Injection) | SQL injection |
| High CPU | ❌ No | ❌ No | ❌ No | System Issue | Inefficient code |
| High CPU | ✅ Yes | ✅ Yes (crypto) | ✅ Yes | Attack (Cryptomining) | Cryptominer malware |
| Timeout | ❌ No | ❌ No | ❌ No | System Issue | Dependency failure |
| Timeout | ✅ Yes | ✅ Yes (flood) | ✅ Yes (100+) | Attack (DoS) | Network flood |

---

## 🎓 JSON Output Format

```json
{
  "problem": "Connection pool exhausted (100/100)",
  "issue_classification": {
    "type": "Security Attack",
    "justification": "High volume of connections (250 events) from 15 external IPs in 2 minutes, causing pool exhaustion. Primary cause is DoS attack, secondary effect is system capacity issue.",
    "confidence": 0.95,
    "primary_cause": "External malicious activity"
  },
  "attack_classification": {
    "mitre_technique": "T1498 - Network Denial of Service",
    "mitre_tactic": "TA0040 - Impact",
    "threat_actor_profile": "Automated bot network",
    "attack_stage": "Impact"
  },
  "root_cause_analysis": {
    "root_cause": "DoS attack causing connection pool exhaustion",
    "why_5": {
      "answer": "Missing WAF and rate limiting controls in deployment"
    }
  }
}
```

vs

```json
{
  "problem": "Connection pool exhausted (100/100)",
  "issue_classification": {
    "type": "System Issue",
    "justification": "Connection pool reached capacity limit during normal business hours. No external attacker IPs detected. Gradual increase in connections from internal services.",
    "confidence": 0.90,
    "primary_cause": "Capacity/Resource limit"
  },
  "attack_classification": null,
  "root_cause_analysis": {
    "root_cause": "Connection pool too small (100) for current traffic volume",
    "why_5": {
      "answer": "Missing capacity planning and load testing in deployment process"
    }
  }
}
```

---

## ✅ Benefits

1. **Accurate Classification** - Phân biệt rõ system issue vs attack
2. **Better Response** - Biết cách xử lý đúng (fix bug vs block attacker)
3. **No False Alarms** - Không báo attack khi chỉ là system issue
4. **Clear Root Cause** - Hiểu rõ nguyên nhân thật sự
5. **Actionable Recommendations** - Hướng dẫn fix phù hợp

---

## 🚀 Testing

### Test 1: System Issue (Connection Pool)
```bash
# Scenario: Normal traffic, pool too small
# Expected: "System Issue - Capacity limit"
# NOT: "DoS Attack"
```

### Test 2: DoS Attack
```bash
# Scenario: 250 REJECTs from 15 IPs in 2 min
# Expected: "Security Attack - DoS"
# Root Cause: "DoS attack causing pool exhaustion"
```

### Test 3: Application Bug
```bash
# Scenario: NullPointerException in logs
# Expected: "System Issue - Application bug"
# NOT: "Attack"
```

### Test 4: SQL Injection
```bash
# Scenario: 15 UNION SELECT queries from same IP
# Expected: "Security Attack - SQL Injection"
# NOT: "System Issue"
```

---

## 📖 Related Docs

- `ATTACK_DETECTION_CAPABILITIES.md` - Full attack types list
- `DETECTION_OVERHAUL.md` - Detection system changes
- `FALSE_POSITIVE_FIX.md` - False positive fixes

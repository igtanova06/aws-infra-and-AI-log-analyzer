# 🏗️ Architecture Diagrams

## 1. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Internet Users                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ HTTPS/HTTP
                             ▼
                    ┌─────────────────┐
                    │  Application    │
                    │  Load Balancer  │ (Public Subnet)
                    │  (ALB)          │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
     ┌────────────┐  ┌────────────┐  ┌────────────┐
     │  Web EC2   │  │  Web EC2   │  │  App EC2   │ (Private Subnet)
     │  (QLSV)    │  │  (QLSV)    │  │ (Streamlit)│
     │  Port 8080 │  │  Port 8080 │  │  Port 8501 │
     └─────┬──────┘  └─────┬──────┘  └─────┬──────┘
           │               │               │
           │               │               │ CloudWatch
           │               │               │   Agent
           └───────────────┼───────────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │   RDS PostgreSQL │ (DB Subnet)
                  │   Port 5432      │
                  └─────────────────┘
```

## 2. Network Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    VPC (10.0.0.0/16)                             │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Public Subnets (10.0.1-3.0/24)                          │   │
│  │                                                           │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐              │   │
│  │  │   ALB    │  │   IGW    │  │          │              │   │
│  │  │  (AZ-1)  │  │          │  │          │              │   │
│  │  │ 80/443   │  │          │  │          │              │   │
│  │  └──────────┘  └──────────┘  └──────────┘              │   │
│  │                                                           │   │
│  └───────────────────────┬───────────────────────────────────┘   │
│                          │                                        │
│  ┌───────────────────────┴───────────────────────────────────┐   │
│  │ Private Subnets (10.0.4-6.0/24)                          │   │
│  │                                                           │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐│   │
│  │  │ Web EC2  │  │ Web EC2  │  │ App EC2  │  │ App EC2  ││   │
│  │  │  (AZ-1)  │  │  (AZ-2)  │  │  (AZ-1)  │  │  (AZ-2)  ││   │
│  │  │ PHP QLSV │  │ PHP QLSV │  │Streamlit │  │Streamlit ││   │
│  │  │ Port 8080│  │ Port 8080│  │ Port 8501│  │ Port 8501││   │
│  │  │ NO SSH!  │  │ NO SSH!  │  │ NO SSH!  │  │ NO SSH!  ││   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘│   │
│  │                                                           │   │
│  └───────────────────────┬───────────────────────────────────┘   │
│                          │                                        │
│  ┌───────────────────────┴───────────────────────────────────┐   │
│  │ DB Subnets (10.0.7-9.0/24)                               │   │
│  │                                                           │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐              │   │
│  │  │   RDS    │  │   RDS    │  │   RDS    │              │   │
│  │  │  MySQL   │  │ Standby  │  │ Standby  │              │   │
│  │  │  (AZ-1)  │  │  (AZ-2)  │  │  (AZ-3)  │              │   │
│  │  │ Port 5432│  │          │  │          │              │   │
│  │  └──────────┘  └──────────┘  └──────────┘              │   │
│  │                                                           │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │ VPC Endpoints (Private) - SSM Access Only                │   │
│  │  • SSM Endpoint (com.amazonaws.ap-southeast-1.ssm)       │   │
│  │  • SSM Messages (com.amazonaws.ap-southeast-1.ssmmessages)│   │
│  │  • EC2 Messages (com.amazonaws.ap-southeast-1.ec2messages)│   │
│  │  • S3 Gateway Endpoint (com.amazonaws.ap-southeast-1.s3) │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘

Security Notes:
• NO SSH Port 22 exposed to internet
• Access via SSM Session Manager only
• Only HTTP/HTTPS (80/443) open on ALB
• All EC2 instances in private subnets
```

## 3. AI Analysis Pipeline Architecture (Chi Tiết 6 Bước)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          🔍 AI LOG ANALYSIS PIPELINE                             │
│                          (6-Step Intelligent Processing)                         │
└─────────────────────────────────────────────────────────────────────────────────┘

STEP 1: 📥 LOG COLLECTION (CloudWatch Client)
═══════════════════════════════════════════════════════════════════════════════════
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  VPC Flow    │  │  CloudTrail  │  │  EC2 Logs    │  │  RDS Logs    │
│  Logs        │  │  API Audit   │  │  (httpd/app) │  │  (error/slow)│
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │                 │
       │ Filter: search_term + time_range (start_dt → end_dt)
       │                 │                 │                 │
       └─────────────────┴─────────────────┴─────────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │  Raw Logs (max 100,000) │
                    │  • Timestamp            │
                    │  • Message              │
                    │  • Log Stream           │
                    └────────────┬────────────┘
                                 │
                                 │
═══════════════════════════════════════════════════════════════════════════════════
STEP 2: 🔍 LOG PARSING (LogParser)
═══════════════════════════════════════════════════════════════════════════════════
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │  Format Detection       │
                    │  (Auto-detect 3 types)  │
                    └────────────┬────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
              ▼                  ▼                  ▼
    ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
    │  VPC Flow Log   │ │  CloudTrail     │ │  Application    │
    │  Parser         │ │  JSON Parser    │ │  Log Parser     │
    │                 │ │                 │ │                 │
    │ Pattern:        │ │ Keys:           │ │ Regex:          │
    │ 2 123... eni... │ │ • eventName     │ │ [ERROR] DB:...  │
    │ REJECT/ACCEPT   │ │ • errorCode     │ │ [timestamp]     │
    │                 │ │ • userIdentity  │ │ severity level  │
    └────────┬────────┘ └────────┬────────┘ └────────┬────────┘
             │                   │                   │
             └───────────────────┴───────────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │  Parsed LogEntry[]      │
                    │  • timestamp            │
                    │  • severity (ERROR/WARN)│
                    │  • component (Web/DB)   │
                    │  • message              │
                    │  • source_ip (if any)   │
                    │  • dest_ip (if any)     │
                    └────────────┬────────────┘
                                 │
                                 │
═══════════════════════════════════════════════════════════════════════════════════
STEP 3: 📊 PATTERN CLUSTERING (PatternAnalyzer)
═══════════════════════════════════════════════════════════════════════════════════
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │  Group Similar Logs     │
                    │  (500 logs → 1 pattern) │
                    └────────────┬────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │  Pattern Extraction     │
                    │  • Remove timestamps    │
                    │  • Remove IPs           │
                    │  • Keep error signature │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │  Analysis Result        │
                    │                         │
                    │  • error_patterns[]     │
                    │    - pattern: "DB conn" │
                    │    - count: 127         │
                    │    - component: "MySQL" │
                    │                         │
                    │  • severity_distribution│
                    │    - ERROR: 450         │
                    │    - WARNING: 120       │
                    │                         │
                    │  • components           │
                    │    - Web: 300           │
                    │    - DB: 200            │
                    │    - Network: 70        │
                    └────────────┬────────────┘
                                 │
                                 │
═══════════════════════════════════════════════════════════════════════════════════
STEP 4: 🎯 RULE-BASED DETECTION (RuleBasedDetector)
═══════════════════════════════════════════════════════════════════════════════════
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │  Keyword Matching       │
                    │  (5 Issue Categories)   │
                    └────────────┬────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
              ▼                  ▼                  ▼
    ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
    │  Connection     │ │  Permission     │ │  Security       │
    │  Issues         │ │  Issues         │ │  Issues         │
    │                 │ │                 │ │                 │
    │ • "timeout"     │ │ • "denied"      │ │ • "injection"   │
    │ • "refused"     │ │ • "forbidden"   │ │ • "brute force" │
    │ • "unreachable" │ │ • "unauthorized"│ │ • "REJECT"      │
    └────────┬────────┘ └────────┬────────┘ └────────┬────────┘
             │                   │                   │
             └───────────────────┴───────────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │  Basic Solutions[]      │
                    │                         │
                    │  • problem: "SQL Inj"   │
                    │  • issue_type: SECURITY │
                    │  • solution: "Use WAF"  │
                    │  • ai_enhanced: false   │
                    └────────────┬────────────┘
                                 │
                                 │
═══════════════════════════════════════════════════════════════════════════════════
STEP 5: 🧠 CONTEXT BUILDING (LogPreprocessor) ⭐ NEW
═══════════════════════════════════════════════════════════════════════════════════
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │  Relevancy Scoring      │
                    │  (0-100 points)         │
                    └────────────┬────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │  Score Calculation:     │
                    │  • ERROR severity: +30  │
                    │  • Security keywords:+25│
                    │  • Suspicious IP: +20   │
                    │  • Recent timestamp:+15 │
                    │  • Unique pattern: +10  │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │  Filter Top Logs        │
                    │  (Keep score ≥ 50)      │
                    │  10,000 → 500 logs      │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │  Extract Context        │
                    │                         │
                    │  • suspicious_ips[]     │
                    │    ["203.0.113.42"]     │
                    │                         │
                    │  • threat_actors[]      │
                    │    ["root", "admin"]    │
                    │                         │
                    │  • failed_apis[]        │
                    │    ["DeleteVpc"]        │
                    │                         │
                    │  • sample_logs[]        │
                    │    (Top 10 highest)     │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │  AIContext Object       │
                    │  (Ready for Bedrock)    │
                    │                         │
                    │  • source_type: "VPC"   │
                    │  • total_logs: 500      │
                    │  • time_range: "1h"     │
                    │  • suspicious_ips: 3    │
                    │  • sample_logs: 10      │
                    │                         │
                    │  Token Reduction:       │
                    │  50,000 → 5,000 tokens  │
                    │  (90% savings 💰)       │
                    └────────────┬────────────┘
                                 │
                                 │
═══════════════════════════════════════════════════════════════════════════════════
STEP 6: 🤖 AI ENHANCEMENT (BedrockEnhancer + Claude 3.5)
═══════════════════════════════════════════════════════════════════════════════════
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │  Build AI Prompt        │
                    │  (Structured Template)  │
                    └────────────┬────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │  Prompt Components:     │
                    │  1. MITRE ATT&CK Guide  │
                    │  2. Log Context         │
                    │  3. Basic Solution      │
                    │  4. JSON Schema         │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │  AWS Bedrock API        │
                    │  invoke_model()         │
                    │                         │
                    │  Model Options:         │
                    │  • claude-3-haiku       │
                    │    (Fast, $0.00025/1K)  │
                    │  • claude-3.5-sonnet    │
                    │    (Smart, $0.003/1K)   │
                    │                         │
                    │  Cross-Region Routing:  │
                    │  • apac.* (Singapore)   │
                    │  • us.* (US East)       │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │  AI Response (JSON)     │
                    │                         │
                    │  {                      │
                    │    "attack_class": {    │
                    │      "mitre": "T1190",  │
                    │      "actor": "Script"  │
                    │      "stage": "Initial" │
                    │    },                   │
                    │    "summary": {         │
                    │      "severity": "High",│
                    │      "impact": "Data",  │
                    │      "confidence": "95%"│
                    │    },                   │
                    │    "investigation": {   │
                    │      "evidence": [...], │
                    │      "timeline": {...}, │
                    │      "metrics": {...}   │
                    │    },                   │
                    │    "action_plan": {     │
                    │      "containment": "", │
                    │      "commands": [...], │
                    │      "prevention": {...}│
                    │    }                    │
                    │  }                      │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │  Enhanced Solutions[]   │
                    │                         │
                    │  • ai_enhanced: true    │
                    │  • structured_solution  │
                    │  • tokens_used: 1,234   │
                    │  • cost: $0.0037        │
                    └────────────┬────────────┘
                                 │
                                 │
═══════════════════════════════════════════════════════════════════════════════════
FINAL OUTPUT: 📊 STREAMLIT DASHBOARD
═══════════════════════════════════════════════════════════════════════════════════
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │  3-Tier UI Rendering    │
                    └────────────┬────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
              ▼                  ▼                  ▼
    ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
    │  Tier 1:        │ │  Tier 2:        │ │  Tier 3:        │
    │  Summary        │ │  Investigation  │ │  Full Action    │
    │                 │ │                 │ │                 │
    │ • Severity      │ │ • Evidence      │ │ • Verification  │
    │ • Impact        │ │ • Timeline      │ │ • Fix Steps     │
    │ • Confidence    │ │ • Metrics       │ │ • Prevention    │
    │ • Quick Command │ │ • Inference     │ │ • Monitoring    │
    └─────────────────┘ └─────────────────┘ └─────────────────┘
              │                  │                  │
              └──────────────────┴──────────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │  Export Options         │
                    │  • JSON (full data)     │
                    │  • CSV (summary table)  │
                    └─────────────────────────┘
```

## 3. Log Flow Architecture (Updated)

```
┌─────────────────────────────────────────────────────────────────┐
│                      Log Sources                                 │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  VPC Traffic │  │  EC2 Logs    │  │  AWS API     │  │  RDS Logs    │
│  (Flow Logs) │  │  (CW Agent)  │  │  (CloudTrail)│  │  (MySQL)     │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │                 │
       │                 │                 │                 │
       ▼                 ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CloudWatch Logs (9 Groups)                    │
│                                                                   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │ Infrastructure   │  │ Web Tier         │  │ App Tier     │  │
│  │                  │  │                  │  │              │  │
│  │ • /aws/vpc/      │  │ • /aws/ec2/      │  │ • /aws/ec2/  │  │
│  │   flowlogs       │  │   web-tier/      │  │   app-tier/  │  │
│  │   (7 days)       │  │   system         │  │   system     │  │
│  │                  │  │   (7 days)       │  │   (7 days)   │  │
│  │ • /aws/          │  │                  │  │              │  │
│  │   cloudtrail/    │  │ • /aws/ec2/      │  │ • /aws/ec2/  │  │
│  │   logs           │  │   web-tier/      │  │   app-tier/  │  │
│  │   (90 days)      │  │   httpd          │  │   streamlit  │  │
│  │                  │  │   (7 days)       │  │   (7 days)   │  │
│  │                  │  │                  │  │              │  │
│  │                  │  │ • /aws/ec2/      │  │              │  │
│  │                  │  │   web-tier/      │  │              │  │
│  │                  │  │   application    │  │              │  │
│  │                  │  │   (14 days)      │  │              │  │
│  └──────────────────┘  └──────────────────┘  └──────────────┘  │
│                                                                   │
│  ┌──────────────────┐                                            │
│  │ Database         │                                            │
│  │                  │                                            │
│  │ • /aws/rds/      │                                            │
│  │   mysql/error    │                                            │
│  │   (7 days)       │                                            │
│  │                  │                                            │
│  │ • /aws/rds/      │                                            │
│  │   mysql/         │                                            │
│  │   slowquery      │                                            │
│  │   (7 days)       │                                            │
│  └──────────────────┘                                            │
│                                                                   │
└────────────────────────────┬──────────────────────────────────────┘
                             │
                             │ Query Logs
                             ▼
                    ┌─────────────────┐
                    │  AI Log Analyzer│
                    │   (Streamlit)   │
                    │  Port 8501      │
                    └────────┬────────┘
                             │
                             │ 1. Parse & Cluster
                             │ 2. Rule-based Detection
                             │ 3. Context Building
                             ▼
                    ┌─────────────────┐
                    │  AWS Bedrock    │
                    │  (Claude 3)     │
                    │  + MITRE ATT&CK │
                    └────────┬────────┘
                             │
                             │ Structured JSON
                             ▼
                    ┌─────────────────┐
                    │  Analysis       │
                    │  • Attack Class │
                    │  • Timeline     │
                    │  • Remediation  │
                    └─────────────────┘
```

## 4. Security Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Security Layers                             │
└─────────────────────────────────────────────────────────────────┘

Layer 1: Network Security
┌─────────────────────────────────────────────────────────────────┐
│  • Security Groups (Stateful Firewall)                           │
│    - ALB SG: Allow 80/443 from Internet                         │
│    - Web SG: Allow 8080 from ALB only                           │
│    - App SG: Allow 80 from ALB only                             │
│    - DB SG: Allow 5432 from App only                            │
│  • Network ACLs (Stateless Firewall)                            │
│  • Private Subnets (No direct internet access)                  │
└─────────────────────────────────────────────────────────────────┘

Layer 2: Access Control
┌─────────────────────────────────────────────────────────────────┐
│  • IAM Roles (Least Privilege)                                  │
│    - EC2 Role: SSM + CloudWatch + Bedrock                       │
│    - CloudTrail Role: Write to CloudWatch                       │
│    - VPC Flow Logs Role: Write to CloudWatch                    │
│  • SSM Session Manager (No SSH keys)                            │
│  • No public IPs on private instances                           │
└─────────────────────────────────────────────────────────────────┘

Layer 3: Monitoring & Detection
┌─────────────────────────────────────────────────────────────────┐
│  • VPC Flow Logs (Network traffic)                              │
│  • CloudTrail (API audit trail)                                 │
│  • CloudWatch Logs (Application logs)                           │
│  • CloudWatch Alarms (Security events)                          │
│  • Metric Filters (Suspicious patterns)                         │
└─────────────────────────────────────────────────────────────────┘

Layer 4: AI Analysis
┌─────────────────────────────────────────────────────────────────┐
│  • Pattern Detection (Rule-based)                               │
│  • AI Enhancement (Bedrock)                                     │
│  • Root Cause Analysis                                          │
│  • Remediation Recommendations                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 5. Application Access Patterns

```
┌─────────────────────────────────────────────────────────────────┐
│                    Access Pattern 1: Web QLSV                    │
└─────────────────────────────────────────────────────────────────┘

User Browser
     │
     │ http://<alb-dns>/qlsv
     ▼
┌─────────────┐
│     ALB     │ (Path-based routing)
└──────┬──────┘
       │ /qlsv/* → Web Target Group
       ▼
┌─────────────┐
│  Web EC2    │ Port 8080
│  (PHP App)  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│     RDS     │ Port 5432
└─────────────┘


┌─────────────────────────────────────────────────────────────────┐
│              Access Pattern 2: Streamlit AI Analyzer             │
└─────────────────────────────────────────────────────────────────┘

User Laptop
     │
     │ aws ssm start-session (SSM tunnel)
     ▼
┌─────────────┐
│ SSM Service │
└──────┬──────┘
       │ Port forwarding 8501 → 8888
       ▼
┌─────────────┐
│  App EC2    │ Port 8501
│ (Streamlit) │
└──────┬──────┘
       │
       │ Query logs
       ▼
┌─────────────┐
│ CloudWatch  │
│    Logs     │
└──────┬──────┘
       │
       │ Analyze
       ▼
┌─────────────┐
│   Bedrock   │
└─────────────┘
```

## 6. Data Flow: Attack Detection (Realistic Attacks)

```
┌─────────────────────────────────────────────────────────────────┐
│                    Attack Detection Flow                         │
└─────────────────────────────────────────────────────────────────┘

Step 1: Attack Occurs (HTTP-based - Realistic)
┌──────────────┐
│  Attacker    │
│  203.0.113.42│
└──────┬───────┘
       │ SQL Injection / HTTP Brute Force / Path Traversal
       │ (No SSH - Port 22 not exposed!)
       ▼
┌──────────────┐
│     ALB      │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Web EC2     │
└──────┬───────┘
       │
       │ Logs generated
       ▼

Step 2: Log Collection (Multi-tier)
┌──────────────────────────────────────┐
│ /var/log/httpd/access_log            │
│ GET /api/login.php?id=1' UNION...    │
│ 203.0.113.42 - - [timestamp] 200     │
└──────┬───────────────────────────────┘
       │
┌──────┴───────────────────────────────┐
│ /var/log/app/application.log         │
│ [ERROR] SQL Injection detected       │
└──────┬───────────────────────────────┘
       │
       │ CloudWatch Agent (2-3 min)
       ▼
┌──────────────────────────────────────┐
│ CloudWatch Log Groups:               │
│ • /aws/ec2/web-tier/httpd            │
│ • /aws/ec2/web-tier/application      │
│ • /aws/rds/mysql/error               │
└──────┬───────────────────────────────┘
       │
       ▼

Step 3: AI Analysis (6-Step Pipeline)
┌──────────────┐
│ 1. Pull Logs │ CloudWatch API
└──────┬───────┘
       │
┌──────┴───────┐
│ 2. Parse     │ LogParser (Apache, Syslog, MySQL)
└──────┬───────┘
       │
┌──────┴───────┐
│ 3. Cluster   │ PatternAnalyzer (500 → 1 pattern)
└──────┬───────┘
       │
┌──────┴───────┐
│ 4. Detect    │ RuleBasedDetector (Basic solutions)
└──────┬───────┘
       │
┌──────┴───────┐
│ 5. Context   │ LogPreprocessor (Score, filter, extract)
└──────┬───────┘
       │
┌──────┴───────┐
│ 6. AI Enhance│ Bedrock + MITRE ATT&CK
└──────┬───────┘
       │
       ▼

Step 4: Structured Response
┌──────────────────────────────────────┐
│  AI Output (JSON):                   │
│                                      │
│  attack_classification:              │
│  • MITRE: T1190 - Exploit Web App   │
│  • Threat Actor: Script Kiddie      │
│  • Stage: Initial Access            │
│                                      │
│  summary:                            │
│  • Severity: High                    │
│  • Impact: Data breach risk          │
│  • Confidence: Confirmed             │
│                                      │
│  investigation:                      │
│  • Evidence: 15 SQL injection URLs   │
│  • Timeline: 10:23-10:27 (4 min)    │
│  • Metrics: 15 attempts/min          │
│  • Source IP: 203.0.113.42           │
│                                      │
│  action_plan:                        │
│  • Containment: Block IP in WAF      │
│  • Command: aws wafv2 update-ip-set  │
│  • Fix: Use prepared statements      │
│  • Prevention: Enable AWS WAF        │
└──────────────────────────────────────┘
```

## 7. Deployment Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      Deployment Pipeline                         │
└─────────────────────────────────────────────────────────────────┘

Phase 1: Infrastructure (Terraform)
┌──────────────┐
│  terraform   │
│    init      │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  terraform   │
│    plan      │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  terraform   │
│    apply     │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────┐
│  Resources Created:                  │
│  • VPC, Subnets, IGW, NAT           │
│  • ALB, Target Groups               │
│  • EC2 Auto Scaling Groups          │
│  • RDS Database                     │
│  • CloudWatch Log Groups            │
│  • VPC Flow Logs                    │
│  • CloudTrail                       │
│  • IAM Roles & Policies             │
│  • Security Groups                  │
└──────┬───────────────────────────────┘
       │
       ▼

Phase 2: Configuration (Ansible)
┌──────────────┐
│  Dynamic     │
│  Inventory   │
└──────┬───────┘
       │ Discover EC2 instances
       ▼
┌──────────────┐
│  EC2 Setup   │
│  Role        │
└──────┬───────┘
       │ Install base packages
       ▼
┌──────────────┐
│  CloudWatch  │
│  Agent       │
└──────┬───────┘
       │ Install & configure
       ▼
┌──────────────┐
│  Docker      │
│  Install     │
└──────┬───────┘
       │ Install Docker & Compose
       ▼
┌──────────────┐
│  Deploy      │
│  Apps        │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────┐
│  Applications Running:               │
│  • Streamlit AI Analyzer (App tier) │
│  • PHP Web QLSV (Web tier)          │
│  • CloudWatch Agent (All instances) │
└──────────────────────────────────────┘
```

## 8. Cost Breakdown

```
┌─────────────────────────────────────────────────────────────────┐
│                    Monthly Cost Estimate (Dev)                   │
└─────────────────────────────────────────────────────────────────┘

Compute
├─ EC2 (4x t3.micro)              $30/month
├─ RDS (db.t3.micro)              $15/month
└─ ALB                            $20/month
                                  ─────────
                                  $65/month

Storage
├─ EBS (4x 8GB)                   $4/month
├─ RDS Storage (20GB)             $2/month
└─ S3 (CloudTrail)                $1/month
                                  ─────────
                                  $7/month

Networking
├─ NAT Gateway (if enabled)       $32/month (disabled in dev)
├─ Data Transfer                  $2/month
└─ VPC Endpoints                  FREE
                                  ─────────
                                  $2/month

Monitoring & Logs
├─ CloudWatch Logs Ingestion      $3/month
├─ CloudWatch Logs Storage        $1/month
├─ VPC Flow Logs                  $2/month
└─ CloudWatch Alarms              FREE (first 10)
                                  ─────────
                                  $6/month

AI Services
├─ Bedrock API (Claude Haiku)     $0.01-0.05/analysis
└─ Estimated monthly              $2/month
                                  ─────────
                                  $2/month

                        TOTAL: ~$82/month (dev environment)

Production Optimizations:
• Reserved Instances: Save 40-60%
• Savings Plans: Save 30-50%
• S3 Intelligent-Tiering: Save 30-70% on logs
• Spot Instances: Save up to 90% (non-critical workloads)
```

---

**Legend:**
- 🟢 Public Subnet
- 🔵 Private Subnet
- 🟣 DB Subnet
- 🔴 Security Group
- 🟡 VPC Endpoint


## 9. AI Context Building - Before vs After (Token Optimization)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    ❌ BEFORE: Naive Approach (Expensive)                         │
└─────────────────────────────────────────────────────────────────────────────────┘

CloudWatch Logs (100,000 entries)
         │
         │ Send ALL logs to AI
         ▼
┌─────────────────────────┐
│  AWS Bedrock API        │
│                         │
│  Input: 500,000 tokens  │
│  Output: 2,000 tokens   │
│  Total: 502,000 tokens  │
│                         │
│  Cost (Haiku):          │
│  $0.125 per analysis    │
│                         │
│  Problems:              │
│  • Very slow (2-3 min)  │
│  • Expensive            │
│  • Context overflow     │
│  • Noise in results     │
└─────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────────┐
│                    ✅ AFTER: Smart Preprocessing (Optimized)                     │
└─────────────────────────────────────────────────────────────────────────────────┘

CloudWatch Logs (100,000 entries)
         │
         │ Step 1: Score each log (0-100)
         ▼
┌─────────────────────────┐
│  Relevancy Scoring      │
│                         │
│  Criteria:              │
│  • Severity: +30        │
│  • Security: +25        │
│  • Suspicious IP: +20   │
│  • Recency: +15         │
│  • Uniqueness: +10      │
└────────┬────────────────┘
         │
         │ Step 2: Filter (keep score ≥ 50)
         ▼
┌─────────────────────────┐
│  Filtered Logs          │
│  100,000 → 500 logs     │
│  (99.5% reduction)      │
└────────┬────────────────┘
         │
         │ Step 3: Extract context
         ▼
┌─────────────────────────┐
│  Context Extraction     │
│                         │
│  • Top 10 sample logs   │
│  • 3 suspicious IPs     │
│  • 5 threat actors      │
│  • 8 failed APIs        │
│  • Pattern summary      │
└────────┬────────────────┘
         │
         │ Step 4: Send compact context
         ▼
┌─────────────────────────┐
│  AWS Bedrock API        │
│                         │
│  Input: 5,000 tokens    │
│  Output: 2,000 tokens   │
│  Total: 7,000 tokens    │
│                         │
│  Cost (Haiku):          │
│  $0.0018 per analysis   │
│                         │
│  Benefits:              │
│  • Fast (5s response)   │
│  • 98.6% cost savings 💰│
│  • No context overflow  │
│  • Focused results      │
└─────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────────┐
│                         📊 COST COMPARISON (Monthly)                             │
└─────────────────────────────────────────────────────────────────────────────────┘

Scenario: 100 analyses per month (100k logs each)

┌──────────────────┬──────────────┬──────────────┬──────────────┐
│  Approach        │  Tokens/Call │  Cost/Call   │  Monthly     │
├──────────────────┼──────────────┼──────────────┼──────────────┤
│  Naive (Before)  │  502,000     │  $0.125      │  $12.50      │
│  Smart (After)   │  7,000       │  $0.0018     │  $0.18       │
├──────────────────┼──────────────┼──────────────┼──────────────┤
│  SAVINGS         │  98.6% less  │  98.6% cheaper│ $12.32/month │
└──────────────────┴──────────────┴──────────────┴──────────────┘

At scale (1,000 analyses/month):
• Before: $125.00/month
• After: $1.80/month
• Savings: $123.20/month (98.6%)
```

## 10. Real Attack Detection Example (SQL Injection)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    🚨 REAL-WORLD ATTACK SCENARIO                                 │
│                    SQL Injection Attack Detection Flow                           │
└─────────────────────────────────────────────────────────────────────────────────┘

TIME: 10:23:15 AM
┌──────────────┐
│  Attacker    │
│ 203.0.113.42 │
└──────┬───────┘
       │
       │ HTTP Request:
       │ GET /api/login.php?id=1' UNION SELECT password FROM users--
       ▼
┌──────────────┐
│     ALB      │ (Allow - no WAF yet)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Web EC2     │ (PHP processes request)
│  Port 8080   │
└──────┬───────┘
       │
       │ Logs Generated (3 sources):
       │
       ├─────────────────────────────────────────────────────────┐
       │                                                           │
       ▼                                                           ▼
┌─────────────────────────┐                          ┌─────────────────────────┐
│  /var/log/httpd/        │                          │  /var/log/app/          │
│  access_log             │                          │  application.log        │
│                         │                          │                         │
│  203.0.113.42 - -       │                          │  [ERROR] SQL Injection  │
│  [10:23:15] "GET        │                          │  detected in login.php  │
│  /api/login.php?id=1'   │                          │  User input: id=1'      │
│  UNION SELECT..." 200   │                          │  UNION SELECT...        │
└────────┬────────────────┘                          └────────┬────────────────┘
         │                                                     │
         │                                                     │
         ▼                                                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│  CloudWatch Agent (2-3 min delay)                                   │
│  Pushes to:                                                          │
│  • /aws/ec2/web-tier/httpd                                          │
│  • /aws/ec2/web-tier/application                                    │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 │
TIME: 10:26:00 AM (3 min later)
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│  AI Log Analyzer (Streamlit)                                        │
│  User clicks "Analyze Logs"                                         │
│  • Log Group: /aws/ec2/web-tier/httpd                              │
│  • Search Term: "UNION"                                             │
│  • Time Range: Last 1 hour                                          │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 │ STEP 1: Pull Logs
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│  CloudWatch API Response                                            │
│  Found: 15 matching logs                                            │
│                                                                      │
│  10:23:15 - GET /api/login.php?id=1' UNION SELECT...               │
│  10:23:18 - GET /api/login.php?id=2' OR 1=1--                      │
│  10:23:21 - GET /api/login.php?id=3' DROP TABLE users--            │
│  ... (12 more similar attempts)                                     │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 │ STEP 2: Parse
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│  LogParser Output                                                   │
│  • Format: Apache Access Log                                        │
│  • Severity: ERROR (SQL keywords detected)                          │
│  • Component: Web                                                   │
│  • Source IP: 203.0.113.42 (extracted)                             │
│  • Pattern: SQL Injection signature                                 │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 │ STEP 3: Cluster
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│  PatternAnalyzer Output                                             │
│  • Pattern: "GET /api/login.php?id=* UNION SELECT"                 │
│  • Count: 15 attempts                                               │
│  • Time Span: 4 minutes (10:23-10:27)                              │
│  • Rate: 3.75 attempts/minute                                       │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 │ STEP 4: Detect
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│  RuleBasedDetector Output                                           │
│  • Issue Type: SECURITY                                             │
│  • Problem: "SQL Injection Attack Detected"                         │
│  • Basic Solution: "Use prepared statements, enable WAF"            │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 │ STEP 5: Build Context
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│  LogPreprocessor Output (AIContext)                                 │
│                                                                      │
│  • source_type: "Web Application Logs"                              │
│  • total_logs_after_scoring: 15 (all high relevance)               │
│  • suspicious_ips: ["203.0.113.42"]                                │
│  • threat_actors: ["anonymous"]                                     │
│  • failed_apis: ["login.php"]                                       │
│  • sample_logs: [top 10 most suspicious]                            │
│  • time_range: "10:23-10:27 (4 min)"                               │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 │ STEP 6: AI Enhance
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│  AWS Bedrock (Claude 3.5 Sonnet)                                    │
│  Prompt: "Analyze this SQL injection attack..."                     │
│  Context: AIContext object (5,000 tokens)                           │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 │ AI Response (JSON)
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Enhanced Solution (Structured JSON)                                │
│                                                                      │
│  {                                                                   │
│    "attack_classification": {                                       │
│      "mitre_technique": "T1190 - Exploit Public-Facing App",       │
│      "threat_actor_profile": "Script Kiddie / Automated Scanner",  │
│      "attack_stage": "Initial Access"                               │
│    },                                                                │
│    "summary": {                                                      │
│      "severity": "High",                                             │
│      "impact": "Potential data breach, user credential theft",      │
│      "confidence": "Confirmed (95%)"                                 │
│    },                                                                │
│    "investigation": {                                                │
│      "evidence_from_logs": [                                         │
│        "15 SQL injection attempts in 4 minutes",                    │
│        "UNION SELECT, OR 1=1, DROP TABLE keywords detected",        │
│        "Single source IP: 203.0.113.42",                            │
│        "Target: /api/login.php (authentication endpoint)"           │
│      ],                                                              │
│      "attack_timeline": {                                            │
│        "first_seen": "10:23:15",                                     │
│        "peak_activity": "10:24:30",                                  │
│        "last_seen": "10:27:12",                                      │
│        "total_duration": "4 minutes"                                 │
│      },                                                              │
│      "attack_metrics": {                                             │
│        "total_attempts": 15,                                         │
│        "attempts_per_minute": 3.75,                                  │
│        "success_rate": "0% (all returned 200 but no data leak)",    │
│        "unique_targets": 1                                           │
│      },                                                              │
│      "inference": [                                                  │
│        "Automated attack (consistent timing pattern)",              │
│        "Testing for vulnerable endpoints",                           │
│        "No authentication bypass achieved (yet)"                     │
│      ]                                                               │
│    },                                                                │
│    "action_plan": {                                                  │
│      "immediate_containment": "Block IP 203.0.113.42 in WAF",      │
│      "next_best_command": "aws wafv2 update-ip-set --name BlockList │
│         --scope REGIONAL --id <id> --addresses 203.0.113.42/32",   │
│      "verification_commands": [                                      │
│        "aws wafv2 get-ip-set --name BlockList --scope REGIONAL",   │
│        "tail -f /var/log/httpd/access_log | grep 203.0.113.42"     │
│      ],                                                              │
│      "fix_steps": [                                                  │
│        "1. Review login.php code for SQL injection vulnerabilities",│
│        "2. Replace string concatenation with prepared statements",  │
│        "3. Add input validation and sanitization",                   │
│        "4. Enable AWS WAF with SQL injection rule set",             │
│        "5. Set up CloudWatch alarm for SQL keywords in logs"        │
│      ],                                                              │
│      "prevention": {                                                 │
│        "aws_services": [                                             │
│          "AWS WAF - Enable SQL injection protection",               │
│          "AWS Shield - DDoS protection",                             │
│          "GuardDuty - Threat detection"                              │
│        ],                                                            │
│        "configuration": [                                            │
│          "Use PDO/MySQLi prepared statements in PHP",               │
│          "Enable ModSecurity on Apache",                             │
│          "Set up rate limiting (max 10 req/min per IP)"             │
│        ],                                                            │
│        "monitoring": [                                               │
│          "CloudWatch Metric Filter: SQL keywords",                   │
│          "SNS alert on 5+ failed login attempts",                    │
│          "Daily security log review"                                 │
│        ]                                                             │
│      }                                                               │
│    }                                                                 │
│  }                                                                   │
│                                                                      │
│  Tokens Used: 6,234                                                 │
│  Cost: $0.0187                                                       │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 │ Render in Streamlit
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Streamlit Dashboard (3-Tier UI)                                    │
│                                                                      │
│  🚨 SQL Injection Attack Detected                                   │
│  ✨ AI Enhanced                                                      │
│                                                                      │
│  🎯 Attack Classification                                           │
│  MITRE: T1190 | Threat Actor: Script Kiddie | Stage: Initial Access│
│                                                                      │
│  🔴 Severity: High | Confidence: Confirmed (95%)                    │
│  💥 Business Impact: Potential data breach, credential theft        │
│                                                                      │
│  🔥 Immediate Containment: Block IP 203.0.113.42 in WAF            │
│  $ aws wafv2 update-ip-set --name BlockList...                      │
│                                                                      │
│  🔍 Investigation Details                                           │
│  Evidence: 15 attempts in 4 min | Timeline: 10:23-10:27            │
│  Metrics: 3.75 attempts/min | Success Rate: 0%                      │
│                                                                      │
│  🔧 Full Action Plan                                                │
│  [Expandable sections with verification, fix steps, prevention]     │
│                                                                      │
│  📥 Export: [JSON] [CSV]                                            │
└─────────────────────────────────────────────────────────────────────┘

TOTAL TIME: ~8 seconds (from user click to results)
TOTAL COST: $0.0187 (Bedrock API call)
```

---

**Key Takeaways:**
- 🚀 **Real-time detection** — 3-minute delay from attack to log availability
- 🧠 **AI-powered analysis** — MITRE ATT&CK classification + actionable commands
- 💰 **Cost-effective** — $0.02 per analysis with 86% token savings
- 🎯 **Actionable** — One-click commands to block attacker immediately
- 📊 **Comprehensive** — Evidence + Timeline + Metrics + Prevention strategy


---

## 11. Multi-Source Correlation Mode - Detailed Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    🧩 MULTI-SOURCE CORRELATION MODE                              │
│                    Advanced Attack Detection Across Log Sources                  │
└─────────────────────────────────────────────────────────────────────────────────┘

USER ACTION: Chọn "Multi-Source Correlation" mode trong Streamlit
             Select 2-4 log groups (VPC Flow, CloudTrail, Application, Database)
             Click "🚀 Analyze Logs"

═══════════════════════════════════════════════════════════════════════════════════
PHASE 1: 📥 PARALLEL LOG COLLECTION (Concurrent)
═══════════════════════════════════════════════════════════════════════════════════

┌──────────────────────────────────────────────────────────────────────────────┐
│  CloudWatch Client (concurrent_fetch)                                        │
│  Pulls logs from multiple log groups simultaneously                          │
└──────────────────────────────────────────────────────────────────────────────┘
                                 │
              ┌──────────────────┼──────────────────┬──────────────────┐
              │                  │                  │                  │
              ▼                  ▼                  ▼                  ▼
    ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
    │  /aws/vpc/      │ │  /aws/          │ │  /aws/ec2/      │ │  /aws/rds/      │
    │  flowlogs       │ │  cloudtrail/    │ │  application    │ │  mysql/error    │
    │                 │ │  logs           │ │                 │ │                 │
    │  VPC Flow Logs  │ │  CloudTrail     │ │  App Logs       │ │  DB Logs        │
    │  (Network)      │ │  (API Audit)    │ │  (Web/Backend)  │ │  (Database)     │
    └────────┬────────┘ └────────┬────────┘ └────────┬────────┘ └────────┬────────┘
             │                   │                   │                   │
             │ Parse             │ Parse             │ Parse             │ Parse
             ▼                   ▼                   ▼                   ▼
    ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
    │ LogEntry[]      │ │ LogEntry[]      │ │ LogEntry[]      │ │ LogEntry[]      │
    │ • timestamp     │ │ • timestamp     │ │ • timestamp     │ │ • timestamp     │
    │ • severity      │ │ • severity      │ │ • severity      │ │ • severity      │
    │ • message       │ │ • message       │ │ • message       │ │ • message       │
    │ • source_ip     │ │ • user_arn      │ │ • trace_id      │ │ • instance_id   │
    │ • dest_ip       │ │ • api_action    │ │ • request_id    │ │ • query_time    │
    └────────┬────────┘ └────────┬────────┘ └────────┬────────┘ └────────┬────────┘
             │                   │                   │                   │
             └───────────────────┴───────────────────┴───────────────────┘
                                         │
                                         │
═══════════════════════════════════════════════════════════════════════════════════
PHASE 2: � PATTERN CLUSTERING (PatternAnalyzer) ⭐ RECOMMENDED
═══════════════════════════════════════════════════════════════════════════════════
                                         │
                                         ▼
                            ┌─────────────────────────┐
                            │  PatternAnalyzer        │
                            │  Cluster similar logs   │
                            │  100,000 → 50 patterns  │
                            └────────────┬────────────┘
                                         │
                    ┌────────────────────┴────────────────────┐
                    │  Benefits:                              │
                    │  • Reduce noise (99.95% reduction)      │
                    │  • Identify attack patterns             │
                    │  • Improve correlation accuracy         │
                    │  • Faster AI processing                 │
                    └────────────────────┬────────────────────┘
                                         │
                                         ▼
                            ┌─────────────────────────┐
                            │  Clustered Patterns     │
                            │                         │
                            │  Pattern 1:             │
                            │  • "SQL injection"      │
                            │  • Count: 500           │
                            │  • Component: App       │
                            │                         │
                            │  Pattern 2:             │
                            │  • "VPC REJECT port 22" │
                            │  • Count: 300           │
                            │  • Component: Network   │
                            │                         │
                            │  Pattern 3:             │
                            │  • "Connection timeout" │
                            │  • Count: 200           │
                            │  • Component: DB        │
                            └────────────┬────────────┘
                                         │
                                         │
═══════════════════════════════════════════════════════════════════════════════════
PHASE 3: �🔍 RICH CORRELATION KEY EXTRACTION (AdvancedCorrelator)
═══════════════════════════════════════════════════════════════════════════════════
                                         │
                                         ▼
                            ┌─────────────────────────┐
                            │  _extract_rich_keys()   │
                            │  Extract from patterns  │
                            │  (not individual logs)  │
                            └────────────┬────────────┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    │                    │                    │
                    ▼                    ▼                    ▼
        ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐
        │ PRIMARY KEYS      │  │ SECONDARY KEYS    │  │ CONTEXTUAL KEYS   │
        │ (Strongest)       │  │ (Medium)          │  │ (Weakest)         │
        │                   │  │                   │  │                   │
        │ • trace_ids[]     │  │ • ip_addresses[]  │  │ • user_agents[]   │
        │   X-Trace-Id      │  │   (public only)   │  │   Browser info    │
        │   X-Request-Id    │  │                   │  │                   │
        │                   │  │ • user_arns[]     │  │ • api_actions[]   │
        │ • request_ids[]   │  │   IAM users       │  │   AWS API calls   │
        │   Request corr.   │  │                   │  │                   │
        │                   │  │ • instance_ids[]  │  │ • timestamps[]    │
        │ • session_ids[]   │  │   EC2 instances   │  │   Temporal data   │
        │   User session    │  │                   │  │                   │
        └───────────────────┘  └───────────────────┘  └───────────────────┘
                    │                    │                    │
                    └────────────────────┴────────────────────┘
                                         │
                                         ▼
                            ┌─────────────────────────┐
                            │  RichCorrelationKey     │
                            │  per Log Source         │
                            │                         │
                            │  VPC Flow:              │
                            │  • IPs: [203.0.113.42]  │
                            │  • trace_ids: []        │
                            │                         │
                            │  Application:           │
                            │  • IPs: [203.0.113.42]  │
                            │  • trace_ids: [abc123]  │
                            │  • request_ids: [req1]  │
                            │                         │
                            │  CloudTrail:            │
                            │  • IPs: [203.0.113.42]  │
                            │  • user_arns: [arn:...] │
                            └────────────┬────────────┘
                                         │
                                         │
═══════════════════════════════════════════════════════════════════════════════════
PHASE 4: 🧩 TIMELINE BUILDING (Priority-Based Correlation)
═══════════════════════════════════════════════════════════════════════════════════
                                         │
                                         ▼
                            ┌─────────────────────────┐
                            │  _build_timelines()     │
                            │  Priority Matching:     │
                            │  1. trace_id (STRONG)   │
                            │  2. request_id (MEDIUM) │
                            │  3. session_id (MEDIUM) │
                            │  4. instance_id (MEDIUM)│
                            │  5. IP address (WEAK)   │
                            └────────────┬────────────┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    │                    │                    │
                    ▼                    ▼                    ▼
        ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐
        │ Timeline for      │  │ Timeline for      │  │ Timeline for      │
        │ trace:abc123      │  │ ip:203.0.113.42   │  │ instance:i-abc123 │
        │ (STRONG)          │  │ (WEAK)            │  │ (MEDIUM)          │
        │                   │  │                   │  │                   │
        │ Events:           │  │ Events:           │  │ Events:           │
        │ 1. 10:23:15       │  │ 1. 10:23:10       │  │ 1. 10:20:00       │
        │    vpc_flow       │  │    vpc_flow       │  │    application    │
        │    network_reject │  │    network_reject │  │    connection_    │
        │    CRITICAL       │  │    HIGH           │  │    timeout        │
        │                   │  │                   │  │    HIGH           │
        │ 2. 10:23:18       │  │ 2. 10:23:20       │  │                   │
        │    application    │  │    cloudtrail     │  │ 2. 10:20:05       │
        │    sql_injection  │  │    api_deny       │  │    database       │
        │    CRITICAL       │  │    HIGH           │  │    too_many_conn  │
        │                   │  │                   │  │    HIGH           │
        │ 3. 10:23:25       │  │ 3. 10:23:30       │  │                   │
        │    cloudtrail     │  │    application    │  └───────────────────┘
        │    api_deny       │  │    sql_injection  │
        │    HIGH           │  │    CRITICAL       │
        └───────────────────┘  └───────────────────┘
                    │                    │                    │
                    └────────────────────┴────────────────────┘
                                         │
                                         ▼
                            ┌─────────────────────────┐
                            │  TimelineEvent[]        │
                            │  (Sorted by timestamp)  │
                            │                         │
                            │  Each event contains:   │
                            │  • timestamp            │
                            │  • source (vpc_flow)    │
                            │  • event_type           │
                            │  • severity             │
                            │  • actor (IP/trace_id)  │
                            │  • message              │
                            │  • metadata             │
                            └────────────┬────────────┘
                                         │
                                         │
═══════════════════════════════════════════════════════════════════════════════════
PHASE 5: 🎯 RULE ENGINE EVALUATION (Config-Driven Detection)
═══════════════════════════════════════════════════════════════════════════════════
                                         │
                                         ▼
                            ┌─────────────────────────┐
                            │  RuleEngine.evaluate()  │
                            │  Load from:             │
                            │  correlation_rules.json │
                            └────────────┬────────────┘
                                         │
              ┌──────────────────────────┼──────────────────────────┐
              │                          │                          │
              ▼                          ▼                          ▼
    ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
    │  Rule R001      │      │  Rule R002      │      │  Rule R004      │
    │  Reconnaissance │      │  Privilege      │      │  App-DB Issue   │
    │  to Exploit     │      │  Escalation     │      │                 │
    │                 │      │                 │      │                 │
    │ Required:       │      │ Required:       │      │ Required:       │
    │ • vpc_flow      │      │ • cloudtrail    │      │ • application   │
    │ • application   │      │ • application   │      │ • database      │
    │                 │      │                 │      │                 │
    │ Sequence:       │      │ Sequence:       │      │ Sequence:       │
    │ 1. network_     │      │ 1. api_deny     │      │ 1. connection_  │
    │    reject       │      │ 2. unauthorized │      │    timeout      │
    │ 2. sql_         │      │    _access      │      │ 2. too_many_    │
    │    injection    │      │                 │      │    connections  │
    │                 │      │                 │      │                 │
    │ Max Gap: 300s   │      │ Max Gap: 600s   │      │ Max Gap: 60s    │
    │                 │      │                 │      │                 │
    │ Base Conf: 70%  │      │ Base Conf: 65%  │      │ Base Conf: 80%  │
    │                 │      │                 │      │                 │
    │ Modifiers:      │      │ Modifiers:      │      │ Modifiers:      │
    │ • trace_id: +20 │      │ • user_arn: +25 │      │ • instance: +15 │
    │ • automated:+10 │      │ • repeated: +15 │      │ • high_freq:+10 │
    └────────┬────────┘      └────────┬────────┘      └────────┬────────┘
             │                        │                        │
             │ MATCH! ✅              │ NO MATCH ❌            │ NO MATCH ❌
             │ Confidence: 90%        │                        │
             │ (70 + 20 trace_id)     │                        │
             │                        │                        │
             └────────────────────────┴────────────────────────┘
                                      │
                                      ▼
                         ┌─────────────────────────┐
                         │  Matched Rules[]        │
                         │  (Sorted by confidence) │
                         │                         │
                         │  1. R001: 90%           │
                         │     Reconnaissance      │
                         │     to Exploit          │
                         │                         │
                         │  MITRE ATT&CK:          │
                         │  • TA0001 (Initial)     │
                         │  • T1190 (Exploit)      │
                         └────────────┬────────────┘
                                      │
                                      │
═══════════════════════════════════════════════════════════════════════════════════
PHASE 6: 📊 ATTACK SEQUENCE DETECTION (Temporal Analysis)
═══════════════════════════════════════════════════════════════════════════════════
                                      │
                                      ▼
                         ┌─────────────────────────┐
                         │  _detect_sequences()    │
                         │  Analyze timing:        │
                         │  • Total duration       │
                         │  • Average delay        │
                         │  • Is automated?        │
                         └────────────┬────────────┘
                                      │
                         ┌────────────┴────────────┐
                         │  Timing Calculation:    │
                         │                         │
                         │  Event 1: 10:23:15      │
                         │  Event 2: 10:23:18      │
                         │  Event 3: 10:23:25      │
                         │                         │
                         │  Delays:                │
                         │  • E1→E2: 3 seconds     │
                         │  • E2→E3: 7 seconds     │
                         │                         │
                         │  Average: 5 seconds     │
                         │  Total: 10 seconds      │
                         │                         │
                         │  Is Automated?          │
                         │  avg_delay < 5s → YES ✅│
                         │  (Bot/Script detected)  │
                         └────────────┬────────────┘
                                      │
                                      ▼
                         ┌─────────────────────────┐
                         │  AttackSequence         │
                         │                         │
                         │  sequence_id: SEQ-R001  │
                         │  pattern: Recon→Exploit │
                         │  events: 3              │
                         │  confidence: 90%        │
                         │                         │
                         │  total_duration: 10s    │
                         │  average_delay: 5s      │
                         │  is_automated: true     │
                         │                         │
                         │  mitre_tactics:         │
                         │  • TA0001 (Initial)     │
                         │  • TA0002 (Execution)   │
                         │                         │
                         │  mitre_techniques:      │
                         │  • T1190 (Exploit)      │
                         │  • T1059 (Command)      │
                         └────────────┬────────────┘
                                      │
                                      │
═══════════════════════════════════════════════════════════════════════════════════
PHASE 7: 🧠 CONTEXT & INTENT ANALYSIS
═══════════════════════════════════════════════════════════════════════════════════
                                      │
                                      ▼
                         ┌─────────────────────────┐
                         │  _determine_intent()    │
                         │  Classify attacker goal │
                         └────────────┬────────────┘
                                      │
              ┌───────────────────────┼───────────────────────┐
              │                       │                       │
              ▼                       ▼                       ▼
    ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
    │ data_theft      │   │ privilege_      │   │ denial_of_      │
    │                 │   │ escalation      │   │ service         │
    │ Indicators:     │   │                 │   │                 │
    │ • sql_injection │   │ Indicators:     │   │ Indicators:     │
    │ • data_exfil    │   │ • api_deny      │   │ • network_      │
    │                 │   │ • unauthorized  │   │   reject > 10   │
    └─────────────────┘   └─────────────────┘   └─────────────────┘
              │                       │                       │
              └───────────────────────┴───────────────────────┘
                                      │
                                      ▼
                         ┌─────────────────────────┐
                         │  _build_context()       │
                         │  Rich metadata:         │
                         │                         │
                         │  • total_events: 3      │
                         │  • sources: [vpc, app]  │
                         │  • severity_dist:       │
                         │    CRITICAL: 2          │
                         │    HIGH: 1              │
                         │  • event_types:         │
                         │    [network_reject,     │
                         │     sql_injection]      │
                         │  • first_seen: 10:23:15 │
                         │  • last_seen: 10:23:25  │
                         │  • duration: 0.17 min   │
                         └────────────┬────────────┘
                                      │
                                      │
═══════════════════════════════════════════════════════════════════════════════════
PHASE 8: 🎨 CORRELATED EVENT ASSEMBLY
═══════════════════════════════════════════════════════════════════════════════════
                                      │
                                      ▼
                         ┌─────────────────────────┐
                         │  AdvancedCorrelatedEvent│
                         │                         │
                         │  correlation_id:        │
                         │  CORR-abc123def456      │
                         │                         │
                         │  primary_key:           │
                         │  trace:abc123           │
                         │                         │
                         │  correlation_strength:  │
                         │  STRONG                 │
                         │                         │
                         │  timeline:              │
                         │  [TimelineEvent × 3]    │
                         │                         │
                         │  attack_sequences:      │
                         │  [AttackSequence × 1]   │
                         │                         │
                         │  event_type:            │
                         │  coordinated_attack     │
                         │                         │
                         │  severity: CRITICAL     │
                         │  confidence: 90%        │
                         │                         │
                         │  intent: data_theft     │
                         │                         │
                         │  context: {...}         │
                         │                         │
                         │  evidence_by_source:    │
                         │  • vpc_flow: [...]      │
                         │  • application: [...]   │
                         └────────────┬────────────┘
                                      │
                                      │
═══════════════════════════════════════════════════════════════════════════════════
PHASE 9: 🤖 AI ENHANCEMENT (Optional - If Enabled)
═══════════════════════════════════════════════════════════════════════════════════
                                      │
                                      ▼
                         ┌─────────────────────────┐
                         │  BedrockEnhancer        │
                         │  (Same as Single-Source)│
                         │                         │
                         │  Input: Correlated Event│
                         │  + Timeline             │
                         │  + Attack Sequences     │
                         │  + MITRE ATT&CK         │
                         └────────────┬────────────┘
                                      │
                                      ▼
                         ┌─────────────────────────┐
                         │  AWS Bedrock API        │
                         │  Claude 3.5 Sonnet      │
                         │                         │
                         │  Enhanced with:         │
                         │  • Root cause analysis  │
                         │  • Remediation steps    │
                         │  • Prevention strategy  │
                         └────────────┬────────────┘
                                      │
                                      ▼
                         ┌─────────────────────────┐
                         │  ai_summary:            │
                         │  "Coordinated attack    │
                         │   detected across       │
                         │   network and app       │
                         │   layers..."            │
                         │                         │
                         │  ai_recommendations:    │
                         │  • Block IP in WAF      │
                         │  • Enable GuardDuty     │
                         │  • Review app code      │
                         └────────────┬────────────┘
                                      │
                                      │
═══════════════════════════════════════════════════════════════════════════════════
FINAL OUTPUT: 📊 STREAMLIT DASHBOARD (Multi-Source Tab)
═══════════════════════════════════════════════════════════════════════════════════
                                      │
                                      ▼
                         ┌─────────────────────────┐
                         │  Tab: 🧩 Correlation    │
                         └────────────┬────────────┘
                                      │
              ┌───────────────────────┼───────────────────────┐
              │                       │                       │
              ▼                       ▼                       ▼
    ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
    │ Correlated      │   │ Attack Timeline │   │ Evidence by     │
    │ Events Summary  │   │ Visualization   │   │ Source          │
    │                 │   │                 │   │                 │
    │ 🚨 Event #1     │   │ 10:23:15        │   │ VPC Flow:       │
    │ Coordinated     │   │ ├─ network_     │   │ • 1 REJECT      │
    │ Attack          │   │ │  reject       │   │                 │
    │                 │   │ │  (vpc_flow)   │   │ Application:    │
    │ Actor:          │   │ │               │   │ • 1 SQL inj.    │
    │ trace:abc123    │   │ 10:23:18        │   │                 │
    │                 │   │ ├─ sql_         │   │ CloudTrail:     │
    │ Strength: STRONG│   │ │  injection    │   │ • 1 API deny    │
    │ Confidence: 90% │   │ │  (application)│   │                 │
    │                 │   │ │               │   └─────────────────┘
    │ Severity:       │   │ 10:23:25        │
    │ CRITICAL        │   │ └─ api_deny     │
    │                 │   │    (cloudtrail) │
    │ Intent:         │   │                 │
    │ data_theft      │   │ Duration: 10s   │
    │                 │   │ Automated: YES  │
    │ MITRE:          │   │                 │
    │ • TA0001        │   └─────────────────┘
    │ • T1190         │
    │                 │
    │ Attack Chain:   │
    │ 1. Network      │
    │    scanning     │
    │ 2. SQL inject   │
    │ 3. API abuse    │
    │                 │
    │ Recommendations:│
    │ • Block IP      │
    │ • Enable WAF    │
    │ • Review code   │
    └─────────────────┘


┌─────────────────────────────────────────────────────────────────────────────────┐
│                         🎯 KEY DIFFERENCES vs Single-Source                      │
└─────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────┬──────────────────────┬──────────────────────────────────┐
│  Feature             │  Single-Source       │  Multi-Source Correlation        │
├──────────────────────┼──────────────────────┼──────────────────────────────────┤
│  Log Sources         │  1 log group         │  2-4 log groups (parallel)       │
│  Correlation         │  None                │  Rich keys (trace_id > IP)       │
│  Timeline            │  Single source       │  Cross-source timeline           │
│  Rule Engine         │  Basic keywords      │  Config-driven sequences         │
│  Attack Detection    │  Pattern-based       │  Sequence + timing analysis      │
│  Confidence Scoring  │  Simple              │  Multi-factor (source + events)  │
│  MITRE Mapping       │  AI-generated        │  Rule-based + AI-enhanced        │
│  Intent Detection    │  AI-inferred         │  Timeline + sequence analysis    │
│  Automation Detect   │  No                  │  Yes (timing analysis)           │
│  Evidence            │  Single source       │  Grouped by source               │
│  Use Case            │  Deep dive           │  Attack discovery                │
└──────────────────────┴──────────────────────┴──────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────────┐
│                         💡 EXAMPLE: Real Attack Correlation                      │
└─────────────────────────────────────────────────────────────────────────────────┘

10:23:10 - VPC Flow Log
  203.0.113.42 → 10.0.1.55:22 REJECT
  (Attacker tries SSH - blocked by Security Group)

10:23:15 - VPC Flow Log
  203.0.113.42 → 10.0.1.55:80 ACCEPT
  (Attacker switches to HTTP - allowed)

10:23:18 - Application Log
  [ERROR] SQL Injection detected: GET /api/login.php?id=1' UNION SELECT...
  Source IP: 203.0.113.42
  Trace-ID: abc123def456
  (Attacker exploits web app)

10:23:25 - CloudTrail
  {
    "eventName": "DeleteVpc",
    "errorCode": "AccessDenied",
    "sourceIPAddress": "203.0.113.42",
    "userIdentity": {"type": "AssumedRole"}
  }
  (Attacker tries to delete VPC - denied)

═══════════════════════════════════════════════════════════════════════════════════
CORRELATION RESULT:
═══════════════════════════════════════════════════════════════════════════════════

✅ Correlated by: IP (203.0.113.42) + Trace-ID (abc123def456)
✅ Correlation Strength: STRONG (trace_id present)
✅ Matched Rule: R001 - Reconnaissance to Exploit
✅ Confidence: 90% (70 base + 20 trace_id)
✅ Attack Sequence: 4 events in 15 seconds
✅ Automated: YES (avg delay 5s)
✅ Intent: data_theft + privilege_escalation
✅ MITRE: TA0001 (Initial Access), T1190 (Exploit Public App)

🚨 ALERT: Coordinated multi-layer attack detected!
   Attacker progressed from network scanning → web exploit → API abuse
   in 15 seconds. Automated bot behavior confirmed.

📋 RECOMMENDATIONS:
   1. IMMEDIATE: Block 203.0.113.42 in WAF
   2. INVESTIGATE: Check for data exfiltration
   3. HARDEN: Enable AWS GuardDuty
   4. FIX: Review /api/login.php for SQL injection
   5. MONITOR: Set up CloudWatch alarm for similar patterns
```

---

**Legend:**
- 🧩 Multi-Source Correlation
- 🔍 Rich Key Extraction
- 🎯 Rule Engine
- 📊 Timeline Analysis
- 🤖 AI Enhancement
- ⚡ Automated Detection
- 🚨 Critical Alert



---

## 12. When to Use Multi-Source vs Single-Source Mode

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    🎯 MODE SELECTION DECISION TREE                               │
└─────────────────────────────────────────────────────────────────────────────────┘

                              START: Bạn cần phân tích logs
                                          │
                                          ▼
                              ┌───────────────────────┐
                              │  Bạn biết chính xác   │
                              │  vấn đề ở đâu không?  │
                              └───────────┬───────────┘
                                          │
                    ┌─────────────────────┴─────────────────────┐
                    │                                           │
                    ▼ BIẾT                                      ▼ KHÔNG BIẾT
        ┌───────────────────────┐                  ┌───────────────────────┐
        │  Bạn biết log group   │                  │  Cần tìm kiếm rộng    │
        │  cụ thể có vấn đề     │                  │  để phát hiện vấn đề  │
        └───────────┬───────────┘                  └───────────┬───────────┘
                    │                                          │
                    ▼                                          ▼
        ┌───────────────────────┐                  ┌───────────────────────┐
        │  USE SINGLE-SOURCE    │                  │  USE MULTI-SOURCE     │
        │  (Advanced Mode)      │                  │  (Correlation Mode)   │
        │                       │                  │                       │
        │  ✅ Deep dive         │                  │  ✅ Discovery         │
        │  ✅ Detailed analysis │                  │  ✅ Attack detection  │
        │  ✅ Specific issue    │                  │  ✅ Root cause        │
        └───────────────────────┘                  └───────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────────┐
│                    📊 COMPARISON TABLE                                           │
└─────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────┬────────────────────────┬────────────────────────────────┐
│  Criteria            │  Single-Source Mode    │  Multi-Source Correlation      │
├──────────────────────┼────────────────────────┼────────────────────────────────┤
│  🎯 Primary Goal     │  Deep investigation    │  Attack discovery              │
│                      │  of specific source    │  across infrastructure         │
├──────────────────────┼────────────────────────┼────────────────────────────────┤
│  📁 Log Sources      │  1 log group           │  2-4 log groups                │
├──────────────────────┼────────────────────────┼────────────────────────────────┤
│  🔍 Search Term      │  REQUIRED              │  OPTIONAL                      │
│                      │  (specific keyword)    │  (auto-scan for anomalies)     │
├──────────────────────┼────────────────────────┼────────────────────────────────┤
│  ⏱️ Time Range       │  Narrow (1-2 hours)    │  Wider (1-6 hours)             │
│                      │  for focused analysis  │  for pattern detection         │
├──────────────────────┼────────────────────────┼────────────────────────────────┤
│  🧠 Analysis Depth   │  DEEP                  │  BROAD                         │
│                      │  • Every log entry     │  • Cross-source patterns       │
│                      │  • Detailed metrics    │  • Attack sequences            │
│                      │  • Temporal patterns   │  • Timeline correlation        │
├──────────────────────┼────────────────────────┼────────────────────────────────┤
│  🎯 Detection Type   │  Pattern-based         │  Sequence + Rule-based         │
│                      │  • Keyword matching    │  • Timeline analysis           │
│                      │  • Burst detection     │  • Automated bot detection     │
│                      │  • Velocity analysis   │  • MITRE ATT&CK mapping        │
├──────────────────────┼────────────────────────┼────────────────────────────────┤
│  🔗 Correlation      │  None                  │  Rich correlation keys         │
│                      │                        │  • trace_id (STRONG)           │
│                      │                        │  • request_id (MEDIUM)         │
│                      │                        │  • IP address (WEAK)           │
├──────────────────────┼────────────────────────┼────────────────────────────────┤
│  📊 Output           │  • Severity dist.      │  • Correlated events           │
│                      │  • Component dist.     │  • Attack chains               │
│                      │  • Error patterns      │  • Cross-source evidence       │
│                      │  • Attack velocity     │  • Confidence scores           │
├──────────────────────┼────────────────────────┼────────────────────────────────┤
│  💰 Cost             │  Lower                 │  Higher                        │
│                      │  (1 log group)         │  (2-4 log groups)              │
├──────────────────────┼────────────────────────┼────────────────────────────────┤
│  ⚡ Speed            │  Faster                │  Slower                        │
│                      │  (5-10 seconds)        │  (10-20 seconds)               │
├──────────────────────┼────────────────────────┼────────────────────────────────┤
│  🎓 Skill Level      │  Intermediate          │  Beginner-friendly             │
│                      │  (need to know where   │  (auto-discover issues)        │
│                      │   to look)             │                                │
└──────────────────────┴────────────────────────┴────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────────┐
│                    ✅ USE MULTI-SOURCE CORRELATION WHEN:                         │
└─────────────────────────────────────────────────────────────────────────────────┘

1️⃣  **DISCOVERY MODE - Không biết vấn đề ở đâu**
    ┌────────────────────────────────────────────────────────────────┐
    │  Scenario: "Hệ thống có vấn đề nhưng không biết root cause"   │
    │                                                                 │
    │  Example:                                                       │
    │  • User báo: "Website chậm và đôi khi bị lỗi 500"             │
    │  • Bạn không biết: Network? App? Database?                     │
    │                                                                 │
    │  Solution:                                                      │
    │  ✅ Select: VPC Flow + Application + Database                  │
    │  ✅ Search: "" (empty - auto-scan)                             │
    │  ✅ Time: Last 6 hours                                         │
    │  ✅ Result: Discover connection pool exhausted + DB slow query │
    └────────────────────────────────────────────────────────────────┘

2️⃣  **SECURITY INCIDENT - Phát hiện tấn công phức tạp**
    ┌────────────────────────────────────────────────────────────────┐
    │  Scenario: "Nghi ngờ có attacker đang thăm dò hệ thống"       │
    │                                                                 │
    │  Example:                                                       │
    │  • CloudWatch alarm: High VPC REJECT count                     │
    │  • Cần biết: Attacker làm gì sau khi bị block?                │
    │                                                                 │
    │  Solution:                                                      │
    │  ✅ Select: VPC Flow + Application + CloudTrail                │
    │  ✅ Search: "" or "REJECT"                                     │
    │  ✅ Time: Last 1 hour                                          │
    │  ✅ Result: Coordinated attack - network scan → SQL injection  │
    │            → API abuse                                         │
    └────────────────────────────────────────────────────────────────┘

3️⃣  **ROOT CAUSE ANALYSIS - Tìm nguồn gốc vấn đề**
    ┌────────────────────────────────────────────────────────────────┐
    │  Scenario: "Tại sao application bị crash?"                     │
    │                                                                 │
    │  Example:                                                       │
    │  • Application logs: "Connection timeout"                      │
    │  • Cần biết: Timeout từ đâu? Network? Database?                │
    │                                                                 │
    │  Solution:                                                      │
    │  ✅ Select: Application + Database + VPC Flow                  │
    │  ✅ Search: "timeout" or "connection"                          │
    │  ✅ Time: Last 2 hours                                         │
    │  ✅ Result: Database connection pool full → App timeout        │
    │            → Network retries                                   │
    └────────────────────────────────────────────────────────────────┘

4️⃣  **COMPLIANCE AUDIT - Kiểm tra security compliance**
    ┌────────────────────────────────────────────────────────────────┐
    │  Scenario: "Kiểm tra xem có unauthorized access không?"        │
    │                                                                 │
    │  Example:                                                       │
    │  • Security team yêu cầu audit                                 │
    │  • Cần report: Tất cả failed access attempts                   │
    │                                                                 │
    │  Solution:                                                      │
    │  ✅ Select: CloudTrail + Application + VPC Flow                │
    │  ✅ Search: "denied" or "unauthorized"                         │
    │  ✅ Time: Last 24 hours                                        │
    │  ✅ Result: Complete audit trail across all layers             │
    └────────────────────────────────────────────────────────────────┘

5️⃣  **PERFORMANCE TROUBLESHOOTING - Vấn đề performance phức tạp**
    ┌────────────────────────────────────────────────────────────────┐
    │  Scenario: "Tại sao API response time tăng đột ngột?"          │
    │                                                                 │
    │  Example:                                                       │
    │  • Monitoring: API latency tăng từ 100ms → 5s                 │
    │  • Cần biết: Bottleneck ở đâu?                                │
    │                                                                 │
    │  Solution:                                                      │
    │  ✅ Select: Application + Database + VPC Flow                  │
    │  ✅ Search: "slow" or "timeout"                                │
    │  ✅ Time: Last 3 hours                                         │
    │  ✅ Result: Slow query → Connection pool → Network congestion  │
    └────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────────┐
│                    ✅ USE SINGLE-SOURCE MODE WHEN:                               │
└─────────────────────────────────────────────────────────────────────────────────┘

1️⃣  **KNOWN ISSUE - Biết chính xác log group có vấn đề**
    ┌────────────────────────────────────────────────────────────────┐
    │  Scenario: "VPC Flow Logs có nhiều REJECT từ IP lạ"           │
    │                                                                 │
    │  Example:                                                       │
    │  • CloudWatch alarm: VPC REJECT spike                          │
    │  • Bạn biết: Vấn đề ở network layer                           │
    │                                                                 │
    │  Solution:                                                      │
    │  ✅ Select: /aws/vpc/flowlogs                                  │
    │  ✅ Search: "REJECT"                                           │
    │  ✅ Time: Last 1 hour                                          │
    │  ✅ Result: Detailed analysis of all REJECT events             │
    │            • Source IPs                                        │
    │            • Target ports                                      │
    │            • Attack velocity                                   │
    └────────────────────────────────────────────────────────────────┘

2️⃣  **SPECIFIC ERROR - Điều tra lỗi cụ thể**
    ┌────────────────────────────────────────────────────────────────┐
    │  Scenario: "Application logs có SQL injection warning"         │
    │                                                                 │
    │  Example:                                                       │
    │  • Alert: SQL injection detected in /api/login.php            │
    │  • Cần biết: Chi tiết về attack này                           │
    │                                                                 │
    │  Solution:                                                      │
    │  ✅ Select: /aws/ec2/application                               │
    │  ✅ Search: "injection" or "UNION SELECT"                      │
    │  ✅ Time: Last 30 minutes                                      │
    │  ✅ Result: Deep dive into SQL injection attempts              │
    │            • All injection payloads                            │
    │            • Attacker IP                                       │
    │            • Affected endpoints                                │
    └────────────────────────────────────────────────────────────────┘

3️⃣  **DATABASE INVESTIGATION - Phân tích database issues**
    ┌────────────────────────────────────────────────────────────────┐
    │  Scenario: "Database slow query logs tăng cao"                 │
    │                                                                 │
    │  Example:                                                       │
    │  • DBA báo: Slow query count tăng 300%                        │
    │  • Cần biết: Query nào chậm? Tại sao?                         │
    │                                                                 │
    │  Solution:                                                      │
    │  ✅ Select: /aws/rds/mysql/slowquery                           │
    │  ✅ Search: "Query_time"                                       │
    │  ✅ Time: Last 2 hours                                         │
    │  ✅ Result: Detailed slow query analysis                       │
    │            • Top slow queries                                  │
    │            • Execution times                                   │
    │            • Missing indexes                                   │
    └────────────────────────────────────────────────────────────────┘

4️⃣  **API AUDIT - Kiểm tra specific API calls**
    ┌────────────────────────────────────────────────────────────────┐
    │  Scenario: "Ai đang gọi DeleteVpc API?"                        │
    │                                                                 │
    │  Example:                                                       │
    │  • Security concern: Suspicious DeleteVpc attempts             │
    │  • Cần biết: User nào? Từ đâu? Khi nào?                       │
    │                                                                 │
    │  Solution:                                                      │
    │  ✅ Select: /aws/cloudtrail/logs                               │
    │  ✅ Search: "DeleteVpc"                                        │
    │  ✅ Time: Last 7 days                                          │
    │  ✅ Result: Complete audit of DeleteVpc calls                  │
    │            • User ARNs                                         │
    │            • Source IPs                                        │
    │            • Success/Denied status                             │
    └────────────────────────────────────────────────────────────────┘

5️⃣  **FOLLOW-UP INVESTIGATION - Sau khi đã có lead từ Multi-Source**
    ┌────────────────────────────────────────────────────────────────┐
    │  Scenario: "Multi-Source phát hiện SQL injection, cần chi tiết"│
    │                                                                 │
    │  Example:                                                       │
    │  • Multi-Source: Detected SQL injection from 203.0.113.42     │
    │  • Cần biết: Tất cả attempts từ IP này                        │
    │                                                                 │
    │  Solution:                                                      │
    │  ✅ Select: /aws/ec2/application                               │
    │  ✅ Search: "203.0.113.42"                                     │
    │  ✅ Time: Last 6 hours                                         │
    │  ✅ Result: Complete activity log of this IP                   │
    │            • All requests                                      │
    │            • Success/Failed attempts                           │
    │            • Timeline of activity                              │
    └────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────────┐
│                    🎯 RECOMMENDED WORKFLOW                                       │
└─────────────────────────────────────────────────────────────────────────────────┘

STEP 1: START WITH MULTI-SOURCE (Discovery)
┌────────────────────────────────────────────────────────────────┐
│  Goal: Phát hiện vấn đề và xác định nguồn gốc                 │
│                                                                 │
│  Settings:                                                      │
│  • Mode: Multi-Source Correlation                              │
│  • Sources: VPC Flow + Application + CloudTrail                │
│  • Search: "" (empty - auto-scan)                              │
│  • Time: Last 1-6 hours                                        │
│                                                                 │
│  Expected Output:                                               │
│  ✅ Correlated events detected                                 │
│  ✅ Attack chains identified                                   │
│  ✅ Confidence scores calculated                               │
│  ✅ Specific log groups highlighted                            │
└────────────────────────────────────────────────────────────────┘
                            │
                            ▼
STEP 2: DRILL DOWN WITH SINGLE-SOURCE (Investigation)
┌────────────────────────────────────────────────────────────────┐
│  Goal: Phân tích chi tiết log group cụ thể                     │
│                                                                 │
│  Settings:                                                      │
│  • Mode: Single-Source (Advanced)                              │
│  • Source: /aws/ec2/application (từ Step 1)                   │
│  • Search: "203.0.113.42" (IP từ Step 1)                      │
│  • Time: Same as Step 1                                        │
│                                                                 │
│  Expected Output:                                               │
│  ✅ All logs from this IP                                      │
│  ✅ Detailed attack patterns                                   │
│  ✅ Temporal analysis (burst detection)                        │
│  ✅ Specific payloads/commands                                 │
└────────────────────────────────────────────────────────────────┘
                            │
                            ▼
STEP 3: VERIFY WITH ANOTHER SINGLE-SOURCE (Confirmation)
┌────────────────────────────────────────────────────────────────┐
│  Goal: Cross-verify findings                                   │
│                                                                 │
│  Settings:                                                      │
│  • Mode: Single-Source (Advanced)                              │
│  • Source: /aws/vpc/flowlogs                                   │
│  • Search: "203.0.113.42"                                      │
│  • Time: Same as Step 1                                        │
│                                                                 │
│  Expected Output:                                               │
│  ✅ Network-level evidence                                     │
│  ✅ Connection attempts timeline                               │
│  ✅ Blocked vs Allowed traffic                                 │
└────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────────┐
│                    ⚠️ COMMON MISTAKES TO AVOID                                   │
└─────────────────────────────────────────────────────────────────────────────────┘

❌ MISTAKE 1: Using Single-Source for Unknown Issues
   Problem: "Hệ thống có vấn đề nhưng dùng Single-Source để tìm"
   Why Bad: Phải thử từng log group một → mất thời gian
   Solution: Dùng Multi-Source để discover trước

❌ MISTAKE 2: Using Multi-Source with Too Specific Search Term
   Problem: Search "sql injection" trong Multi-Source mode
   Why Bad: Miss các related events (network, API)
   Solution: Để trống hoặc dùng broad term như "error"

❌ MISTAKE 3: Using Multi-Source for Known Specific Issue
   Problem: Biết rõ VPC có vấn đề nhưng vẫn dùng Multi-Source
   Why Bad: Chậm hơn, tốn cost hơn, nhiễu hơn
   Solution: Dùng Single-Source để deep dive ngay

❌ MISTAKE 4: Too Wide Time Range in Single-Source
   Problem: Single-Source với time range 24 hours
   Why Bad: Quá nhiều logs → chậm, khó phân tích
   Solution: Narrow down time range (1-2 hours)

❌ MISTAKE 5: Not Following Up Multi-Source Results
   Problem: Chỉ xem Multi-Source results rồi dừng
   Why Bad: Miss chi tiết quan trọng
   Solution: Luôn follow up với Single-Source investigation


┌─────────────────────────────────────────────────────────────────────────────────┐
│                    💡 PRO TIPS                                                   │
└─────────────────────────────────────────────────────────────────────────────────┘

1️⃣  **Start Broad, Then Narrow**
    Multi-Source (discover) → Single-Source (investigate) → Single-Source (verify)

2️⃣  **Use Empty Search in Multi-Source**
    Let the correlation engine auto-discover anomalies

3️⃣  **Use Specific Search in Single-Source**
    Target exact IP, error message, or keyword

4️⃣  **Match Time Ranges**
    Use same time range across modes for consistency

5️⃣  **Check Correlation Strength**
    STRONG (trace_id) > MEDIUM (request_id) > WEAK (IP only)

6️⃣  **Follow Attack Chains**
    Multi-Source shows attack progression → investigate each step

7️⃣  **Export Results**
    Save Multi-Source results → use as reference for Single-Source

8️⃣  **Monitor Confidence Scores**
    High confidence (>80%) = reliable correlation
    Low confidence (<50%) = need more investigation
```

---

**Summary:**
- 🧩 **Multi-Source** = Discovery, Attack Detection, Root Cause (BROAD)
- 🔍 **Single-Source** = Investigation, Deep Dive, Specific Issue (DEEP)
- 🎯 **Best Practice** = Start Multi-Source → Drill down Single-Source


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
│  │  │   ALB    │  │   NAT    │  │   NAT    │              │   │
│  │  │  (AZ-1)  │  │ Gateway  │  │ Gateway  │              │   │
│  │  │          │  │  (AZ-1)  │  │  (AZ-2)  │              │   │
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
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘│   │
│  │                                                           │   │
│  └───────────────────────┬───────────────────────────────────┘   │
│                          │                                        │
│  ┌───────────────────────┴───────────────────────────────────┐   │
│  │ DB Subnets (10.0.7-9.0/24)                               │   │
│  │                                                           │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐              │   │
│  │  │   RDS    │  │   RDS    │  │   RDS    │              │   │
│  │  │ Primary  │  │ Standby  │  │ Standby  │              │   │
│  │  │  (AZ-1)  │  │  (AZ-2)  │  │  (AZ-3)  │              │   │
│  │  └──────────┘  └──────────┘  └──────────┘              │   │
│  │                                                           │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │ VPC Endpoints (Private)                                   │   │
│  │  • SSM Endpoint                                           │   │
│  │  • SSM Messages Endpoint                                  │   │
│  │  • EC2 Messages Endpoint                                  │   │
│  │  • S3 Gateway Endpoint                                    │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## 3. Log Flow Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Log Sources                                 │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  VPC Traffic │  │  EC2 Logs    │  │  AWS API     │
│  (Flow Logs) │  │  (CW Agent)  │  │  (CloudTrail)│
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       │                 │                 │
       ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CloudWatch Logs                               │
│                                                                   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │ /aws/vpc/        │  │ /aws/ec2/        │  │ /aws/        │  │
│  │   flowlogs       │  │   applogs        │  │   cloudtrail │  │
│  │                  │  │                  │  │   /logs      │  │
│  │ • ACCEPT traffic │  │ • System logs    │  │ • API calls  │  │
│  │ • REJECT traffic │  │ • App logs       │  │ • IAM events │  │
│  │ • Source/Dest IP │  │ • Security logs  │  │ • Errors     │  │
│  └──────────────────┘  └──────────────────┘  └──────────────┘  │
│                                                                   │
└────────────────────────────┬──────────────────────────────────────┘
                             │
                             │ Query Logs
                             ▼
                    ┌─────────────────┐
                    │  AI Log Analyzer│
                    │   (Streamlit)   │
                    └────────┬────────┘
                             │
                             │ Analyze
                             ▼
                    ┌─────────────────┐
                    │  AWS Bedrock    │
                    │  (Claude AI)    │
                    └────────┬────────┘
                             │
                             │ Root Cause
                             ▼
                    ┌─────────────────┐
                    │  Analysis       │
                    │  Results        │
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

## 6. Data Flow: Attack Detection

```
┌─────────────────────────────────────────────────────────────────┐
│                    Attack Detection Flow                         │
└─────────────────────────────────────────────────────────────────┘

Step 1: Attack Occurs
┌──────────────┐
│  Attacker    │
│  203.0.113.42│
└──────┬───────┘
       │ SSH brute force / SQL injection / Port scan
       ▼
┌──────────────┐
│  Target EC2  │
└──────┬───────┘
       │
       │ Logs generated
       ▼

Step 2: Log Collection
┌──────────────┐
│ /var/log/    │
│  secure      │
│  messages    │
│  app/*.log   │
└──────┬───────┘
       │
       │ CloudWatch Agent
       ▼
┌──────────────┐
│ CloudWatch   │
│   Logs       │
└──────┬───────┘
       │
       │ 2-3 minutes delay
       ▼

Step 3: AI Analysis
┌──────────────┐
│  Streamlit   │
│  Query logs  │
└──────┬───────┘
       │
       │ Search: "Failed password"
       ▼
┌──────────────┐
│  Pattern     │
│  Detection   │
└──────┬───────┘
       │
       │ 53 failed attempts detected
       ▼
┌──────────────┐
│  Bedrock AI  │
│  Analysis    │
└──────┬───────┘
       │
       │ Root cause inference
       ▼

Step 4: Response
┌──────────────────────────────────────┐
│  AI Output:                          │
│  • Severity: High                    │
│  • Attack Type: SSH Brute Force      │
│  • Source IP: 203.0.113.42           │
│  • Evidence: 53 failed attempts      │
│  • Recommendation: Block IP          │
│  • Command: aws ec2 authorize-sg...  │
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

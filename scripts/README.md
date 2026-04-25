# 🛠️ Helper Scripts

## 📋 Available Scripts

### 1. `ssm-connect-layer2.sh` - Connect to Layer 2 (Recommended)

Tự động connect đến Layer 2 (Log Analyzer) qua SSM Port Forwarding.

**Features:**
- ✅ Auto-detect instance ID từ Terraform output
- ✅ Verify AWS credentials
- ✅ Check SSM connectivity
- ✅ Check port availability
- ✅ Colored output với progress indicators

**Usage:**

```bash
# Default: localhost:8080
./scripts/ssm-connect-layer2.sh

# Custom port
./scripts/ssm-connect-layer2.sh 8081
```

**Output:**
```
╔════════════════════════════════════════════════════════════╗
║  AWS SSM Port Forwarding - Layer 2 (Log Analyzer)         ║
╚════════════════════════════════════════════════════════════╝

[1/5] Checking prerequisites...
✅ AWS CLI: aws-cli/2.15.0
✅ Session Manager Plugin: Installed

[2/5] Verifying AWS credentials...
✅ Authenticated as: admin
✅ Account: 123456789012

[3/5] Finding Layer 2 instance...
✅ Found instance: i-0fedcba9876543210

[4/5] Checking SSM connectivity...
✅ SSM Status: Online

[5/5] Checking local port availability...
✅ Port 8080 is available

╔════════════════════════════════════════════════════════════╗
║  Starting Port Forwarding Session                         ║
╚════════════════════════════════════════════════════════════╝

📡 Remote: i-0fedcba9876543210:80
💻 Local:  localhost:8080
🌐 Access: http://localhost:8080

⏹️  Press Ctrl+C to stop
```

---

### 2. `ssm-connect-all.sh` - Connect to All Services

Forward cả Streamlit UI (port 80) và Versus Incident (port 3000) cùng lúc.

**Usage:**

```bash
./scripts/ssm-connect-all.sh
```

**Output:**
```
╔════════════════════════════════════════════════════════════╗
║  AWS SSM Port Forwarding - All Services                   ║
╚════════════════════════════════════════════════════════════╝

Finding Layer 2 instance...
✅ Found: i-0fedcba9876543210

Starting Streamlit UI forwarding (port 8080)...
Starting Versus Incident forwarding (port 3000)...

╔════════════════════════════════════════════════════════════╗
║  Port Forwarding Active                                   ║
╚════════════════════════════════════════════════════════════╝

✅ Streamlit UI:      http://localhost:8080
✅ Versus Incident:   http://localhost:3000

📋 Logs:
   Streamlit:  tail -f /tmp/ssm-sessions/streamlit.log
   Versus:     tail -f /tmp/ssm-sessions/versus.log

⏹️  Press Ctrl+C to stop all sessions
```

---

## 🔧 Setup

### Make Scripts Executable

```bash
chmod +x scripts/*.sh
```

### Set Environment Variables (Optional)

```bash
# Add to ~/.bashrc or ~/.zshrc
export AWS_REGION="ap-southeast-1"
export TERRAFORM_DIR="./environments/dev"
```

---

## 🐛 Troubleshooting

### Script Not Found

```bash
# Make sure you're in project root
cd /path/to/AI_Log_Analysis-Project-1

# Run with relative path
./scripts/ssm-connect-layer2.sh
```

### Permission Denied

```bash
chmod +x scripts/ssm-connect-layer2.sh
```

### jq Not Found

```bash
# Ubuntu/Debian
sudo apt-get install jq

# macOS
brew install jq

# Or remove jq dependency (edit script)
# Replace:
#   AWS_ACCOUNT=$(echo $CALLER_IDENTITY | jq -r '.Account')
# With:
#   AWS_ACCOUNT=$(echo $CALLER_IDENTITY | grep -o '"Account": "[^"]*' | cut -d'"' -f4)
```

---

## 📚 Related Documentation

- [SSM Access Guide](../docs/SSM_ACCESS_GUIDE.md)
- [Quick Start](../docs/QUICK_START.md)
- [Setup Guide](../docs/SETUP_GUIDE.md)

---

**Tác giả:** AI Log Analysis System  
**Ngày:** 2026-04-24

# 🤖 AI-Powered Log Analysis System

**Streamlit-based log analyzer with AWS Bedrock AI enhancement and Telegram alerts**

## ✨ Features

- 🔍 **Multi-source log analysis** - Analyze logs from 9 CloudWatch log groups simultaneously
- 🤖 **AI-powered insights** - AWS Bedrock (Claude) for root cause analysis
- 🔗 **Cross-source correlation** - Detect attack patterns across multiple log sources
- 📱 **Telegram alerts** - Real-time security notifications
- 📊 **Interactive UI** - Streamlit-based dashboard with time range selection
- 🎯 **Smart detection** - Rule-based + AI hybrid approach

## 🏗️ Architecture

### Supported Log Groups (9 total)

**Infrastructure Logs:**
- `/aws/vpc/flowlogs` - Network traffic analysis
- `/aws/cloudtrail/logs` - API activity tracking

**Web Tier (Layer 1):**
- `/aws/ec2/web-tier/system` - System logs (messages, secure)
- `/aws/ec2/web-tier/httpd` - Apache access/error logs
- `/aws/ec2/web-tier/application` - PHP application logs

**App Tier (Layer 2):**
- `/aws/ec2/app-tier/system` - System logs
- `/aws/ec2/app-tier/streamlit` - Streamlit application logs

**Database:**
- `/aws/rds/mysql/error` - MySQL error logs
- `/aws/rds/mysql/slowquery` - Slow query logs

## 🚀 Quick Start

### 1. Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
nano .env  # Edit with your settings
```

### 2. Configuration

Edit `.env` file:

```bash
# AWS Configuration
AWS_REGION=ap-southeast-1
AWS_PROFILE=default

# Telegram Bot (RECOMMENDED)
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
TELEGRAM_ALERTS_ENABLED=true

# Bedrock Model
BEDROCK_MODEL=anthropic.claude-3-haiku-20240307-v1:0
```

### 3. Run Application

```bash
# Local development
streamlit run streamlit_app.py

# Production (Docker)
docker build -t log-analyzer .
docker run -p 8501:8501 --env-file .env log-analyzer
```

### 4. Access

Open browser: `http://localhost:8501`

## 📊 Usage

### Basic Analysis

1. **Select Log Groups** - Choose from 9 available sources (all selected by default)
2. **Set Time Range** - Pick start/end date and time
3. **Optional Search** - Enter keywords or leave blank for auto-scan
4. **Enable AI** - Toggle AI enhancement for deeper insights
5. **Analyze** - Click "Analyze Logs" button

### Advanced Features

**Cross-source Correlation:**
- Automatically enabled when 2+ log groups selected
- Detects attack patterns across multiple sources
- Uses correlation rules from `correlation_rules.json`

**AI Analysis:**
- Global Root Cause Analysis (1 comprehensive AI call)
- 5 Why Analysis for deep root cause
- Control Gap identification
- MITRE ATT&CK mapping
- Immediate action recommendations

**Telegram Alerts:**
- Automatic alerts when attacks detected
- Rich formatting with severity, confidence, evidence
- Direct Telegram API (no middleware needed)

## 🔧 Configuration Files

### correlation_rules.json

Define custom correlation rules:

```json
{
  "rules": [
    {
      "name": "SQL Injection Attack",
      "description": "Detect SQL injection attempts",
      "conditions": [
        {
          "source": "/aws/ec2/web-tier/httpd",
          "pattern": "(?i)(union|select|insert|update|delete|drop).*from"
        },
        {
          "source": "/aws/rds/mysql/error",
          "pattern": "(?i)syntax error"
        }
      ],
      "severity": "Critical",
      "time_window_seconds": 300
    }
  ]
}
```

### CloudWatch Agent Config

See `ansible/templates/cloudwatch_agent_config_*.json.j2` for agent configuration.

## 🧪 Testing

### Test Telegram Bot

```bash
python3 test_telegram.py
```

### Generate Test Logs

```bash
python3 generate_omni_logs.py
```

### Debug Correlator

```bash
python3 debug_correlator.py
```

## 📦 Project Structure

```
bedrock-log-analyzer-ui/
├── streamlit_app.py              # Main Streamlit application
├── src/
│   ├── advanced_correlator.py    # Cross-source correlation engine
│   ├── bedrock_enhancer.py       # AWS Bedrock AI integration
│   ├── log_parser.py             # Log parsing and normalization
│   ├── log_preprocessor.py       # Event abstraction layer
│   ├── pattern_analyzer.py       # Pattern detection and clustering
│   ├── rule_detector.py          # Rule-based detection
│   ├── telegram_notifier.py      # Telegram alert sender
│   └── models.py                 # Data models
├── correlation_rules.json        # Correlation rule definitions
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Container image
└── .env.example                  # Environment template
```

## 🔐 Security

### IAM Permissions Required

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams",
        "logs:GetLogEvents"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "*"
    }
  ]
}
```

### Telegram Bot Setup

1. Create bot with `@BotFather` on Telegram
2. Get `BOT_TOKEN`
3. Send message to your bot
4. Get `CHAT_ID` from: `https://api.telegram.org/bot<BOT_TOKEN>/getUpdates`
5. Add to `.env` file

## 🐛 Troubleshooting

### No logs appearing

```bash
# Check CloudWatch Agent
sudo systemctl status amazon-cloudwatch-agent

# Restart agent
sudo systemctl restart amazon-cloudwatch-agent

# View agent logs
sudo tail -f /opt/aws/amazon-cloudwatch-agent/logs/amazon-cloudwatch-agent.log
```

### Bedrock errors

```bash
# Check model availability
aws bedrock list-foundation-models --region ap-southeast-1

# Test model access
aws bedrock invoke-model \
    --model-id anthropic.claude-3-haiku-20240307-v1:0 \
    --body '{"prompt":"Hello","max_tokens":100}' \
    --region ap-southeast-1 \
    output.json
```

### Telegram not working

```bash
# Test bot manually
curl -X POST "https://api.telegram.org/bot<BOT_TOKEN>/sendMessage" \
    -d "chat_id=<CHAT_ID>&text=Test message"

# Run test script
python3 test_telegram.py
```

## 📈 Performance

- **Log retrieval**: ~2-5 seconds per log group
- **Pattern analysis**: ~1-3 seconds for 10k logs
- **AI analysis**: ~5-10 seconds (1 API call)
- **Total**: ~15-30 seconds for full analysis

## 💰 Cost Estimation

**AWS Bedrock (Claude Haiku):**
- Input: $0.00025 per 1K tokens
- Output: $0.00125 per 1K tokens
- Typical analysis: ~$0.01-0.05 per run

**CloudWatch Logs:**
- Ingestion: $0.50 per GB
- Storage: $0.03 per GB/month
- Typical: ~$5-10 per month

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- AWS Bedrock for AI capabilities
- Streamlit for UI framework
- Claude AI for analysis engine

---

**Built with ❤️ for security operations teams**

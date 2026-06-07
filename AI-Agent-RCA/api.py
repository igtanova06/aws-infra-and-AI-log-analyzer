import os
import sys
import json
import logging
from datetime import datetime, timedelta
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# Load env vars
load_dotenv()

# Import schemas and graph
from schemas import AgentState
from graph import INVESTIGATION_GRAPH

# Import local elements
from incident_store import IncidentStore
from src.telegram_notifier import TelegramNotifier

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AIOps RCA Agent Webhook Service",
    description="Receives CloudWatch Alarms and triggers LangGraph RCA investigation loops.",
    version="1.0.0"
)


# Helper classes to prevent attribute crashes in TelegramNotifier
class TimelineEntryWrapper:
    def __init__(self, timestamp: str, source: str, message: str):
        self.timestamp = timestamp
        self.source = source
        self.message = message


class CorrelatedEventWrapper:
    def __init__(self, rule_name: str, confidence: float, reason: str, findings: list):
        self.correlation_keys = {"source_ip": "AWS Alarm Trigger"}
        self.timeline = [
            TimelineEntryWrapper(
                f.get("timestamp") or datetime.utcnow().isoformat(),
                f.get("datasource") or "Tool",
                f.get("finding") or ""
            )
            for f in findings
        ]


def run_investigation_background(alarm_data: dict):
    """Executes the investigation graph, writes outcome to IncidentStore, and notifies Telegram."""
    logger.info("Starting background investigation for alarm...")
    try:
        # 1. Initialize State
        state = AgentState(alert=alarm_data)
        
        # 2. Run the graph
        final_state = INVESTIGATION_GRAPH.invoke(state)
        logger.info(f"LangGraph execution finished. Loop count: {final_state.current_iteration_count}, Validations: {final_state.validation_count}")
        
        # 3. Format and save to incident store
        batch_id = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        status = "incident" if final_state.validation_count > 0 else "clean"
        
        # Extract active sources
        sources = list(set(
            step.get("datasource") 
            for inv in final_state.investigation_history 
            if isinstance(inv, dict)
            for step in inv.get("investigate_findings_from_tool_results", [])
        ))
        if not sources:
            sources = ["CloudWatch"]
            
        signals = [f.model_dump() for f in final_state.initial_findings]
        
        # Convert history for storage
        correlated_events_summary = [
            {
                "rule_name": inv.get("hypothesis", {}).get("fingerprint", {}).get("category", "Unknown") if isinstance(inv, dict) else "Unknown",
                "confidence_score": inv.get("hypothesis_conclusion", {}).get("confidence", 0.0) if isinstance(inv, dict) else 0.0,
                "description": inv.get("hypothesis_conclusion", {}).get("reason", "N/A") if isinstance(inv, dict) else "N/A"
            }
            for inv in final_state.investigation_history
        ]
        
        store = IncidentStore()
        store.save_incident(
            batch_id=batch_id,
            time_range={
                "start": (datetime.utcnow() - timedelta(minutes=5)).isoformat() + "Z",
                "end": (datetime.utcnow() + timedelta(minutes=5)).isoformat() + "Z"
            },
            status=status,
            total_logs=100,
            sources=sources,
            signals=signals,
            correlated_events_summary=correlated_events_summary,
            global_rca=final_state.final_rca,
            telegram_sent=False,
            cost={"tokens": 0, "usd": 0.0}
        )
        
        # 4. Trigger Telegram notifications if rca generated
        if final_state.final_rca:
            notifier = TelegramNotifier()
            
            wrapped_events = []
            for inv in final_state.investigation_history:
                if isinstance(inv, dict):
                    hyp = inv.get("hypothesis", {})
                    conc = inv.get("hypothesis_conclusion", {})
                    findings = inv.get("investigate_findings_from_tool_results", [])
                    
                    wrapped_events.append(
                        CorrelatedEventWrapper(
                            hyp.get("fingerprint", {}).get("category", "Unknown"),
                            conc.get("confidence", 0.0),
                            conc.get("reason", ""),
                            findings
                        )
                    )
            
            metadata = {
                "time_range": f"Last 10 minutes",
                "total_logs": 100
            }
            
            logger.info("Sending attack alert to Telegram...")
            telegram_sent = notifier.send_attack_alert(
                global_rca=final_state.final_rca,
                correlated_events=wrapped_events,
                analysis_metadata=metadata
            )
            
            # Re-save with updated telegram status if successful
            if telegram_sent:
                store.save_incident(
                    batch_id=batch_id,
                    time_range={
                        "start": (datetime.utcnow() - timedelta(minutes=5)).isoformat() + "Z",
                        "end": (datetime.utcnow() + timedelta(minutes=5)).isoformat() + "Z"
                    },
                    status=status,
                    total_logs=100,
                    sources=sources,
                    signals=signals,
                    correlated_events_summary=correlated_events_summary,
                    global_rca=final_state.final_rca,
                    telegram_sent=True,
                    cost={"tokens": 0, "usd": 0.0}
                )
                logger.info("Telegram notification sent and saved.")
                
    except Exception as e:
        logger.error(f"Error running background investigation: {str(e)}", exc_info=True)


@app.post("/webhook/cloudwatch")
async def receive_cloudwatch_alert(request: Request, background_tasks: BackgroundTasks):
    """
    Webhook receiving real-time payloads from CloudWatch Alarms via SNS.
    Automatically confirms SNS subscriptions.
    """
    try:
        body_bytes = await request.body()
        body = json.loads(body_bytes.decode("utf-8"))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON payload: {str(e)}")
        
    # Handle SNS Subscription Confirmation
    if body.get("Type") == "SubscriptionConfirmation":
        subscribe_url = body.get("SubscribeURL")
        if subscribe_url:
            logger.info(f"SNS Subscription Confirmation URL received: {subscribe_url}")
            try:
                import requests
                requests.get(subscribe_url, timeout=10)
                logger.info("SNS Subscription successfully confirmed.")
                return JSONResponse(content={"status": "confirmed"})
            except Exception as ex:
                logger.error(f"Failed to confirm subscription: {str(ex)}")
                raise HTTPException(status_code=500, detail="Failed to confirm SNS subscription")
                
    # Handle normal Alarm Notification
    if body.get("Type") == "Notification":
        message_str = body.get("Message", "{}")
        try:
            alarm_data = json.loads(message_str)
        except Exception:
            alarm_data = {"raw_message": message_str}
            
        logger.info(f"Received CloudWatch Alarm Notification: {alarm_data.get('AlarmName', 'Unnamed Alarm')}")
        background_tasks.add_task(run_investigation_background, alarm_data)
        return {"status": "processing", "message": "Investigation started in background."}
        
    # Support direct JSON alarm triggers (e.g. for testing)
    logger.info("Received direct JSON trigger payload.")
    background_tasks.add_task(run_investigation_background, body)
    return {"status": "processing", "message": "Investigation started in background."}


@app.get("/api/status")
async def get_service_status():
    """Returns the API service health status."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat() + "Z"}


@app.post("/api/test-alert")
async def trigger_test_alert(background_tasks: BackgroundTasks):
    """Manually triggers a mock incident security alert to test the full pipeline."""
    mock_alarm = {
        "AlarmName": "Mock-SQL-Injection-Alert",
        "NewStateValue": "ALARM",
        "StateChangeTime": datetime.utcnow().isoformat() + "Z",
        "Reason": "Threshold Crossed: 1 datapoint [10.0] was greater than or equal to threshold [1.0]."
    }
    background_tasks.add_task(run_investigation_background, mock_alarm)
    return {"status": "processing", "message": "Test investigation started."}

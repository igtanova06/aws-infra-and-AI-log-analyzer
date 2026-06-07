import asyncio
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from schemas import AgentState
from graph import INVESTIGATION_GRAPH


async def test_rca_agent():
    """Manual on-demand command-line execution for the AI-Agent-RCA."""
    
    # Mock SNS Alarm payload representing a SQL Injection attempt
    mock_alarm = {
        "AlarmName": "SQL-Injection-Detected",
        "NewStateValue": "ALARM",
        "StateChangeTime": datetime.utcnow().isoformat() + "Z",
        "Reason": "Threshold Crossed: 1 datapoint [10.0] was greater than or equal to threshold [1.0]."
    }

    print("="*80)
    print("STARTING AI-AGENT-RCA INVESTIGATION LOOP")
    print("="*80)
    
    initial_state = AgentState(alert=mock_alarm)
    
    try:
        final_state = await INVESTIGATION_GRAPH.ainvoke(initial_state)
        
        print("\n" + "="*80)
        print("INVESTIGATION COMPLETE - FINAL ROOT CAUSE REPORT")
        print("="*80)
        
        rca_report = final_state.final_rca
        if rca_report:
            print(f"Severity: {rca_report.get('threat_assessment', {}).get('severity')}")
            print(f"Confidence: {rca_report.get('threat_assessment', {}).get('confidence')}")
            print(f"Root Cause Statement: {rca_report.get('root_cause')}")
            print("\nAttack Narrative:")
            print(rca_report.get('attack_narrative'))
            print("\nImmediate Isolation Actions:")
            for action in rca_report.get('immediate_actions', []):
                print(f"- {action.get('action')}: {action.get('command')}")
        else:
            print("No RCA report compiled.")
            if final_state.error:
                print(f"Error: {final_state.error}")
                
    except Exception as e:
        print(f"Execution failed: {str(e)}")


if __name__ == "__main__":
    asyncio.run(test_rca_agent())

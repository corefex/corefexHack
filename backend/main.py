"""
backend/main.py
Servidor FastAPI que orquesta el grafo de LangGraph, expone herramientas MCP
y gestiona la reanudacion de la compuerta humana (Human-in-the-Loop).
"""

import uuid
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.workflow import app_graph, CentralContract
from backend.tools.mcp_tools import MCP_TOOLS_MANIFEST, MCPToolRegistry

app = FastAPI(
    title="TESTIGO Multi-Agent & MCP Execution Engine",
    version="1.0.0",
    description="Backend para orquestacion de agentes LangGraph con herramientas MCP y protocolo AG-UI"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class WorkflowRunRequest(BaseModel):
    user_intent: str
    thread_id: Optional[str] = None
    mock_mode: bool = True

class HumanApprovalRequest(BaseModel):
    thread_id: str
    approved: bool
    user_notes: Optional[str] = "Accion aprobada por el operador."

@app.get("/api/mcp/tools")
async def list_mcp_tools():
    return {"tools": MCP_TOOLS_MANIFEST}

@app.post("/api/workflow/run")
async def start_workflow(req: WorkflowRunRequest):
    thread_id = req.thread_id or f"session-{uuid.uuid4().hex[:8]}"
    config = {"configurable": {"thread_id": thread_id}}

    initial_contract = CentralContract().model_dump()
    state_input = {
        "contract": initial_contract,
        "user_intent": req.user_intent,
        "current_task_id": None,
        "iteration_count": 0,
        "max_iterations": 3,
        "error_log": None,
        "mock_mode": req.mock_mode,
    }

    for _ in app_graph.stream(state_input, config=config):
        pass

    snapshot = app_graph.get_state(config)
    contract_state = snapshot.values.get("contract", {})

    return {
        "thread_id": thread_id,
        "next_step": snapshot.next,
        "status": contract_state.get("status"),
        "active_view": contract_state.get("ui_state_sync", {}).get("active_view"),
        "logs": contract_state.get("ui_state_sync", {}).get("logs", [])
    }

@app.post("/api/workflow/resume-approval")
async def resume_human_approval(req: HumanApprovalRequest):
    config = {"configurable": {"thread_id": req.thread_id}}
    snapshot = app_graph.get_state(config)

    if not snapshot.next or "human_gate" not in snapshot.next:
        raise HTTPException(
            status_code=400,
            detail="El grafo no se encuentra suspendido en la compuerta humana ('human_gate')."
        )

    current_contract = snapshot.values.get("contract", {})
    current_contract["guardrails"]["human_approval_receipt"] = {
        "approved": req.approved,
        "approved_by": "Operator_Interactive",
        "notes": req.user_notes,
        "approval_token": str(uuid.uuid4())
    }

    if req.approved:
        current_contract["status"] = "completed"
        action_result = MCPToolRegistry.execute_action_tool(
            action_type="write_disk",
            payload={"target": "src/backend/service.py"},
            has_human_approval=True
        )
        current_contract["ui_state_sync"]["logs"].append({
            "agent": "SecurityGate",
            "message": f"Accion aprobada. MCP ejecuto: {action_result['status']}",
            "timestamp": "2026-10-30T15:30:00Z"
        })
    else:
        current_contract["status"] = "failed"
        current_contract["ui_state_sync"]["logs"].append({
            "agent": "SecurityGate",
            "message": "Operador rechazo la ejecucion. Tarea abortada.",
            "timestamp": "2026-10-30T15:30:00Z"
        })

    app_graph.update_state(config, {"contract": current_contract})
    for _ in app_graph.stream(None, config=config):
        pass

    final_snapshot = app_graph.get_state(config)
    return {
        "status": final_snapshot.values.get("contract", {}).get("status"),
        "contract": final_snapshot.values.get("contract")
    }

@app.get("/health")
async def health_check():
    return {"status": "ok", "engine": "LangGraph + MCP Tools"}

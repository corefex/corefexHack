"""
backend/workflow.py
Implementacion del Grafo de Estados Multiagente con LangGraph.
Sigue el Metodo HACK-AGENT: Orquestador Central -> Creador -> Evaluador (Ralph Loop) -> Human Gate.
"""

from __future__ import annotations
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Literal, TypedDict
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

class TaskItem(BaseModel):
    task_id: str
    owner: Literal["orchestrator", "investigator_agent", "creator_agent", "evaluator_judge", "human"]
    description: str
    status: Literal["pending", "in_progress", "done", "blocked"] = "pending"
    dependencies: List[str] = Field(default_factory=list)
    output_payload: Dict[str, Any] = Field(default_factory=dict)

class GuardrailsConfig(BaseModel):
    tool_permissions: Dict[str, List[str]] = Field(default_factory=lambda: {
        "read_access": ["vector_search", "inspect_contract"],
        "write_access": ["buffer_code", "stage_file"],
        "action_access": ["deploy_service", "apply_action", "write_disk"]
    })
    require_human_confirmation: bool = True
    human_approval_receipt: Dict[str, Any] = Field(default_factory=dict)

class CentralContract(BaseModel):
    project_id: str = "HACK-AGENT-DEMO"
    execution_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: Literal["idle", "planning", "running", "awaiting_human_approval", "completed", "failed"] = "idle"
    tasks: List[TaskItem] = Field(default_factory=list)
    guardrails: GuardrailsConfig = Field(default_factory=GuardrailsConfig)
    ui_state_sync: Dict[str, Any] = Field(default_factory=lambda: {
        "active_view": "dashboard",
        "logs": []
    })

class AgentGraphState(TypedDict):
    contract: Dict[str, Any]
    user_intent: str
    current_task_id: Optional[str]
    iteration_count: int
    max_iterations: int
    error_log: Optional[str]
    mock_mode: bool

def orchestrator_node(state: AgentGraphState) -> Dict[str, Any]:
    contract_data = state["contract"]
    user_intent = state["user_intent"]
    logs = contract_data.get("ui_state_sync", {}).get("logs", [])
    logs.append({
        "agent": "Orchestrator",
        "message": f"Analizando intencion: '{user_intent}'. Desglosando en tablero Kanban...",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    tasks = contract_data.get("tasks", [])
    if not tasks:
        task_code = TaskItem(
            task_id="TASK-01",
            owner="creator_agent",
            description=f"Implementar componente de produccion para: '{user_intent}'",
            status="in_progress"
        )
        task_review = TaskItem(
            task_id="TASK-02",
            owner="evaluator_judge",
            description="Validar especificacion SDD y pruebas unitarias de TASK-01",
            status="pending",
            dependencies=["TASK-01"]
        )
        tasks = [task_code.model_dump(), task_review.model_dump()]
        active_task = "TASK-01"
    else:
        active_task = state.get("current_task_id")
        
    contract_data["status"] = "running"
    contract_data["tasks"] = tasks
    contract_data["ui_state_sync"]["active_view"] = "timeline_logs"
    contract_data["ui_state_sync"]["logs"] = logs
    
    return {
        "contract": contract_data,
        "current_task_id": active_task
    }

def creator_agent_node(state: AgentGraphState) -> Dict[str, Any]:
    contract_data = state["contract"]
    task_id = state.get("current_task_id")
    iteration = state.get("iteration_count", 0)
    logs = contract_data.get("ui_state_sync", {}).get("logs", [])
    
    if iteration == 0 and not state.get("error_log"):
        code_artifact = {
            "filename": "src/backend/service.py",
            "code": "# Implementation draft\ndef execute():\n    return {'status': 200}",
            "typecheck": "ERROR: Missing explicit Pydantic return model schema"
        }
        summary = "Codigo preliminar generado. Pendiente de tipado estricto."
    else:
        code_artifact = {
            "filename": "src/backend/service.py",
            "code": "from pydantic import BaseModel\n\nclass ResponseModel(BaseModel):\n    status: int\n    message: str\n\ndef execute() -> ResponseModel:\n    return ResponseModel(status=200, message='Execution successful')\n",
            "typecheck": "PASSED (0 errors, strict typing compliant)"
        }
        summary = "Codigo corregido y validado con Pydantic v2."

    for t in contract_data.get("tasks", []):
        if t["task_id"] == task_id:
            t["status"] = "in_progress"
            t["output_payload"] = {
                "summary": summary,
                "data": code_artifact,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
    logs.append({
        "agent": "CreatorAgent",
        "message": f"Iteracion {iteration + 1}: Artefacto de codigo generado en {code_artifact['filename']}",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    contract_data["ui_state_sync"]["logs"] = logs
    
    return {
        "contract": contract_data,
        "iteration_count": iteration + 1
    }

def evaluator_judge_node(state: AgentGraphState) -> Dict[str, Any]:
    contract_data = state["contract"]
    task_id = state.get("current_task_id")
    logs = contract_data.get("ui_state_sync", {}).get("logs", [])
    
    target_task = next((t for t in contract_data["tasks"] if t["task_id"] == task_id), None)
    payload = target_task.get("output_payload", {}) if target_task else {}
    typecheck = payload.get("data", {}).get("typecheck", "")
    
    validation_passed = "PASSED" in typecheck
    
    if validation_passed:
        if target_task:
            target_task["status"] = "done"
            target_task["output_payload"]["validation_passed"] = True
            target_task["output_payload"]["critique_notes"] = "Aprobado: Cero errores de tipado, contratos Pydantic respetados."
        
        logs.append({
            "agent": "EvaluatorJudge",
            "message": "[Ralph Loop]: APROBADO. Criterios de aceptacion cumplidos al 100%.",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        error_msg = None
    else:
        logs.append({
            "agent": "EvaluatorJudge",
            "message": f"[Ralph Loop]: RECHAZADO. Fallo detectado: {typecheck}. Ordenando auto-correccion inmediata...",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        error_msg = typecheck
        if target_task:
            target_task["output_payload"]["validation_passed"] = False
            target_task["output_payload"]["critique_notes"] = typecheck
            
    contract_data["ui_state_sync"]["logs"] = logs
    
    return {
        "contract": contract_data,
        "error_log": error_msg
    }

def human_approval_gate_node(state: AgentGraphState) -> Dict[str, Any]:
    contract_data = state["contract"]
    logs = contract_data.get("ui_state_sync", {}).get("logs", [])
    
    contract_data["status"] = "awaiting_human_approval"
    contract_data["ui_state_sync"]["active_view"] = "approval_gate"
    
    logs.append({
        "agent": "SecurityGate",
        "message": "Accion critica detectada. Esperando confirmacion interactiva en CopilotKit UI...",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    contract_data["ui_state_sync"]["logs"] = logs
    
    return {
        "contract": contract_data
    }

def should_continue_ralph_loop(state: AgentGraphState) -> Literal["creator_agent", "human_gate", "finalize_failed"]:
    error = state.get("error_log")
    iteration = state.get("iteration_count", 0)
    max_iter = state.get("max_iterations", 3)
    
    if error:
        if iteration < max_iter:
            return "creator_agent"
        return "finalize_failed"
    
    guardrails = state["contract"].get("guardrails", {})
    if guardrails.get("require_human_confirmation", True):
        return "human_gate"
        
    return "human_gate"

def build_hackagent_graph() -> StateGraph:
    workflow = StateGraph(AgentGraphState)
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("creator_agent", creator_agent_node)
    workflow.add_node("evaluator_judge", evaluator_judge_node)
    workflow.add_node("human_gate", human_approval_gate_node)

    workflow.add_edge(START, "orchestrator")
    workflow.add_edge("orchestrator", "creator_agent")
    workflow.add_edge("creator_agent", "evaluator_judge")

    workflow.add_conditional_edges(
        "evaluator_judge",
        should_continue_ralph_loop,
        {
            "creator_agent": "creator_agent",
            "human_gate": "human_gate",
            "finalize_failed": END
        }
    )
    workflow.add_edge("human_gate", END)
    return workflow

checkpointer = MemorySaver()
app_graph = build_hackagent_graph().compile(
    checkpointer=checkpointer,
    interrupt_before=["human_gate"]
)

if __name__ == "__main__":
    initial_contract = CentralContract(project_id="HACK-2026-TEST").model_dump()
    initial_state: AgentGraphState = {
        "contract": initial_contract,
        "user_intent": "Generar microservicio de verificacion con esquema Pydantic",
        "current_task_id": None,
        "iteration_count": 0,
        "max_iterations": 3,
        "error_log": None,
        "mock_mode": True
    }
    thread_config = {"configurable": {"thread_id": "session-demo-01"}}
    print("=== INICIANDO GRAFO MULTIAGENTE (HACK-AGENT WORKFLOW) ===")
    for event in app_graph.stream(initial_state, config=thread_config):
        for node_name, output in event.items():
            print(f"[Nodo Completado]: {node_name}")
            logs = output.get("contract", {}).get("ui_state_sync", {}).get("logs", [])
            if logs:
                print(f"  > Evento UI: {logs[-1]['message']}")
    
    snapshot = app_graph.get_state(thread_config)
    print(f"\n[ESTADO SUSPENDIDO EN]: {snapshot.next}")
    print(f"Estado del Contrato: {snapshot.values['contract']['status']}")

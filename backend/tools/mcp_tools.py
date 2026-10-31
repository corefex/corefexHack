"""
backend/tools/mcp_tools.py
Servidor y catalogo de herramientas bajo el estandar Model Context Protocol (MCP).
Alineado con las barandas de seguridad (Leer / Redactar / Actuar).
"""

from __future__ import annotations
import os
from typing import Dict, Any, List
from pydantic import BaseModel, Field

class ReadFileInput(BaseModel):
    filepath: str = Field(description="Ruta relativa del archivo a leer dentro de los boundaries")

class BufferCodeInput(BaseModel):
    filename: str = Field(description="Ruta destino del archivo")
    content: str = Field(description="Codigo fuente a almacenar en el buffer de staging")

class ExecuteActionInput(BaseModel):
    action_type: str = Field(description="Tipo de accion critica (deploy | write_disk)")
    payload: Dict[str, Any] = Field(description="Parametros requeridos para ejecutar la accion")

class MCPToolRegistry:
    @staticmethod
    def read_spec_tool(filepath: str, mock_mode: bool = True) -> Dict[str, Any]:
        if mock_mode:
            return {
                "status": "success",
                "filepath": filepath,
                "content": "# MOCK SPEC CONTENT\nProject: TESTIGO\nFeatures: [Auth, Consensus, Verification]"
            }
        if not os.path.exists(filepath):
            return {"status": "error", "message": f"Archivo '{filepath}' no encontrado"}
        with open(filepath, "r", encoding="utf-8") as f:
            return {"status": "success", "filepath": filepath, "content": f.read()}

    @staticmethod
    def buffer_code_tool(filename: str, content: str) -> Dict[str, Any]:
        return {
            "status": "staged",
            "filename": filename,
            "bytes_buffered": len(content.encode("utf-8")),
            "ready_for_review": True
        }

    @staticmethod
    def execute_action_tool(action_type: str, payload: Dict[str, Any], has_human_approval: bool) -> Dict[str, Any]:
        if not has_human_approval:
            return {
                "status": "blocked",
                "error": "SECURITY_VIOLATION: Accion de tipo 'action_access' bloqueada sin aprobacion humana."
            }
        return {
            "status": "executed",
            "action": action_type,
            "details": payload,
            "timestamp": "2026-10-30T15:30:00Z"
        }

MCP_TOOLS_MANIFEST = [
    {
        "name": "mcp_read_spec",
        "description": "Lee el plan.md o archivos de configuracion permitidos",
        "category": "read_access",
        "parameters": ReadFileInput.model_json_schema()
    },
    {
        "name": "mcp_buffer_code",
        "description": "Coloca codigo generado en staging para validacion del Ralph Loop",
        "category": "write_access",
        "parameters": BufferCodeInput.model_json_schema()
    },
    {
        "name": "mcp_execute_action",
        "description": "Aplica cambios a disco o ejecuta despliegues (requiere compuerta humana)",
        "category": "action_access",
        "parameters": ExecuteActionInput.model_json_schema()
    }
]

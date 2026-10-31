# SPECIFICATION & ARCHITECTURAL PLAN (HACK-AGENT)
Archivo: cloud/plan.md

## 1. Executive Summary & Problem Intent
* **Problema Raiz**: En flujos operativos criticos, los LLMs monoliticos sufren alucinaciones, rompen esquemas tipados y ejecutan acciones sin verificacion de consenso.
* **Usuario Objetivo**: Operadores y auditores de procesos tecnicos.
* **Propuesta de Valor (ROI)**: Reduccion del 80% en reprocesos manuales y eliminacion de ejecuciones no autorizadas.
* **Arquitectura de Ejecucion**: Orquestador Central con Contrato Central unificado y 3 especialistas (Investigador, Creador, Juez Evaluador).

---

## 2. Scope Lock Decisions (Decisiones Congeladas de Alcance)
* [x] Stack Frontend: React / Next.js con componentes interactivos y Generative UI (CopilotKit / AG-UI).
* [x] Stack Backend: Python 3.12 con FastAPI y LangGraph.
* [x] Contrato de Intercambio: JSON Schema estricto validado via Pydantic (cloud/contract.json).
* [x] Aislamiento de Fallos (Mock Mode): Modo contingencia en memoria para estabilidad sin conexion externa.

---

## 3. Strict Module Boundaries (Fronteras de Carpetas y Permisos)
* Orquestador (/src/orchestrator): Desglose de tareas y gestion de estado global. Prohibido escribir codigo directo.
* Frontend (/src/frontend): Vistas, estados y renderizado interactivo. Prohibido alterar backend o contratos.
* Backend (/src/backend): Endpoints REST/SSE y grafo de ejecucion. Prohibido modificar vistas.
* Safety & Guardrails (/src/safety): Matriz de permisos (Leer / Redactar / Actuar). Compuerta humana (Human-in-the-Loop) obligatoria para acciones fisicas.

---

## 4. Architectural Decision Records (ADR)
* ADR-001: Orquestador Central y Contrato Central Tipado
  - Estatus: Aceptado.
  - Contexto: Evitar bucles infinitos y saturacion de ventana de contexto.
  - Decision: Canalizar el estado compartido mediante contrato JSON inmutable.
  - Consecuencia: Cero reprocesos de integracion y trazabilidad total.

---

## 5. Delta de Capacidades (Criterios de Aceptacion)
* CAP-01: El usuario ingresa la intencion; el Orquestador clasifica y asigna tareas en el tablero.
* CAP-02: Los especialistas generan codigo y artefactos dentro de sus boundaries.
* CAP-03: El agente critico evalua contra criterios tecnicos; si detecta error, ordena bucle Ralph Loop automatico.
* CAP-04: Acciones criticas suspenden el grafo en memoria hasta recibir aprobacion interactiva.

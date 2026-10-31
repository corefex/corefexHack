# TESTIGO: Multi-Agent Consensus & Continuous Verification Architecture

> **Alineado con el Metodo HACK-AGENT | Spec-Driven Development (SDD) & Ralph Loops**  
> *Reduccion del 80% en reprocesos manuales y eliminacion del riesgo de ejecuciones no autorizadas en flujos de IA.*

---

## Executive Brief (Lectura de 30 Segundos para Jurados)

* **El Problema Real**: En procesos operativos criticos, los LLMs monoliticos alucinan, rompen esquemas tipados y carecen de barandas fisicas, ejecutando acciones externas irreversibles sin autorizacion demostrable.
* **Nuestra Solucion**: Un sistema multiagente determinista coordinado por una maquina de estados en **LangGraph**, respaldado por un **Contrato Central inmutable en JSON**, un bucle adversarial de autorrecuperacion en caliente (**Ralph Loop**) y una compuerta obligatoria de aprobacion humana (**Human-in-the-Loop**).
* **El "Aha! Moment" en la Demo**: Si el agente creador genera codigo con inconsistencias de tipado, el **Juez Evaluador detecta el fallo automaticamente, suspende la emision y fuerza la autorreparacion del codigo en milisegundos** antes de notificar al usuario.

---

## Arquitectura del Sistema (Supervisor-Ejecutores)

A diferencia de los asistentes conversacionales convencionales, el estado y el historial se gestionan fuera de la ventana de contexto mediante un **tablero tipado de tareas** para garantizar cero desperdicio de tokens y prevenir colisiones entre agentes:

```
                  +-------------------------------+
                  |      Entrada de Usuario       |
                  +---------------+---------------+
                                  |
                                  v
                  +-------------------------------+
                  |    ORCHESTRATOR SUPERVISOR    |
                  |  (Gobierna cloud/contract.json)|
                  +---------------+---------------+
                                  | Desglosa y asigna tarea
                                  v
                  +-------------------------------+
                  |         CREATOR AGENT         |
                  | (Ejecuta en /src/ Boundaries) |
                  +---------------+---------------+
                                  | Emite output_payload
                                  v
    +----------------> +---------------------------+
    |                 |   EVALUATOR JUDGE NODE    |
    |  Reintento      |    (Bucle Ralph Loop)     |
    |  Autonomo       +-----------+---------------+
    | (Max 3 ciclos)              |
    +---- Fallo / Tipado Roto ----+ Aprobado (PASSED)
                                  v
                      +---------------------------+
                      |    HUMAN SECURITY GATE    | <--- Interrupt en memoria
                      | (Aprobacion interactiva)  |
                      +-----------+---------------+
                                  | [Usuario autoriza accion]
                                  v
                      +---------------------------+
                      |   COMPLETED & UI SYNC     |
                      +---------------------------+
```

### Roles y Limites Estrictos de Modulos (Boundaries)

| Agente | Directorio / Boundary | Responsabilidad Operativa | Barandas y Restricciones |
| :--- | :--- | :--- | :--- |
| **Orquestador** | `/src/orchestrator` | Interpreta la intencion del usuario y asigna tarjetas de tareas en el tablero. | Prohibido escribir codigo directo de frontend/backend. |
| **Creador** | `/src/backend` | Implementa microservicios tipados con FastAPI y Pydantic v2. | Prohibido alterar configuraciones globales o esquemas raiz. |
| **Evaluador (Ralph)** | `/src/evaluator` | Valida de forma adversarial que el codigo compile y cumpla `cloud/contract.json`. | Ordena hasta 3 ciclos automaticos de correccion ante fallos. |
| **Seguridad / Gate** | `/src/safety` | Protege acciones externas sensibles (despliegues, APIs fisicas). | **Bloqueo nativo**: Requiere confirmacion interactiva expresa. |

---

## Guia de Inicio Rapido (Quickstart en 2 Minutos)

El proyecto esta disenado bajo el principio **Zero-Friction Judging**: cuenta con un interruptor `MOCK_MODE=true` para que cualquier evaluador pueda comprobar el flujo agentico completo en local **sin necesidad de configurar claves API ni depender del Wi-Fi del evento**.

### 1. Clonar e Instalar Dependencias
```bash
git clone <URL_DE_TU_REPOSITORIO>
cd testigo-hackagent-repo

# Crear y activar entorno virtual
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate

# Instalar requerimientos minimos
pip install -r backend/requirements.txt
```

### 2. Configurar Variables de Entorno
```bash
cp .env.example .env
# MOCK_MODE viene habilitado por defecto para garantizar estabilidad en demo
```

### 3. Ejecutar la Simulacion del Grafo Agentico
```bash
python backend/workflow.py
```

### 4. Iniciar Servidor FastAPI y Endpoints MCP
```bash
uvicorn backend.main:app --reload --port 8000
```

---

## Estructura del Repositorio

```text
├── cloud/
│   ├── plan.md                 # Especificacion tecnica, fronteras y ADR congeladas (SDD)
│   ├── contract.json           # Esquema formal JSON Schema del Contrato Central
│   └── agentes/                # Prompts modulares de sistema
│       ├── orchestrator.md     # Directrices del Agente Orquestador
│       ├── creator_agent.md    # Instrucciones operativas del Creador
│       └── evaluator_judge.md  # Protocolo de evaluacion adversarial y Ralph Loops
├── backend/
│   ├── requirements.txt        # Dependencias de produccion (LangGraph, FastAPI, Pydantic)
│   ├── main.py                 # API REST para interoperabilidad de estados
│   ├── workflow.py             # Grafo ejecutable compilado con MemorySaver
│   ├── tools/
│   │   └── mcp_tools.py        # Herramientas MCP categorizadas (Read/Write/Action)
│   └── mock_data/              # Respuestas estables para contingencia de red
└── frontend/                   # Visualizador de razonamiento en tiempo real (CopilotKit)
    ├── package.json
    └── src/
        ├── App.tsx
        └── components/
            └── ApprovalGate.tsx # Componente interactivo Generative UI para el Human-in-the-Loop
```

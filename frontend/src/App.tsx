/**
 * frontend/src/App.tsx
 */
import React, { useState } from 'react';
import { CopilotKit } from '@copilotkit/react-core';
import { CopilotSidebar } from '@copilotkit/react-ui';
import '@copilotkit/react-ui/styles.css';
import { ApprovalGate } from './components/ApprovalGate';

export default function App() {
  const [threadId] = useState('session-demo-01');
  const [requiresApproval, setRequiresApproval] = useState(true);

  return (
    <CopilotKit runtimeUrl="http://localhost:8000/api/workflow/run">
      <div className="min-h-screen bg-slate-950 text-slate-100 p-8">
        <header className="mb-8 border-b border-slate-800 pb-4">
          <h1 className="text-2xl font-bold text-white">TESTIGO: Control de Seguridad Multiagente</h1>
          <p className="text-sm text-slate-400 mt-1">Consola interactiva de orquestacion y barandas MCP</p>
        </header>

        <main className="max-w-4xl mx-auto space-y-6">
          {requiresApproval && (
            <ApprovalGate
              threadId={threadId}
              toolName="mcp_write_file_disk"
              category="action_access"
              payload={{
                target: "src/backend/service.py",
                action: "write_disk",
                bytes: 420
              }}
              onApprovalCompleted={(status) => {
                console.log(`Compuerta resuelta con estado: ${status}`);
              }}
            />
          )}
        </main>

        <CopilotSidebar
          instructions="Eres el copiloto del sistema. Guia al usuario y explica las acciones antes de ejecutarlas."
          defaultOpen={true}
        />
      </div>
    </CopilotKit>
  );
}

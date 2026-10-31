/**
 * frontend/src/components/ApprovalGate.tsx
 * Tarjeta interactiva de Generative UI con CopilotKit para la compuerta de seguridad MCP.
 */

import React, { useState } from 'react';
import { useCopilotAction } from '@copilotkit/react-core';
import { ShieldAlert, CheckCircle2, XCircle, Terminal, Clock, Lock } from 'lucide-react';

interface ToolPayload {
  target?: string;
  command?: string;
  [key: string]: any;
}

interface ApprovalGateProps {
  threadId: string;
  toolName?: string;
  category?: 'read_access' | 'write_access' | 'action_access';
  payload?: ToolPayload;
  onApprovalCompleted?: (status: 'approved' | 'rejected') => void;
}

export const ApprovalGate: React.FC<ApprovalGateProps> = ({
  threadId,
  toolName = 'mcp_execute_action',
  category = 'action_access',
  payload = { target: 'src/backend/service.py', action: 'write_disk' },
  onApprovalCompleted,
}) => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [decision, setDecision] = useState<'approved' | 'rejected' | null>(null);
  const [operatorNotes, setOperatorNotes] = useState('Accion verificada por el operador tecnico.');

  useCopilotAction({
    name: 'authorizeSecurityGate',
    description: 'Permite al usuario interactivo autorizar o rechazar una herramienta MCP critica.',
    parameters: [
      {
        name: 'approved',
        type: 'boolean',
        description: 'True si el operador aprueba la accion, False si la rechaza.',
        required: true,
      },
      {
        name: 'notes',
        type: 'string',
        description: 'Comentarios u observaciones del operador.',
        required: false,
      },
    ],
    handler: async ({ approved, notes }) => {
      await handleDecision(approved, notes || operatorNotes);
    },
  });

  const handleDecision = async (approved: boolean, notes: string) => {
    setIsSubmitting(true);
    try {
      const response = await fetch('http://localhost:8000/api/workflow/resume-approval', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          thread_id: threadId,
          approved: approved,
          user_notes: notes,
        }),
      });

      if (!response.ok) {
        throw new Error('Error al reanudar el grafo en el backend.');
      }

      setDecision(approved ? 'approved' : 'rejected');
      if (onApprovalCompleted) {
        onApprovalCompleted(approved ? 'approved' : 'rejected');
      }
    } catch (error) {
      console.error('Error al procesar la aprobacion:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="w-full max-w-xl mx-auto my-4 bg-slate-900 border border-amber-500/40 rounded-xl shadow-2xl overflow-hidden font-sans">
      <div className="bg-amber-500/10 border-b border-amber-500/20 px-5 py-3.5 flex items-center justify-between">
        <div className="flex items-center space-x-2.5">
          <ShieldAlert className="w-5 h-5 text-amber-400 animate-pulse" />
          <h3 className="text-sm font-semibold text-amber-200 tracking-wide uppercase">
            Human-in-the-Loop Security Gate
          </h3>
        </div>
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-mono font-medium bg-red-950 text-red-300 border border-red-800">
          <Lock className="w-3 h-3 mr-1" />
          {category}
        </span>
      </div>

      <div className="p-5 space-y-4 text-slate-300 text-sm">
        <div>
          <p className="text-xs text-slate-400 font-mono">HERRAMIENTA MCP SOLICITADA</p>
          <div className="flex items-center space-x-2 mt-1">
            <Terminal className="w-4 h-4 text-cyan-400" />
            <span className="font-mono text-cyan-300 font-medium">{toolName}</span>
          </div>
        </div>

        <div>
          <p className="text-xs text-slate-400 font-mono mb-1.5">PARAMETROS DE EJECUCION (PAYLOAD)</p>
          <pre className="bg-slate-950 p-3 rounded-lg border border-slate-800 text-xs font-mono text-emerald-400 overflow-x-auto">
            {JSON.stringify(payload, null, 2)}
          </pre>
        </div>

        {!decision && (
          <div>
            <label className="block text-xs font-mono text-slate-400 mb-1">
              NOTAS DE AUDITORIA / CONFORMIDAD:
            </label>
            <input
              type="text"
              value={operatorNotes}
              onChange={(e) => setOperatorNotes(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
              placeholder="Ingresa justificacion tecnica..."
            />
          </div>
        )}

        {decision && (
          <div
            className={`p-3.5 rounded-lg flex items-center space-x-3 ${
              decision === 'approved'
                ? 'bg-emerald-950/50 border border-emerald-500/30 text-emerald-300'
                : 'bg-rose-950/50 border border-rose-500/30 text-rose-300'
            }`}
          >
            {decision === 'approved' ? (
              <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
            ) : (
              <XCircle className="w-5 h-5 text-rose-400 shrink-0" />
            )}
            <div className="text-xs">
              <p className="font-semibold">
                {decision === 'approved' ? 'Accion MCP Autorizada' : 'Accion MCP Rechazada'}
              </p>
              <p className="text-slate-400 mt-0.5 font-mono">{operatorNotes}</p>
            </div>
          </div>
        )}
      </div>

      {!decision && (
        <div className="bg-slate-950/80 px-5 py-3.5 border-t border-slate-800 flex items-center justify-end space-x-3">
          <button
            onClick={() => handleDecision(false, operatorNotes)}
            disabled={isSubmitting}
            className="px-4 py-2 rounded-lg text-xs font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-rose-900/60 border border-slate-700 hover:border-rose-700 transition-colors disabled:opacity-50"
          >
            Rechazar y Abortar
          </button>
          <button
            onClick={() => handleDecision(true, operatorNotes)}
            disabled={isSubmitting}
            className="px-4 py-2 rounded-lg text-xs font-medium text-white bg-emerald-600 hover:bg-emerald-500 transition-colors shadow-lg shadow-emerald-900/40 disabled:opacity-50 flex items-center space-x-1.5"
          >
            {isSubmitting ? (
              <Clock className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <CheckCircle2 className="w-3.5 h-3.5" />
            )}
            <span>Autorizar Ejecucion MCP</span>
          </button>
        </div>
      )}
    </div>
  );
};

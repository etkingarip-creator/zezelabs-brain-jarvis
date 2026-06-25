import type { ChatMessage, JarvisState } from '../../../types/department';

// ── Department color mapping ──────────────────────────────────────────────────
export const DEPT_COLORS: Record<string, { color: string; dim: string; border: string; label: string }> = {
  zeze_dev:        { color: '#38bdf8', dim: 'rgba(56,189,248,0.09)',   border: 'rgba(56,189,248,0.22)',   label: 'DEV' },
  crypto_trading:  { color: '#34d399', dim: 'rgba(52,211,153,0.09)',   border: 'rgba(52,211,153,0.22)',   label: 'CRYPTO' },
  zeze_design:     { color: '#f472b6', dim: 'rgba(244,114,182,0.09)',  border: 'rgba(244,114,182,0.22)',  label: 'DESIGN' },
  zeze_sec:        { color: '#fb7185', dim: 'rgba(251,113,133,0.09)',  border: 'rgba(251,113,133,0.22)',  label: 'SEC' },
  zeze_business:   { color: '#10b981', dim: 'rgba(16,185,129,0.09)',   border: 'rgba(16,185,129,0.22)',   label: 'BUSINESS' },
  zeze_ops:        { color: '#a78bfa', dim: 'rgba(167,139,250,0.09)',  border: 'rgba(167,139,250,0.22)',  label: 'OPS' },
  zeze_rnd:        { color: '#fbbf24', dim: 'rgba(251,191,36,0.09)',   border: 'rgba(251,191,36,0.22)',   label: 'R&D' },
  app_factory:     { color: '#fb923c', dim: 'rgba(251,146,60,0.09)',   border: 'rgba(251,146,60,0.22)',   label: 'FACTORY' },
};

export const DEFAULT_DEPT = { color: '#22d3ee', dim: 'rgba(34,211,238,0.09)', border: 'rgba(34,211,238,0.22)', label: 'ZOM' };

export const AVAILABLE_MODELS = [
  { id: 'antigravity', label: 'Antigravity (Otonom Yönlendirme)' },
  { id: 'glm-5.2', label: 'Zenmux GLM-5.2 (Akıl Yürütme)' },
  { id: 'openrouter_free', label: 'OpenRouter Free Tier (Hızlı)' },
  { id: 'claude_35', label: 'Claude 3.5 Sonnet (Global)' },
];

export function getDeptStyle(deptId?: string | null) {
  return deptId ? (DEPT_COLORS[deptId] ?? DEFAULT_DEPT) : DEFAULT_DEPT;
}

// ── Build activity steps from messages ────────────────────────────────────────
export function buildActivitySteps(messages: ChatMessage[], state: JarvisState) {
  const taskMessages = messages.filter(m => m.departmentId && m.role === 'jarvis');
  if (taskMessages.length === 0 && state !== 'thinking') return [];

  const steps = [];
  if (state === 'thinking' || taskMessages.length > 0) {
    steps.push({
      id: 'routing',
      label: 'Bilişsel yönlendirme',
      status: taskMessages.length > 0 ? 'done' : 'active',
      detail: 'Departman belirleniyor...',
    });
  }
  taskMessages.slice(-3).forEach((m, i) => {
    steps.push({
      id: `step-${i}`,
      label: m.departmentId ? `${m.departmentId} yürütüyor` : 'Yanıt üretiliyor',
      status: i === taskMessages.length - 1 && state !== 'idle' ? 'active' : 'done',
      dept: m.departmentId,
    });
  });
  return steps as Array<{ id: string; label: string; status: any; detail?: string; dept?: string }>;
}

// ── Format time helper ─────────────────────────────────────────────────────────
export function formatTime(date?: Date | string | number): string {
  try {
    const d = date ? new Date(date) : new Date();
    return d.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
  } catch {
    return new Date().toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
  }
}

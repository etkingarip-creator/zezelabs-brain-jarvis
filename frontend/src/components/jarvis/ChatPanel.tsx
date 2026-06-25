import { memo, useEffect, useRef, useState, useCallback, useMemo } from 'react';
import { Mic, MicOff, Send, Volume2, VolumeX, FileText, X, StopCircle, Copy, Star, ChevronDown, ChevronRight, Zap, Terminal, ArrowRight, ArrowLeft } from 'lucide-react';
import MarkdownMessage from '../ui/MarkdownMessage';
import JarvisOrb from './JarvisOrb';
import ActionApprovalModal from './ActionApprovalModal';
import AgentActivityStream from './AgentActivityStream';
import type { ChatMessage, JarvisState, ChatAttachment } from '../../types/department';
import { API_BASE } from '../../lib/config';
import { useUIStore, useJarvisStore } from '../../stores';

interface Props {
  messages: ChatMessage[];
  state: JarvisState;
  volume: number;
  voiceEnabled: boolean;
  onSend: (text: string, files?: File[]) => void;
  onToggleMic: () => void;
  onToggleVoice: () => void;
  onActionResponse?: (actionId: string, approved: boolean) => void;
  disabled?: boolean;
  agentDept?: string;
  onSendWsControl?: (type: string, val: any) => void;
}

// ── Department color mapping ──────────────────────────────────────────────────
const DEPT_COLORS: Record<string, { color: string; dim: string; border: string; label: string }> = {
  zeze_dev:        { color: '#38bdf8', dim: 'rgba(56,189,248,0.09)',   border: 'rgba(56,189,248,0.22)',   label: 'DEV' },
  crypto_trading:  { color: '#34d399', dim: 'rgba(52,211,153,0.09)',   border: 'rgba(52,211,153,0.22)',   label: 'CRYPTO' },
  zeze_design:     { color: '#f472b6', dim: 'rgba(244,114,182,0.09)',  border: 'rgba(244,114,182,0.22)',  label: 'DESIGN' },
  zeze_sec:        { color: '#fb7185', dim: 'rgba(251,113,133,0.09)',  border: 'rgba(251,113,133,0.22)',  label: 'SEC' },
  zeze_business:   { color: '#10b981', dim: 'rgba(16,185,129,0.09)',   border: 'rgba(16,185,129,0.22)',   label: 'BUSINESS' },
  zeze_ops:        { color: '#a78bfa', dim: 'rgba(167,139,250,0.09)',  border: 'rgba(167,139,250,0.22)',  label: 'OPS' },
  zeze_rnd:        { color: '#fbbf24', dim: 'rgba(251,191,36,0.09)',   border: 'rgba(251,191,36,0.22)',   label: 'R&D' },
  app_factory:     { color: '#fb923c', dim: 'rgba(251,146,60,0.09)',   border: 'rgba(251,146,60,0.22)',   label: 'FACTORY' },
};

const DEFAULT_DEPT = { color: '#22d3ee', dim: 'rgba(34,211,238,0.09)', border: 'rgba(34,211,238,0.22)', label: 'ZOM' };

const AVAILABLE_MODELS = [
  { id: 'antigravity', label: 'Antigravity (Otonom Yönlendirme)' },
  { id: 'glm-5.2', label: 'Zenmux GLM-5.2 (Akıl Yürütme)' },
  { id: 'openrouter_free', label: 'OpenRouter Free Tier (Hızlı)' },
  { id: 'claude_35', label: 'Claude 3.5 Sonnet (Global)' },
];

function getDeptStyle(deptId?: string | null) {
  return deptId ? (DEPT_COLORS[deptId] ?? DEFAULT_DEPT) : DEFAULT_DEPT;
}

// ── Build activity steps from messages ────────────────────────────────────────
function buildActivitySteps(messages: ChatMessage[], state: JarvisState) {
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
function formatTime(date?: Date | string | number): string {
  try {
    const d = date ? new Date(date) : new Date();
    return d.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
  } catch {
    return new Date().toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
  }
}

// ── Semantic Block Components ─────────────────────────────────────────────────

/** ATTACHMENTS VIEW BLOCK */
function AttachmentsBlock({ attachments }: { attachments?: ChatAttachment[] }) {
  if (!attachments || attachments.length === 0) return null;
  return (
    <div className="flex flex-wrap gap-2.5 mt-2.5">
      {attachments.map((file, idx) => {
        const isImage = file.type.startsWith('image/');
        const isAudio = file.type.startsWith('audio/');
        const isVideo = file.type.startsWith('video/');
        const sizeKB = (file.size / 1024).toFixed(1);

        return (
          <div 
            key={idx}
            className="flex flex-col border rounded-xl overflow-hidden bg-slate-900/40 relative max-w-sm"
            style={{ borderColor: 'rgba(255, 255, 255, 0.06)' }}
          >
            {isImage && (
              <img 
                src={file.url} 
                alt={file.name} 
                className="max-h-48 object-contain bg-black/20" 
              />
            )}
            {isVideo && (
              <video 
                src={file.url} 
                controls 
                className="max-h-48 object-contain bg-black/20" 
              />
            )}
            {isAudio && (
              <div className="p-3">
                <audio src={file.url} controls className="w-full max-w-xs" />
              </div>
            )}
            {!isImage && !isVideo && !isAudio && (
              <div className="flex items-center gap-2.5 p-3">
                <FileText className="w-8 h-8 p-1.5 rounded bg-slate-800 text-cyan-400" />
                <div className="min-w-0 flex-1">
                  <span className="block text-xs text-slate-200 truncate font-medium">{file.name}</span>
                  <span className="block text-[10px] text-slate-500 font-mono">{sizeKB} KB</span>
                </div>
              </div>
            )}
            
            {(isImage || isVideo) && (
              <div className="p-2 bg-slate-950/40 border-t border-white/5 flex items-center justify-between text-[10px] text-slate-400 font-mono">
                <span className="truncate max-w-[150px]">{file.name}</span>
                <span>{sizeKB} KB</span>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

/** USER INPUT BLOCK */
function InputBlock({ text, attachments }: { text: string; time?: string; attachments?: ChatAttachment[] }) {
  return (
    <div
      className="self-end max-w-[80%] animate-fade-in-up"
      style={{
        background: 'rgba(255, 255, 255, 0.05)',
        border: '1px solid rgba(255, 255, 255, 0.04)',
        borderRadius: '16px',
        padding: '10px 14px',
        marginBottom: '12px',
        marginLeft: 'auto',
      }}
    >
      <p style={{ fontSize: 'var(--text-sm)', color: 'var(--content-primary)', lineHeight: 1.5 }}>
        {text}
      </p>
      <AttachmentsBlock attachments={attachments} />
    </div>
  );
}

/** ROUTING INDICATOR BLOCK */
function RoutingBlock({ deptId }: { deptId?: string; time?: string }) {
  const dept = getDeptStyle(deptId);
  return (
    <div
      className="flex items-center gap-2 animate-fade-in py-2 justify-center"
      style={{ marginBottom: '12px' }}
    >
      <span style={{ fontSize: 'var(--text-2xs)', color: 'var(--content-tertiary)', fontFamily: 'var(--font-mono)', letterSpacing: '0.06em' }}>
        {deptId
          ? <><span style={{ color: dept.color }}>{dept.label.toUpperCase()}</span> departmanına yönlendiriliyor...</>
          : 'Bilişsel yönlendirme…'}
      </span>
    </div>
  );
}

/** ZOM OUTPUT BLOCK — main response block */
function OutputBlock({
  message,
  isLatest,
  state,
  volume,
  onOpenReport,
  onRetry,
}: {
  message: ChatMessage;
  isLatest: boolean;
  state: JarvisState;
  volume: number;
  onOpenReport: (taskId: string, deptId: string) => void;
  onRetry?: (message: ChatMessage) => void;
}) {
  const [copied, setCopied] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [favorited, setFavorited] = useState(() => {
    try { return localStorage.getItem(`zom_fav_${message.id}`) === '1'; } catch { return false; }
  });
  const isThinking = isLatest && state === 'thinking';
  const dept = getDeptStyle(message.departmentId);

  const handleCopy = useCallback(() => {
    navigator.clipboard.writeText(message.text).then(() => { setCopied(true); setTimeout(() => setCopied(false), 1500); });
  }, [message.text]);

  // İşlevlendirme: sesli okuma (Web Speech API)
  const handleSpeak = useCallback(() => {
    try {
      if (speaking) { window.speechSynthesis.cancel(); setSpeaking(false); return; }
      const u = new SpeechSynthesisUtterance(message.text);
      u.lang = 'tr-TR';
      u.onend = () => setSpeaking(false);
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(u);
      setSpeaking(true);
    } catch { setSpeaking(false); }
  }, [message.text, speaking]);

  // İşlevlendirme: kalıcı favori (localStorage)
  const toggleFavorite = useCallback(() => {
    setFavorited(prev => {
      const next = !prev;
      try {
        if (next) localStorage.setItem(`zom_fav_${message.id}`, '1');
        else localStorage.removeItem(`zom_fav_${message.id}`);
      } catch { /* storage unavailable */ }
      return next;
    });
  }, [message.id]);

  // İşlevlendirme: gerçek yeniden dene
  const handleRetry = useCallback(() => { onRetry?.(message); }, [onRetry, message]);

  return (
    <div className="w-full mb-8 animate-fade-in-up">
      {isThinking ? (
        <div className="flex items-center gap-2.5 py-4">
          <JarvisOrb state="thinking" volume={volume} />
          <div className="flex gap-1.5">
            <div className="typing-dot" />
            <div className="typing-dot" />
            <div className="typing-dot" />
          </div>
          <span style={{ fontSize: 'var(--text-xs)', color: 'var(--content-tertiary)' }}>ZOM düşünüyor…</span>
        </div>
      ) : (
        <div className="space-y-3">
          {/* Content */}
          <div className="md-body leading-relaxed text-[var(--content-primary)]" style={{ fontSize: 'var(--text-sm)', lineHeight: 1.7 }}>
            <MarkdownMessage text={message.text} />
          </div>

          <AttachmentsBlock attachments={message.attachments} />

          {/* Action tools line below message */}
          <div className="flex items-center gap-3 pt-2 text-[var(--content-tertiary)]">
            <button
              type="button"
              onClick={handleCopy}
              className="hover:text-[var(--content-primary)] transition-colors p-1"
              title="Kopyala"
            >
              <Copy className="w-3.5 h-3.5" style={{ color: copied ? 'var(--brand-primary)' : 'inherit' }} />
            </button>
            {message.taskId && message.departmentId && (
              <button
                type="button"
                onClick={() => onOpenReport(message.taskId!, message.departmentId!)}
                className="hover:text-[var(--content-primary)] transition-colors p-1 flex items-center gap-1 font-mono text-[var(--text-2xs)]"
                title="Raporu Görüntüle"
              >
                <FileText className="w-3.5 h-3.5" />
                <span>Rapor</span>
              </button>
            )}
            
            {/* İşlevsel aksiyon butonları */}
            <button
              type="button"
              onClick={handleSpeak}
              className="hover:text-[var(--content-primary)] transition-colors p-1"
              title={speaking ? 'Okumayı durdur' : 'Sesli oku'}
              aria-label={speaking ? 'Okumayı durdur' : 'Sesli oku'}
            >
              {speaking
                ? <VolumeX className="w-3.5 h-3.5" style={{ color: 'var(--brand-primary)' }} />
                : <Volume2 className="w-3.5 h-3.5" />}
            </button>
            <button
              type="button"
              onClick={toggleFavorite}
              className="hover:text-[var(--content-primary)] transition-colors p-1"
              title={favorited ? 'Favoriden çıkar' : 'Favorile'}
              aria-label={favorited ? 'Favoriden çıkar' : 'Favorile'}
              aria-pressed={favorited}
            >
              <Star className="w-3.5 h-3.5" style={favorited ? { color: 'var(--brand-primary)', fill: 'var(--brand-primary)' } : undefined} />
            </button>
            <button
              type="button"
              onClick={handleRetry}
              disabled={!onRetry}
              className="hover:text-[var(--content-primary)] transition-colors p-1 disabled:opacity-40 disabled:cursor-not-allowed"
              title="Yeniden Dene"
              aria-label="Yeniden Dene"
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 1121.21 7.89M9 11l3-3 3 3m-3-3v12" /></svg>
            </button>

            {/* Departman bilgisi */}
            {message.departmentId && (
              <span className="ml-auto font-mono text-[var(--text-2xs)] font-bold text-[var(--content-secondary)] border border-[rgba(255,255,255,0.08)] px-2 py-0.5 rounded-full bg-[rgba(255,255,255,0.03)] uppercase tracking-wider">
                {dept.label}
              </span>
            )}
          </div>

          {/* Action card (non-pending command outputs) */}
          {message.action && message.action.status !== 'pending' && (
            <div
              className="mt-3 p-3.5 rounded-xl text-[var(--text-xs)] animate-fade-in"
              style={{
                background: 'rgba(10, 14, 26, 0.4)',
                border: '1px solid rgba(255, 255, 255, 0.05)',
              }}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="font-mono font-semibold text-[var(--content-secondary)]">
                  {message.action.type === 'command' ? '⌗ CMD' : message.action.type === 'write_file' ? '📝 WRITE' : '⎆ GIT'}
                </span>
                <span
                  className="badge"
                  style={{
                    fontSize: 'var(--text-2xs)',
                    background: message.action.status === 'success' ? 'var(--status-success-dim)' : message.action.status === 'failed' ? 'var(--status-error-dim)' : 'var(--surface-interactive)',
                    color: message.action.status === 'success' ? 'var(--status-success)' : message.action.status === 'failed' ? 'var(--status-error)' : 'var(--content-tertiary)',
                    border: `1px solid ${message.action.status === 'success' ? 'var(--status-success-border)' : message.action.status === 'failed' ? 'var(--status-error-border)' : 'var(--surface-border)'}`,
                  }}
                >
                  {message.action.status === 'success' ? 'Başarılı' : message.action.status === 'failed' ? 'Başarısız' : message.action.status === 'rejected' ? 'Reddedildi' : 'Çalışıyor'}
                </span>
              </div>
              <code
                className="block px-2 py-1.5 rounded"
                style={{ fontSize: 'var(--text-2xs)', background: 'var(--surface-base)', color: 'var(--brand-primary)', fontFamily: 'var(--font-mono)' }}
              >
                {message.action.target}
              </code>
              {message.action.output && (
                <pre
                  className="mt-2 px-2 py-1.5 rounded overflow-x-auto"
                  style={{ fontSize: 'var(--text-2xs)', background: 'var(--surface-base)', color: '#8b9ab0', maxHeight: '120px', fontFamily: 'var(--font-mono)' }}
                >
                  {message.action.output}
                </pre>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Main ChatPanel ─────────────────────────────────────────────────────────────
const ChatPanel = memo(function ChatPanel({
  messages,
  state,
  volume,
  voiceEnabled,
  onSend,
  onToggleMic,
  onToggleVoice,
  onActionResponse,
  disabled,
  agentDept,
  onSendWsControl,
}: Props) {
  const [input, setInput] = useState('');
  const [attachedFiles, setAttachedFiles] = useState<File[]>([]);
  const [showFileReview, setShowFileReview] = useState(false);

  // Görsel önizleme URL'leri: bir kez üret, temizlikte revoke et (bellek sızıntısı yok)
  const filePreviewUrls = useMemo(() => {
    const map = new Map<File, string>();
    attachedFiles.forEach(f => { if (f.type.startsWith('image/')) map.set(f, URL.createObjectURL(f)); });
    return map;
  }, [attachedFiles]);
  useEffect(() => {
    return () => { filePreviewUrls.forEach(url => URL.revokeObjectURL(url)); };
  }, [filePreviewUrls]);
  
  const brainStatus = useJarvisStore(state => state.brainStatus);
  const activeModelId = brainStatus.model || 'antigravity';
  
  const activeModelLabel = AVAILABLE_MODELS.find(m => 
    m.id === activeModelId || 
    activeModelId.toLowerCase().endsWith(m.id.toLowerCase()) ||
    (m.id === 'antigravity' && (activeModelId.toLowerCase().includes('gemma') || activeModelId.toLowerCase().includes('antigravity'))) ||
    (m.id === 'glm-5.2' && (activeModelId.toLowerCase().includes('glm-5.2') || activeModelId.toLowerCase().includes('glm_5.2') || activeModelId.toLowerCase().includes('glm-4.5'))) ||
    (m.id === 'openrouter_free' && (activeModelId.toLowerCase().includes('openrouter_free') || activeModelId.toLowerCase().includes('openrouter/free') || activeModelId.toLowerCase().includes('free'))) ||
    (m.id === 'claude_35' && (activeModelId.toLowerCase().includes('claude-3.5') || activeModelId.toLowerCase().includes('claude_35') || activeModelId.toLowerCase().includes('claude-3-5')))
  )?.label || activeModelId;

  const [showModelDropdown, setShowModelDropdown] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const ui = useUIStore();

  useEffect(() => {
    if (ui.pendingChatInput) {
      setInput(ui.pendingChatInput);
      ui.setPendingChatInput('');
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [ui.pendingChatInput, ui]);

  const [approvalAction, setApprovalAction] = useState<any | null>(null);
  const [selectedReport, setSelectedReport] = useState<any | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const endRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const showSlash = input.startsWith('/') && input.length > 1;


  const activitySteps = buildActivitySteps(messages, state);
  const showActivityStream = state === 'thinking' || (activitySteps.length > 0 && state !== 'idle');

  // Track pending action for modal
  useEffect(() => {
    const pending = messages.find(m => m.action?.status === 'pending');
    if (pending?.action) setApprovalAction(pending.action);
    else setApprovalAction(null);
  }, [messages]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, state]);

  // İşlevlendirme: bir ZOM yanıtını "yeniden dene" = önceki kullanıcı mesajını tekrar gönder
  const handleRetry = useCallback((target: ChatMessage) => {
    const idx = messages.findIndex(m => m.id === target.id);
    for (let i = idx - 1; i >= 0; i--) {
      if (messages[i].role === 'user') {
        onSend(messages[i].text);
        return;
      }
    }
  }, [messages, onSend]);

  const handleOpenReport = async (taskId: string, departmentId: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/ecosystem/departments/${departmentId}/reports/${taskId}`);
      if (!res.ok) throw new Error('Rapor alınamadı');
      setSelectedReport(await res.json());
      setIsModalOpen(true);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Hata';
      setToast(msg);
      setTimeout(() => setToast(null), 3500);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setAttachedFiles(prev => [...prev, ...Array.from(e.target.files!)]);
      setShowFileReview(true);
    }
  };

  const submit = () => {
    if (!input.trim() && attachedFiles.length === 0) return;
    onSend(input.trim(), attachedFiles);
    setInput('');
    setAttachedFiles([]);
    setShowFileReview(false);
  };

  const SLASH_COMMANDS = [
    { cmd: '/dev ', desc: 'zeze_dev: Kod yazma ve geliştirme' },
    { cmd: '/sec ', desc: 'zeze_sec: Güvenlik taraması ve analiz' },
    { cmd: '/trade ', desc: 'crypto_trading: Portföy ve cüzdan durum' },
    { cmd: '/business ', desc: 'zeze_business: Şirket strateji raporu' },
    { cmd: '/clear', desc: 'Sohbet oturumunu tamamen sil' },
    { cmd: '/sys', desc: 'Canlı telemetri ve sistem stresi raporla' },
  ].filter(s => s.cmd.startsWith(input) || input === '/');

  // ── Render welcome screen ──
  const showWelcome = messages.length <= 1 && !disabled;

  return (
    <>
      {/* Hata bildirimi (engellemeyen toast) */}
      {toast && (
        <div
          className="fixed bottom-6 left-1/2 -translate-x-1/2 z-[60] px-4 py-2.5 rounded-xl animate-fade-in-up"
          style={{
            background: 'var(--status-error-dim, rgba(239,68,68,0.12))',
            border: '1px solid var(--status-error-border, rgba(239,68,68,0.3))',
            color: 'var(--status-error, #f87171)',
            fontSize: 'var(--text-xs)',
            boxShadow: 'var(--shadow-elevated)',
          }}
          role="alert"
        >
          {toast}
        </div>
      )}

      {/* Action Approval Modal */}
      <ActionApprovalModal
        action={approvalAction}
        onApprove={(id) => { onActionResponse?.(id, true); setApprovalAction(null); }}
        onReject={(id) => { onActionResponse?.(id, false); setApprovalAction(null); }}
      />

      <div className="flex-1 flex flex-col min-h-0 gap-0">
        {/* Agent Activity Stream */}
        {showActivityStream && (
          <AgentActivityStream
            visible={showActivityStream}
            steps={activitySteps}
            agentDept={agentDept}
            onClose={() => {}}
          />
        )}

        {/* ── Message area ── */}
        <div className="flex-1 overflow-y-auto min-h-0 scrollbar-brand flex justify-center w-full" style={{ padding: '16px 20px' }}>
          <div className="max-w-3xl w-full flex flex-col gap-1">

          {/* ── Welcome state ── */}
          {showWelcome && (
            <div className="flex-1 flex flex-col items-center justify-center py-6 px-4 my-auto w-full">
              <div
                className="max-w-xl w-full p-8 rounded-2xl text-center flex flex-col items-center gap-6"
                style={{
                  background: 'rgba(22, 29, 46, 0.45)',
                  border: '1px solid var(--surface-border)',
                  backdropFilter: 'blur(20px)',
                  WebkitBackdropFilter: 'blur(20px)',
                  boxShadow: 'var(--shadow-elevated)',
                }}
              >
                <div className="relative">
                  <JarvisOrb state="idle" volume={0} size="master" />
                </div>
                <div className="space-y-2.5">
                  <span
                    className="font-mono uppercase tracking-[0.22em] text-[var(--brand-primary)] block font-bold"
                    style={{ fontSize: 'var(--text-2xs)' }}
                  >
                    KOMUTA KONSOLU
                  </span>
                  <h1
                    className="font-display font-semibold tracking-tight text-[var(--content-primary)]"
                    style={{ fontSize: '24px' }}
                  >
                    Görevi tanımla, <span className="text-[var(--brand-secondary)]">kuleye devret.</span>
                  </h1>
                  <p style={{ fontSize: 'var(--text-sm)', color: 'var(--content-secondary)', lineHeight: 1.6 }}>
                    ZOM Çekirdeği hazır. Bir talimat girin veya kısayollar için{' '}
                    <code
                      className="px-1.5 py-0.5 rounded font-mono"
                      style={{ background: 'var(--surface-interactive)', color: 'var(--brand-primary)', fontSize: 'var(--text-xs)' }}
                    >
                      /
                    </code>{' '}
                    yazın.
                  </p>
                </div>

                {/* Quick suggestions chips in a row (horizontal layout matching monolith quick-chips) */}
                <div className="flex flex-wrap justify-center gap-2.5 pt-2 max-w-lg">
                  {[
                    { text: '📈 Portföy analizi', cmd: '/trade Portföy analizi' },
                    { text: '🎨 Tasarım üret', cmd: 'Yeni giriş ekranı için Aurora Glow temalı bir tasarım hazırla' },
                    { text: '📣 İçerik fikri', cmd: 'Bu hafta sosyal medyada paylaşılacak 3 içerik fikri çıkar' },
                    { text: '🛡️ Güvenlik taraması', cmd: '/sys Telemetri raporla' },
                  ].map(s => (
                    <button
                      key={s.cmd}
                      type="button"
                      onClick={() => onSend(s.cmd)}
                      className="transition-all duration-150"
                      style={{
                        border: '1px solid var(--surface-border)',
                        background: 'rgba(255,255,255,0.03)',
                        color: 'var(--content-secondary)',
                        borderRadius: '999px',
                        padding: '8px 16px',
                        fontSize: 'var(--text-sm)',
                        cursor: 'pointer',
                      }}
                      onMouseEnter={e => {
                        e.currentTarget.style.borderColor = 'rgba(255,255,255,0.16)';
                        e.currentTarget.style.color = 'var(--content-primary)';
                        e.currentTarget.style.background = 'rgba(255,255,255,0.06)';
                      }}
                      onMouseLeave={e => {
                        e.currentTarget.style.borderColor = 'var(--surface-border)';
                        e.currentTarget.style.color = 'var(--content-secondary)';
                        e.currentTarget.style.background = 'rgba(255,255,255,0.03)';
                      }}
                    >
                      {s.text}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* ── Semantic Block Log ── */}
          {messages
            .filter(m => {
              if (m.id === 'welcome' && messages.length <= 1) return false;
              if (m.role === 'jarvis') {
                const text = m.text;
                if (
                  text.startsWith('⚙️') ||
                  text.startsWith('🧠 Plan hazır') ||
                  text.startsWith('📡') ||
                  text.startsWith('🔄') ||
                  text.includes('[SİSTEM')
                ) {
                  return false;
                }
              }
              return true;
            })
            .map((m, idx, filteredArray) => {
              const isUser = m.role === 'user';
              const isLatest = idx === filteredArray.length - 1;
              const nextMsg = filteredArray[idx + 1];
              const showRouting = isUser && nextMsg && nextMsg.role !== 'user';

              return (
                <div key={m.id}>
                  {isUser ? (
                    <InputBlock
                      text={m.text}
                      time={formatTime()}
                      attachments={m.attachments}
                    />
                  ) : (
                    <OutputBlock
                      message={m}
                      isLatest={isLatest}
                      state={state}
                      volume={volume}
                      onOpenReport={handleOpenReport}
                      onRetry={handleRetry}
                    />
                  )}
                  {/* Routing connector between user msg and dept response */}
                  {showRouting && nextMsg.departmentId && (
                    <RoutingBlock deptId={nextMsg.departmentId} />
                  )}
                </div>
              );
            })}

          {/* Thinking indicator (only if last message is from user) */}
          {state === 'thinking' && (messages.length === 0 || messages[messages.length - 1].role === 'user') && (
            <div className="animate-fade-in">
              <RoutingBlock deptId={agentDept} />
              <div
                style={{
                  background: 'rgba(34,211,238,0.04)',
                  border: '1px solid rgba(34,211,238,0.12)',
                  borderLeft: '3px solid rgba(34,211,238,0.4)',
                  borderRadius: '12px',
                  padding: '12px 16px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                }}
              >
                <JarvisOrb state="thinking" volume={volume} />
                <div className="flex gap-1.5">
                  <div className="typing-dot" />
                  <div className="typing-dot" />
                  <div className="typing-dot" />
                </div>
                <span style={{ fontSize: '12px', color: 'var(--content-tertiary)' }}>ZOM düşünüyor…</span>
              </div>
            </div>
          )}

            <div ref={endRef} />
          </div>
        </div>

        {/* ── Slash Commands Popover ── */}
        {showSlash && SLASH_COMMANDS.length > 0 && (
          <div
            className="mx-4 mb-1 rounded-xl overflow-y-auto max-h-48 scrollbar-brand"
            style={{ background: 'var(--surface-overlay)', border: '1px solid var(--surface-border)', boxShadow: 'var(--shadow-elevated)' }}
          >
            <div
              className="px-3 py-1.5 font-bold uppercase tracking-wider"
              style={{ fontSize: '10px', color: 'var(--content-tertiary)', borderBottom: '1px solid var(--surface-border-subtle)', fontFamily: 'var(--font-mono)' }}
            >
              Komutlar
            </div>
            {SLASH_COMMANDS.map((item) => (
              <button
                key={item.cmd}
                type="button"
                onClick={() => { setInput(item.cmd); inputRef.current?.focus(); }}
                className="w-full flex items-center justify-between px-3 py-2 text-left transition-colors"
                style={{ fontSize: '12px', color: 'var(--content-secondary)' }}
                onMouseEnter={e => (e.currentTarget.style.background = 'var(--surface-interactive)')}
                onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
              >
                <code className="font-bold" style={{ color: 'var(--brand-primary)', fontFamily: 'var(--font-mono)', fontSize: '11px' }}>{item.cmd}</code>
                <span style={{ color: 'var(--content-tertiary)', fontSize: '11px' }}>{item.desc}</span>
              </button>
            ))}
          </div>
        )}

        {/* ── Input Bar ── */}
        <div
          className="px-4 pb-6 pt-3 flex flex-col items-center shrink-0 w-full animate-fade-in"
          style={{ borderTop: 'none' }}
        >
          <div className="max-w-3xl w-full">
          <div
            className="flex flex-col w-full"
            style={{
              background: 'rgba(22, 29, 46, 0.4)',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              borderRadius: '24px',
              padding: '12px 14px 8px',
              transition: 'border-color 0.2s ease, box-shadow 0.2s ease',
              boxShadow: 'var(--shadow-card)',
            }}
            onFocusCapture={(e) => {
              e.currentTarget.style.borderColor = 'var(--brand-primary)';
              e.currentTarget.style.boxShadow = '0 0 0 3px rgba(34, 211, 238, 0.06)';
            }}
            onBlurCapture={(e) => {
              e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.08)';
              e.currentTarget.style.boxShadow = 'none';
            }}
          >
            {/* Attached Files Bar (matching screenshot) */}
            <div 
              className="flex items-center gap-3 pb-2.5 mb-2 border-b"
              style={{ borderColor: 'rgba(255, 255, 255, 0.05)', opacity: attachedFiles.length > 0 ? 1 : 0.5 }}
            >
              {/* Back Arrow button to clear all */}
              <button
                type="button"
                onClick={() => { setAttachedFiles([]); setShowFileReview(false); }}
                disabled={attachedFiles.length === 0}
                className="p-1 hover:text-white transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                title="Tümünü Kaldır"
                style={{ background: 'none', border: 'none', cursor: 'pointer' }}
              >
                <ArrowLeft className="w-4 h-4 text-slate-400" />
              </button>
              
              {/* File Count Info */}
              <div className="flex items-center gap-1.5 text-xs text-slate-400 font-mono">
                <FileText className="w-4 h-4 text-cyan-400" />
                <span>{attachedFiles.length} dosya seçildi</span>
              </div>
              
              {/* Review Changes Button */}
              <button
                type="button"
                onClick={() => setShowFileReview(!showFileReview)}
                disabled={attachedFiles.length === 0}
                className="ml-auto text-[10px] font-mono px-2.5 py-1 rounded-lg border transition-all hover:bg-slate-800 disabled:opacity-30 disabled:cursor-not-allowed"
                style={{
                  background: 'rgba(255,255,255,0.03)',
                  borderColor: 'rgba(255,255,255,0.07)',
                  color: '#e8ecf4',
                  cursor: 'pointer'
                }}
              >
                Değişiklikleri İncele
              </button>
            </div>

            {/* File Review Detail List */}
            {attachedFiles.length > 0 && showFileReview && (
              <div 
                className="p-3 mb-3 rounded-xl space-y-2 border overflow-y-auto max-h-48 scrollbar-brand"
                style={{
                  background: 'rgba(10, 14, 26, 0.6)',
                  borderColor: 'rgba(255, 255, 255, 0.08)'
                }}
              >
                {attachedFiles.map((file, idx) => {
                  const isImage = file.type.startsWith('image/');
                  const sizeKB = (file.size / 1024).toFixed(1);
                  
                  return (
                     <div 
                      key={idx}
                      className="flex items-center justify-between p-2 rounded-lg bg-slate-900/40 border border-white/5 text-xs"
                    >
                      <div className="flex items-center gap-2 min-w-0">
                        {isImage ? (
                          <img
                            src={filePreviewUrls.get(file)}
                            alt="preview"
                            className="w-8 h-8 rounded object-cover"
                          />
                        ) : (
                          <FileText className="w-8 h-8 p-1.5 rounded bg-slate-800 text-cyan-400" />
                        )}
                        <div className="min-w-0">
                          <span className="block text-slate-200 truncate font-medium">{file.name}</span>
                          <span className="block text-[10px] text-slate-500 font-mono">{sizeKB} KB · {file.type || 'Bilinmeyen'}</span>
                        </div>
                      </div>
                      
                      <button
                        type="button"
                        onClick={() => {
                          const updated = attachedFiles.filter((_, i) => i !== idx);
                          setAttachedFiles(updated);
                          if (updated.length === 0) setShowFileReview(false);
                        }}
                        className="p-1 rounded text-slate-500 hover:text-red-400 hover:bg-slate-800 transition-colors"
                        title="Kaldır"
                        style={{ background: 'none', border: 'none', cursor: 'pointer' }}
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  );
                })}
              </div>
            )}

            {/* Hidden File Input */}
            <input
              type="file"
              ref={fileInputRef}
              multiple
              onChange={handleFileChange}
              className="hidden"
              accept="image/*,video/*,audio/*,.pdf,.txt,.doc,.docx,.xls,.xlsx,.zip,.csv"
            />

            {/* Input field (completely borderless textarea) */}
            <textarea
              ref={inputRef}
              rows={1}
              value={input}
              onChange={(e) => {
                setInput(e.target.value);
                // Auto-grow height calculation
                e.target.style.height = 'auto';
                e.target.style.height = `${Math.min(160, e.target.scrollHeight)}px`;
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  submit();
                }
              }}
              placeholder={disabled ? 'ZOM çevrimdışı…' : "Bir talimat girin..."}
              disabled={disabled}
              className="w-full bg-transparent border-none outline-none text-[var(--content-primary)] text-[var(--text-sm)] placeholder-[var(--content-tertiary)] resize-none py-1 min-h-[24px] max-h-[160px]"
              style={{
                fontFamily: 'var(--font-sans)',
              }}
            />

            {/* Bottom Actions Row inside the container */}
            <div className="flex items-center justify-between mt-3 pt-2" style={{ borderTop: '1px solid rgba(255, 255, 255, 0.03)' }}>
              {/* Left Group: (+) and Model Selector */}
              <div className="flex items-center gap-2">
                {/* Left action button (+) */}
                <button
                  type="button"
                  className="w-8 h-8 rounded-full flex items-center justify-center transition-all bg-[rgba(255,255,255,0.03)] border border-[rgba(255,255,255,0.05)] text-[var(--content-secondary)] hover:bg-[rgba(255,255,255,0.07)] hover:text-[var(--content-primary)]"
                  onClick={() => {
                    fileInputRef.current?.click();
                  }}
                  title="Dosya / Medya Yükle"
                >
                  <span className="text-lg font-light leading-none">+</span>
                </button>

                {/* Model Selector Dropdown Chip (from screenshot) */}
                <div className="relative">
                  <button 
                    type="button"
                    className="font-mono font-bold text-[10px] text-[var(--content-secondary)] border border-[rgba(255,255,255,0.08)] bg-[rgba(255,255,255,0.03)] px-3 py-1.5 rounded-full flex items-center gap-1.5 cursor-pointer hover:border-[rgba(255,255,255,0.16)] transition-all"
                    onClick={() => setShowModelDropdown(!showModelDropdown)}
                    title="Model Değiştir"
                  >
                    <span>{activeModelLabel}</span>
                    <ChevronDown className="w-3 h-3 text-slate-500" />
                  </button>
                  
                  {showModelDropdown && (
                    <div
                      className="absolute bottom-full left-0 mb-2 rounded-xl border z-30 w-64 py-1"
                      style={{
                        background: 'var(--surface-overlay)',
                        borderColor: 'var(--surface-border)',
                        boxShadow: 'var(--shadow-elevated)'
                      }}
                    >
                      {AVAILABLE_MODELS.map((model) => (
                        <button
                          key={model.id}
                          type="button"
                          onClick={() => {
                            onSendWsControl?.('model_change', model.id);
                            setShowModelDropdown(false);
                          }}
                          className="w-full text-left px-3 py-2 text-xs hover:bg-white/5 transition-colors"
                          style={{
                            color: activeModelId === model.id ? 'var(--brand-primary)' : 'var(--content-secondary)'
                          }}
                        >
                          {model.label}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* Right Group: ZOM specific features, Mic, Send */}
              <div className="flex items-center gap-2">
                {/* Department Selector Chip */}
                <button
                  type="button"
                  className="font-mono font-bold text-[10px] text-[var(--content-secondary)] border border-[rgba(255,255,255,0.08)] bg-[rgba(255,255,255,0.03)] px-2 py-1 rounded-full flex items-center gap-1.5 cursor-pointer hover:border-[rgba(255,255,255,0.16)] transition-all"
                  onClick={() => {
                    setInput(input === '/' ? '' : '/');
                    inputRef.current?.focus();
                  }}
                  title="Yönlendirme Odak Değiştir"
                  aria-label="Departman yönlendirme odağını değiştir"
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-[var(--brand-primary)]" />
                  <span>{agentDept ? `${agentDept.toUpperCase()}` : 'DYNAMIC ROUTING'}</span>
                </button>

                {/* Voice inside container */}
                <button
                  type="button"
                  onClick={onToggleVoice}
                  aria-label={voiceEnabled ? 'Sesi kapat' : 'Sesi aç'}
                  className="p-1.5 rounded-full transition-all text-[var(--content-tertiary)] hover:text-[var(--content-primary)]"
                  style={{
                    background: voiceEnabled ? 'rgba(34,211,238,0.08)' : 'transparent',
                    color: voiceEnabled ? 'var(--brand-primary)' : undefined,
                  }}
                >
                  {voiceEnabled ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
                </button>

                {/* Mic inside container */}
                <button
                  type="button"
                  onClick={onToggleMic}
                  disabled={disabled}
                  aria-label={state === 'listening' ? 'Mikrofonu kapat' : 'Mikrofonu aç'}
                  className="p-1.5 rounded-full transition-all text-[var(--content-tertiary)] hover:text-[var(--content-primary)]"
                  style={{
                    background: state === 'listening' ? 'rgba(239,68,68,0.12)' : 'transparent',
                    color: state === 'listening' ? '#ef4444' : undefined,
                  }}
                >
                  {state === 'listening' ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                </button>

                {/* Send / Stop Action Button */}
                {(state === 'thinking' || state === 'listening') ? (
                  <button
                    type="button"
                    onClick={() => onSend('/stop')}
                    className="ml-1 border-none rounded-full w-8 h-8 flex items-center justify-center text-[#f87171] bg-[rgba(239,68,68,0.12)] transition-all hover:bg-[rgba(239,68,68,0.2)]"
                    title="Durdur"
                  >
                    <StopCircle className="w-4 h-4" />
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={submit}
                    disabled={disabled || (!input.trim() && attachedFiles.length === 0)}
                    className="ml-1 border-none rounded-full w-8 h-8 flex items-center justify-center text-white cursor-pointer transition-all hover:brightness-110 active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed disabled:transform-none"
                    style={{
                      background: 'var(--brand-primary)',
                    }}
                    title="Gönder"
                  >
                    <ArrowRight className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

      {/* ── Report Detail Modal ── */}
      {isModalOpen && selectedReport && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          style={{ background: 'rgba(2,6,23,0.85)', backdropFilter: 'blur(8px)' }}
        >
          <div
            className="w-full max-w-2xl max-h-[85vh] flex flex-col rounded-2xl overflow-hidden animate-scale-in"
            style={{ background: 'var(--surface-overlay)', border: '1px solid var(--surface-border)', boxShadow: 'var(--shadow-modal)' }}
          >
            <div
              className="flex items-center justify-between p-4"
              style={{ borderBottom: '1px solid var(--surface-border-subtle)' }}
            >
              <div>
                <h3 className="font-semibold" style={{ fontSize: '13px', color: 'var(--content-primary)' }}>Rapor Detayı</h3>
                <p className="mt-0.5 font-mono" style={{ fontSize: '10px', color: 'var(--content-tertiary)' }}>
                  {selectedReport.task_id} · {selectedReport.timestamp ? new Date(selectedReport.timestamp).toLocaleString('tr-TR') : ''}
                </p>
              </div>
              <button
                type="button"
                onClick={() => { setIsModalOpen(false); setSelectedReport(null); }}
                className="btn-icon"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-5 space-y-4 scrollbar-brand">
              <div>
                <p className="label mb-1.5">Kullanıcı Talebi</p>
                <p
                  className="p-3 rounded-lg"
                  style={{ fontSize: '13px', background: 'var(--surface-card)', border: '1px solid var(--surface-border)', color: 'var(--content-secondary)', lineHeight: 1.65 }}
                >
                  {selectedReport.query ?? 'Belirtilmemiş.'}
                </p>
              </div>
              <div>
                <p className="label mb-1.5">Rapor Çıktısı</p>
                <div
                  className="p-4 rounded-lg whitespace-pre-wrap leading-relaxed max-h-80 overflow-y-auto scrollbar-brand font-mono"
                  style={{ fontSize: '11px', background: 'var(--surface-base)', border: '1px solid var(--surface-border)', color: '#8b9ab0' }}
                >
                  {selectedReport.output ?? 'Rapor çıktısı bulunamadı.'}
                </div>
              </div>
              <div
                className="flex gap-4 flex-wrap pt-2"
                style={{ borderTop: '1px solid var(--surface-border-subtle)' }}
              >
                <span style={{ fontSize: '10px', color: 'var(--content-tertiary)' }}>
                  Departman: <span className="badge badge-brand">{selectedReport.department}</span>
                </span>
                <span style={{ fontSize: '10px', color: 'var(--content-tertiary)' }}>
                  Durum: <span style={{ color: 'var(--status-success)', fontWeight: 600 }}>{selectedReport.status}</span>
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
});

export default ChatPanel;

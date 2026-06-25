import { useState, useCallback } from 'react';
import { Volume2, VolumeX, FileText, Copy, Star } from 'lucide-react';
import MarkdownMessage from '../../ui/MarkdownMessage';
import JarvisOrb from '../JarvisOrb';
import AttachmentsBlock from './AttachmentsBlock';
import { getDeptStyle } from './chatHelpers';
import type { ChatMessage, JarvisState } from '../../../types/department';

/** ZOM OUTPUT BLOCK — main response block */
export default function OutputBlock({
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
      // Ayarlardaki ses tercihini gerçekten uygula (zom_settings_voice_gender)
      const gender = localStorage.getItem('zom_settings_voice_gender') || 'robot';
      if (gender === 'robot') {
        u.pitch = 0.4; u.rate = 0.95;
      } else {
        const trVoices = window.speechSynthesis.getVoices().filter(v => v.lang.startsWith('tr'));
        const pick = trVoices.find(v =>
          gender === 'female' ? /female|kad|woman/i.test(v.name) : /male|erkek|man/i.test(v.name)
        ) || trVoices[0];
        if (pick) u.voice = pick;
        u.pitch = gender === 'female' ? 1.25 : 0.85;
      }
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

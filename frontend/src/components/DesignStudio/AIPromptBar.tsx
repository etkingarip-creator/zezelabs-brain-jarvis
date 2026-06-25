// AIPromptBar — Bağımsız AI prompt çubuğu bileşeni (G2)
// index.tsx'de render edilir, CanvasView'e bağlı değil

import React from 'react';

interface AIPromptBarProps {
  promptInput: string;
  isGenerating: boolean;
  generationLog: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
}

export function AIPromptBar({
  promptInput,
  isGenerating,
  generationLog,
  onChange,
  onSubmit,
}: AIPromptBarProps) {
  return (
    <div className="absolute bottom-10 left-1/2 -translate-x-1/2 w-full max-w-lg px-4 z-30 pointer-events-none">
      <div className="bg-slate-900/90 dark:bg-slate-900/95 backdrop-blur-md border border-slate-800/80 rounded-2xl shadow-2xl flex items-center p-3 gap-3 pointer-events-auto">
        <span
          className="material-symbols-outlined text-indigo-400 animate-pulse shrink-0"
          style={{ fontVariationSettings: "'FILL' 1" }}
        >
          auto_awesome
        </span>
        <input
          id="ai-prompt-input"
          value={promptInput}
          onChange={e => onChange(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter') onSubmit(); }}
          disabled={isGenerating}
          className="bg-transparent border-none focus:outline-none flex-1 text-xs text-white placeholder-slate-400 min-w-0"
          placeholder={
            isGenerating
              ? `İşleniyor: ${generationLog}`
              : "AI ile kanvası güncelle ('glassmorphic', 'neon', 'kutucuk ekle')..."
          }
          type="text"
          aria-label="AI komut satırı"
          autoComplete="off"
        />
        <button
          id="ai-prompt-submit"
          onClick={onSubmit}
          disabled={isGenerating}
          className="bg-indigo-600 text-white hover:bg-indigo-500 px-4 py-2 rounded-xl font-bold text-xs transition-all hover:scale-105 active:scale-95 cursor-pointer shadow-md shadow-indigo-600/10 shrink-0 disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {isGenerating ? (
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full border-2 border-white/40 border-t-white animate-spin inline-block" />
              İşleniyor
            </span>
          ) : 'AI Üret'}
        </button>
      </div>
    </div>
  );
}

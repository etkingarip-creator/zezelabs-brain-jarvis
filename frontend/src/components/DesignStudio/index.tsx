// DesignStudio/index.tsx — Ana kompozisyon bileşeni
// G1: setCanvasConfig → InspectorPanel'e taşındı (F4)
// G2: AIPromptBar bağımsız bileşen
// F3: snapGrid state + toggle butonu
// Sprint E,F,G tamamlandı

import React, { useState, useCallback, useEffect } from 'react';
import { AnimatePresence } from 'framer-motion';
import {
  Search,
  Sun,
  Moon,
  ArrowLeft,
  Grid,
} from 'lucide-react';
import { useUIStore } from '../../stores';
import { useCanvasState } from '../../hooks/useCanvasState';
import { useKeyboardShortcuts } from '../../hooks/useKeyboardShortcuts';
import { runAIPromptEngine } from '../../hooks/useAIPromptEngine';
import { KonvaCanvasView } from './KonvaCanvasView';
import { LayersPanel } from './LayersPanel';
import { InspectorPanel } from './InspectorPanel';
import { ExportModal } from './ExportModal';
import { PreviewModal } from './PreviewModal';
import { AIPromptBar } from './AIPromptBar';
import type { ToolType, CanvasElement, CanvasConfig } from '../../types/canvas';

interface Props {
  onSendWsControl?: (type: string, val: unknown) => void;
}

export default function DesignStudio({ onSendWsControl: _ws }: Props) {
  // ─── Tema ──────────────────────────────────────────────────────────────────
  const [isDark, setIsDark] = useState(true);

  // ─── Araç, Zoom, Snap durumu ────────────────────────────────────────────────
  const [activeTool, setActiveTool] = useState<ToolType>('select');
  const [zoom, setZoom] = useState(1);
  const [snapGrid, setSnapGrid] = useState(8); // F3: 0 = kapalı, 8 = açık

  // ─── Modal durumları ────────────────────────────────────────────────────────
  const [showPreview, setShowPreview] = useState(false);
  const [showExport, setShowExport] = useState(false);

  // ─── Katman arama (gerçek filtre) ───────────────────────────────────────────
  const [layerSearch, setLayerSearch] = useState('');

  // ─── AI Prompt ──────────────────────────────────────────────────────────────
  const [promptInput, setPromptInput] = useState('');
  const [isAIGenerating, setIsAIGenerating] = useState(false);
  const [generationLog, setGenerationLog] = useState('');

  // ─── Canvas durumu ──────────────────────────────────────────────────────────
  const {
    elements,
    canvasConfig,
    setCanvasConfig,
    selectedId,
    setSelectedId,
    selectedElement,
    updateElement,
    commitBulk,
    addElement,
    deleteElement,
    duplicateElement,
    bringForward,
    sendBackward,
    undo,
    redo,
    canUndo,
    canRedo,
  } = useCanvasState();

  // ─── Keyboard kısayolları ───────────────────────────────────────────────────
  useKeyboardShortcuts({
    selectedId,
    onDelete: deleteElement,
    onDeselect: () => setSelectedId(null),
    onUndo: undo,
    onRedo: redo,
    onDuplicate: duplicateElement,
    canUndo,
    canRedo,
  });

  // Escape ile modalleri kapat
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setShowPreview(false);
        setShowExport(false);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  // ─── AI Prompt — Backend + Yerel Motor ──────────────────────────────────────
  const applyAIPrompt = useCallback(async () => {
    if (!promptInput.trim() || isAIGenerating) return;
    const prompt = promptInput.trim();
    setIsAIGenerating(true);
    setGenerationLog('AI prompt analiz ediliyor...');

    let usedBackend = false;

    try {
      // ─ 1. Backend LLM ——————————————————————————─
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 4000); // 4s timeout

      const response = await fetch('/api/ecosystem/design/ai-apply', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, elements, canvasConfig }),
        signal: controller.signal,
      });
      clearTimeout(timeoutId);

      if (response.ok) {
        const { operations } = await response.json() as {
          operations: Array<{
            op: 'update_canvas' | 'update_element' | 'add_element' | 'clear';
            id?: string;
            changes?: Partial<CanvasElement> | Partial<CanvasConfig>;
            element?: CanvasElement;
          }>
        };
        setGenerationLog('Backend operasyonları uygulanıyor...');

        let nextElements = [...elements];
        let nextConfig = { ...canvasConfig };

        for (const op of operations) {
          if (op.op === 'update_canvas' && op.changes) {
            nextConfig = { ...nextConfig, ...(op.changes as Partial<CanvasConfig>) };
          } else if (op.op === 'update_element' && op.id && op.changes) {
            nextElements = nextElements.map(el =>
              el.id === op.id ? { ...el, ...(op.changes as Partial<CanvasElement>) } : el
            );
          } else if (op.op === 'add_element' && op.element) {
            nextElements = [...nextElements, op.element];
          } else if (op.op === 'clear') {
            nextElements = [];
          }
        }

        commitBulk(nextElements);
        setCanvasConfig(nextConfig);
        usedBackend = true;
      }
    } catch {
      // Backend bağlantı hatası — yerel motora geç
    }

    // ─ 2. Yerel AI Motor ─────────────────────────────────────────────────────
    if (!usedBackend) {
      setGenerationLog('Yerel AI motoru çalıştırılıyor...');
      await new Promise(r => setTimeout(r, 350));

      const result = runAIPromptEngine(prompt, elements, canvasConfig);

      let nextElements = [...elements];
      let nextConfig = { ...canvasConfig };

      for (const op of result.operations) {
        if (op.type === 'config') {
          nextConfig = { ...nextConfig, ...(op.changes as Partial<CanvasConfig>) };
        } else if (op.type === 'element' && op.id) {
          nextElements = nextElements.map(el =>
            el.id === op.id ? { ...el, ...(op.changes as Partial<CanvasElement>) } : el
          );
        } else if (op.type === 'bulk_elements' && op.nextElements) {
          nextElements = op.nextElements;
        }
      }

      commitBulk(nextElements);
      setCanvasConfig(nextConfig);
      setGenerationLog(result.description);
    }

    setIsAIGenerating(false);
    setPromptInput('');
    setTimeout(() => setGenerationLog(''), 2500);
  }, [
    promptInput, isAIGenerating, elements, canvasConfig,
    commitBulk, setCanvasConfig,
  ]);

  return (
    <div
      className={`w-full h-full flex flex-col overflow-hidden font-sans relative ${
        isDark ? 'dark bg-slate-950 text-slate-100' : 'bg-slate-50 text-slate-900'
      }`}
    >
      {/* Stil enjeksiyonu */}
      <style>{`
        .material-symbols-outlined {
          font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 20;
          user-select: none;
        }
        .canvas-dot-grid {
          background-image: radial-gradient(circle, #cbd5e1 1.2px, transparent 1.2px);
          background-size: 24px 24px;
        }
        .dark .canvas-dot-grid {
          background-image: radial-gradient(circle, #334155 1.2px, transparent 1.2px);
        }
        @keyframes laser-sweep-canvas {
          0% { top: 0%; opacity: 0; }
          10% { opacity: 0.8; }
          90% { opacity: 0.8; }
          100% { top: 100%; opacity: 0; }
        }
        .laser-scan-canvas {
          position: absolute;
          left: 0; right: 0;
          height: 2.5px;
          background: linear-gradient(90deg, transparent, #10b981, transparent);
          box-shadow: 0 0 10px #10b981;
          pointer-events: none;
          z-index: 45;
          animation: laser-sweep-canvas 1.6s ease-in-out infinite;
        }
      `}</style>

      {/* ─── Üst Başlık ─────────────────────────────────────────────────────── */}
      <header className="flex justify-between items-center h-16 px-4 w-full bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 shrink-0 z-20 transition-colors shadow-sm">
        <div className="flex items-center gap-4">
          <button
            id="ds-back-to-zom"
            onClick={() => useUIStore.getState().setActiveModule('jarvis')}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-800 hover:bg-slate-100 dark:hover:bg-slate-800 transition-all font-bold text-xs cursor-pointer text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white shadow-sm"
          >
            <ArrowLeft className="w-3.5 h-3.5 text-indigo-500 dark:text-indigo-400" />
            <span>← ZOM</span>
          </button>

          <div className="flex items-center gap-2 ml-1">
            <span className="text-xl font-bold tracking-tight text-indigo-600 dark:text-indigo-400">
              Stitch Studio
            </span>
            <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border border-indigo-500/20 font-bold uppercase tracking-wider">
              PRO v4
            </span>
          </div>

        </div>

        <div className="flex-1 max-w-xs mx-8 hidden lg:block">
          <div className="bg-slate-100 dark:bg-slate-950 rounded-xl flex items-center px-3 border border-slate-200 dark:border-slate-800">
            <Search className="w-3.5 h-3.5 text-slate-400 mr-2" />
            <input
              id="ds-search"
              value={layerSearch}
              onChange={e => setLayerSearch(e.target.value)}
              className="bg-transparent border-none focus:outline-none w-full text-xs py-2 text-slate-700 dark:text-slate-200"
              placeholder="Katmanları ara..."
              type="text"
              autoComplete="off"
            />
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Undo/Redo */}
          <div className="flex items-center gap-0.5 border-r border-slate-200 dark:border-slate-800 pr-2 mr-1">
            <button id="ds-undo" onClick={undo} disabled={!canUndo}
              className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl transition-all text-slate-400 disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer" title="Geri Al (Ctrl+Z)">
              <span className="material-symbols-outlined text-[16px]">undo</span>
            </button>
            <button id="ds-redo" onClick={redo} disabled={!canRedo}
              className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl transition-all text-slate-400 disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer" title="Yinele (Ctrl+Y)">
              <span className="material-symbols-outlined text-[16px]">redo</span>
            </button>
          </div>

          {/* F3: Snap toggle */}
          <button
            id="ds-snap-toggle"
            onClick={() => setSnapGrid(g => g > 0 ? 0 : 8)}
            className={`p-2 rounded-xl border transition-all cursor-pointer text-xs font-bold flex items-center gap-1 ${
              snapGrid > 0
                ? 'bg-indigo-500/10 border-indigo-500/30 text-indigo-500'
                : 'border-slate-200 dark:border-slate-800 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
            }`}
            title={`Snap ${snapGrid > 0 ? 'Kapat' : 'Aç'} (8px grid)`}
          >
            <Grid className="w-3.5 h-3.5" />
            <span className="text-[9px] font-mono">{snapGrid > 0 ? '8px' : 'free'}</span>
          </button>

          {/* Tema */}
          <button id="ds-theme-toggle" onClick={() => setIsDark(d => !d)}
            className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full transition-all cursor-pointer text-slate-500 dark:text-slate-400 border border-slate-200 dark:border-slate-800 shadow-sm" title="Tema Değiştir">
            {isDark ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-indigo-600" />}
          </button>

          <button id="ds-play" onClick={() => setShowPreview(true)}
            className="bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-indigo-600 dark:text-indigo-400 font-bold px-4 py-2 rounded-xl transition-all active:scale-95 text-xs cursor-pointer border border-slate-200 dark:border-slate-700">
            Önizle
          </button>
          <button id="ds-export" onClick={() => setShowExport(true)}
            className="bg-indigo-600 hover:bg-indigo-500 text-white font-bold px-4 py-2 rounded-xl transition-all active:scale-95 text-xs cursor-pointer shadow-lg shadow-indigo-600/20">
            Export
          </button>
        </div>
      </header>

      {/* ─── Ana Çalışma Alanı ───────────────────────────────────────────────── */}
      <div className="flex flex-1 overflow-hidden min-h-0 relative">
        {/* Sol: Katmanlar (arama filtresi gerçek olarak uygulanır) */}
        <LayersPanel
          elements={layerSearch.trim()
            ? elements.filter(el =>
                (el.name || el.type).toLowerCase().includes(layerSearch.trim().toLowerCase()))
            : elements}
          selectedId={selectedId}
          onSelectId={setSelectedId}
          onUpdateElement={(id, changes) => updateElement(id, changes)}
          onDeleteElement={deleteElement}
          onBringForward={bringForward}
          onSendBackward={sendBackward}
        />

        {/* Merkez: Kanvas + AI Prompt */}
        <div className="flex-1 relative">
          <KonvaCanvasView
            elements={elements}
            canvasConfig={canvasConfig}
            selectedId={selectedId}
            activeTool={activeTool}
            zoom={zoom}
            isDark={isDark}
            isGenerating={isAIGenerating}
            snapGrid={snapGrid}
            onToolChange={setActiveTool}
            onZoomChange={setZoom}
            onSelectId={id => setSelectedId(id)}
            onAddElement={addElement}
            onCommitBulk={commitBulk}
            onUpdateElement={(id, changes) => updateElement(id, changes)}
          />

          {/* G2: AIPromptBar bağımsız bileşen — CanvasView dışında */}
          <AIPromptBar
            promptInput={promptInput}
            isGenerating={isAIGenerating}
            generationLog={generationLog}
            onChange={setPromptInput}
            onSubmit={applyAIPrompt}
          />
        </div>

        {/* Sağ: Inspector (F4: canvas config dahil) */}
        <InspectorPanel
          selectedElement={selectedElement}
          canvasConfig={canvasConfig}
          onUpdateElement={(id, changes) => updateElement(id, changes)}
          onDeleteElement={deleteElement}
          onDuplicate={duplicateElement}
          onCanvasConfigChange={changes => setCanvasConfig(prev => ({ ...prev, ...changes }))}
        />
      </div>

      {/* ─── Modaller ───────────────────────────────────────────────────────── */}
      <AnimatePresence>
        {showPreview && (
          <PreviewModal
            elements={elements}
            canvasConfig={canvasConfig}
            isDark={isDark}
            onClose={() => setShowPreview(false)}
          />
        )}
      </AnimatePresence>

      <AnimatePresence>
        {showExport && (
          <ExportModal
            elements={elements}
            canvasConfig={canvasConfig}
            onClose={() => setShowExport(false)}
          />
        )}
      </AnimatePresence>
    </div>
  );
}

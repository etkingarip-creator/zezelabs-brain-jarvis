// InspectorPanel — Sağ panel: seçili eleman özellik düzenleyici
// F4: Canvas boyut kontrolü (eleman seçili değilken)
// F5: Opacity, border-radius, rotation

import React from 'react';
import { Eye, EyeOff, Lock, Unlock, Trash2 } from 'lucide-react';
import type { CanvasElement, CanvasConfig } from '../../types/canvas';

interface InspectorPanelProps {
  selectedElement: CanvasElement | null;
  canvasConfig: CanvasConfig;
  onUpdateElement: (id: string, changes: Partial<CanvasElement>) => void;
  onDeleteElement: (id: string) => void;
  onDuplicate: (id: string) => void;
  onCanvasConfigChange: (changes: Partial<CanvasConfig>) => void;
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-[10px] text-slate-400 dark:text-slate-500 font-semibold font-mono uppercase tracking-wide">
        {label}
      </label>
      {children}
    </div>
  );
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <h4 className="font-bold text-[13px] text-slate-800 dark:text-white mb-3">{children}</h4>
  );
}

const inputCls =
  'bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-3 py-1.5 text-slate-800 dark:text-slate-100 focus:outline-none focus:border-indigo-500 text-xs w-full';

const sliderCls = 'w-full h-1.5 rounded-full accent-indigo-500 cursor-pointer';

// ─── Canvas Boyut Paneli (F4) ─────────────────────────────────────────────

function CanvasPanel({
  canvasConfig,
  onCanvasConfigChange,
}: {
  canvasConfig: CanvasConfig;
  onCanvasConfigChange: (c: Partial<CanvasConfig>) => void;
}) {
  const PRESETS = [
    { label: 'HD 16:9', w: 1280, h: 720 },
    { label: 'Card', w: 800, h: 500 },
    { label: 'Square', w: 600, h: 600 },
    { label: 'Mobile', w: 390, h: 844 },
    { label: 'Banner', w: 1200, h: 300 },
  ];

  return (
    <aside className="w-64 h-full bg-slate-50 dark:bg-slate-900 border-l border-slate-200 dark:border-slate-800 overflow-y-auto shrink-0 transition-colors">
      <div className="p-4 flex flex-col gap-5 text-xs">
        {/* Canvas boyutu */}
        <section>
          <SectionTitle>Kanvas · Boyut</SectionTitle>

          <div className="grid grid-cols-2 gap-2.5 mb-3">
            <Field label="Genişlik (W)">
              <input type="text" className={inputCls} value={canvasConfig.width}
                onChange={e => onCanvasConfigChange({ width: Math.max(100, parseInt(e.target.value) || 800) })} />
            </Field>
            <Field label="Yükseklik (H)">
              <input type="text" className={inputCls} value={canvasConfig.height}
                onChange={e => onCanvasConfigChange({ height: Math.max(100, parseInt(e.target.value) || 500) })} />
            </Field>
          </div>

          {/* Preset boyutlar */}
          <p className="text-[9px] font-mono text-slate-400 uppercase tracking-wider mb-2">Hazır Boyutlar</p>
          <div className="flex flex-wrap gap-1.5">
            {PRESETS.map(p => (
              <button
                key={p.label}
                onClick={() => onCanvasConfigChange({ width: p.w, height: p.h })}
                className={`text-[9px] px-2 py-1 rounded-lg border font-mono cursor-pointer transition-colors ${
                  canvasConfig.width === p.w && canvasConfig.height === p.h
                    ? 'bg-indigo-500/20 border-indigo-500/40 text-indigo-400'
                    : 'bg-white dark:bg-slate-950 border-slate-200 dark:border-slate-800 text-slate-500 hover:border-indigo-400'
                }`}
              >
                {p.label}<br />
                <span className="opacity-60">{p.w}×{p.h}</span>
              </button>
            ))}
          </div>
        </section>

        {/* Arka plan */}
        <section className="border-t border-slate-200 dark:border-slate-800 pt-4">
          <SectionTitle>Arka Plan</SectionTitle>
          <div className="flex items-center gap-3">
            <input type="color"
              value={canvasConfig.fill.startsWith('#') ? canvasConfig.fill : '#ffffff'}
              onChange={e => onCanvasConfigChange({ fill: e.target.value })}
              className="w-9 h-9 rounded-xl border border-slate-200 dark:border-slate-800 cursor-pointer overflow-hidden p-0 shrink-0" />
            <input type="text" value={canvasConfig.fill}
              onChange={e => onCanvasConfigChange({ fill: e.target.value })}
              className="font-mono text-xs text-slate-800 dark:text-slate-200 bg-transparent border-b border-slate-300 dark:border-slate-700 focus:outline-none focus:border-indigo-500 w-28" />
          </div>
        </section>

        {/* Çerçeve */}
        <section className="border-t border-slate-200 dark:border-slate-800 pt-4">
          <SectionTitle>Çerçeve</SectionTitle>
          <div className="flex items-center gap-3 mb-3">
            <input type="color"
              value={canvasConfig.stroke.startsWith('#') ? canvasConfig.stroke : '#6366f1'}
              onChange={e => onCanvasConfigChange({ stroke: e.target.value })}
              className="w-9 h-9 rounded-xl border border-slate-200 dark:border-slate-800 cursor-pointer overflow-hidden p-0 shrink-0" />
            <input type="text" value={canvasConfig.stroke}
              onChange={e => onCanvasConfigChange({ stroke: e.target.value })}
              className="font-mono text-xs text-slate-800 dark:text-slate-200 bg-transparent border-b border-slate-300 dark:border-slate-700 focus:outline-none focus:border-indigo-500 w-28" />
          </div>
          <Field label="Kalınlık">
            <input type="number" min={0} max={20} value={canvasConfig.strokeWidth}
              onChange={e => onCanvasConfigChange({ strokeWidth: parseInt(e.target.value) || 0 })}
              className={inputCls} />
          </Field>
        </section>

        <p className="text-[10px] text-slate-400 text-center font-mono mt-2">
          Eleman seçmek için kanvasa tıklayın
        </p>
      </div>
    </aside>
  );
}

// ─── Element Inspector ────────────────────────────────────────────────────

export function InspectorPanel({
  selectedElement: sel,
  canvasConfig,
  onUpdateElement,
  onDeleteElement,
  onDuplicate,
  onCanvasConfigChange,
}: InspectorPanelProps) {
  // Eleman seçili değilse canvas paneli göster (F4)
  if (!sel) {
    return (
      <CanvasPanel
        canvasConfig={canvasConfig}
        onCanvasConfigChange={onCanvasConfigChange}
      />
    );
  }

  const update = (changes: Partial<CanvasElement>) => onUpdateElement(sel.id, changes);

  return (
    <aside className="w-64 h-full bg-slate-50 dark:bg-slate-900 border-l border-slate-200 dark:border-slate-800 overflow-y-auto shrink-0 transition-colors" aria-label="Özellik denetçisi">
      <div className="p-4 flex flex-col gap-5 text-xs">

        {/* Boyut & Koordinat */}
        <section>
          <h4 className="font-bold text-[13px] text-slate-800 dark:text-white mb-3 capitalize">
            Düzen · <span className="text-indigo-400">{sel.type}</span>
          </h4>
          <div className="grid grid-cols-2 gap-2.5">
            {[
              { label: 'W', key: 'width' as const, min: 20 },
              { label: 'H', key: 'height' as const, min: 20 },
              { label: 'X', key: 'x' as const, min: undefined },
              { label: 'Y', key: 'y' as const, min: undefined },
            ].map(({ label, key, min }) => (
              <Field key={key} label={label}>
                <input type="text" className={inputCls} value={sel[key]}
                  onChange={e => {
                    const v = parseInt(e.target.value) || 0;
                    update({ [key]: min !== undefined ? Math.max(min, v) : v });
                  }} />
              </Field>
            ))}
          </div>
        </section>

        {/* Metin düzenleme */}
        {sel.type === 'text' && (
          <section className="border-t border-slate-200 dark:border-slate-800 pt-4">
            <SectionTitle>Metin</SectionTitle>
            <Field label="İçerik">
              <textarea value={sel.text || ''} rows={3}
                onChange={e => update({ text: e.target.value })}
                className={`${inputCls} resize-none`} />
            </Field>
            <div className="mt-2.5 grid grid-cols-2 gap-2">
              <Field label="Boyut (px)">
                <input type="text" className={inputCls} value={sel.fontSize || 16}
                  onChange={e => update({ fontSize: parseInt(e.target.value) || 12 })} />
              </Field>
              <Field label="Hizalama">
                <select className={inputCls} value={sel.textAlign || 'center'}
                  onChange={e => update({ textAlign: e.target.value as 'left' | 'center' | 'right' })}>
                  <option value="left">Sol</option>
                  <option value="center">Orta</option>
                  <option value="right">Sağ</option>
                </select>
              </Field>
            </div>
            <div className="mt-2">
              <Field label="Kalınlık">
                <select className={inputCls} value={sel.fontWeight || 'bold'}
                  onChange={e => update({ fontWeight: e.target.value as 'normal' | 'bold' })}>
                  <option value="normal">Normal</option>
                  <option value="bold">Kalın</option>
                </select>
              </Field>
            </div>
          </section>
        )}

        {/* Buton grubu */}
        {sel.type === 'button-group' && (
          <section className="border-t border-slate-200 dark:border-slate-800 pt-4">
            <SectionTitle>Buton Metinleri</SectionTitle>
            <div className="flex flex-col gap-2.5">
              <Field label="Birincil">
                <input type="text" className={inputCls} value={sel.textBtn1 || ''}
                  onChange={e => update({ textBtn1: e.target.value })} />
              </Field>
              <Field label="İkincil">
                <input type="text" className={inputCls} value={sel.textBtn2 || ''}
                  onChange={e => update({ textBtn2: e.target.value })} />
              </Field>
            </div>
          </section>
        )}

        {/* Dolgu rengi */}
        <section className="border-t border-slate-200 dark:border-slate-800 pt-4">
          <SectionTitle>Dolgu (Fill)</SectionTitle>
          <div className="flex items-center gap-3">
            <input type="color"
              value={sel.fill.startsWith('#') ? sel.fill : '#6366f1'}
              onChange={e => update({ fill: e.target.value })}
              className="w-9 h-9 rounded-xl border border-slate-200 dark:border-slate-800 bg-white cursor-pointer overflow-hidden p-0 shrink-0" />
            <input type="text" value={sel.fill}
              onChange={e => update({ fill: e.target.value })}
              className="font-mono text-xs text-slate-800 dark:text-slate-200 bg-transparent border-b border-slate-300 dark:border-slate-700 focus:outline-none focus:border-indigo-500 w-28" />
          </div>
        </section>

        {/* Çizgi (text hariç) */}
        {sel.type !== 'text' && (
          <section className="border-t border-slate-200 dark:border-slate-800 pt-4">
            <SectionTitle>Çizgi (Stroke)</SectionTitle>
            <div className="flex items-center gap-3 mb-3">
              <input type="color"
                value={sel.stroke.startsWith('#') ? sel.stroke : '#4f46e5'}
                onChange={e => update({ stroke: e.target.value })}
                className="w-9 h-9 rounded-xl border border-slate-200 dark:border-slate-800 cursor-pointer overflow-hidden p-0 shrink-0" />
              <input type="text" value={sel.stroke}
                onChange={e => update({ stroke: e.target.value })}
                className="font-mono text-xs text-slate-800 dark:text-slate-200 bg-transparent border-b border-slate-300 dark:border-slate-700 focus:outline-none focus:border-indigo-500 w-28" />
            </div>
            <Field label="Kalınlık">
              <input type="number" min={0} max={20} value={sel.strokeWidth}
                onChange={e => update({ strokeWidth: parseInt(e.target.value) || 0 })}
                className={inputCls} />
            </Field>
          </section>
        )}

        {/* F5: Görsel efektler */}
        <section className="border-t border-slate-200 dark:border-slate-800 pt-4">
          <SectionTitle>Görsel Efektler</SectionTitle>

          {/* Opaklık */}
          <div className="mb-3">
            <div className="flex justify-between mb-1.5">
              <span className="text-[10px] text-slate-400 font-mono uppercase tracking-wide">Opaklık</span>
              <span className="text-[10px] text-slate-500 font-mono">{sel.opacity ?? 100}%</span>
            </div>
            <input type="range" min={0} max={100} step={1}
              value={sel.opacity ?? 100}
              onChange={e => update({ opacity: parseInt(e.target.value) })}
              className={sliderCls} />
          </div>

          {/* Yuvarlatma (text ve circle hariç) */}
          {sel.type !== 'text' && sel.type !== 'circle' && (
            <div className="mb-3">
              <div className="flex justify-between mb-1.5">
                <span className="text-[10px] text-slate-400 font-mono uppercase tracking-wide">Köşe Yuvarlaması</span>
                <span className="text-[10px] text-slate-500 font-mono">{sel.borderRadius ?? 0}px</span>
              </div>
              <input type="range" min={0} max={200} step={1}
                value={sel.borderRadius ?? 0}
                onChange={e => update({ borderRadius: parseInt(e.target.value) })}
                className={sliderCls} />
            </div>
          )}

          {/* Döndürme */}
          <div>
            <div className="flex justify-between mb-1.5">
              <span className="text-[10px] text-slate-400 font-mono uppercase tracking-wide">Döndürme</span>
              <span className="text-[10px] text-slate-500 font-mono">{sel.rotation ?? 0}°</span>
            </div>
            <input type="range" min={0} max={360} step={1}
              value={sel.rotation ?? 0}
              onChange={e => update({ rotation: parseInt(e.target.value) })}
              className={sliderCls} />
          </div>
        </section>

        {/* Katman kontrolü */}
        <section className="border-t border-slate-200 dark:border-slate-800 pt-4">
          <SectionTitle>Katman</SectionTitle>
          <div className="grid grid-cols-2 gap-2 mb-2">
            <button onClick={() => update({ visible: !sel.visible })}
              className="flex items-center justify-center gap-1.5 py-2 rounded-xl bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 hover:bg-slate-100 dark:hover:bg-slate-900 transition-all font-semibold cursor-pointer">
              {sel.visible ? <Eye className="w-3.5 h-3.5 text-indigo-400" /> : <EyeOff className="w-3.5 h-3.5 text-slate-400" />}
              <span>{sel.visible ? 'Gizle' : 'Göster'}</span>
            </button>
            <button onClick={() => update({ locked: !sel.locked })}
              className="flex items-center justify-center gap-1.5 py-2 rounded-xl bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 hover:bg-slate-100 dark:hover:bg-slate-900 transition-all font-semibold cursor-pointer">
              {sel.locked ? <Lock className="w-3.5 h-3.5 text-indigo-400" /> : <Unlock className="w-3.5 h-3.5 text-slate-400" />}
              <span>{sel.locked ? 'Kilitle' : 'Kilit Aç'}</span>
            </button>
          </div>
          <button onClick={() => onDuplicate(sel.id)}
            className="w-full py-2 rounded-xl border border-indigo-200 dark:border-indigo-900 hover:bg-indigo-500/10 text-indigo-500 font-bold transition-all cursor-pointer text-[10px] uppercase font-mono tracking-wider flex items-center justify-center gap-1.5 mb-2">
            <span className="material-symbols-outlined text-[14px]">content_copy</span>
            <span>Çoğalt (Ctrl+D)</span>
          </button>
          <button onClick={() => onDeleteElement(sel.id)}
            className="w-full py-2 rounded-xl border border-red-200 dark:border-red-950 hover:bg-red-500/10 hover:border-red-500/30 text-red-500 font-bold transition-all cursor-pointer text-[10px] uppercase font-mono tracking-wider flex items-center justify-center gap-1.5">
            <Trash2 className="w-3.5 h-3.5" />
            <span>Katmanı Sil (Del)</span>
          </button>
        </section>

      </div>
    </aside>
  );
}

// LayersPanel — Sol panel: katman listesi yönetimi

import React from 'react';
import {
  Layers3,
  Folder,
  HelpCircle,
  MessageSquare,
  Eye,
  EyeOff,
  Lock,
  Unlock,
  Trash2,
  Square,
  Circle as CircleIcon,
  Triangle as TriangleIcon,
  Type,
  Image as ImageIcon,
} from 'lucide-react';
import type { CanvasElement } from '../../types/canvas';

interface LayersPanelProps {
  elements: CanvasElement[];
  selectedId: string | null;
  onSelectId: (id: string) => void;
  onUpdateElement: (id: string, changes: Partial<CanvasElement>) => void;
  onDeleteElement: (id: string) => void;
  onBringForward: (id: string) => void;
  onSendBackward: (id: string) => void;
}

function LayerIcon({ type }: { type: CanvasElement['type'] }) {
  switch (type) {
    case 'text':       return <Type className="w-3.5 h-3.5 text-indigo-400 shrink-0" />;
    case 'rect':       return <Square className="w-3.5 h-3.5 text-blue-400 shrink-0" />;
    case 'circle':     return <CircleIcon className="w-3.5 h-3.5 text-emerald-400 shrink-0" />;
    case 'triangle':   return <TriangleIcon className="w-3.5 h-3.5 text-amber-500 shrink-0" />;
    case 'button-group': return <span className="material-symbols-outlined text-[14px] text-fuchsia-400 shrink-0">smart_button</span>;
    case 'image':      return <ImageIcon className="w-3.5 h-3.5 text-rose-400 shrink-0" />;
    default:           return null;
  }
}

export function LayersPanel({
  elements,
  selectedId,
  onSelectId,
  onUpdateElement,
  onDeleteElement,
  onBringForward,
  onSendBackward,
}: LayersPanelProps) {
  // z-index'e göre tersten sırala (üstteki katman listede de üstte görünür)
  const sorted = [...elements].sort((a, b) => b.zIndex - a.zIndex);

  return (
    <aside
      className="w-64 flex flex-col py-4 px-3 gap-4 bg-slate-50 dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 shrink-0 overflow-y-auto transition-colors"
      aria-label="Katmanlar paneli"
    >
      {/* Başlık */}
      <div className="flex items-center gap-3 px-1 mb-1">
        <div className="w-9 h-9 rounded-xl bg-indigo-500/10 text-indigo-600 dark:bg-indigo-600/15 dark:text-indigo-400 flex items-center justify-center shadow-sm">
          <Layers3 className="w-5 h-5" />
        </div>
        <div>
          <h3 className="font-semibold text-xs text-slate-900 dark:text-white">Stitch Katmanları</h3>
          <p className="text-[10px] text-slate-400 dark:text-slate-500 font-mono">{elements.length} katman</p>
        </div>
      </div>

      <div className="flex flex-col gap-1 flex-1">
        {/* Çalışma alanı etiketi */}
        <div className="flex items-center gap-2.5 p-2.5 rounded-xl text-indigo-600 dark:text-indigo-400 font-bold bg-indigo-500/5 dark:bg-indigo-500/10 cursor-default text-xs border border-indigo-500/10">
          <Folder className="w-4 h-4" />
          <span>Bileşen Katmanları</span>
        </div>

        {/* Katman listesi */}
        <div className="mt-4 pt-4 border-t border-slate-200 dark:border-slate-800 flex-1">
          <p className="text-[9px] uppercase tracking-wider text-slate-400 dark:text-slate-500 font-bold px-1.5 mb-3 font-mono">
            KATMAN LİSTESİ
          </p>

          <div className="space-y-1 overflow-y-auto max-h-[400px] pr-1" role="listbox">
            {sorted.length === 0 ? (
              <div className="text-center text-[10px] text-slate-400 py-8 border border-dashed border-slate-200 dark:border-slate-800 rounded-xl">
                Henüz katman yok.<br />Yukarıdan bir şekil ekleyin.
              </div>
            ) : (
              sorted.map(el => {
                const isSelected = selectedId === el.id;
                return (
                  <div
                    key={el.id}
                    role="option"
                    aria-selected={isSelected}
                    onClick={() => onSelectId(el.id)}
                    className={`flex items-center gap-2 px-2.5 py-2 rounded-xl cursor-pointer group transition-all text-xs border ${
                      isSelected
                        ? 'bg-indigo-500/10 dark:bg-indigo-500/15 border-indigo-500/30 text-indigo-600 dark:text-indigo-300'
                        : 'bg-white dark:bg-slate-950/40 hover:bg-slate-100 dark:hover:bg-slate-800/80 border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400'
                    }`}
                  >
                    <LayerIcon type={el.type} />
                    <span className="flex-1 truncate font-medium">{el.name}</span>

                    {/* Satır içi kontroller */}
                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      {/* Z-index */}
                      <button
                        title="Öne getir"
                        onClick={e => { e.stopPropagation(); onBringForward(el.id); }}
                        className="text-slate-400 hover:text-indigo-500 cursor-pointer"
                        aria-label="Öne getir"
                      >
                        <span className="material-symbols-outlined text-[14px]">arrow_upward</span>
                      </button>
                      <button
                        title="Arkaya gönder"
                        onClick={e => { e.stopPropagation(); onSendBackward(el.id); }}
                        className="text-slate-400 hover:text-indigo-500 cursor-pointer"
                        aria-label="Arkaya gönder"
                      >
                        <span className="material-symbols-outlined text-[14px]">arrow_downward</span>
                      </button>

                      {/* Kilit */}
                      <button
                        onClick={e => { e.stopPropagation(); onUpdateElement(el.id, { locked: !el.locked }); }}
                        className="cursor-pointer"
                        title={el.locked ? 'Kilidi aç' : 'Kilitle'}
                      >
                        {el.locked
                          ? <Lock className="w-3 h-3 text-indigo-500" />
                          : <Unlock className="w-3 h-3 text-slate-400 hover:text-indigo-500" />
                        }
                      </button>

                      {/* Görünürlük */}
                      <button
                        onClick={e => { e.stopPropagation(); onUpdateElement(el.id, { visible: !el.visible }); }}
                        className="cursor-pointer"
                        title={el.visible ? 'Gizle' : 'Göster'}
                      >
                        {el.visible
                          ? <Eye className="w-3.5 h-3.5 text-slate-400 hover:text-indigo-500" />
                          : <EyeOff className="w-3.5 h-3.5 text-red-400 hover:text-indigo-500" />
                        }
                      </button>

                      {/* Sil */}
                      <button
                        onClick={e => { e.stopPropagation(); onDeleteElement(el.id); }}
                        className="cursor-pointer"
                        title="Katmanı sil"
                      >
                        <Trash2 className="w-3.5 h-3.5 text-slate-400 hover:text-red-500" />
                      </button>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>

      {/* Alt kısayollar */}
      <div className="mt-auto pt-4 border-t border-slate-200 dark:border-slate-800 flex flex-col gap-1 text-slate-400">
        <div className="flex items-center gap-2.5 p-2 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer text-xs transition-colors">
          <HelpCircle className="w-4 h-4" />
          <span>Yardım</span>
        </div>
        <div className="flex items-center gap-2.5 p-2 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer text-xs transition-colors">
          <MessageSquare className="w-4 h-4" />
          <span>Geri Bildirim</span>
        </div>
      </div>
    </aside>
  );
}

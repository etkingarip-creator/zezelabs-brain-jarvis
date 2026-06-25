// Toolbar — Araç çubuğu bileşeni
// Yüzen, glassmorphic araç seçici

import React from 'react';
import {
  MousePointer,
  Square,
  Circle as CircleIcon,
  Triangle as TriangleIcon,
  Type,
  Image as ImageIcon,
} from 'lucide-react';
import type { ToolType } from '../../types/canvas';

interface ToolbarProps {
  activeTool: ToolType;
  onToolChange: (tool: ToolType) => void;
}

interface ToolConfig {
  tool: ToolType;
  icon: React.ReactNode;
  title: string;
}

const TOOLS: ToolConfig[] = [
  { tool: 'select', icon: <MousePointer className="w-4 h-4" />, title: 'Seç (V)' },
  { tool: 'rect', icon: <Square className="w-4 h-4" />, title: 'Dikdörtgen (R)' },
  { tool: 'circle', icon: <CircleIcon className="w-4 h-4" />, title: 'Daire (O)' },
  { tool: 'triangle', icon: <TriangleIcon className="w-4 h-4" />, title: 'Üçgen (T)' },
  { tool: 'text', icon: <Type className="w-4 h-4" />, title: 'Metin (T)' },
  {
    tool: 'btn_group',
    icon: <span className="material-symbols-outlined text-[18px]">smart_button</span>,
    title: 'Buton Grubu (B)',
  },
  { tool: 'image', icon: <ImageIcon className="w-4 h-4" />, title: 'Görsel Alanı (I)' },
];

export function Toolbar({ activeTool, onToolChange }: ToolbarProps) {
  return (
    <div
      className="absolute top-4 left-1/2 -translate-x-1/2 bg-white/90 dark:bg-slate-900/90 backdrop-blur-md border border-slate-200 dark:border-slate-800 rounded-2xl flex items-center gap-1.5 p-1.5 shadow-xl z-30 pointer-events-auto"
      role="toolbar"
      aria-label="Çizim araçları"
    >
      {TOOLS.map((cfg, i) => (
        <React.Fragment key={cfg.tool}>
          {/* Seçim aracından sonra ayraç */}
          {i === 1 && (
            <div className="w-px h-6 bg-slate-200 dark:bg-slate-800 mx-0.5" aria-hidden="true" />
          )}
          <button
            onClick={() => onToolChange(cfg.tool)}
            className={`p-2 rounded-xl transition-all cursor-pointer ${
              activeTool === cfg.tool
                ? 'bg-indigo-500 text-white shadow-md shadow-indigo-500/30'
                : 'hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500 dark:text-slate-400'
            }`}
            title={cfg.title}
            aria-pressed={activeTool === cfg.tool}
          >
            {cfg.icon}
          </button>
        </React.Fragment>
      ))}
    </div>
  );
}

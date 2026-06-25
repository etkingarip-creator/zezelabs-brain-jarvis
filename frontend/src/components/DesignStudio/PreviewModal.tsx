// PreviewModal — Tam ekran sunum önizleme modu
// F5 güncellendi: opacity, rotation, borderRadius dahil

import React from 'react';
import { motion } from 'framer-motion';
import type { CanvasElement, CanvasConfig } from '../../types/canvas';

interface PreviewModalProps {
  elements: CanvasElement[];
  canvasConfig: CanvasConfig;
  isDark: boolean;
  onClose: () => void;
}

function renderPreviewElement(element: CanvasElement, isDark: boolean) {
  const rotation = element.rotation ?? 0;
  const opacity = (element.opacity ?? 100) / 100;
  const br = element.borderRadius ?? 0;

  const baseStyle: React.CSSProperties = {
    position: 'absolute',
    left: element.x,
    top: element.y,
    width: element.width,
    height: element.height,
    opacity,
    transform: rotation ? `rotate(${rotation}deg)` : undefined,
  };

  switch (element.type) {
    case 'text':
      return (
        <div
          key={element.id}
          style={{
            ...baseStyle,
            color: element.fill,
            fontSize: element.fontSize || 16,
            fontWeight: element.fontWeight || 'bold',
            textAlign: (element.textAlign as React.CSSProperties['textAlign']) || 'center',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            lineHeight: 1.2,
          }}
        >
          {element.text}
        </div>
      );
    case 'rect':
      return (
        <div key={element.id} style={baseStyle}>
          <svg width="100%" height="100%">
            <rect width="100%" height="100%" fill={element.fill} stroke={element.stroke} strokeWidth={element.strokeWidth} rx={br} />
          </svg>
        </div>
      );
    case 'circle':
      return (
        <div key={element.id} style={baseStyle}>
          <svg width="100%" height="100%">
            <ellipse cx="50%" cy="50%" rx="50%" ry="50%" fill={element.fill} stroke={element.stroke} strokeWidth={element.strokeWidth} />
          </svg>
        </div>
      );
    case 'triangle':
      return (
        <div key={element.id} style={baseStyle}>
          <svg width="100%" height="100%" viewBox="0 0 100 100" preserveAspectRatio="none">
            <polygon points="50,0 100,100 0,100" fill={element.fill} stroke={element.stroke} strokeWidth={element.strokeWidth} vectorEffect="non-scaling-stroke" />
          </svg>
        </div>
      );
    case 'button-group':
      return (
        <div key={element.id} style={{ ...baseStyle, display: 'flex', gap: 16, justifyContent: 'center', alignItems: 'center' }}>
          <button style={{ background: element.fill, color: '#fff', borderRadius: element.borderRadius ?? 9999, padding: '10px 24px', fontWeight: 700, fontSize: 13 }}>
            {element.textBtn1 || 'Button 1'}
          </button>
          <button style={{ border: `1px solid ${element.stroke}`, borderRadius: element.borderRadius ?? 9999, padding: '10px 24px', fontWeight: 700, background: 'transparent', color: isDark ? '#fff' : '#0f172a', fontSize: 13 }}>
            {element.textBtn2 || 'Button 2'}
          </button>
        </div>
      );
    case 'image':
      return (
        <div key={element.id} style={{ ...baseStyle, border: '1px dashed #94a3b8', borderRadius: br, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(148,163,184,0.1)' }}>
          <span className="material-symbols-outlined text-slate-400 text-4xl">image</span>
        </div>
      );
    default:
      return null;
  }
}

export function PreviewModal({ elements, canvasConfig, isDark, onClose }: PreviewModalProps) {
  // Kanvas çok büyükse viewport'a sığdır
  const maxW = Math.min(canvasConfig.width, window.innerWidth - 80);
  const scale = maxW / canvasConfig.width;
  const displayH = canvasConfig.height * scale;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-slate-950/98 z-50 flex flex-col items-center justify-center p-8 text-white font-sans"
      onClick={onClose}
    >
      {/* Üst bar */}
      <div className="absolute top-4 left-6 right-6 flex justify-between items-center z-50">
        <span className="text-xs font-bold tracking-wider font-mono text-slate-400">
          Presentation Mode · {elements.filter(el => el.visible).length} katman · {canvasConfig.width}×{canvasConfig.height}
        </span>
        <button
          onClick={onClose}
          className="px-4 py-2 bg-red-600 hover:bg-red-500 text-white rounded-xl text-xs font-bold transition-all cursor-pointer shadow-lg"
        >
          Çıkış (ESC)
        </button>
      </div>

      {/* Kanvas önizleme — viewport'a sığdırılmış */}
      <div
        className="relative shadow-2xl overflow-hidden rounded-3xl"
        onClick={e => e.stopPropagation()}
        style={{
          width: `${maxW}px`,
          height: `${displayH}px`,
          backgroundColor: canvasConfig.fill,
          border: `${canvasConfig.strokeWidth}px solid ${canvasConfig.stroke}`,
        }}
      >
        {/* İç scaler — orijinal koordinatlarda render */}
        <div
          className="absolute top-0 left-0 origin-top-left"
          style={{
            width: `${canvasConfig.width}px`,
            height: `${canvasConfig.height}px`,
            transform: `scale(${scale})`,
          }}
        >
          <div className="absolute inset-0 bg-[radial-gradient(#cbd5e1_1px,transparent_1px)] [background-size:24px_24px] opacity-5 pointer-events-none" />
          <div className="w-full h-full relative">
            {elements
              .filter(el => el.visible)
              .sort((a, b) => a.zIndex - b.zIndex)
              .map(el => renderPreviewElement(el, isDark))
            }
          </div>
        </div>
      </div>

      <p className="mt-5 text-xs text-slate-500 font-mono">
        Kapatmak için ESC tuşuna basın veya arka plana tıklayın
      </p>
    </motion.div>
  );
}

// ExportModal — F2: PNG Export + React JSX kod üretici
// html2canvas ile yüksek çözünürlüklü PNG indirme
// Injection-safe: JSON.stringify ile değer escape

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { FileText, CheckCircle, Copy, Download, Image } from 'lucide-react';
import type { CanvasElement, CanvasConfig } from '../../types/canvas';

interface ExportModalProps {
  elements: CanvasElement[];
  canvasConfig: CanvasConfig;
  onClose: () => void;
}

type ExportTab = 'png' | 'jsx';

function safe(val: string | number | undefined): string {
  return JSON.stringify(val ?? '');
}

function generateCode(elements: CanvasElement[], config: CanvasConfig): string {
  const visibleEls = elements.filter(el => el.visible).sort((a, b) => a.zIndex - b.zIndex);

  const elCodes = visibleEls.map(el => {
    const rotation = el.rotation ?? 0;
    const opacity = (el.opacity ?? 100) / 100;
    const br = el.borderRadius ?? 0;

    const baseStyle = `position:'absolute', left:${el.x}, top:${el.y}, width:${el.width}, height:${el.height}, opacity:${opacity}${rotation ? `, transform:'rotate(${rotation}deg)'` : ''}`;

    if (el.type === 'text') {
      return `  {/* ${el.name} */}
  <div style={{ ${baseStyle}, color:${safe(el.fill)}, fontSize:${el.fontSize || 16}, fontWeight:${safe(el.fontWeight || 'bold')}, textAlign:${safe(el.textAlign || 'center')}, display:'flex', alignItems:'center', justifyContent:'center', lineHeight:1.2 }}>
    ${el.text ?? ''}
  </div>`;
    }
    if (el.type === 'rect') {
      return `  {/* ${el.name} */}
  <div style={{ ${baseStyle} }}>
    <svg width="100%" height="100%"><rect width="100%" height="100%" fill=${safe(el.fill)} stroke=${safe(el.stroke)} strokeWidth={${el.strokeWidth}} rx={${br}} /></svg>
  </div>`;
    }
    if (el.type === 'circle') {
      return `  {/* ${el.name} */}
  <div style={{ ${baseStyle} }}>
    <svg width="100%" height="100%"><ellipse cx="50%" cy="50%" rx="50%" ry="50%" fill=${safe(el.fill)} stroke=${safe(el.stroke)} strokeWidth={${el.strokeWidth}} /></svg>
  </div>`;
    }
    if (el.type === 'triangle') {
      return `  {/* ${el.name} */}
  <div style={{ ${baseStyle} }}>
    <svg width="100%" height="100%" viewBox="0 0 100 100" preserveAspectRatio="none">
      <polygon points="50,0 100,100 0,100" fill=${safe(el.fill)} stroke=${safe(el.stroke)} strokeWidth={${el.strokeWidth}} vectorEffect="non-scaling-stroke" />
    </svg>
  </div>`;
    }
    if (el.type === 'button-group') {
      return `  {/* ${el.name} */}
  <div style={{ ${baseStyle}, display:'flex', gap:16, justifyContent:'center', alignItems:'center' }}>
    <button style={{ background:${safe(el.fill)}, color:'#fff', borderRadius:${el.borderRadius ?? 9999}, padding:'10px 24px', fontWeight:700 }}>${el.textBtn1 ?? 'Button 1'}</button>
    <button style={{ border:\`1px solid ${el.stroke}\`, borderRadius:${el.borderRadius ?? 9999}, padding:'10px 24px', fontWeight:700, background:'transparent' }}>${el.textBtn2 ?? 'Button 2'}</button>
  </div>`;
    }
    if (el.type === 'image') {
      return `  {/* ${el.name} — src ile değiştirin */}
  <img src="" alt="placeholder" style={{ ${baseStyle}, objectFit:'cover', borderRadius:${br} }} />`;
    }
    return '';
  }).join('\n\n');

  return `// Stitch Studio — Generated Production-Ready Component
import React from 'react';

export default function ExportedDesign() {
  return (
    <div style={{
      position: 'relative',
      width: ${config.width},
      height: ${config.height},
      backgroundColor: ${safe(config.fill)},
      border: \`${config.strokeWidth}px solid ${config.stroke}\`,
      borderRadius: 24,
      overflow: 'hidden',
    }}>
${elCodes}
    </div>
  );
}`;
}

export function ExportModal({ elements, canvasConfig, onClose }: ExportModalProps) {
  const [tab, setTab] = useState<ExportTab>('png');
  const [copied, setCopied] = useState(false);
  const [pngLoading, setPngLoading] = useState(false);

  const code = generateCode(elements, canvasConfig);

  const handleCopy = () => {
    navigator.clipboard.writeText(code).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  // F2: PNG Export — html2canvas dinamik import
  const handlePNGExport = async () => {
    setPngLoading(true);
    try {
      const canvasInner = document.getElementById('canvas-inner');
      if (!canvasInner) {
        alert('Kanvas bulunamadı. Lütfen editör ekranında olduğunuzdan emin olun.');
        return;
      }

      // Dynamic import — bundle'ı büyütmez, sadece gerektiğinde yüklenir
      const { default: html2canvas } = await import('html2canvas');

      const canvas = await html2canvas(canvasInner as HTMLElement, {
        scale: 2,              // 2× çözünürlük (Retina)
        useCORS: true,
        backgroundColor: canvasConfig.fill,
        width: canvasConfig.width,
        height: canvasConfig.height,
        logging: false,
      });

      const link = document.createElement('a');
      link.download = `stitch-export-${Date.now()}.png`;
      link.href = canvas.toDataURL('image/png');
      link.click();
    } catch (err) {
      console.error('PNG export hatası:', err);
      alert('PNG export başarısız. Konsolu kontrol edin.');
    } finally {
      setPngLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-6 text-white font-sans"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.95, y: 10 }}
        animate={{ scale: 1, y: 0 }}
        exit={{ scale: 0.95, y: 10 }}
        className="bg-slate-900 border border-slate-800 rounded-3xl p-6 max-w-2xl w-full flex flex-col space-y-4 shadow-2xl"
        onClick={e => e.stopPropagation()}
      >
        {/* Başlık */}
        <div className="flex justify-between items-center border-b border-slate-800 pb-3">
          <h3 className="text-xs font-bold uppercase tracking-wider font-mono flex items-center gap-2">
            <FileText className="w-4 h-4 text-indigo-400" />
            Dışa Aktar
          </h3>
          <button onClick={onClose}
            className="px-3.5 py-2 bg-slate-800 hover:bg-red-900/60 border border-slate-700 rounded-xl text-xs font-bold cursor-pointer transition-colors">
            Kapat
          </button>
        </div>

        {/* Tab seçici */}
        <div className="flex gap-2">
          {[
            { id: 'png' as ExportTab, icon: <Image className="w-3.5 h-3.5" />, label: 'PNG Görsel' },
            { id: 'jsx' as ExportTab, icon: <FileText className="w-3.5 h-3.5" />, label: 'React JSX Kodu' },
          ].map(t => (
            <button key={t.id} onClick={() => setTab(t.id)}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold border transition-all cursor-pointer ${
                tab === t.id
                  ? 'bg-indigo-600 border-indigo-500 text-white'
                  : 'bg-slate-800 border-slate-700 text-slate-400 hover:text-white'
              }`}>
              {t.icon}
              {t.label}
            </button>
          ))}
        </div>

        {/* PNG sekmesi */}
        {tab === 'png' && (
          <div className="flex flex-col items-center justify-center py-10 gap-6">
            <div className="w-20 h-20 rounded-2xl bg-indigo-600/10 border border-indigo-500/20 flex items-center justify-center">
              <Image className="w-10 h-10 text-indigo-400" />
            </div>
            <div className="text-center">
              <p className="font-bold text-white mb-1">2× Çözünürlüklü PNG</p>
              <p className="text-xs text-slate-400">
                {canvasConfig.width * 2} × {canvasConfig.height * 2}px · Yüksek kalite
              </p>
            </div>
            <button
              id="export-png-btn"
              onClick={handlePNGExport}
              disabled={pngLoading}
              className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white font-bold px-8 py-3 rounded-2xl text-sm transition-all hover:scale-105 active:scale-95 cursor-pointer shadow-lg shadow-indigo-600/20 disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {pngLoading ? (
                <>
                  <span className="w-4 h-4 rounded-full border-2 border-white/40 border-t-white animate-spin" />
                  Oluşturuluyor...
                </>
              ) : (
                <>
                  <Download className="w-4 h-4" />
                  PNG İndir
                </>
              )}
            </button>
          </div>
        )}

        {/* JSX sekmesi */}
        {tab === 'jsx' && (
          <>
            <div className="flex justify-end">
              <button onClick={handleCopy}
                className="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-xl text-xs font-bold flex items-center gap-2 transition-all cursor-pointer">
                {copied ? <CheckCircle className="w-4 h-4 text-emerald-400" /> : <Copy className="w-3.5 h-3.5 text-indigo-400" />}
                {copied ? 'Kopyalandı!' : 'Kodu Kopyala'}
              </button>
            </div>
            <div className="h-80 overflow-y-auto rounded-2xl bg-slate-950 p-4 border border-slate-800">
              <pre className="text-[10px] font-mono text-slate-300 text-left whitespace-pre leading-relaxed select-all">
                {code}
              </pre>
            </div>
            <p className="text-[10px] text-slate-500 font-mono text-center">
              {elements.filter(el => el.visible).length} eleman · opacity, rotation, borderRadius dahil
            </p>
          </>
        )}
      </motion.div>
    </motion.div>
  );
}

import React, { useState, useEffect } from 'react';
import { Shield, TrendingUp, Sparkles, Film, GraduationCap, BarChart3, Lock, AlertTriangle, Play, CheckCircle } from 'lucide-react';
import { getDepartmentTheme } from '../../lib/theme';

interface MorphicCanvasProps {
  departmentId: string;
}

export default function MorphicCanvas({ departmentId }: MorphicCanvasProps) {
  const theme = getDepartmentTheme(departmentId);
  const [ticker, setTicker] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setTicker(prev => prev + 1);
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  // 1. Crypto Trading Canvas Widget
  if (departmentId === 'crypto_trading') {
    const btcPrice = (98340 + Math.sin(ticker) * 120).toFixed(2);
    const ethPrice = (3420 + Math.cos(ticker) * 15).toFixed(2);
    const profit = (4.12 + Math.sin(ticker) * 0.1).toFixed(2);
    
    return (
      <div className={`p-4 rounded-xl border ${theme.borderClass} bg-slate-900/45 relative overflow-hidden transition-all duration-300`}>
        <div className="absolute top-2 right-2 flex items-center gap-1.5 text-[9px] text-emerald-400 font-mono">
          <TrendingUp className="w-3.5 h-3.5 animate-bounce" /> LIVE METRICS
        </div>
        <h4 className="text-xs font-semibold text-slate-400 mb-3 flex items-center gap-1.5 font-['Rajdhani']">
          💰 Portfolio valuation & Order Logs
        </h4>
        <div className="grid grid-cols-3 gap-3">
          <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800">
            <div className="text-[10px] text-slate-500 mb-0.5">BTC/USD</div>
            <div className="text-sm font-mono font-bold text-slate-200">${btcPrice}</div>
          </div>
          <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800">
            <div className="text-[10px] text-slate-500 mb-0.5">ETH/USD</div>
            <div className="text-sm font-mono font-bold text-slate-200">${ethPrice}</div>
          </div>
          <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800">
            <div className="text-[10px] text-slate-500 mb-0.5">Estimated ROI</div>
            <div className="text-sm font-mono font-bold text-emerald-400">+{profit}%</div>
          </div>
        </div>
      </div>
    );
  }

  // 2. Siber Güvenlik (Sec) Canvas Widget
  if (departmentId === 'zeze_sec') {
    const threatLevel = ticker % 3 === 0 ? 'Düşük' : 'Sıfır';
    return (
      <div className={`p-4 rounded-xl border ${theme.borderClass} bg-slate-900/45 relative overflow-hidden transition-all duration-300`}>
        <div className="absolute top-2 right-2 flex items-center gap-1.5 text-[9px] text-rose-400 font-mono">
          <Shield className="w-3.5 h-3.5 animate-pulse" /> SECURITY SHIELD ACTIVE
        </div>
        <h4 className="text-xs font-semibold text-slate-400 mb-3 flex items-center gap-1.5 font-['Rajdhani']">
          🛡️ Firewall & Penetration Audit Logs
        </h4>
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800 flex items-center justify-between">
            <div>
              <div className="text-[10px] text-slate-500">Security Index</div>
              <div className="text-base font-bold text-emerald-400">99.2%</div>
            </div>
            <Lock className="w-5 h-5 text-emerald-500" />
          </div>
          <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800 flex items-center justify-between">
            <div>
              <div className="text-[10px] text-slate-500">Active Vulnerabilities</div>
              <div className="text-base font-bold text-slate-300">{threatLevel === 'Sıfır' ? 0 : 1}</div>
            </div>
            <AlertTriangle className={`w-5 h-5 ${threatLevel === 'Sıfır' ? 'text-slate-650' : 'text-rose-500 animate-bounce'}`} />
          </div>
        </div>
      </div>
    );
  }

  // 3. Medya Fabrikası Canvas Widget
  if (departmentId === 'media_factory') {
    return (
      <div className={`p-4 rounded-xl border ${theme.borderClass} bg-slate-900/45 relative overflow-hidden transition-all duration-300`}>
        <div className="absolute top-2 right-2 flex items-center gap-1.5 text-[9px] text-cyan-400 font-mono">
          <Film className="w-3.5 h-3.5" /> SCHEDULER
        </div>
        <h4 className="text-xs font-semibold text-slate-400 mb-2.5 flex items-center gap-1.5 font-['Rajdhani']">
          🎥 Media Content Scheduler & Render Queue
        </h4>
        <div className="space-y-1.5">
          <div className="bg-slate-950/50 p-2 rounded-lg border border-slate-800 flex justify-between items-center text-xs">
            <span className="text-slate-350 truncate pr-2">Post: "Jarvis Autonomous Holding OS Showcase"</span>
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 shrink-0">Zamanlandı (14:30)</span>
          </div>
          <div className="bg-slate-950/50 p-2 rounded-lg border border-slate-800 flex justify-between items-center text-xs">
            <span className="text-slate-350 truncate pr-2">Video: "Inside the AI R&D Laboratory"</span>
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-400 shrink-0">Render Ediliyor (45%)</span>
          </div>
        </div>
      </div>
    );
  }

  // 4. Tasarım Atölyesi (Design) Canvas Widget
  if (departmentId === 'zeze_design') {
    return (
      <div className={`p-4 rounded-xl border ${theme.borderClass} bg-slate-900/45 relative overflow-hidden transition-all duration-300`}>
        <div className="absolute top-2 right-2 flex items-center gap-1.5 text-[9px] text-pink-400 font-mono">
          <Sparkles className="w-3.5 h-3.5" /> PALETTE ACTIVE
        </div>
        <h4 className="text-xs font-semibold text-slate-400 mb-3 flex items-center gap-1.5 font-['Rajdhani']">
          🎨 Corporate Style Tokens & Accent Palettes
        </h4>
        <div className="flex gap-2">
          <div className="flex-1 h-10 rounded bg-cyan-500 flex items-end p-1 shadow-inner"><span className="text-[8px] font-mono text-slate-950 font-bold">#06B6D4</span></div>
          <div className="flex-1 h-10 rounded bg-violet-600 flex items-end p-1 shadow-inner"><span className="text-[8px] font-mono text-white font-bold">#7C3AED</span></div>
          <div className="flex-1 h-10 rounded bg-pink-500 flex items-end p-1 shadow-inner"><span className="text-[8px] font-mono text-white font-bold">#EC4899</span></div>
          <div className="flex-1 h-10 rounded bg-slate-950 border border-slate-800 flex items-end p-1 shadow-inner"><span className="text-[8px] font-mono text-slate-400 font-bold">#020617</span></div>
        </div>
      </div>
    );
  }

  // 5. Sürekli Gelişim Akademi (Academy) Canvas Widget
  if (departmentId === 'zeze_academy') {
    const trainingProgress = (60 + (ticker * 8) % 40);
    return (
      <div className={`p-4 rounded-xl border ${theme.borderClass} bg-slate-900/45 relative overflow-hidden transition-all duration-300`}>
        <div className="absolute top-2 right-2 flex items-center gap-1.5 text-[9px] text-indigo-400 font-mono">
          <GraduationCap className="w-3.5 h-3.5 animate-bounce" /> LEARNING LOOP ACTIVE
        </div>
        <h4 className="text-xs font-semibold text-slate-400 mb-3 flex items-center gap-1.5 font-['Rajdhani']">
          🎓 Active Ajan Curriculums & Neural Retraining
        </h4>
        <div className="space-y-2">
          <div className="flex justify-between items-center text-xs">
            <span className="text-slate-350">Curriculum v2.4 (Crypto Trader Fine-Tuning)</span>
            <span className="text-indigo-400 font-bold font-mono">{trainingProgress}%</span>
          </div>
          <div className="w-full bg-slate-950 rounded-full h-2 border border-slate-800">
            <div 
              className="bg-indigo-500 h-1.5 rounded-full transition-all duration-500"
              style={{ width: `${trainingProgress}%` }}
            />
          </div>
        </div>
      </div>
    );
  }

  // Default fall-back: Simple Analytics KPI card
  return (
    <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/10">
      <h4 className="text-xs font-semibold text-slate-400 mb-2 flex items-center gap-1.5 font-['Rajdhani']">
        <BarChart3 className="w-3.5 h-3.5 text-cyan-400" /> Standart Departman Analitiği
      </h4>
      <p className="text-xs text-slate-500 leading-relaxed">
        Bu departmanın kendine has bir kanvas kartı tanımlanmamış. Canlı metrikler ve veri akışı sağ taraftaki Telemetri paneli üzerinden izlenebilir.
      </p>
    </div>
  );
}

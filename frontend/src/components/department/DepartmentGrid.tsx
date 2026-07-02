import { useState, useEffect } from 'react';
import { Play, Cpu, HardDrive, Zap } from 'lucide-react';
import type { DepartmentStatus } from '../../types/department';
import { getFloorColor } from './FloorList';
import { API_BASE } from '../../lib/config';

interface LiveTelemetry {
  cpu_percent: number | null; ram_percent: number | null; query_ms: number | null;
  roi_score: number | null; total_tokens: number; total_cost_usd: number;
}

interface DeptCard {
  id: string;
  label: string;
  floorId: number;
  icon: React.ElementType;
  color: string;
}

// Map department IDs to catalog information matching floors
const DEPT_CATALOG: DeptCard[] = [
  { id: 'zeze_dev', label: 'Geliştirme', floorId: 12, icon: Zap, color: '#38bdf8' },
  { id: 'crypto_trading', label: 'Kripto Trading', floorId: 2, icon: Zap, color: '#34d399' },
  { id: 'zeze_sec', label: 'Güvenlik', floorId: 15, icon: Zap, color: '#fb7185' },
  { id: 'zeze_design', label: 'Tasarım', floorId: 4, icon: Zap, color: '#f472b6' },
  { id: 'zeze_business', label: 'İş Geliştirme', floorId: 11, icon: Zap, color: '#10b981' },
  { id: 'zeze_ops', label: 'Operasyon', floorId: 6, icon: Zap, color: '#a78bfa' },
  { id: 'zeze_rnd', label: 'Ar-Ge', floorId: 14, icon: Zap, color: '#fbbf24' },
  { id: 'app_factory', label: 'App Factory', floorId: 8, icon: Zap, color: '#22d3ee' },
  { id: 'zeze_game', floorId: 9, label: 'Oyun', icon: Zap, color: '#c084fc' },
  { id: 'zeze_aro', floorId: 10, label: 'ARO', icon: Zap, color: '#67e8f9' },
  { id: 'zeze_comms', floorId: 13, label: 'İletişim', icon: Zap, color: '#86efac' },
  { id: 'zeze_compliance', floorId: 7, label: 'Uyumluluk', icon: Zap, color: '#fca5a5' },
  { id: 'media_factory', floorId: 5, label: 'Medya', icon: Zap, color: '#fb923c' },
  { id: 'zeze_betting', floorId: 16, label: 'Bahis', icon: Zap, color: '#facc15' },
  { id: 'zeze_trend', floorId: 1, label: 'Trend', icon: Zap, color: '#f59e0b' },
  { id: 'zeze_academy', floorId: 17, label: 'Akademi', icon: Zap, color: '#818cf8' },
  { id: 'zeze_production', floorId: 3, label: 'Prodüksiyon', icon: Zap, color: '#4ade80' },
];

interface Props {
  departments: Record<string, DepartmentStatus>;
  onSelect: (deptId: string) => void;
  selectedId?: string;
  onQuickLaunch?: (cmd: string, executeImmediately: boolean) => void;
}

export default function DepartmentGrid({ departments, onSelect, selectedId, onQuickLaunch }: Props) {
  const [quickCmds, setQuickCmds] = useState<Record<string, string>>({});

  // GERÇEK canlı telemetri (/api/telemetry/live) — 5sn'de bir, kaynak yoksa null → '—'
  const [tel, setTel] = useState<LiveTelemetry | null>(null);
  useEffect(() => {
    let alive = true;
    const fetchTel = async () => {
      try {
        const r = await fetch(`${API_BASE}/api/telemetry/live`);
        if (r.ok && alive) setTel(await r.json());
      } catch { /* offline → null → '—' */ }
    };
    fetchTel();
    // Ayarlardan okunan gerçek telemetri sıklığı (zom_settings_telemetry_delay, saniye)
    const delayMs = (parseInt(localStorage.getItem('zom_settings_telemetry_delay') || '5', 10) || 5) * 1000;
    const iv = setInterval(fetchTel, delayMs);
    return () => { alive = false; clearInterval(iv); };
  }, []);

  const onlineCnt = Object.values(departments).filter(d => d.status === 'healthy').length;
  const totalTasks = Object.values(departments).reduce((s, d) => s + (d.queue_depth ?? 0), 0);

  return (
    <div 
      className="h-full flex flex-col overflow-hidden"
      style={{ fontFamily: "'Inter', sans-serif" }}
    >
      {/* ── BENTO HEADER SECTION (Global Metrics) ── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 px-6 pt-5 pb-3 shrink-0">
        
        {/* ZOM System Status Card */}
        <div
          className="rounded-2xl p-5 border flex flex-col justify-between"
          style={{
            background: 'rgba(22, 29, 46, 0.52)',
            borderColor: 'rgba(255, 255, 255, 0.07)',
            backdropFilter: 'blur(18px)',
            WebkitBackdropFilter: 'blur(18px)',
          }}
        >
          <div className="flex items-start justify-between mb-3">
            <div>
              <span 
                className="mono uppercase"
                style={{ 
                  fontFamily: "'JetBrains Mono', monospace", 
                  fontSize: '0.72rem', 
                  letterSpacing: '0.14em', 
                  color: '#58e5c9',
                  fontWeight: 600
                }}
              >
                ZOM SİSTEM SAĞLIĞI
              </span>
              <h3 
                className="font-semibold mt-1"
                style={{ 
                  fontFamily: "'Space Grotesk', sans-serif", 
                  fontSize: '0.94rem', 
                  color: '#e8ecf4' 
                }}
              >
                {onlineCnt}/{DEPT_CATALOG.length} Departman Aktif
              </h3>
            </div>
            <div className="text-right">
              <span 
                className="mono font-semibold"
                style={{ 
                  fontFamily: "'JetBrains Mono', monospace", 
                  fontSize: '1.35rem', 
                  color: '#58e5c9' 
                }}
              >
                {Math.round((onlineCnt / DEPT_CATALOG.length) * 100)}%
              </span>
              <span className="block text-[8px] text-slate-500 font-mono tracking-wider">INTEGRITY</span>
            </div>
          </div>
          
          <div className="space-y-3">
            <div>
              <div className="h-[5px] w-full bg-slate-800/60 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full"
                  style={{ 
                    width: `${(onlineCnt / DEPT_CATALOG.length) * 100}%`,
                    background: 'linear-gradient(90deg, #58e5c9, #9d7bff)'
                  }}
                />
              </div>
            </div>
            
            <div className="grid grid-cols-3 gap-2">
              <div className="rounded-lg p-2 bg-slate-950/40 border border-white/5 flex flex-col justify-center">
                <div 
                  className="mono flex items-center gap-1.5"
                  style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '0.72rem', color: '#6e7893' }}
                >
                  <Cpu className="w-3 h-3 text-[#58e5c9]" /> CPU
                </div>
                <div
                  className="mono font-semibold mt-0.5"
                  style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '0.88rem', color: '#e8ecf4' }}
                >
                  {tel?.cpu_percent != null ? `${tel.cpu_percent.toFixed(1)}%` : '—'}
                </div>
              </div>
              <div className="rounded-lg p-2 bg-slate-950/40 border border-white/5 flex flex-col justify-center">
                <div 
                  className="mono flex items-center gap-1.5"
                  style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '0.72rem', color: '#6e7893' }}
                >
                  <HardDrive className="w-3 h-3 text-[#9d7bff]" /> RAM
                </div>
                <div
                  className="mono font-semibold mt-0.5"
                  style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '0.88rem', color: '#e8ecf4' }}
                >
                  {tel?.ram_percent != null ? `${tel.ram_percent.toFixed(1)}%` : '—'}
                </div>
              </div>
              <div className="rounded-lg p-2 bg-slate-950/40 border border-white/5 flex flex-col justify-center">
                <div 
                  className="mono"
                  style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '0.72rem', color: '#6e7893' }}
                >
                  GÖREV SÜRESİ
                </div>
                <div
                  className="mono font-semibold mt-0.5"
                  style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '0.88rem', color: '#4ade80' }}
                >
                  {tel?.query_ms != null ? `${tel.query_ms}ms` : '—'}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Active Task / Auto-Pipeline Card */}
        <div
          className="rounded-2xl p-5 border flex flex-col justify-between"
          style={{
            background: 'rgba(22, 29, 46, 0.52)',
            borderColor: 'rgba(255, 255, 255, 0.07)',
            backdropFilter: 'blur(18px)',
            WebkitBackdropFilter: 'blur(18px)',
          }}
        >
          <div className="mb-2">
            <span 
              className="mono uppercase"
              style={{ 
                fontFamily: "'JetBrains Mono', monospace", 
                fontSize: '0.72rem', 
                letterSpacing: '0.14em', 
                color: '#9d7bff',
                fontWeight: 600
              }}
            >
              AKTİF TELEMETRİ / PIPELINE
            </span>
            <h3 
              className="font-semibold mt-1 truncate"
              style={{ 
                fontFamily: "'Space Grotesk', sans-serif", 
                fontSize: '0.94rem', 
                color: '#e8ecf4' 
              }}
            >
              {totalTasks > 0 ? `${totalTasks} Departman Görevi İşleniyor` : 'Hazır / Komut Bekleniyor'}
            </h3>
          </div>
          
          <div className="mt-2.5">
            <div className="flex items-center justify-between relative px-2">
              <div className="absolute top-1/2 left-0 right-0 h-[1px] bg-slate-800/80 -translate-y-1/2 z-0" />
              {[
                { label: 'Routing', done: true, current: false },
                { label: 'Execute', done: totalTasks > 0, current: totalTasks > 0 },
                { label: 'Quality', done: false, current: false },
                { label: 'Done', done: false, current: false },
              ].map((step, idx) => (
                <div key={idx} className="flex flex-col items-center z-10">
                  <div
                    className="w-3.5 h-3.5 rounded-full flex items-center justify-center border text-[8px] transition-all"
                    style={{
                      background: step.current
                        ? '#9d7bff'
                        : step.done
                        ? '#4ade80'
                        : 'var(--surface-card)',
                      borderColor: step.current
                        ? '#9d7bff'
                        : step.done
                        ? '#4ade80'
                        : 'rgba(255,255,255,0.07)',
                    }}
                  >
                    {step.done && !step.current && <span className="text-slate-950 font-bold">✓</span>}
                  </div>
                  <span 
                    className="mono mt-1"
                    style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '0.7rem', color: '#6e7893' }}
                  >
                    {step.label}
                  </span>
                </div>
              ))}
            </div>
            
            <div 
              className="mt-3.5 flex justify-between items-center mono"
              style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '0.74rem', color: '#6e7893' }}
            >
              <span className="truncate">Son durum: {totalTasks > 0 ? 'yürütülüyor' : 'ZOM Beklemede'}</span>
              <span className="text-violet-400 shrink-0 font-semibold">{totalTasks > 0 ? 'aktif' : 'bekliyor'}</span>
            </div>
          </div>
        </div>

        {/* ROI Performance Card */}
        <div
          className="rounded-2xl p-5 border flex flex-col justify-between"
          style={{
            background: 'rgba(22, 29, 46, 0.52)',
            borderColor: 'rgba(255, 255, 255, 0.07)',
            backdropFilter: 'blur(18px)',
            WebkitBackdropFilter: 'blur(18px)',
          }}
        >
          <div className="flex justify-between items-start mb-2">
            <span 
              className="mono uppercase"
              style={{ 
                fontFamily: "'JetBrains Mono', monospace", 
                fontSize: '0.72rem', 
                letterSpacing: '0.14em', 
                color: '#4ade80',
                fontWeight: 600
              }}
            >
              ROI VERİM
            </span>
            <span
              className="font-mono text-[9px] font-bold"
              style={{
                color: '#4ade80',
                background: 'rgba(74,222,128,0.12)',
                border: '1px solid rgba(74,222,128,0.25)',
                padding: '2px 7px',
                borderRadius: '6px'
              }}
            >
              {tel?.roi_score != null ? `ROI ${tel.roi_score}` : '—'}
            </span>
          </div>

          <div className="my-1.5">
            <h4
              className="mono font-semibold"
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: '1.35rem',
                color: '#e8ecf4'
              }}
            >
              {tel != null ? `$${tel.total_cost_usd.toFixed(2)}` : '—'}
            </h4>
            <span className="block text-[8px] text-slate-500 font-mono tracking-wider">TOPLAM HARCAMA (GERÇEK)</span>
          </div>

          <div
            className="space-y-1.5 mono"
            style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '0.74rem', color: '#6e7893' }}
          >
            <div className="flex justify-between">
              <span>Toplam token:</span>
              <span style={{ color: '#e8ecf4' }}>{tel != null ? tel.total_tokens.toLocaleString('tr-TR') : '—'}</span>
            </div>
            <div className="flex justify-between">
              <span>Aktif görev:</span>
              <span style={{ color: '#e8ecf4' }}>{totalTasks}</span>
            </div>
          </div>
        </div>
      </div>

      {/* ── DEPARTMENTS GRID ── */}
      <div className="flex-1 overflow-y-auto p-6 pt-3.5 scrollbar-brand">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {DEPT_CATALOG.map((dept) => {
            const data = departments[dept.id];
            const isSelected = selectedId === dept.id;
            const activeAgents = data?.active_agents ?? 0;
            const queueDepth = data?.queue_depth ?? 0;
            const apiCalls = data?.api_calls ?? 0;
            const color = getFloorColor(dept.floorId);
            const isFeatured = ['zeze_dev', 'crypto_trading', 'zeze_sec', 'zeze_design'].includes(dept.id);
            
            // Yük aktivitesi: yalnızca GERÇEK veriden; veri yoksa 0 (sahte aktivite yok)
            const baseActivity = data
              ? Math.min(100, Math.max(5, (data.active_agents * 25) + (data.queue_depth * 10) + (parseInt(data.system_usage.cpu) || 10)))
              : 0;

            // Featured Card Layout
            if (isFeatured) {
              return (
                <div
                  key={dept.id}
                  onClick={() => onSelect(dept.id)}
                  className="relative flex flex-col justify-between p-5 text-left rounded-2xl transition-all duration-150 border cursor-pointer select-none col-span-1 md:col-span-2 min-h-[170px] group"
                  style={{
                    background: isSelected 
                      ? 'rgba(255, 255, 255, 0.045)' 
                      : 'rgba(22, 29, 46, 0.52)',
                    borderColor: isSelected ? 'rgba(255, 255, 255, 0.16)' : 'rgba(255, 255, 255, 0.07)',
                    backdropFilter: 'blur(18px)',
                    WebkitBackdropFilter: 'blur(18px)',
                  }}
                  onMouseEnter={(e) => {
                    if (!isSelected) {
                      e.currentTarget.style.background = 'rgba(255, 255, 255, 0.03)';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!isSelected) {
                      e.currentTarget.style.background = 'rgba(22, 29, 46, 0.52)';
                    }
                  }}
                >
                  {/* Top Bar */}
                  <div className="flex items-start justify-between relative z-10 w-full mb-3">
                    <div className="flex items-center gap-3">
                      <span 
                        className="mono" 
                        style={{ 
                          fontFamily: "'JetBrains Mono', monospace", 
                          fontSize: '0.78rem', 
                          color: '#6e7893' 
                        }}
                      >
                        K{dept.floorId}
                      </span>
                      <div>
                        <h4 
                          className="font-semibold"
                          style={{ 
                            fontFamily: "'Space Grotesk', sans-serif", 
                            fontSize: '0.94rem', 
                            color: '#e8ecf4' 
                          }}
                        >
                          {dept.label}
                        </h4>
                        <span 
                          className="mono block"
                          style={{ 
                            fontFamily: "'JetBrains Mono', monospace", 
                            fontSize: '0.7rem', 
                            color: '#6e7893' 
                          }}
                        >
                          {dept.id}
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <span 
                        className="mono"
                        style={{ 
                          fontFamily: "'JetBrains Mono', monospace", 
                          fontSize: '0.7rem', 
                          color: '#6e7893',
                          background: 'rgba(255, 255, 255, 0.04)',
                          border: '1px solid rgba(255, 255, 255, 0.07)',
                          padding: '2px 8px',
                          borderRadius: '6px'
                        }}
                      >
                        {activeAgents} AJAN
                      </span>

                      <div
                        className="w-2 h-2 rounded-full shrink-0"
                        style={{
                          background: data?.status === 'healthy' ? '#4ade80' : data?.status === 'down' ? '#f87171' : '#fbbf24',
                        }}
                      />
                    </div>
                  </div>

                  {/* Activity Bar */}
                  <div className="w-full mb-3 shrink-0">
                    <div 
                      className="glow" 
                      style={{ 
                        width: '100%', 
                        height: '5px', 
                        borderRadius: '3px', 
                        background: 'rgba(255,255,255,0.06)', 
                        overflow: 'hidden' 
                      }}
                    >
                      <span 
                        className="glow-fill" 
                        style={{ 
                          display: 'block', 
                          height: '100%', 
                          borderRadius: '3px', 
                          width: `${baseActivity}%`, 
                          background: color 
                        }}
                      />
                    </div>
                  </div>

                  {/* Body Content */}
                  <div className="grid grid-cols-3 gap-2 w-full relative z-10 mb-2 text-center">
                    <div className="flex flex-col">
                      <span 
                        className="mono" 
                        style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '0.7rem', color: '#6e7893' }}
                      >
                        API ÇAĞRISI
                      </span>
                      <span 
                        className="mono font-semibold"
                        style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '0.88rem', color: '#e8ecf4' }}
                      >
                        {apiCalls}
                      </span>
                    </div>
                    <div className="flex flex-col">
                      <span 
                        className="mono" 
                        style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '0.7rem', color: '#6e7893' }}
                      >
                        KUYRUK
                      </span>
                      <span 
                        className="mono font-semibold"
                        style={{ 
                          fontFamily: "'JetBrains Mono', monospace", 
                          fontSize: '0.88rem', 
                          color: queueDepth > 0 ? '#fbbf24' : '#e8ecf4' 
                        }}
                      >
                        {queueDepth}
                      </span>
                    </div>
                    <div className="flex flex-col min-w-0">
                      <span
                        className="mono"
                        style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '0.7rem', color: '#6e7893' }}
                      >
                        DURUM
                      </span>
                      <span
                        className="mono font-semibold truncate"
                        style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '0.82rem',
                                 color: data?.activity === 'working' ? '#34d399' : (data?.activity === 'queued' ? '#fbbf24' : '#6e7893') }}
                        title={data?.current_task || (data?.activity ?? 'boşta')}
                      >
                        {data?.activity === 'working' ? (data?.current_task ? '▶ ' + data.current_task : '▶ çalışıyor')
                          : data?.activity === 'queued' ? '⏳ kuyrukta' : '● boşta'}
                      </span>
                    </div>
                  </div>

                  {/* Quick Launch — DOĞRUDAN o departmanın execute endpoint'ine (garantili routing) */}
                  <form
                    onSubmit={async (e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      const text = quickCmds[dept.id];
                      if (!text?.trim()) return;
                      setQuickCmds(prev => ({ ...prev, [dept.id]: '' }));
                      try {
                        // Router'ı atla → görev KESİN bu departmana gider
                        await fetch(`${API_BASE}/api/departments/${dept.id}/execute`, {
                          method: 'POST',
                          headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify({ description: text }),
                        });
                      } catch { /* offline */ }
                      onQuickLaunch?.(`[${dept.label}] ${text}`, false);  // sohbete iz düş (bilgi)
                    }}
                    onClick={(e) => e.stopPropagation()}
                    className="mt-1 flex gap-2 items-center w-full"
                    style={{
                      background: 'rgba(10, 14, 26, 0.6)',
                      border: '1px solid rgba(255, 255, 255, 0.16)',
                      borderRadius: '10px',
                      padding: '4px 4px 4px 10px'
                    }}
                  >
                    <input
                      type="text"
                      placeholder={`${dept.label} departmanına hızlı talimat…`}
                      value={quickCmds[dept.id] || ''}
                      onChange={(e) => {
                        const val = e.target.value;
                        setQuickCmds(prev => ({ ...prev, [dept.id]: val }));
                      }}
                      className="text-xs bg-transparent border-none outline-none text-[#e8ecf4] placeholder-[#6e7893] flex-1 py-1"
                    />
                    <button
                      type="submit"
                      disabled={!(quickCmds[dept.id] || '').trim()}
                      className="px-3 py-1.5 rounded-lg text-xs font-semibold cursor-pointer disabled:opacity-50"
                      style={{
                        background: 'linear-gradient(135deg, #58e5c9, #9d7bff)',
                        color: '#0a0e1a'
                      }}
                      title="Talimatı Gönder"
                    >
                      <Play className="w-3.5 h-3.5 fill-current" />
                    </button>
                  </form>
                </div>
              );
            }

            // Compact Card Layout (other 12)
            return (
              <div
                key={dept.id}
                onClick={() => onSelect(dept.id)}
                className="relative flex flex-col justify-between p-4 text-left rounded-2xl transition-all duration-150 border cursor-pointer select-none col-span-1 min-h-[125px] group"
                style={{
                  background: isSelected 
                    ? 'rgba(255, 255, 255, 0.045)' 
                    : 'rgba(22, 29, 46, 0.52)',
                  borderColor: isSelected ? 'rgba(255, 255, 255, 0.16)' : 'rgba(255, 255, 255, 0.07)',
                  backdropFilter: 'blur(18px)',
                  WebkitBackdropFilter: 'blur(18px)',
                }}
                onMouseEnter={(e) => {
                  if (!isSelected) {
                    e.currentTarget.style.background = 'rgba(255, 255, 255, 0.03)';
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isSelected) {
                    e.currentTarget.style.background = 'rgba(22, 29, 46, 0.52)';
                  }
                }}
              >
                {/* Top header line */}
                <div className="flex items-start justify-between relative z-10 w-full mb-1">
                  <span 
                    className="mono" 
                    style={{ 
                      fontFamily: "'JetBrains Mono', monospace", 
                      fontSize: '0.78rem', 
                      color: '#6e7893' 
                    }}
                  >
                    K{dept.floorId}
                  </span>

                  <div className="flex items-center gap-1.5">
                    {/* Hover prefill zap button */}
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        onQuickLaunch?.(`${dept.label}: `, false);
                      }}
                      className="opacity-0 group-hover:opacity-100 transition-all p-1 rounded hover:bg-slate-900 text-slate-500 hover:text-[#58e5c9] cursor-pointer"
                      title="Sohbette bu departmanı seç"
                    >
                      <Zap className="w-3.5 h-3.5" />
                    </button>

                    {/* Status dot */}
                    <div
                      className="w-1.5 h-1.5 rounded-full shrink-0"
                      style={{
                        background: data?.status === 'healthy' ? '#4ade80' : data?.status === 'down' ? '#f87171' : '#fbbf24',
                      }}
                    />
                  </div>
                </div>

                {/* Name */}
                <div className="relative z-10 mb-2">
                  <div 
                    className="font-semibold truncate leading-tight"
                    style={{ 
                      fontFamily: "'Space Grotesk', sans-serif", 
                      fontSize: '0.88rem', 
                      color: '#e8ecf4' 
                    }}
                  >
                    {dept.label}
                  </div>
                  <div 
                    className="mono leading-none"
                    style={{ 
                      fontFamily: "'JetBrains Mono', monospace", 
                      fontSize: '0.7rem', 
                      color: '#6e7893' 
                    }}
                  >
                    {dept.id}
                  </div>
                </div>

                {/* Activity bar */}
                <div className="w-full mb-2 shrink-0">
                  <div 
                    className="glow" 
                    style={{ 
                      width: '100%', 
                      height: '4px', 
                      borderRadius: '2px', 
                      background: 'rgba(255,255,255,0.06)', 
                      overflow: 'hidden' 
                    }}
                  >
                    <span 
                      className="glow-fill" 
                      style={{ 
                        display: 'block', 
                        height: '100%', 
                        borderRadius: '2px', 
                        width: `${baseActivity}%`, 
                        background: color 
                      }}
                    />
                  </div>
                </div>

                {/* Bottom line: metrics & label */}
                <div 
                  className="flex justify-between items-center relative z-10 w-full mt-1 mono border-t border-white/5 pt-1.5"
                  style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '0.7rem', color: '#6e7893' }}
                >
                  <span title={data?.current_task || (data?.activity ?? 'boşta')}
                        style={{ color: data?.activity === 'working' ? '#34d399' : (data?.activity === 'queued' ? '#fbbf24' : '#6e7893') }}>
                    {data?.activity === 'working' ? '▶ çalışıyor' : data?.activity === 'queued' ? '⏳ kuyruk' : '● boşta'}
                  </span>
                  <span>KUYRUK: <strong style={{ color: queueDepth > 0 ? '#fbbf24' : '#e8ecf4' }}>{queueDepth}</strong></span>
                </div>

                {/* Quick Launch (tüm departmanlarda) — doğrudan o departmanın execute'ine */}
                <form
                  onSubmit={async (e) => {
                    e.preventDefault(); e.stopPropagation();
                    const text = quickCmds[dept.id];
                    if (!text?.trim()) return;
                    setQuickCmds(prev => ({ ...prev, [dept.id]: '' }));
                    try {
                      await fetch(`${API_BASE}/api/departments/${dept.id}/execute`, {
                        method: 'POST', headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ description: text }),
                      });
                    } catch { /* offline */ }
                    onQuickLaunch?.(`[${dept.label}] ${text}`, false);
                  }}
                  onClick={(e) => e.stopPropagation()}
                  className="mt-2 flex gap-1.5 items-center w-full relative z-10"
                  style={{ background: 'rgba(10,14,26,0.6)', border: '1px solid rgba(255,255,255,0.14)', borderRadius: '8px', padding: '3px 3px 3px 8px' }}
                >
                  <input
                    type="text"
                    placeholder={`${dept.label} talimat…`}
                    value={quickCmds[dept.id] || ''}
                    onChange={(e) => setQuickCmds(prev => ({ ...prev, [dept.id]: e.target.value }))}
                    className="text-[11px] bg-transparent border-none outline-none text-[#e8ecf4] placeholder-[#6e7893] flex-1 py-0.5"
                  />
                  <button type="submit" disabled={!(quickCmds[dept.id] || '').trim()}
                    className="shrink-0 p-1 rounded disabled:opacity-30 text-[#58e5c9] hover:bg-slate-800" title="Gönder">
                    <Zap className="w-3.5 h-3.5" />
                  </button>
                </form>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

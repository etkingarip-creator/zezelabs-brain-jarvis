import { useState, useEffect, useRef } from 'react';

interface TelemetryPanelProps {
  selectedDeptId: string;
}

const DEPT_DATA: Record<string, { name: string; icon: string; color: string; agents: number; floor: number }> = {
  zeze_prompt:  { name: 'PROMPT MİMARİSİ', icon: '🧠', color: '#00f2fe', agents: 4, floor: 7 },
  zeze_sec:     { name: 'SİBER SAVUNMA',   icon: '🛡️', color: '#ef4444', agents: 3, floor: 6 },
  zeze_guard:   { name: 'YÖNETİŞİM',       icon: '🤖', color: '#db2777', agents: 2, floor: 5 },
  zeze_rnd:     { name: 'AR&GE',            icon: '⚛️', color: '#fbbf24', agents: 5, floor: 4 },
  zeze_eng:     { name: 'MÜHENDİSLİK',     icon: '🛠️', color: '#f59e0b', agents: 6, floor: 3 },
  zeze_trading: { name: 'KRİPTO TİCARET',  icon: '📈', color: '#10b981', agents: 3, floor: 2 },
  zeze_media:   { name: 'MEDYA FABRİKASI', icon: '🎬', color: '#a855f7', agents: 4, floor: 1 },
};

function AnimatedBar({ label, value, color }: { label: string; value: number; color: string }) {
  const [display, setDisplay] = useState(0);
  useEffect(() => {
    const t = setTimeout(() => setDisplay(value), 100);
    return () => clearTimeout(t);
  }, [value]);

  return (
    <div style={{ marginBottom: '10px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
        <span style={{ fontSize: '9px', color: '#94a3b8', letterSpacing: '1px' }}>{label}</span>
        <span style={{ fontSize: '9px', color, fontFamily: 'Consolas', fontWeight: 'bold' }}>{value}%</span>
      </div>
      <div style={{ height: '6px', background: '#0d1527', borderRadius: '3px', overflow: 'hidden' }}>
        <div style={{
          height: '100%',
          width: `${display}%`,
          background: `linear-gradient(90deg, ${color}80, ${color})`,
          borderRadius: '3px',
          transition: 'width 0.8s ease',
          boxShadow: `0 0 6px ${color}80`,
        }} />
      </div>
    </div>
  );
}

function LogFeed() {
  const [lines, setLines] = useState<string[]>([
    '⚡ JARVIS v4.0 başlatıldı',
    '→ Backend bağlantısı kuruldu',
    '→ Plugin sistemi aktif',
  ]);
  const bottomRef = useRef<HTMLDivElement>(null);

  const LOG_POOL = [
    '→ Ajan mesh senkronize edildi',
    '→ CEO kanalı dinleniyor',
    '→ Strateji modülü hazır',
    '→ Finans verisi güncellendi',
    '→ Güvenlik taraması tamamlandı',
    '→ AI inference motoru hazır',
    '→ WebSocket bağlantısı stabil',
    '→ Bellek optimizasyonu yapıldı',
    '→ Yeni görev kuyruğa alındı',
    '→ Kripto sinyal alındı',
    '→ Medya ajanı rapor gönderdi',
  ];

  useEffect(() => {
    const interval = setInterval(() => {
      const now = new Date().toLocaleTimeString('tr-TR');
      const msg = LOG_POOL[Math.floor(Math.random() * LOG_POOL.length)];
      setLines(prev => [...prev.slice(-30), `[${now}] ${msg}`]);
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [lines]);

  return (
    <div style={{
      flex: 1,
      overflowY: 'auto',
      fontFamily: 'Consolas, monospace',
      fontSize: '9px',
      color: '#10b981',
      lineHeight: '1.6',
      padding: '6px',
      background: '#03050f',
      borderRadius: '4px',
      border: '1px solid #1c2842',
    }}>
      {lines.map((l, i) => <div key={i}>{l}</div>)}
      <div ref={bottomRef} />
    </div>
  );
}

export default function TelemetryPanel({ selectedDeptId }: TelemetryPanelProps) {
  const dept = DEPT_DATA[selectedDeptId] || DEPT_DATA['zeze_prompt'];
  const [metrics, setMetrics] = useState({ cpu: 42, ram: 58, net: 23, ai: 71 });

  useEffect(() => {
    const iv = setInterval(() => {
      setMetrics({
        cpu: Math.floor(20 + Math.random() * 60),
        ram: Math.floor(35 + Math.random() * 45),
        net: Math.floor(10 + Math.random() * 50),
        ai:  Math.floor(30 + Math.random() * 65),
      });
    }, 2000);
    return () => clearInterval(iv);
  }, []);

  return (
    <div style={{
      width: '290px',
      minWidth: '290px',
      display: 'flex',
      flexDirection: 'column',
      gap: '12px',
      padding: '14px',
      background: '#0d1527',
      borderLeft: '1px solid #1c2842',
      height: '100%',
      overflowY: 'auto',
    }}>
      {/* Title */}
      <div style={{ color: '#00f2fe', fontSize: '10px', fontWeight: 'bold', letterSpacing: '2px', borderBottom: '1px solid #1c2842', paddingBottom: '8px' }}>
        📊  CANLI TELEMETRİ
      </div>

      {/* System Bars */}
      <AnimatedBar label="CPU" value={metrics.cpu} color="#00f2fe" />
      <AnimatedBar label="RAM" value={metrics.ram} color="#a855f7" />
      <AnimatedBar label="AĞBANT" value={metrics.net} color="#10b981" />
      <AnimatedBar label="AI YÜKÜ" value={metrics.ai} color="#db2777" />

      {/* Divider */}
      <div style={{ borderTop: '1px solid #1c2842' }} />

      {/* Selected Department */}
      <div>
        <div style={{ color: '#4a6080', fontSize: '8px', letterSpacing: '2px', marginBottom: '6px' }}>SEÇİLİ DEPARTMAN</div>
        <div style={{
          padding: '10px',
          background: '#070d19',
          border: `1px solid ${dept.color}`,
          borderRadius: '8px',
          boxShadow: `0 0 12px ${dept.color}30`,
        }}>
          <div style={{ fontSize: '20px', marginBottom: '4px' }}>{dept.icon}</div>
          <div style={{ color: dept.color, fontWeight: 'bold', fontSize: '12px', letterSpacing: '1px' }}>{dept.name}</div>
          <div style={{ color: '#94a3b8', fontSize: '10px', marginTop: '4px' }}>
            {dept.agents} Aktif Ajan  •  Kat {dept.floor}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginTop: '6px' }}>
            <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#10b981', boxShadow: '0 0 4px #10b981' }} />
            <span style={{ color: '#10b981', fontSize: '9px' }}>AKTİF</span>
          </div>
        </div>
      </div>

      {/* Divider */}
      <div style={{ borderTop: '1px solid #1c2842' }} />

      {/* Agent count */}
      <div>
        <div style={{ color: '#4a6080', fontSize: '8px', letterSpacing: '2px', marginBottom: '6px' }}>TOPLAM SİSTEM</div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px' }}>
          {[
            { label: 'AJAN', value: '27', color: '#00f2fe' },
            { label: 'DEPT', value: '7', color: '#a855f7' },
            { label: 'GÖREV', value: '143', color: '#10b981' },
            { label: 'UYARI', value: '2', color: '#f59e0b' },
          ].map(({ label, value, color }) => (
            <div key={label} style={{ padding: '8px', background: '#070d19', borderRadius: '6px', border: `1px solid ${color}40`, textAlign: 'center' }}>
              <div style={{ color, fontSize: '16px', fontWeight: 'bold', fontFamily: 'Consolas' }}>{value}</div>
              <div style={{ color: '#4a6080', fontSize: '8px', letterSpacing: '1px' }}>{label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Divider */}
      <div style={{ borderTop: '1px solid #1c2842' }} />

      {/* Live Log */}
      <div style={{ color: '#10b981', fontSize: '8px', fontWeight: 'bold', letterSpacing: '2px' }}>⚡  SİSTEM LOGU</div>
      <LogFeed />
    </div>
  );
}

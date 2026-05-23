import { motion } from 'framer-motion';

interface TelemetryProps {
  selectedDeptId: string;
}

interface DeptTelemetryData {
  skills: { name: string; score: number }[];
  selfTraining: number;
  learningSpeed: string;
  roadmap: string[];
  agents: { name: string; role: string; state: string; tokenSpend: number; motivation: number }[];
}

const DEPT_TELEMETRIES: Record<string, DeptTelemetryData> = {
  zeze_prompt: {
    skills: [
      { name: 'Sistem Prompt Yapılandırma', score: 94 },
      { name: 'Context Optimizasyonu', score: 88 },
      { name: 'Yanıt Doğrulama (Guardrails)', score: 92 }
    ],
    selfTraining: 85,
    learningSpeed: 'Yüksek (88 token/sn)',
    roadmap: ['Docker Sandbox Entegrasyonu', 'Otonom Prompt İyileştirme Mimarisi', 'LLM Maliyet Azaltma Analizi'],
    agents: [
      { name: 'Prompt Architect', role: 'System Prompt Engineering', state: 'Hazır', tokenSpend: 54000, motivation: 95 },
      { name: 'Context Optimizer', role: 'RAG Prompt Refinement', state: 'Optimize Ediyor', tokenSpend: 42000, motivation: 90 },
      { name: 'Output Validator', role: 'Response Guardrails', state: 'Boşta', tokenSpend: 23000, motivation: 85 }
    ]
  },
  zeze_guard: {
    skills: [
      { name: 'Bütçe Denetimi', score: 98 },
      { name: 'Güvenlik Politikası Yönetimi', score: 95 },
      { name: 'Hassas Veri Filtreleme (DLP)', score: 90 }
    ],
    selfTraining: 90,
    learningSpeed: 'Optimal (94 token/sn)',
    roadmap: ['Haftalık Token Sınırı Koruyucu', 'Dynamic Rate Limiting', 'DLP Pattern Generator'],
    agents: [
      { name: 'Budget Enforcement', role: 'Token Spend Limit', state: 'İzliyor', tokenSpend: 135000, motivation: 92 },
      { name: 'Policy Engine', role: 'Compliance & DLP', state: 'Aktif', tokenSpend: 48000, motivation: 88 }
    ]
  },
  zeze_sec: {
    skills: [
      { name: 'Kaynak Kod Analizi', score: 91 },
      { name: 'Enjeksiyon Koruması', score: 96 },
      { name: 'API Ağ Geçidi Güvenliği', score: 89 }
    ],
    selfTraining: 82,
    learningSpeed: 'Orta (64 token/sn)',
    roadmap: ['Statik Kod Analiz Kütüphanesi', 'Auto Patch Modülü', 'WAF Kural Jeneratörü'],
    agents: [
      { name: 'Vulnerability Scanner', role: 'Source Code Audit', state: 'Tarıyor', tokenSpend: 95000, motivation: 94 },
      { name: 'Code Healer', role: 'Auto Patch & Inject Guard', state: 'Boşta', tokenSpend: 6200, motivation: 89 },
      { name: 'Network Shield', role: 'WAF & API Guard', state: 'İzliyor', tokenSpend: 82000, motivation: 91 }
    ]
  },
  zeze_rnd: {
    skills: [
      { name: 'Makale & Trend Analizi', score: 93 },
      { name: 'Kütüphane Test & Kıyaslama', score: 87 },
      { name: 'Otonom Patch Entegrasyonu', score: 90 }
    ],
    selfTraining: 92,
    learningSpeed: 'Çok Yüksek (120 token/sn)',
    roadmap: ['arXiv Günlük Arama Ajanı', 'Otomatik Docker Test Odası', 'Package Benchmark v2'],
    agents: [
      { name: 'Trend Scout', role: 'GitHub & arXiv Monitor', state: 'Arıyor', tokenSpend: 18000, motivation: 96 },
      { name: 'Sandbox Engineer', role: 'Package Benchmarking', state: 'Test Ediyor', tokenSpend: 12000, motivation: 92 }
    ]
  },
  zeze_eng: {
    skills: [
      { name: 'Kod Sentezleme & Refaktör', score: 95 },
      { name: 'Mesaj Kuyruk Entegrasyonu', score: 92 },
      { name: 'CI/CD Otomasyonu', score: 88 }
    ],
    selfTraining: 89,
    learningSpeed: 'Yüksek (92 token/sn)',
    roadmap: ['FastAPI WebSocket Optimizasyonu', 'Tauri Rust Köprü Revizyonu', 'Auto Test Koşturucu'],
    agents: [
      { name: 'Dev Lead', role: 'Code Synthesis & Refactor', state: 'Yazıyor', tokenSpend: 195000, motivation: 95 },
      { name: 'RabbitMQ Integrator', role: 'Message Broker Setup', state: 'Kuruyor', tokenSpend: 84000, motivation: 91 },
      { name: 'CI/CD Test Runner', role: 'Auto Test Execution', state: 'Tarıyor', tokenSpend: 52000, motivation: 89 }
    ]
  },
  crypto_trading: {
    skills: [
      { name: 'Derin Defter Analizi', score: 96 },
      { name: 'Margin & Risk Yönetimi', score: 94 },
      { name: 'Smart Order Yönlendirme', score: 91 }
    ],
    selfTraining: 95,
    learningSpeed: 'Maksimum (150 token/sn)',
    roadmap: ['Order Book Liquidity Scan', 'Hedge Risk Koruyucu', 'Cross-Exchange Arbitraj'],
    agents: [
      { name: 'Market Scanner', role: 'Order Book Monitor', state: 'İzliyor', tokenSpend: 160000, motivation: 97 },
      { name: 'Risk Evaluator', role: 'Leverage & Margin Guard', state: 'Hazır', tokenSpend: 75000, motivation: 93 },
      { name: 'Execution Bot', role: 'Smart Order Routing', state: 'Boşta', tokenSpend: 46000, motivation: 90 }
    ]
  },
  media_factory: {
    skills: [
      { name: 'Video Sentezleme', score: 92 },
      { name: 'Post-Processing', score: 89 },
      { name: 'Meta Veri Optimizasyonu', score: 91 }
    ],
    selfTraining: 80,
    learningSpeed: 'Orta (58 token/sn)',
    roadmap: ['Holografik Frame Render', 'Metadata Auto Tagging', 'Dynamic Compression Engine'],
    agents: [
      { name: 'Content Generator', role: 'Video Render Pipeline', state: 'İşliyor', tokenSpend: 45000, motivation: 92 },
      { name: 'Asset Pipeline', role: 'Post-processing & Meta', state: 'Boşta', tokenSpend: 11000, motivation: 87 }
    ]
  }
};

export default function Telemetry({ selectedDeptId }: TelemetryProps) {
  const data = DEPT_TELEMETRIES[selectedDeptId] || DEPT_TELEMETRIES.zeze_prompt;

  return (
    <div style={{
      width: '320px',
      background: '#0d1527',
      borderLeft: '1px solid #1c2842',
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      padding: '20px 15px',
      gap: '15px',
      overflowY: 'auto'
    }}>
      <span style={{ fontSize: '11px', fontWeight: 'bold', color: '#ff007f', letterSpacing: '1.5px', paddingLeft: '5px' }}>
        📊 DEPARTMAN TELEMETRİSİ
      </span>

      {/* Skills score grid */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', background: 'rgba(7, 11, 22, 0.5)', padding: '12px', border: '1px solid #1c2842', borderRadius: '8px' }}>
        <span style={{ fontSize: '10px', color: '#ff007f', fontWeight: 'bold' }}>⚡ YETENEK PUANLARI</span>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {data.skills.map((skill) => (
            <div key={skill.name} style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px' }}>
                <span style={{ color: '#64748b' }}>{skill.name}</span>
                <span style={{ color: '#00f2fe', fontWeight: 'bold' }}>{skill.score}/100</span>
              </div>
              <div style={{ height: '4px', background: '#1c2842', borderRadius: '2px', overflow: 'hidden' }}>
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${skill.score}%` }}
                  transition={{ duration: 0.8, ease: 'easeOut' }}
                  style={{ height: '100%', background: '#00f2fe' }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Self learning capability */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', background: 'rgba(7, 11, 22, 0.5)', padding: '12px', border: '1px solid #1c2842', borderRadius: '8px' }}>
        <span style={{ fontSize: '10px', color: '#00f2fe', fontWeight: 'bold' }}>⚛️ KENDİNİ EĞİTME METRİKLERİ</span>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: '10px', color: '#64748b' }}>Öğrenim Kapasitesi:</span>
          <span style={{ fontSize: '14px', fontWeight: 'bold', color: '#10b981' }}>%{data.selfTraining}</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: '10px', color: '#64748b' }}>Öğrenme Hızı:</span>
          <span style={{ fontSize: '10px', color: '#ffffff' }}>{data.learningSpeed}</span>
        </div>
      </div>

      {/* Autonomous roadmap */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', background: 'rgba(7, 11, 22, 0.5)', padding: '12px', border: '1px solid #1c2842', borderRadius: '8px' }}>
        <span style={{ fontSize: '10px', color: '#ff007f', fontWeight: 'bold' }}>🚀 OTONOM YOL HARİTASI</span>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          {data.roadmap.map((item, idx) => (
            <div key={item} style={{ display: 'flex', gap: '6px', fontSize: '10px', alignItems: 'flex-start' }}>
              <span style={{ color: '#ff007f', fontWeight: 'bold' }}>{idx + 1}.</span>
              <span style={{ color: '#ffffff' }}>{item}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Virtual Agent metrics / Behaviour */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <span style={{ fontSize: '10px', color: '#00f2fe', fontWeight: 'bold', paddingLeft: '5px' }}>👥 OFİS ÇALIŞANLARI & METRİK DAVRANIŞLAR</span>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {data.agents.map((agent) => (
            <div key={agent.name} style={{
              background: 'rgba(13, 21, 39, 0.5)',
              border: '1px solid #1c2842',
              borderRadius: '8px',
              padding: '10px 12px',
              display: 'flex',
              flexDirection: 'column',
              gap: '4px'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '12px', fontWeight: 'bold', color: '#ffffff' }}>{agent.name}</span>
                <span style={{
                  fontSize: '8px',
                  fontWeight: 'bold',
                  padding: '1px 4px',
                  borderRadius: '3px',
                  background: 'rgba(0, 242, 254, 0.15)',
                  color: '#00f2fe'
                }}>{agent.state}</span>
              </div>
              <span style={{ fontSize: '9px', color: '#64748b' }}>Rol: {agent.role}</span>
              
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '9px', color: '#64748b', marginTop: '3px' }}>
                <span>Harcanan Token: {agent.tokenSpend.toLocaleString()}</span>
                <span style={{ color: '#ff007f', fontWeight: 'bold' }}>Gelişim Arzusu: %{agent.motivation}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

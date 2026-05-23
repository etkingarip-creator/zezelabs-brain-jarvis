import { motion } from 'framer-motion';

export interface Department {
  id: string;
  name: string;
  status: 'AKTİF' | 'MEŞGUL' | 'TARANIYOR' | 'ALARM';
  activeTask: string;
  queueDepth: number;
  icon: string;
}

interface SidebarProps {
  selectedDeptId: string;
  onSelectDept: (id: string) => void;
}

export const DEPARTMENTS: Department[] = [
  { id: 'zeze_prompt', name: 'Zeze Prompt', status: 'AKTİF', activeTask: 'RAG Prompt Optimizasyonu', queueDepth: 0, icon: '⚛️' },
  { id: 'zeze_guard', name: 'Zeze Guard', status: 'AKTİF', activeTask: 'Ajan Bütçe Denetimi', queueDepth: 0, icon: '📊' },
  { id: 'zeze_sec', name: 'Zeze Sec', status: 'AKTİF', activeTask: 'Kaynak Kod Güvenlik Analizi', queueDepth: 1, icon: '🛡️' },
  { id: 'zeze_rnd', name: 'Zeze Rnd', status: 'TARANIYOR', activeTask: 'arXiv & GitHub Scout', queueDepth: 2, icon: '🔍' },
  { id: 'zeze_eng', name: 'Zeze Eng', status: 'MEŞGUL', activeTask: 'Masaüstü WebSocket Köprüleme', queueDepth: 4, icon: '🛠️' },
  { id: 'crypto_trading', name: 'Crypto Trading', status: 'AKTİF', activeTask: 'Likidite Defter Tarama', queueDepth: 0, icon: '📈' },
  { id: 'media_factory', name: 'Media Factory', status: 'AKTİF', activeTask: 'Video Sentezleme & Render', queueDepth: 1, icon: '🎬' }
];

export default function Sidebar({ selectedDeptId, onSelectDept }: SidebarProps) {
  return (
    <div style={{
      width: '280px',
      background: '#0d1527',
      borderRight: '1px solid #1c2842',
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      padding: '20px 15px',
      gap: '15px',
      overflowY: 'auto'
    }}>
      {/* CEO Info Panel */}
      <div style={{
        padding: '15px',
        background: 'rgba(255, 0, 127, 0.05)',
        border: '1px solid rgba(255, 0, 127, 0.25)',
        borderRadius: '10px',
        display: 'flex',
        flexDirection: 'column',
        gap: '4px',
        marginBottom: '10px'
      }}>
        <span style={{ fontSize: '10px', fontWeight: 'bold', color: '#ff007f', letterSpacing: '1.5px' }}>👑 CEO KOMUTA ODASI</span>
        <span style={{ fontSize: '14px', fontWeight: 'bold', color: '#ffffff' }}>Zezelabs Genel Müdürü</span>
        <span style={{ fontSize: '11px', color: '#64748b' }}>Yetki Seviyesi: Tam Erişim (ROOT)</span>
      </div>

      <span style={{ fontSize: '11px', fontWeight: 'bold', color: '#00f2fe', letterSpacing: '1px', paddingLeft: '5px' }}>
        🏢 DEPARTMAN KATMANLARI
      </span>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {DEPARTMENTS.map((dept) => {
          const isSelected = dept.id === selectedDeptId;
          
          return (
            <motion.div
              key={dept.id}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => onSelectDept(dept.id)}
              style={{
                padding: '12px 15px',
                background: isSelected ? 'rgba(0, 242, 254, 0.08)' : 'rgba(13, 21, 39, 0.5)',
                border: isSelected ? '1px solid #00f2fe' : '1px solid #1c2842',
                borderRadius: '8px',
                cursor: 'pointer',
                display: 'flex',
                flexDirection: 'column',
                gap: '6px',
                transition: 'border-color 0.2s, background-color 0.2s'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '16px' }}>{dept.icon}</span>
                  <span style={{ fontWeight: 'bold', fontSize: '13px', color: isSelected ? '#00f2fe' : '#ffffff' }}>
                    {dept.name}
                  </span>
                </div>
                
                {/* Status indicator badge */}
                <span style={{
                  fontSize: '9px',
                  fontWeight: 'bold',
                  padding: '2px 6px',
                  borderRadius: '4px',
                  background: dept.status === 'AKTİF' ? 'rgba(16, 185, 129, 0.15)' : 
                              dept.status === 'MEŞGUL' ? 'rgba(245, 158, 11, 0.15)' :
                              dept.status === 'TARANIYOR' ? 'rgba(37, 99, 235, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                  color: dept.status === 'AKTİF' ? '#10b981' : 
                         dept.status === 'MEŞGUL' ? '#f59e0b' :
                         dept.status === 'TARANIYOR' ? '#2563eb' : '#ef4444'
                }}>
                  {dept.status}
                </span>
              </div>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                <span style={{ fontSize: '10px', color: '#64748b', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  İşlem: {dept.activeTask}
                </span>
                <span style={{ fontSize: '9px', color: '#64748b' }}>
                  Kuyruk Derinliği: {dept.queueDepth}
                </span>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Building2,
  Users,
  Monitor,
  Thermometer,
  Wifi,
  Shield,
  Zap,
  Clock,
  TrendingUp,
  Activity,
  Bell,
  Coffee,
  Server,
  Video,
  Lightbulb,
  Briefcase,
  UserCheck,
  AlertTriangle,
  Radio,
  MapPin,
  Layers,
  Target
} from 'lucide-react';

interface Floor {
  id: number;
  name: string;
  type: 'executive' | 'office' | 'meeting' | 'cafeteria' | 'tech' | 'gym';
  occupancy: number;
  capacity: number;
  temperature: number;
  devices: number;
  activeDevices: number;
  status: 'active' | 'quiet' | 'maintenance';
}

interface Employee {
  id: number;
  name: string;
  avatar: string;
  department: string;
  status: 'in-office' | 'remote' | 'meeting' | 'break' | 'offline';
  floor: number;
  checkIn: string;
  role: string;
}

interface ActivityItem {
  id: number;
  type: 'entry' | 'exit' | 'meeting' | 'delivery' | 'alert' | 'system';
  message: string;
  time: string;
  icon: React.ElementType;
  priority: 'low' | 'medium' | 'high';
}

interface BuildingStats {
  totalEmployees: number;
  presentEmployees: number;
  visitors: number;
  meetings: number;
  energyUsage: number;
  parkingOccupancy: number;
}

const floors: Floor[] = [
  { id: 12, name: 'The Council (Yönetim)', type: 'executive', occupancy: 1, capacity: 1, temperature: 21, devices: 100, activeDevices: 100, status: 'active' },
  { id: 11, name: 'Visionary Strategy Office', type: 'executive', occupancy: 1, capacity: 1, temperature: 22, devices: 45, activeDevices: 45, status: 'active' },
  { id: 10, name: 'Sovereign Engineering Lab', type: 'tech', occupancy: 1, capacity: 1, temperature: 19, devices: 250, activeDevices: 250, status: 'active' },
  { id: 9, name: 'Cinematic Media Studio', type: 'tech', occupancy: 1, capacity: 1, temperature: 20, devices: 180, activeDevices: 180, status: 'active' },
  { id: 8, name: 'ZezePedia (Global Memory)', type: 'tech', occupancy: 1, capacity: 1, temperature: 18, devices: 500, activeDevices: 500, status: 'active' },
  { id: 7, name: 'E-Commerce Profit Hub', type: 'office', occupancy: 1, capacity: 1, temperature: 22, devices: 60, activeDevices: 60, status: 'active' },
  { id: 6, name: 'Market Intel & Sales', type: 'office', occupancy: 1, capacity: 1, temperature: 22, devices: 40, activeDevices: 40, status: 'active' },
  { id: 5, name: 'Audit & Quality Control', type: 'executive', occupancy: 1, capacity: 1, temperature: 21, devices: 30, activeDevices: 30, status: 'active' },
  { id: 4, name: 'Sovereign CLI Terminal', type: 'tech', occupancy: 1, capacity: 1, temperature: 18, devices: 15, activeDevices: 15, status: 'active' },
  { id: 3, name: 'Global Network Core', type: 'tech', occupancy: 1, capacity: 1, temperature: 17, devices: 1000, activeDevices: 1000, status: 'active' },
  { id: 2, name: 'Internal Auth & Security', type: 'executive', occupancy: 1, capacity: 1, temperature: 20, devices: 50, activeDevices: 50, status: 'active' },
  { id: 1, name: 'Lobby & Interface', type: 'office', occupancy: 1, capacity: 1, temperature: 23, devices: 20, activeDevices: 20, status: 'active' },
];

const employees: Employee[] = [
  { id: 1, name: 'The Oracle', avatar: 'OR', department: 'Strategy', status: 'in-office', floor: 11, checkIn: '00:00', role: 'Visionary Agent' },
  { id: 2, name: 'Sovereign Coder', avatar: 'SC', department: 'Engineering', status: 'in-office', floor: 10, checkIn: '00:00', role: 'Supreme Architect' },
  { id: 3, name: 'Media Director', avatar: 'MD', department: 'Content', status: 'in-office', floor: 9, checkIn: '00:00', role: 'Supreme Director' },
  { id: 4, name: 'Audit Master', avatar: 'AM', department: 'Quality', status: 'in-office', floor: 5, checkIn: '00:00', role: 'Ruthless Inspector' },
  { id: 5, name: 'Merchant Master', avatar: 'MM', department: 'E-Commerce', status: 'in-office', floor: 7, checkIn: '00:00', role: 'Global Merchant' },
  { id: 6, name: 'Shadow CEO', avatar: 'CEO', department: 'Management', status: 'in-office', floor: 12, checkIn: '00:00', role: 'ZOM Controller' },
];

const initialActivities: ActivityItem[] = [
  { id: 1, type: 'system', message: 'Sovereign Coder: Repo analizi tamamlandı', time: '21:54', icon: Server, priority: 'medium' },
  { id: 2, type: 'alert', message: 'Visionary Oracle: Yeni pazar trendi tespit edildi', time: '21:55', icon: Target, priority: 'high' },
  { id: 3, type: 'meeting', message: 'The Council: Haftalık strateji planı onaylandı', time: '21:56', icon: Users, priority: 'high' },
  { id: 4, type: 'system', message: 'Media Director: Sinematik render başlatıldı', time: '21:57', icon: Video, priority: 'low' },
];

export default function ZezelabsDashboard() {
  const [selectedFloor, setSelectedFloor] = useState<Floor | null>(null);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [activities, setActivities] = useState<ActivityItem[]>(initialActivities);
  const [buildingStats, setBuildingStats] = useState<BuildingStats>({
    totalEmployees: 245,
    presentEmployees: 187,
    visitors: 12,
    meetings: 8,
    energyUsage: 78,
    parkingOccupancy: 65,
  });
  const [viewMode, setViewMode] = useState<'building' | 'office'>('building');

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
      setBuildingStats(prev => ({
        ...prev,
        energyUsage: Math.min(100, Math.max(50, prev.energyUsage + (Math.random() - 0.5) * 2)),
        presentEmployees: Math.min(245, Math.max(180, prev.presentEmployees + Math.floor((Math.random() - 0.5) * 3))),
      }));

      if (Math.random() > 0.7) {
        const randomActivity: ActivityItem = {
          id: Date.now(),
          type: ['system', 'alert', 'meeting', 'system'][Math.floor(Math.random() * 4)] as ActivityItem['type'],
          message: [
            'Sovereign Coder: Kod refaktörü tamamlandı',
            'Audit Master: Kalite denetimi onay verdi',
            'Merchant Master: Satış trendi analizi bitti',
            'Visionary Oracle: Unicorn doping planı hazır',
            'ZezePedia: Yeni bilgi girişi yapıldı'
          ][Math.floor(Math.random() * 5)],
          time: new Date().toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' }),
          icon: [Server, Target, Users, Video, Lightbulb][Math.floor(Math.random() * 5)],
          priority: ['low', 'medium', 'high'][Math.floor(Math.random() * 3)] as ActivityItem['priority'],
        };
        setActivities(prev => [randomActivity, ...prev].slice(0, 10));
      }
    }, 3000);
    return () => clearInterval(timer);
  }, []);

  const getFloorTypeIcon = (type: Floor['type']) => {
    const icons = { executive: Building2, office: Monitor, meeting: Video, cafeteria: Utensils, tech: Server, gym: Dumbbell };
    return icons[type] || Building2;
  };

  const getStatusColor = (status: Floor['status']) => {
    const colors = { active: 'text-emerald-400 bg-emerald-500/20', quiet: 'text-yellow-400 bg-yellow-500/20', maintenance: 'text-red-400 bg-red-500/20' };
    return colors[status];
  };

  return (
    <div className="h-full flex flex-col bg-slate-950 overflow-hidden">
      <div className="border-b border-cyan-500/20 bg-slate-900/80 backdrop-blur-xl px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center shadow-lg shadow-violet-500/30">
            <Building2 className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="font-orbitron text-lg font-bold text-white tracking-wide">ZEZELABS HOLDING</h1>
            <p className="text-xs text-cyan-400/60 font-['Rajdhani']">Levent, İstanbul • 12 Kat • Canlı</p>
          </div>
        </div>
        <div className="flex bg-slate-800/50 rounded-lg p-1 border border-cyan-500/10">
          <button onClick={() => setViewMode('building')} className={`px-3 py-1 rounded text-xs ${viewMode==='building'?'bg-violet-500/20 text-violet-300':'text-cyan-400/60'}`}>Bina</button>
          <button onClick={() => setViewMode('office')} className={`px-3 py-1 rounded text-xs ${viewMode==='office'?'bg-violet-500/20 text-violet-300':'text-cyan-400/60'}`}>Ofis</button>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        <aside className="w-64 border-r border-cyan-500/20 bg-slate-900/50 overflow-y-auto p-2 space-y-1">
          {[...floors].reverse().map(floor => (
            <button 
              key={floor.id} 
              onClick={() => {
                setSelectedFloor(floor);
                setViewMode('office');
              }} 
              className={`w-full rounded-lg p-2 text-left border ${selectedFloor?.id===floor.id?'bg-violet-500/10 border-violet-500/40':'border-transparent hover:bg-white/5'}`}
            >
              <div className="flex justify-between items-center mb-1">
                <span className="font-orbitron text-xs font-bold text-cyan-400">{floor.id}. Kat</span>
                <span className={`w-2 h-2 rounded-full ${floor.status==='active'?'bg-emerald-400':'bg-yellow-400'}`} />
              </div>
              <p className="text-xs text-white truncate">{floor.name}</p>
            </button>
          ))}
        </aside>

        <main className="flex-1 p-6 relative overflow-y-auto">
          {viewMode === 'building' ? (
            <div className="grid grid-cols-3 gap-4 h-full">
              <div className="col-span-2 glass-card rounded-2xl p-6 bg-slate-900/40 relative overflow-hidden">
                <div className="absolute inset-0 opacity-10 bg-[radial-gradient(circle_at_center,_var(--color-primary)_0%,_transparent_70%)]" />
                <h2 className="font-orbitron text-sm mb-4 text-cyan-400 uppercase tracking-widest">Sistem Matrisi</h2>
                <div className="grid grid-cols-2 gap-4">
                  {[
                    { label: 'Enerji Tüketimi', val: buildingStats.energyUsage, color: 'yellow' },
                    { label: 'Hava Kalitesi', val: 94, color: 'emerald' },
                    { label: 'Ağ Yoğunluğu', val: 62, color: 'cyan' },
                    { label: 'Güvenlik Puanı', val: 100, color: 'violet' }
                  ].map(s => (
                    <div key={s.label} className="p-4 bg-black/20 rounded-xl border border-white/5">
                      <div className="flex justify-between text-xs mb-2 text-white/60"><span>{s.label}</span><span>{Math.round(s.val)}%</span></div>
                      <div className="h-1 bg-white/5 rounded-full overflow-hidden">
                        <div className={`h-full bg-${s.color}-500`} style={{width:`${s.val}%`}} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="glass-card rounded-2xl p-4 bg-slate-900/40 flex flex-col">
                <h2 className="font-orbitron text-xs mb-4 text-cyan-400 uppercase">Canlı Akış</h2>
                <div className="flex-1 space-y-3 overflow-y-auto pr-2 custom-scrollbar">
                  {activities.map(a => (
                    <div key={a.id} className="text-[10px] p-2 bg-white/5 rounded border border-white/5 hover:bg-white/10 transition-colors">
                      <div className="text-white/40 mb-1 flex justify-between">
                        <span>{a.time}</span>
                        <span className={`px-1 rounded ${a.priority === 'high' ? 'bg-red-500/20 text-red-400' : 'text-cyan-400'}`}>{a.priority}</span>
                      </div>
                      <div className="text-cyan-100">{a.message}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <AnimatePresence mode="wait">
              {selectedFloor ? (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  className="h-full flex flex-col space-y-4"
                >
                  <div className="flex justify-between items-center">
                    <div>
                      <h2 className="font-orbitron text-2xl text-white font-bold">{selectedFloor.name}</h2>
                      <p className="text-cyan-400/60 text-sm font-['Rajdhani']">Kat {selectedFloor.id} • Operasyonel Merkez</p>
                    </div>
                    <div className="flex gap-4">
                      <div className="text-right">
                        <p className="text-[10px] text-white/40 uppercase">Ajan Kapasitesi</p>
                        <p className="text-xl font-orbitron text-emerald-400">{selectedFloor.occupancy}/{selectedFloor.capacity}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-[10px] text-white/40 uppercase">Sistem Yükü</p>
                        <p className="text-xl font-orbitron text-cyan-400">%{selectedFloor.activeDevices}</p>
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-4 gap-4 flex-1">
                    <div className="col-span-3 glass-card rounded-2xl p-6 bg-slate-900/60 border border-cyan-500/20 relative overflow-hidden">
                       <div className="absolute top-4 right-6 flex gap-2">
                          <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                          <span className="text-[10px] text-emerald-400 uppercase font-bold tracking-tighter">Live Monitor</span>
                       </div>
                       
                       {/* Department Specific Layouts */}
                       <div className="h-full flex flex-col">
                          <div className="flex-1 bg-black/40 rounded-xl border border-white/5 p-4 font-mono text-[11px] text-cyan-400 overflow-hidden relative">
                             <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-black/60 pointer-events-none" />
                             {selectedFloor.id === 10 ? (
                               <div className="space-y-1">
                                  <p className="text-emerald-400">{">>>"} SovereignCoder initializing workspace...</p>
                                  <p>{">>>"} Scanning repository: manifests-core-v2</p>
                                  <p className="text-white/60">import {"{ SovereignCoder }"} from './zeze_eng';</p>
                                  <p className="text-white/60">const arch = new SovereignCoder();</p>
                                  <p className="text-yellow-400">WARNING: Memory optimization required in line 442</p>
                                  <p>{">>>"} Applying patch: O1_Performance_Boost</p>
                                  <p className="animate-pulse">_</p>
                               </div>
                             ) : selectedFloor.id === 9 ? (
                               <div className="flex flex-col h-full justify-center items-center space-y-4">
                                  <div className="w-48 h-2 bg-white/10 rounded-full overflow-hidden">
                                     <div className="h-full bg-violet-500 animate-[loading_2s_infinite]" style={{width: '65%'}} />
                                  </div>
                                  <p className="text-violet-300 font-orbitron animate-pulse">RENDERING: K-DRAMA_EP01_4K.mp4</p>
                                  <p className="text-[10px] text-white/40">Frame 442/1200 • GPU Load: 88%</p>
                               </div>
                             ) : (
                               <div className="space-y-2">
                                  <p>{">>>"} Accessing Global Memory (ZezePedia)...</p>
                                  <p>{">>>"} Analyzing market vectors: {new Date().toLocaleDateString()}</p>
                                  <p className="text-fuchsia-400">Found 3 new opportunities in SaaS-AI automation</p>
                                  <p>{">>>"} Reporting to The Council...</p>
                               </div>
                             )}
                          </div>
                       </div>
                    </div>

                    <div className="space-y-4">
                      <div className="glass-card rounded-2xl p-4 bg-slate-900/60 border border-white/10">
                        <h3 className="text-[10px] text-white/40 uppercase mb-3 tracking-widest font-bold">Aktif Ajanlar</h3>
                        <div className="space-y-2">
                          {employees.filter(e => e.floor === selectedFloor.id).map(agent => (
                            <div key={agent.id} className="flex items-center gap-3 p-2 bg-white/5 rounded-lg border border-white/5">
                              <div className="w-8 h-8 rounded-lg bg-cyan-500/20 flex items-center justify-center text-[10px] font-bold text-cyan-400 border border-cyan-500/40">
                                {agent.avatar}
                              </div>
                              <div>
                                <p className="text-xs text-white font-bold">{agent.name}</p>
                                <p className="text-[9px] text-cyan-400/60">{agent.role}</p>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                      
                      <div className="glass-card rounded-2xl p-4 bg-slate-900/60 border border-white/10 flex-1">
                         <h3 className="text-[10px] text-white/40 uppercase mb-3 tracking-widest font-bold">Mevcut Görevler</h3>
                         <div className="space-y-2">
                            <div className="p-2 bg-emerald-500/10 border border-emerald-500/20 rounded text-[9px]">
                               <p className="text-emerald-400 font-bold">PROJE_X_OPTIMIZE</p>
                               <p className="text-white/60">Ajan: SovereignCoder</p>
                            </div>
                            <div className="p-2 bg-white/5 border border-white/5 rounded text-[9px]">
                               <p className="text-white/80 font-bold">MARKET_SCAN_2026</p>
                               <p className="text-white/40">Durum: Beklemede</p>
                            </div>
                         </div>
                      </div>
                    </div>
                  </div>
                </motion.div>
              ) : (
                <div className="h-full flex items-center justify-center text-cyan-400/20 flex-col space-y-4">
                   <Layers className="w-16 h-16" />
                   <p className="font-orbitron text-sm">Lütfen İzlemek İstediğiniz Departmanı Seçin</p>
                </div>
              )}
            </AnimatePresence>
          )}
        </main>
      </div>
    </div>
  );
}

function Utensils(props: any) { return <Coffee {...props} /> }
function Dumbbell(props: any) { return <Activity {...props} /> }

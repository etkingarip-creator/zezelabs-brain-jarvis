import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Mic, 
  MicOff, 
  Send, 
  Cpu, 
  Wifi, 
  Thermometer,
  Clock,
  Zap,
  Globe,
  Lock,
  Activity,
  MessageCircle,
  Volume2,
  VolumeX,
} from 'lucide-react';
import Navigation from './components/Navigation';
import ZezelabsDashboard from './components/ZezelabsDashboard';

interface Message {
  id: string;
  role: 'user' | 'jarvis';
  text: string;
  timestamp: number;
}

interface SystemStats {
  cpu: number;
  memory: number;
  network: string;
  uptime: string;
}

export default function App() {
  const [activeModule, setActiveModule] = useState<'jarvis' | 'zezelabs'>('jarvis');
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [state, setState] = useState<'idle' | 'listening' | 'thinking' | 'speaking'>('idle');
  const [volume, setVolume] = useState(0);
  const [brainStatus, setBrainStatus] = useState<{val: string, model?: string}>({val: 'connecting'});
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [systemStats, setSystemStats] = useState<SystemStats>({
    cpu: 0, memory: 0, network: 'Connected', uptime: 'Standby'
  });
  
  const wsRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // ── WebSocket Connection ─────────────────────────────────
  useEffect(() => {
    let socket: WebSocket | null = null;
    const connect = () => {
      console.log('🔗 Jarvis Bağlantısı Kuruluyor...');
      socket = new WebSocket('ws://localhost:5000/ws');
      wsRef.current = socket;

      socket.onopen = () => {
        console.log('✅ Jarvis Bağlantısı Başarılı!');
        setBrainStatus({val: 'online'});
      };

      socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        switch (data.type) {
          case 'state': setState(data.val); break;
          case 'transcript': addMessage('user', data.val); break;
          case 'response': addMessage('jarvis', data.val, data.id); break;
          case 'volume': setVolume(data.val); break;
          case 'brain_status': setBrainStatus({val: data.val, model: data.model}); break;
          case 'stats':
            setSystemStats({
              cpu: data.cpu, memory: data.memory,
              network: 'Stable', uptime: data.uptime
            });
            break;
        }
      };
      socket.onclose = () => {
        console.log('❌ Jarvis Bağlantısı Koptu, Yenileniyor...');
        setBrainStatus({val: 'offline'});
        setTimeout(connect, 2000);
      };
    };
    connect();
    return () => socket?.close();
  }, []);

  const processedIds = useRef(new Set<string>()); // Anti-dupe for IDs
  const lastMsgRef = useRef({ text: '', time: 0 }); // Anti-dupe for content

  const addMessage = (role: 'user' | 'jarvis', text: string, id?: string) => {
    // 1. Check ID-based duplication
    if (id && processedIds.current.has(id)) return;
    if (id) processedIds.current.add(id);

    // 2. Check Content-based duplication (within 1s)
    const now = Date.now();
    if (role === 'jarvis' && text === lastMsgRef.current.text && (now - lastMsgRef.current.time) < 1000) return;
    lastMsgRef.current = { text, time: now };

    setMessages(prev => [...prev, { id: id || Math.random().toString(36), role, text, timestamp: Date.now() }]);
    setTimeout(() => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 100);
  };

  const handleSendMessage = () => {
    if (!input.trim() || !wsRef.current) return;
    const val = input.trim();
    addMessage('user', val);
    wsRef.current.send(JSON.stringify({ type: 'command', val: val }));
    setInput('');
  };

  const toggleMic = () => {
    const newState = state === 'listening' ? 'idle' : 'listening';
    setState(newState);
    if (wsRef.current) {
      wsRef.current.send(JSON.stringify({ 
        type: 'mic_toggle', 
        val: newState === 'listening' 
      }));
    }
  };

  const toggleVoice = () => {
    const newState = !voiceEnabled;
    setVoiceEnabled(newState);
    if (wsRef.current) {
      wsRef.current.send(JSON.stringify({ 
        type: 'voice_toggle', 
        val: newState 
      }));
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 grid-bg relative overflow-hidden font-['Rajdhani'] text-white">
      <div className="scanline" />
      
      {/* Background Glows */}
      <div className="fixed inset-0 pointer-events-none opacity-20">
        <div className="absolute top-1/4 -left-32 w-96 h-96 bg-cyan-500 rounded-full blur-[120px]" />
        <div className="absolute bottom-1/4 -right-32 w-96 h-96 bg-blue-600 rounded-full blur-[120px]" />
      </div>

      <div className="relative z-10 flex flex-col h-screen">
        {/* Header */}
        <header className="border-b border-cyan-500/20 bg-slate-900/50 backdrop-blur-xl px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="relative w-12 h-12">
              <div className="absolute inset-0 rounded-full border-2 border-cyan-400/30 rotate-ring" />
              <div className="absolute inset-2 rounded-full border border-cyan-400/50 rotate-ring" style={{ animationDirection: 'reverse', animationDuration: '15s' }} />
              <div className="absolute inset-4 rounded-full bg-gradient-to-br from-cyan-400 to-blue-500 pulse-glow" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="font-orbitron text-xl font-bold text-cyan-400 glow-text tracking-wider">J.A.R.V.I.S.</h1>
                <div className={`w-2 h-2 rounded-full ${brainStatus.val==='online'?'bg-emerald-500 animate-pulse':'bg-red-500'}`} />
              </div>
              <p className="text-[10px] text-cyan-400/60 font-orbitron tracking-widest uppercase">
                {brainStatus.val==='online' ? `Brain Active: ${brainStatus.model}` : `Brain Status: ${brainStatus.val.toUpperCase()}`}
              </p>
            </div>
          </div>

          <Navigation activeModule={activeModule} onModuleChange={setActiveModule} />

          <div className="hidden lg:flex items-center gap-6 text-xs text-cyan-400/60">
             <div className="flex items-center gap-2"><Cpu className="w-4 h-4 text-cyan-400" /> CPU: {Math.round(systemStats.cpu)}%</div>
             <div className="flex items-center gap-2"><Wifi className="w-4 h-4 text-emerald-400" /> NETWORK: STABLE</div>
             <div className="font-orbitron text-cyan-400 text-lg">{new Date().toLocaleTimeString('tr-TR', { hour12: false })}</div>
          </div>
        </header>

        <main className="flex-1 overflow-hidden">
          <AnimatePresence mode="wait">
            {activeModule === 'jarvis' ? (
              <motion.div key="jarvis" initial={{opacity:0}} animate={{opacity:1}} exit={{opacity:0}} className="h-full flex">
                {/* Left Actions */}
                <aside className="w-64 border-r border-cyan-500/20 bg-slate-900/30 p-4 space-y-4">
                   <h2 className="font-orbitron text-[10px] text-cyan-400/80 tracking-widest mb-4">OTONOM KOMUTLAR</h2>
                   {[
                     { label: 'Ajanları Denetle', cmd: 'Ajanların durumunu denetle ve rapor ver.' },
                     { label: 'Pazar Analizi', cmd: '2026 pazar trendlerini analiz et.' },
                     { label: 'Kreatif Render', cmd: 'Yeni bir dikey video konsepti hazırla.' },
                     { label: 'Güvenlik Taraması', cmd: 'Sovereign Coder ile repoyu analiz et.' }
                   ].map(a => (
                     <button key={a.label} onClick={() => { setInput(a.cmd); setTimeout(handleSendMessage, 100); }} className="w-full glass-card rounded-lg p-3 text-left text-xs hover:bg-cyan-500/10 transition-all border border-cyan-500/10">
                       <span className="block text-cyan-400 font-bold mb-1">{a.label}</span>
                       <span className="text-[9px] text-white/40 truncate block">{a.cmd}</span>
                     </button>
                   ))}
                </aside>

                {/* Center AI */}
                <div className="flex-1 flex flex-col items-center justify-between p-8">
                   <div className="relative w-64 h-64 flex items-center justify-center">
                      <div className="absolute inset-0 rounded-full border border-cyan-400/10 rotate-ring" />
                      <div className="absolute inset-4 rounded-full border border-cyan-400/20 rotate-ring" style={{animationDirection:'reverse'}} />
                      <motion.div 
                        animate={{ 
                          scale: state==='listening' ? 1 + (volume * 1.5) : 1,
                          boxShadow: state==='thinking' ? '0 0 50px rgba(0,245,255,0.4)' : '0 0 20px rgba(0,245,255,0.2)'
                        }}
                        className="relative w-24 h-24 rounded-full bg-cyan-400 shadow-[0_0_30px_rgba(0,245,255,0.6)] flex items-center justify-center"
                      >
                         <div className="w-full h-full rounded-full bg-[radial-gradient(circle_at_center,_transparent_30%,_rgba(0,0,0,0.4)_100%)]" />
                         {state === 'thinking' && <Zap className="absolute w-8 h-8 text-white animate-pulse" />}
                         {state === 'listening' && <Mic className="absolute w-8 h-8 text-white" />}
                      </motion.div>
                   </div>

                   {/* Messages Log */}
                   <div className="w-full max-w-2xl flex-1 mt-8 glass-card rounded-2xl flex flex-col overflow-hidden">
                      <div className="px-4 py-2 border-b border-white/5 text-[10px] font-orbitron text-white/30 tracking-widest">SIGNAL LOGS</div>
                      <div className="flex-1 overflow-y-auto p-4 space-y-4">
                         {messages.map(m => (
                           <div key={m.id} className={`flex ${m.role==='user'?'justify-end':'justify-start'}`}>
                              <div className={`max-w-[80%] p-3 rounded-2xl text-sm ${m.role==='user'?'bg-cyan-500/10 border border-cyan-500/20':'bg-white/5 border border-white/10'}`}>
                                <span className="block text-[9px] font-orbitron text-white/30 mb-1 uppercase">{m.role}</span>
                                {m.text}
                              </div>
                           </div>
                         ))}
                         <div ref={messagesEndRef} />
                      </div>
                      <div className="p-4 bg-black/20 flex gap-2">
                        <button onClick={toggleMic} className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all ${state==='listening'?'bg-red-500':'bg-white/5'}`}>
                           {state==='listening' ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
                        </button>
                        <button onClick={toggleVoice} className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all ${voiceEnabled?'bg-cyan-500/20':'bg-white/5'}`}>
                           {voiceEnabled ? <Volume2 className="w-5 h-5 text-cyan-400" /> : <VolumeX className="w-5 h-5 text-white/40" />}
                        </button>
                        <input value={input} onChange={e=>setInput(e.target.value)} onKeyDown={e=>e.key==='Enter'&&handleSendMessage()} placeholder="Mesaj yazın..." className="flex-1 bg-transparent px-4 text-sm outline-none" />
                        <button onClick={handleSendMessage} className="bg-cyan-500 px-4 rounded-xl text-black font-bold text-xs">GÖNDER</button>
                      </div>
                   </div>
                </div>

                {/* Right Stats */}
                <aside className="w-64 border-l border-cyan-500/20 bg-slate-900/30 p-4 space-y-4">
                   <h2 className="font-orbitron text-[10px] text-cyan-400/80 tracking-widest mb-4">SİSTEM DURUMU</h2>
                   <div className="glass-card rounded-xl p-4 space-y-4">
                      <div>
                        <div className="flex justify-between text-[10px] mb-1 text-white/40"><span>CPU</span><span>{Math.round(systemStats.cpu)}%</span></div>
                        <div className="h-1 bg-white/5 rounded-full overflow-hidden"><div className="h-full bg-cyan-500" style={{width:`${systemStats.cpu}%`}} /></div>
                      </div>
                      <div>
                        <div className="flex justify-between text-[10px] mb-1 text-white/40"><span>RAM</span><span>{Math.round(systemStats.memory)}%</span></div>
                        <div className="h-1 bg-white/5 rounded-full overflow-hidden"><div className="h-full bg-violet-500" style={{width:`${systemStats.memory}%`}} /></div>
                      </div>
                   </div>
                </aside>
              </motion.div>
            ) : (
              <motion.div key="zezelabs" initial={{opacity:0, scale:0.95}} animate={{opacity:1, scale:1}} exit={{opacity:0}} className="h-full">
                <ZezelabsDashboard />
              </motion.div>
            )}
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
}

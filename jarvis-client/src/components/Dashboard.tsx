import { useState, useEffect, useRef } from 'react';
import NeuralNetwork3D from './NeuralNetwork3D';
import ChatBubbles, { Message } from './ChatBubbles';

export default function Dashboard() {
  const [messages, setMessages] = useState<Message[]>([
    { id: '1', sender: 'jarvis', text: 'Merhaba komutanım! Tauri + React tabanlı premium siber-punk Jarvis v3.0 arayüzüne hoş geldiniz. 3B sinir ağı ve akıcı Framer animasyonları başarıyla devrededir.' }
  ]);
  const [inputVal, setInputVal] = useState('');
  const [connStatus, setConnStatus] = useState('AKTİF');
  const [stats, setStats] = useState({ cpu: 12, memory: 45, uptime: '00:00:00' });
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Connect websocket to local FastAPI server
    const ws = new WebSocket('ws://localhost:5000/ws');
    wsRef.current = ws;

    ws.onopen = () => {
      setConnStatus('AKTİF');
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'response') {
        setMessages((prev) => [...prev, { id: data.id || Date.now().toString(), sender: 'jarvis', text: data.val }]);
      } else if (data.type === 'stats') {
        setStats({ cpu: data.cpu, memory: data.memory, uptime: data.uptime });
      }
    };

    ws.onerror = () => {
      setConnStatus('BAĞLANTI HATASI');
    };

    ws.onclose = () => {
      setConnStatus('BAĞLANTI KESİLDİ');
    };

    return () => {
      ws.close();
    };
  }, []);

  const handleSendMessage = () => {
    if (!inputVal.trim()) return;

    // Send user message
    const userMsg: Message = { id: Date.now().toString(), sender: 'user', text: inputVal };
    setMessages((prev) => [...prev, userMsg]);

    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'chat',
        content: inputVal
      }));
    } else {
      // Offline fallback simulated query
      setTimeout(() => {
        setMessages((prev) => [...prev, {
          id: (Date.now() + 1).toString(),
          sender: 'jarvis',
          text: 'Masaüstü ağ geçidi bağlantısı kapalı, yerel motor simüle ediliyor.'
        }]);
      }, 1000);
    }

    setInputVal('');
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', background: '#070d19', color: '#ffffff', fontFamily: 'Segoe UI' }}>
      
      {/* Title bar */}
      <header style={{ height: '50px', background: '#0d1527', borderBottom: '1px solid #1c2842', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 25px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ fontSize: '18px', color: '#00f2fe' }}>⚡</span>
          <span style={{ fontWeight: 'bold', fontSize: '14px', letterSpacing: '1px', color: '#00f2fe' }}>
            ZEZELABS HOLDING | JARVIS v3.0 (TAURI + REACT)
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
          <span style={{ fontSize: '12px', fontWeight: 'bold', color: connStatus === 'AKTİF' ? '#10b981' : '#ef4444' }}>
            BAĞLANTI: {connStatus}
          </span>
        </div>
      </header>

      {/* Main Container Splitter */}
      <div style={{ display: 'flex', flex: 1, padding: '20px', gap: '20px', overflow: 'hidden' }}>
        
        {/* Left strip - 3D Neural Net & Telemetry Info */}
        <div style={{ display: 'flex', flexDirection: 'column', flex: 5, gap: '20px' }}>
          <NeuralNetwork3D />

          {/* Telemetry card */}
          <div style={{ background: '#0d1527', border: '1px solid #1c2842', borderRadius: '12px', padding: '20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <span style={{ color: '#ff007f', fontWeight: 'bold', fontSize: '12px' }}>📊 SİSTEM TELEMETRİ VERİLERİ</span>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '15px' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                <span style={{ fontSize: '11px', color: '#64748b' }}>CPU KULLANIMI</span>
                <span style={{ fontSize: '18px', fontWeight: 'bold', color: '#00f2fe' }}>%{stats.cpu}</span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                <span style={{ fontSize: '11px', color: '#64748b' }}>RAM BELLEK</span>
                <span style={{ fontSize: '18px', fontWeight: 'bold', color: '#00f2fe' }}>%{stats.memory}</span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                <span style={{ fontSize: '11px', color: '#64748b' }}>UPTIME</span>
                <span style={{ fontSize: '18px', fontWeight: 'bold', color: '#ff007f' }}>{stats.uptime}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Console - Chats */}
        <div style={{ display: 'flex', flexDirection: 'column', flex: 6, background: '#0d1527', border: '1px solid #1c2842', borderRadius: '12px', padding: '20px', overflow: 'hidden' }}>
          <ChatBubbles messages={messages} />

          {/* Form input */}
          <div style={{ display: 'flex', gap: '12px', marginTop: '15px' }}>
            <input
              type="text"
              placeholder="Jarvis'e yazılı talimat ver..."
              value={inputVal}
              onChange={(e) => setInputVal(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
              style={{
                flex: 1,
                background: '#070d19',
                border: '1px solid #1c2842',
                borderRadius: '8px',
                padding: '10px 16px',
                color: '#ffffff',
                fontFamily: 'Segoe UI',
                fontSize: '14px',
                outline: 'none',
              }}
            />
            <button
              onClick={handleSendMessage}
              style={{
                background: 'linear-gradient(135deg, #00f2fe, #ff007f)',
                border: 'none',
                borderRadius: '8px',
                color: '#ffffff',
                padding: '0 20px',
                fontWeight: 'bold',
                cursor: 'pointer',
                fontFamily: 'Segoe UI',
              }}
            >
              GÖNDER
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

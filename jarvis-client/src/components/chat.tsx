import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export interface Message {
  id: string;
  sender: 'user' | 'jarvis' | 'system';
  text: string;
}

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([
    { id: '1', sender: 'jarvis', text: 'Merhaba komutanım! ZEZELABS HQ siber karargah paneline hoş geldiniz. Faz 1 React bileşenleri ve dynamic Framer animasyonları başarıyla devrededir.' }
  ]);
  const [inputVal, setInputVal] = useState('');
  const [connStatus, setConnStatus] = useState('BAĞLANTI ARANIYOR');
  
  // Audio state parameters
  const [micActive, setMicActive] = useState(true);
  const [voiceActive, setVoiceActive] = useState(true);
  const [thinking, setThinking] = useState(false);
  
  const wsRef = useRef<WebSocket | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Establish WS connection to port 8000
    const ws = new WebSocket('ws://localhost:8000/ws');
    wsRef.current = ws;

    ws.onopen = () => {
      setConnStatus('AKTİF');
      ws.send(JSON.stringify({ type: 'voice_toggle', val: voiceActive }));
      ws.send(JSON.stringify({ type: 'mic_toggle', val: micActive }));
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'response') {
        setMessages((prev) => [...prev, { id: data.id || Date.now().toString(), sender: 'jarvis', text: data.val }]);
        setThinking(false);
      } else if (data.type === 'state') {
        setThinking(data.val === 'thinking');
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

  useEffect(() => {
    // Auto-scroll chat area
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, thinking]);

  const handleSendMessage = () => {
    if (!inputVal.trim()) return;

    const userMsg: Message = { id: Date.now().toString(), sender: 'user', text: inputVal };
    setMessages((prev) => [...prev, userMsg]);
    setThinking(true);

    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'chat',
        content: inputVal
      }));
    } else {
      setTimeout(() => {
        setMessages((prev) => [...prev, {
          id: (Date.now() + 1).toString(),
          sender: 'jarvis',
          text: 'Masaüstü asistan ağ geçidi bağlantısı pasif, yerel simülatör devrede.'
        }]);
        setThinking(false);
      }, 1000);
    }

    setInputVal('');
  };

  const toggleSpeaker = () => {
    const nextState = !voiceActive;
    setVoiceActive(nextState);
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'voice_toggle', val: nextState }));
    }
    setMessages((prev) => [...prev, {
      id: Date.now().toString(),
      sender: 'system',
      text: `Sesli asistan yanıtı (TTS): ${nextState ? 'ETKİN' : 'DEAKTİF'}`
    }]);
  };

  const toggleMicrophone = () => {
    const nextState = !micActive;
    setMicActive(nextState);
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'mic_toggle', val: nextState }));
    }
    setMessages((prev) => [...prev, {
      id: Date.now().toString(),
      sender: 'system',
      text: `Mikrofon ses dinleme motoru: ${nextState ? 'AKTİF' : 'KAPATILDI'}`
    }]);
  };

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      background: '#0d1527',
      border: '1px solid #1c2842',
      borderRadius: '12px',
      padding: '20px',
      height: '100%',
      overflow: 'hidden'
    }}>
      {/* Header telemetry badge */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #1c2842', paddingBottom: '10px', marginBottom: '15px' }}>
        <span style={{ fontSize: '11px', fontWeight: 'bold', color: '#00f2fe', letterSpacing: '1px' }}>
          💬 JARVIS SOHBET VE GÖREV MERKEZİ
        </span>
        <span style={{
          fontSize: '9px',
          fontWeight: 'bold',
          color: connStatus === 'AKTİF' ? '#10b981' : '#ef4444'
        }}>
          BAĞLANTI: {connStatus}
        </span>
      </div>

      {/* Messages list */}
      <div ref={scrollRef} style={{ display: 'flex', flexDirection: 'column', gap: '12px', overflowY: 'auto', flex: 1, paddingRight: '5px' }}>
        <AnimatePresence initial={false}>
          {messages.map((msg) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 15, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ type: 'spring', stiffness: 300, damping: 25 }}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignSelf: msg.sender === 'user' ? 'flex-end' : msg.sender === 'jarvis' ? 'flex-start' : 'center',
                maxWidth: '85%'
              }}
            >
              <span style={{
                fontSize: '9px',
                fontWeight: 'bold',
                marginBottom: '3px',
                fontFamily: 'Segoe UI',
                alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start',
                color: msg.sender === 'user' ? '#64748b' : msg.sender === 'jarvis' ? '#00f2fe' : '#f59e0b'
              }}>
                {msg.sender === 'user' ? '👤 KULLANICI' : msg.sender === 'jarvis' ? '⚡ JARVIS' : '⚠️ SİSTEM'}
              </span>

              <div style={{
                padding: '10px 14px',
                borderRadius: '10px',
                fontSize: '13px',
                color: '#ffffff',
                background: msg.sender === 'user' ? 'linear-gradient(135deg, #ff007f, #7928ca)' : msg.sender === 'jarvis' ? '#070b16' : 'transparent',
                border: msg.sender === 'user' ? 'none' : msg.sender === 'jarvis' ? '1px solid #1c2842' : '1px solid #ff007f',
                boxShadow: msg.sender === 'user' ? '0 4px 12px rgba(255, 0, 127, 0.2)' : 'none'
              }}>
                {msg.text}
              </div>
            </motion.div>
          ))}
          
          {/* Thinking indicator bubble */}
          {thinking && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              style={{ alignSelf: 'flex-start', display: 'flex', gap: '4px', padding: '10px 15px', background: '#070b16', border: '1px solid #1c2842', borderRadius: '10px' }}
            >
              <span style={{ fontSize: '11px', color: '#00f2fe', fontWeight: 'bold' }}>Jarvis düşünüyor</span>
              <motion.span animate={{ opacity: [0, 1, 0] }} transition={{ repeat: Infinity, duration: 1 }} style={{ color: '#00f2fe' }}>.</motion.span>
              <motion.span animate={{ opacity: [0, 1, 0] }} transition={{ repeat: Infinity, duration: 1, delay: 0.2 }} style={{ color: '#00f2fe' }}>.</motion.span>
              <motion.span animate={{ opacity: [0, 1, 0] }} transition={{ repeat: Infinity, duration: 1, delay: 0.4 }} style={{ color: '#00f2fe' }}>.</motion.span>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Mic and Speaker switches */}
      <div style={{ display: 'flex', gap: '10px', margin: '12px 0 5px 0' }}>
        <button
          onClick={toggleSpeaker}
          style={{
            background: '#070b16',
            color: voiceActive ? '#00f2fe' : '#64748b',
            border: voiceActive ? '1px solid #00f2fe' : '1px solid #1c2842',
            borderRadius: '6px',
            padding: '6px 12px',
            fontSize: '11px',
            fontWeight: 'bold',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            transition: 'all 0.2s'
          }}
        >
          {voiceActive ? '🔊 SES: AÇIK' : '🔇 SES: KAPALI'}
        </button>
        
        <button
          onClick={toggleMicrophone}
          style={{
            background: '#070b16',
            color: micActive ? '#ff007f' : '#64748b',
            border: micActive ? '1px solid #ff007f' : '1px solid #1c2842',
            borderRadius: '6px',
            padding: '6px 12px',
            fontSize: '11px',
            fontWeight: 'bold',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            transition: 'all 0.2s'
          }}
        >
          {micActive ? '🎙️ MİK: AÇIK' : '🔇 MİK: KAPALI'}
        </button>
      </div>

      {/* Input area */}
      <div style={{ display: 'flex', gap: '10px' }}>
        <input
          type="text"
          placeholder="Asistana talimat ver..."
          value={inputVal}
          onChange={(e) => setInputVal(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
          style={{
            flex: 1,
            background: '#070b16',
            border: '1px solid #1c2842',
            borderRadius: '8px',
            padding: '10px 14px',
            color: '#ffffff',
            fontSize: '13px',
            outline: 'none',
            fontFamily: 'Segoe UI'
          }}
        />
        <button
          onClick={handleSendMessage}
          style={{
            background: 'linear-gradient(135deg, #00f2fe, #ff007f)',
            border: 'none',
            borderRadius: '8px',
            color: '#070b16',
            fontWeight: 'bold',
            padding: '0 18px',
            cursor: 'pointer',
            fontSize: '12px',
            fontFamily: 'Segoe UI'
          }}
        >
          GÖNDER
        </button>
      </div>
    </div>
  );
}

import { useState, useEffect } from 'react';
import Sidebar from './components/sidebar';
import NeuralNetwork3D from './components/NeuralNetwork3D';
import TelemetryPanel from './components/TelemetryPanel';
import Chat from './components/chat';
import './App.css';

function App() {
  const [selectedDeptId, setSelectedDeptId] = useState('zeze_prompt');
  const [time, setTime] = useState(new Date().toLocaleTimeString('tr-TR'));
  const [backendStatus, setBackendStatus] = useState<'online' | 'offline' | 'checking'>('checking');

  // Clock
  useEffect(() => {
    const iv = setInterval(() => setTime(new Date().toLocaleTimeString('tr-TR')), 1000);
    return () => clearInterval(iv);
  }, []);

  // Backend health check
  useEffect(() => {
    const check = () =>
      fetch('http://127.0.0.1:8000/health')
        .then(() => setBackendStatus('online'))
        .catch(() => setBackendStatus('offline'));
    check();
    const iv = setInterval(check, 10000);
    return () => clearInterval(iv);
  }, []);

  // Listen for Godot/iframe dept selection events
  useEffect(() => {
    const handler = (e: MessageEvent) => {
      if (e.data?.type === 'SELECT_DEPT') setSelectedDeptId(e.data.deptId);
    };
    window.addEventListener('message', handler);
    return () => window.removeEventListener('message', handler);
  }, []);

  const statusColor = backendStatus === 'online' ? '#10b981' : backendStatus === 'offline' ? '#ef4444' : '#f59e0b';
  const statusText  = backendStatus === 'online' ? 'BACKEND AKTİF' : backendStatus === 'offline' ? 'BACKEND KAPALI' : 'BAĞLANIYOR...';

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100vh',
      background: '#03050f',
      color: '#f8fafc',
      fontFamily: '"Segoe UI", system-ui, sans-serif',
      overflow: 'hidden',
    }}>
      {/* ── TOP HEADER ── */}
      <header style={{
        height: '50px',
        minHeight: '50px',
        background: '#070d19',
        borderBottom: '1px solid #1c2842',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 20px',
        zIndex: 10,
        flexShrink: 0,
      }}>
        {/* Left: Logo + Title */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            width: '30px', height: '30px', borderRadius: '8px',
            background: 'linear-gradient(135deg, #00f2fe, #a855f7)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontWeight: '900', fontSize: '16px', color: '#03050f',
          }}>Z</div>
          <div>
            <div style={{ fontWeight: 'bold', fontSize: '13px', color: '#00f2fe', letterSpacing: '1px' }}>
              ZEZELABS SİBER KARARGAH
            </div>
            <div style={{ fontSize: '9px', color: '#4a6080', letterSpacing: '2px' }}>
              JARVIS v4.0 — YETKİ: KÖK ERİŞİM
            </div>
          </div>
        </div>

        {/* Right: Status + Clock */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <div style={{
              width: '7px', height: '7px', borderRadius: '50%',
              background: statusColor,
              boxShadow: `0 0 6px ${statusColor}`,
            }} />
            <span style={{ fontSize: '10px', color: statusColor, fontWeight: 'bold' }}>{statusText}</span>
          </div>
          <div style={{
            fontFamily: 'Consolas, monospace', fontSize: '12px',
            color: '#10b981', letterSpacing: '1px',
          }}>⏱ {time}</div>
        </div>
      </header>

      {/* ── MAIN CONTENT ── */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>

        {/* Left Sidebar */}
        <Sidebar selectedDeptId={selectedDeptId} onSelectDept={setSelectedDeptId} />

        {/* Center Column */}
        <main style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          background: '#050811',
        }}>
          {/* Neural Network Canvas — 60% height */}
          <div style={{
            flex: '0 0 60%',
            padding: '12px',
            paddingBottom: '6px',
          }}>
            <div style={{
              height: '100%',
              background: '#070d19',
              borderRadius: '12px',
              border: '1px solid #1c2842',
              overflow: 'hidden',
              position: 'relative',
            }}>
              <NeuralNetwork3D selectedDeptId={selectedDeptId} />
            </div>
          </div>

          {/* Chat Panel — 40% height */}
          <div style={{
            flex: '0 0 40%',
            padding: '6px 12px 12px 12px',
            overflow: 'hidden',
          }}>
            <Chat />
          </div>
        </main>

        {/* Right Telemetry */}
        <TelemetryPanel selectedDeptId={selectedDeptId} />
      </div>
    </div>
  );
}

export default App;

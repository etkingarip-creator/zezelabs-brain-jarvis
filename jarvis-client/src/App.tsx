import { useState, useEffect } from 'react';
import Sidebar from './components/sidebar';
import Telemetry from './components/telemetry';
import Chat from './components/chat';
import './App.css';

function App() {
  const [selectedDeptId, setSelectedDeptId] = useState('zeze_prompt');

  useEffect(() => {
    // Phase 3 Bridge: Listen to postMessages coming from Godot WebGL simulator iframe
    const handleMessage = (event: MessageEvent) => {
      if (event.data && event.data.type === 'SELECT_DEPT') {
        setSelectedDeptId(event.data.deptId);
      }
    };
    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, []);

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100vh',
      background: '#050811',
      color: '#ffffff',
      fontFamily: 'Segoe UI',
      overflow: 'hidden'
    }}>
      {/* Premium Top Navigation / Header */}
      <header style={{
        height: '54px',
        background: '#0d1527',
        borderBottom: '1px solid #1c2842',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 25px',
        zIndex: 10
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ fontSize: '20px', color: '#00f2fe' }}>⚡</span>
          <span style={{ fontWeight: 'bold', fontSize: '14px', letterSpacing: '1px', color: '#00f2fe' }}>
            ZEZELABS HOLDING | JARVIS v3.0 | SİBER KARARGAH (ZEZE-HQ)
          </span>
        </div>
        
        {/* Connection telemetry status indicator */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
          <span style={{ fontSize: '11px', color: '#64748b' }}>YETKİ: KÖK ERİŞİM (ROOT)</span>
        </div>
      </header>

      {/* Main split dashboard pane */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Left sidebar listing corporate departments */}
        <Sidebar selectedDeptId={selectedDeptId} onSelectDept={setSelectedDeptId} />

        {/* Central visual core area (Godot WebGL Embedded iframe) */}
        <main style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          padding: '20px',
          gap: '20px',
          overflowY: 'auto',
          background: '#050811'
        }}>
          {/* Godot WebGL Embedded isometric 2.5D building simulator */}
          <div style={{
            background: '#070d19',
            borderRadius: '12px',
            border: '1px solid #1c2842',
            overflow: 'hidden',
            height: '380px',
            position: 'relative'
          }}>
            <iframe
              src="/godot_webgl_simulator.html"
              style={{
                width: '100%',
                height: '100%',
                border: 'none',
                background: 'transparent'
              }}
              title="Godot 2.5D Isometric Building WebGL Simulator"
            />
          </div>

          {/* Underneath chat assistant core */}
          <div style={{ flex: 1, minHeight: '380px' }}>
            <Chat />
          </div>
        </main>

        {/* Right side individual telemetry tracking metrics */}
        <Telemetry selectedDeptId={selectedDeptId} />
      </div>
    </div>
  );
}

export default App;

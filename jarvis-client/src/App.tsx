import { useState } from 'react';
import Sidebar from './components/sidebar';
import Telemetry from './components/telemetry';
import Chat from './components/chat';
import NeuralNetwork3D from './components/NeuralNetwork3D';
import './App.css';

function App() {
  const [selectedDeptId, setSelectedDeptId] = useState('zeze_prompt');

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

        {/* Central visual core area (Godot placeholder ThreeJS network) */}
        <main style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          padding: '20px',
          gap: '20px',
          overflowY: 'auto',
          background: '#050811'
        }}>
          {/* Central 3D neural grid visualizer */}
          <NeuralNetwork3D />

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

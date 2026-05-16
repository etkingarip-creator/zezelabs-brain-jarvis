import React, { useState, useEffect } from 'react';
import TopologyGrid from './components/TopologyGrid';

function App() {
  const [state, setState] = useState({
    cpu_percent: 0,
    ram_percent: 0,
    total_tasks: 0,
    token_spent_estimate: 0,
    token_per_sec: 0,
    agent_efficiency: 0,
    gpu_temp: 0,
    vram_usage: 0,
    rabbitmq_queue_size: 0,
    active_agents: {},
    last_messages: []
  });

  useEffect(() => {
    const fetchState = async () => {
      try {
        const response = await fetch('http://localhost:8502/api/state');
        if (response.ok) {
          const data = await response.json();
          setState(data);
        }
      } catch (error) {
        console.error("Fetch error:", error);
      }
    };
    fetchState();
    const intervalId = setInterval(fetchState, 1000);
    return () => clearInterval(intervalId);
  }, []);

  return (
    <div className="dashboard-container">
      {/* Security Headers */}
      <div className="security-banner">
        <span>ZOM PROTOCOL: ENFORCED</span>
        <span>FASTAPI GUARD: <span className="blink" style={{color: '#00ff00'}}>ACTIVE</span></span>
        <span>SECURE PORT: 443</span>
        <span>ENCRYPTION: AES-256</span>
      </div>

      <div className="sidebar">
        <div className="brand-header">
          <span className="brand-title">ZOM WAR_ROOM</span>
          <span className="brand-subtitle">COST-EFFICIENCY DOCTRINE ENFORCED</span>
        </div>

        {/* TULPAR CORE METRICS */}
        <div className="tulpar-core">
          <div className="core-title">
            <span>TULPAR CORE STATUS</span>
            <span className={state.gpu_temp > 75 ? 'blink' : ''} style={{color: state.gpu_temp > 75 ? 'var(--text-alert)' : 'var(--text-primary)'}}>
              TEMP: {state.gpu_temp}°C
            </span>
          </div>
          <div style={{fontSize: '0.7rem', color: 'var(--text-secondary)'}}>VRAM ALLOCATED: {state.vram_usage} GB</div>
          <div className="progress-bar-container">
            <div className={`progress-bar-fill ${state.gpu_temp > 75 ? 'high' : ''}`} style={{width: `${Math.min((state.gpu_temp / 100) * 100, 100)}%`}}></div>
          </div>
        </div>

        {/* PERFORMANCE GRID */}
        <div className="metrics-section">
          <div className="metric-card">
            <span className="metric-label">THROUGHPUT</span>
            <span className="metric-value">{state.token_per_sec}</span>
            <span className="metric-unit"> T/s</span>
          </div>
          <div className={`metric-card ${state.agent_efficiency < 0.9 ? 'alert' : ''}`}>
            <span className="metric-label">EFFICIENCY (AEC)</span>
            <span className="metric-value">{state.agent_efficiency}</span>
            <span className="metric-unit"> COEF</span>
          </div>
          <div className="metric-card">
            <span className="metric-label">RABBITMQ QUEUE</span>
            <span className="metric-value">{state.rabbitmq_queue_size}</span>
            <span className="metric-unit"> MSGS</span>
          </div>
          <div className="metric-card">
            <span className="metric-label">SYS. RAM LOAD</span>
            <span className="metric-value">{state.ram_percent}</span>
            <span className="metric-unit"> %</span>
          </div>
        </div>

        {/* TERMINAL LOGS */}
        <div className="terminal-section">
          <div style={{color: 'var(--text-secondary)', marginBottom: '10px', borderBottom: '1px solid var(--border-dim)', paddingBottom: '5px'}}>
            > TAIL -F /VAR/LOG/ZOM_STDOUT
          </div>
          {state.last_messages && state.last_messages.length > 0 ? (
            state.last_messages.map((msg, idx) => {
              const isError = msg.toLowerCase().includes('error') || msg.toLowerCase().includes('fail') || msg.toLowerCase().includes('ihlal');
              return (
                <div key={idx} className="log-line">
                  <span className="log-time">[SYS]</span>
                  <span className={isError ? 'log-error' : 'log-info'}>{msg}</span>
                </div>
              );
            })
          ) : (
            <div className="log-line">
              <span className="log-time">[SYS]</span>
              <span className="log-warn">Awaiting initialization signals...</span>
            </div>
          )}
        </div>
      </div>

      <TopologyGrid state={state} />
    </div>
  );
}

export default App;

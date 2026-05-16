import React from 'react';

const AgentNode = ({ id, type, name, active, status, left, top }) => {
  return (
    <div 
      className={`agent-node ${active ? 'active' : 'inactive'}`}
      style={{ left, top, '--node-color': `var(--agent-${type})` }}
    >
      <div className="node-header">
        <span>[{id.toUpperCase()}]</span>
        <span>{active ? 'ONLINE' : 'STANDBY'}</span>
      </div>
      <div className="node-body">
        <div className="node-metric">
          <span style={{color: 'var(--text-secondary)'}}>ROLE</span>
          <span style={{color: '#fff'}}>{name}</span>
        </div>
        <div className="node-metric">
          <span style={{color: 'var(--text-secondary)'}}>LATENCY</span>
          <span style={{color: '#fff'}}>{active ? Math.floor(Math.random() * 20 + 5) : 0}ms</span>
        </div>
        <div className="node-state">
          {active ? `> ${status || 'EXECUTING_PROTOCOL...'}` : '> IDLE'}
        </div>
      </div>
    </div>
  );
};

export default AgentNode;

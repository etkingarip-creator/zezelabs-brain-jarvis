import React from 'react';
import AgentNode from './AgentNode';

const NODES = [
  { id: 'orchestrator', type: 'orchestrator', name: 'ORCHESTRATOR', left: '50%', top: '50%' },
  { id: 'dev', type: 'dev', name: 'ENGINEERING_CORE', left: '20%', top: '20%' },
  { id: 'reviewer', type: 'reviewer', name: 'AUDIT_MODULE', left: '80%', top: '20%' },
  { id: 'media', type: 'media', name: 'MEDIA_AUTOMATION', left: '20%', top: '80%' },
  { id: 'academy', type: 'academy', name: 'ACADEMY_ARCHIVE', left: '80%', top: '80%' },
];

const TopologyGrid = ({ state }) => {
  const activeAgents = state.active_agents || {};

  return (
    <div className="map-area">
      {/* SVG Background for connection lines */}
      <svg className="topology-svg">
        {/* Connection from Orchestrator to Dev */}
        <line x1="50%" y1="50%" x2="20%" y2="20%" className={`data-flow-line ${activeAgents['dev'] ? 'data-flow-active' : ''}`} />
        {/* Connection from Dev to Reviewer */}
        <line x1="20%" y1="20%" x2="80%" y2="20%" className={`data-flow-line ${activeAgents['reviewer'] ? 'data-flow-active' : ''}`} />
        {/* Connection from Orchestrator to Media */}
        <line x1="50%" y1="50%" x2="20%" y2="80%" className={`data-flow-line ${activeAgents['media'] ? 'data-flow-active' : ''}`} />
        {/* Connection from Orchestrator to Academy */}
        <line x1="50%" y1="50%" x2="80%" y2="80%" className={`data-flow-line ${activeAgents['academy'] ? 'data-flow-active' : ''}`} />
      </svg>

      {/* Render Nodes */}
      {NODES.map(node => {
        // Simple logic to find if a key matches the node type (e.g. dev_agent_1 -> dev)
        let isActive = false;
        let status = '';
        for (const [key, agentData] of Object.entries(activeAgents)) {
          if (key.toLowerCase().includes(node.type)) {
            isActive = true;
            if (typeof agentData === 'object' && agentData.status) {
              status = agentData.status;
            }
            break;
          }
        }

        return (
          <AgentNode
            key={node.id}
            id={node.id}
            type={node.type}
            name={node.name}
            left={node.left}
            top={node.top}
            active={isActive}
            status={status}
          />
        );
      })}
    </div>
  );
};

export default TopologyGrid;

import React from 'react';
import OfficeRoom from './OfficeRoom';

// Adjusting layout to match a vertical cutaway multi-floor building structure
const ROOM_LAYOUTS = [
  { id: 'academy', type: 'academy', name: 'Academy', left: '20%', top: '15%' }, // Top floor
  { id: 'media', type: 'media', name: 'Scriptwriter', left: '20%', top: '35%' }, // Second floor down
  { id: 'reviewer', type: 'reviewer', name: 'The Studio (Review)', left: '20%', top: '55%' }, // Middle floor
  { id: 'dev', type: 'dev', name: 'Dev', left: '80%', top: '45%' }, // Middle right
  { id: 'orchestrator', type: 'orchestrator', name: 'The Forge (Orchestrator)', left: '50%', top: '80%' }, // Ground floor core
];

const IsometricMap = ({ activeAgents = [] }) => {
  const isRoomActive = (type) => {
    return activeAgents.some(agent => agent.toLowerCase().includes(type));
  };

  return (
    <div className="map-container">
      {/* The stunning AI generated background */}
      <div className="map-background"></div>
      
      {/* HUD Overlays (Pins) */}
      <div className="hud-layer">
        {ROOM_LAYOUTS.map((room) => (
          <OfficeRoom
            key={room.id}
            type={room.type}
            name={room.name}
            left={room.left}
            top={room.top}
            active={isRoomActive(room.type)}
          />
        ))}
      </div>
    </div>
  );
};

export default IsometricMap;

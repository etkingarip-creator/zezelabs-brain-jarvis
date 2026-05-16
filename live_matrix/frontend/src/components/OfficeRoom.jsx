import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Activity, Code, Eye, PenTool, GraduationCap } from 'lucide-react';

const icons = {
  orchestrator: Activity,
  dev: Code,
  reviewer: Eye,
  media: PenTool,
  academy: GraduationCap,
};

const OfficeRoom = ({ type, name, active, left, top }) => {
  const Icon = icons[type] || Activity;

  return (
    <div 
      className={`hud-pin pin-${type} ${active ? 'active' : ''}`}
      style={{ left, top }}
    >
      {/* The floating label */}
      <div className="pin-label-container">
        <div className="pin-label">
          {name}
        </div>
        <div className="pin-line"></div>
      </div>

      {/* The marker core on the map */}
      <div className="pin-core">
        <Icon size={18} strokeWidth={2.5} className="pin-icon" />
        
        {/* Pulsing ring when active */}
        <AnimatePresence>
          {active && (
            <motion.div 
              className="pin-pulse"
              initial={{ scale: 0.8, opacity: 0.8 }}
              animate={{ scale: 2.5, opacity: 0 }}
              exit={{ opacity: 0 }}
              transition={{ repeat: Infinity, duration: 1.5, ease: "easeOut" }}
            />
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default OfficeRoom;

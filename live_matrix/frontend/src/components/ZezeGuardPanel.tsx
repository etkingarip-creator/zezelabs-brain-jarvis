import React, { useEffect, useState } from 'react';

interface ZezeGuardSnapshot {
  anti_loop: {
    active_loops: number;
    freeze_recommendations: string[];
  };
  roi: {
    agents: string[];
    total_cost_usd: number;
    successful_tasks: number;
    failed_tasks: number;
  };
  alerts: Array<{ title: string; severity: string; message: string }>;
  updated_at: string;
}

export const ZezeGuardPanel: React.FC = () => {
  const [snapshot, setSnapshot] = useState<ZezeGuardSnapshot | null>(null);

  useEffect(() => {
    // In real usage, this would fetch from /api/zeze-guard/snapshot
    // or connect to the telemetry websocket.
    fetch('/api/zeze-guard/snapshot')
      .then(res => res.json())
      .then(data => setSnapshot(data))
      .catch(err => console.error("Failed to load ZEZE-GUARD snapshot", err));
  }, []);

  if (!snapshot) {
    return <div className="p-4 bg-gray-900 text-white rounded-md">Loading ZEZE-GUARD Metrics...</div>;
  }

  return (
    <div className="p-4 bg-gray-900 text-white rounded-md shadow-lg font-mono text-sm">
      <h2 className="text-xl font-bold mb-4 text-green-400">ZEZE-GUARD Dashboard</h2>
      
      <div className="grid grid-cols-2 gap-4">
        {/* ANTI-LOOP */}
        <div className="border border-red-500 p-3 rounded">
          <h3 className="font-semibold text-red-400">Anti-Loop Engine</h3>
          <p>Active Loops: <span className="font-bold">{snapshot.anti_loop.active_loops}</span></p>
          {snapshot.anti_loop.freeze_recommendations.map((rec, i) => (
            <div key={i} className="text-xs text-gray-300 mt-1">⚠️ {rec}</div>
          ))}
        </div>

        {/* ROI TRACKER */}
        <div className="border border-blue-500 p-3 rounded">
          <h3 className="font-semibold text-blue-400">ROI Tracker</h3>
          <p>Total Cost: <span className="font-bold">${snapshot.roi.total_cost_usd.toFixed(2)}</span></p>
          <p className="text-green-400">Success: {snapshot.roi.successful_tasks}</p>
          <p className="text-red-400">Failed: {snapshot.roi.failed_tasks}</p>
        </div>
      </div>

      {/* ALERTS */}
      <div className="mt-4 border border-yellow-500 p-3 rounded">
        <h3 className="font-semibold text-yellow-400 mb-2">Shadow CEO Alerts</h3>
        {snapshot.alerts.map((alert, i) => (
          <div key={i} className="mb-1 text-xs">
            <span className="font-bold">[{alert.severity.toUpperCase()}]</span> {alert.title} - {alert.message}
          </div>
        ))}
      </div>
      
      <div className="text-xs text-gray-500 mt-4 text-right">
        Last Sync: {snapshot.updated_at}
      </div>
    </div>
  );
};

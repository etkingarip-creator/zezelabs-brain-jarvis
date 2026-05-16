import React, { Suspense, useState, useEffect } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, PerspectiveCamera, Environment, Float, Text, ContactShadows } from '@react-three/drei';
import { motion } from 'framer-motion-3d';

const DepartmentNode = ({ position, name, color, status }: { position: [number, number, number], name: string, color: string, status: string }) => {
  const [hovered, setHover] = useState(false);

  return (
    <group position={position}>
      <Float speed={2} rotationIntensity={0.5} floatIntensity={0.5}>
        <motion.mesh
          onPointerOver={() => setHover(true)}
          onPointerOut={() => setHover(false)}
          animate={{
            scale: hovered || status === 'working' ? 1.2 : 1,
            rotateY: status === 'working' ? Math.PI * 2 : 0,
            y: status === 'working' ? 0.5 : 0
          }}
          transition={{ 
            duration: status === 'working' ? 2 : 0.3, 
            repeat: status === 'working' ? Infinity : 0, 
            ease: "easeInOut" 
          }}
        >
          <boxGeometry args={[1.5, 0.2, 1.5]} />
          <meshStandardMaterial color={color} emissive={color} emissiveIntensity={status === 'working' || hovered ? 2 : 0.5} />
        </motion.mesh>
        
        {/* Agent Sprite (Glow effect when working) */}
        <mesh position={[0, 0.8, 0]}>
          <boxGeometry args={[0.5, 1, 0.5]} />
          <meshStandardMaterial 
            color={status === 'working' ? color : "#ffffff"} 
            opacity={0.8} 
            transparent 
            emissive={status === 'working' ? color : "black"}
            emissiveIntensity={2}
          />
        </mesh>
      </Float>

      <Text
        position={[0, -0.5, 0]}
        fontSize={0.3}
        color="white"
        anchorX="center"
        anchorY="middle"
      >
        {name}
      </Text>
      
      <Text
        position={[0, -0.8, 0]}
        fontSize={0.2}
        color={status === 'working' ? '#4ade80' : '#94a3b8'}
        anchorX="center"
        anchorY="middle"
      >
        {status.toUpperCase()}
      </Text>
    </group>
  );
};

const OfficeScene = ({ agentStates }: { agentStates: any }) => {
  return (
    <>
      <PerspectiveCamera makeDefault position={[10, 10, 10]} fov={50} />
      <OrbitControls makeDefault minPolarAngle={0} maxPolarAngle={Math.PI / 2.1} />
      
      <ambientLight intensity={0.5} />
      <spotLight position={[10, 10, 10]} angle={0.15} penumbra={1} intensity={100} castShadow />
      <pointLight position={[-10, -10, -10]} intensity={50} />

      <group position={[0, 0, 0]}>
        {/* Floor */}
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -1, 0]} receiveShadow>
          <planeGeometry args={[20, 20]} />
          <meshStandardMaterial color="#020617" roughness={0.1} metalness={0.8} />
        </mesh>
        <gridHelper args={[20, 20, '#1e293b', '#0f172a']} position={[0, -0.99, 0]} />
        
        {/* Departments linked to real-time state */}
        <DepartmentNode position={[-4, 0, -4]} name="ENGINEERING" color="#3b82f6" status={agentStates.eng || 'idle'} />
        <DepartmentNode position={[4, 0, -4]} name="FINANCE" color="#eab308" status={agentStates.fin || 'idle'} />
        <DepartmentNode position={[-4, 0, 4]} name="MEDIA" color="#ef4444" status={agentStates.media || 'idle'} />
        <DepartmentNode position={[4, 0, 4]} name="ARO" color="#a855f7" status={agentStates.aro || 'idle'} />
        <DepartmentNode position={[0, 1, 0]} name="ORCHESTRATOR" color="#10b981" status={agentStates.orchestrator || 'idle'} />
      </group>

      <ContactShadows position={[0, -0.9, 0]} opacity={0.4} scale={20} blur={2.4} far={4.5} />
      <Environment preset="city" />
    </>
  );
};

export default function App() {
  const [agentStates, setAgentStates] = useState<any>({
    eng: 'idle',
    fin: 'idle',
    media: 'idle',
    aro: 'idle',
    orchestrator: 'idle'
  });
  const [lastMessage, setLastMessage] = useState("Sistem Hazır...");

  useEffect(() => {
    const connectWS = () => {
      const ws = new WebSocket('ws://localhost:8001');
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          const target = data.target_agent || data.origin_agent || 'system';
          const msg = data.message || "Görev işleniyor...";
          
          setLastMessage(`[${target.toUpperCase()}] ${msg}`);

          // Agent ismine göre state güncelle (örn: zeze_eng_coder -> eng)
          let key = '';
          if (target.includes('eng')) key = 'eng';
          else if (target.includes('fin')) key = 'fin';
          else if (target.includes('media')) key = 'media';
          else if (target.includes('aro')) key = 'aro';
          else if (target.includes('orchestrator')) key = 'orchestrator';

          if (key) {
            setAgentStates((prev: any) => ({ ...prev, [key]: 'working' }));
            // 5 saniye sonra idle'a çek
            setTimeout(() => {
              setAgentStates((prev: any) => ({ ...prev, [key]: 'idle' }));
            }, 5000);
          }
        } catch (e) {
          console.error("WS Parse Error:", e);
        }
      };

      ws.onclose = () => setTimeout(connectWS, 3000);
      return ws;
    };

    const ws = connectWS();
    return () => ws.close();
  }, []);

  return (
    <div className="h-screen w-screen bg-slate-950">
      <div className="absolute top-8 left-8 z-10">
        <h1 className="text-4xl font-bold tracking-tighter text-white">ZEZELABS <span className="text-blue-500">WAR ROOM</span></h1>
        <p className="text-slate-400 font-mono text-sm">{lastMessage}</p>
      </div>

      <div className="absolute bottom-8 right-8 z-10 flex gap-4">
        <div className="px-4 py-2 bg-slate-900/80 border border-slate-800 rounded-lg backdrop-blur-md">
          <p className="text-xs text-slate-500 uppercase">System Status</p>
          <p className="text-sm font-mono text-green-400">All Systems Operational</p>
        </div>
        <div className="px-4 py-2 bg-slate-900/80 border border-slate-800 rounded-lg backdrop-blur-md">
          <p className="text-xs text-slate-500 uppercase">Voice Engine</p>
          <p className="text-sm font-mono text-blue-400">Jarvis Listening...</p>
        </div>
      </div>

      <Canvas shadows>
        <Suspense fallback={null}>
          <OfficeScene agentStates={agentStates} />
        </Suspense>
      </Canvas>
    </div>
  );
}

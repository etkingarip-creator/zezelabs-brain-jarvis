import { useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Points, PointMaterial } from '@react-three/drei';
import * as THREE from 'three';

function NeuralNetworkParticles() {
  const ref = useRef<THREE.Points>(null);
  
  // Create randomized neural point cloud coords
  const pointsCount = 400;
  const positions = new Float32Array(pointsCount * 3);

  for (let i = 0; i < pointsCount; i++) {
    const x = (Math.random() - 0.5) * 10;
    const y = (Math.random() - 0.5) * 10;
    const z = (Math.random() - 0.5) * 10;
    positions[i * 3] = x;
    positions[i * 3 + 1] = y;
    positions[i * 3 + 2] = z;
  }

  useFrame((_, delta) => {
    if (ref.current) {
      ref.current.rotation.x += delta * 0.05;
      ref.current.rotation.y += delta * 0.075;
    }
  });

  return (
    <group>
      <Points ref={ref} positions={positions} stride={3}>
        <PointMaterial
          color="#00f2fe"
          size={0.12}
          sizeAttenuation={true}
          transparent
          opacity={0.8}
          depthWrite={false}
        />
      </Points>
    </group>
  );
}

export default function NeuralNetwork3D() {
  return (
    <div style={{ width: '100%', height: '350px', background: '#070d19', borderRadius: '12px', border: '1px solid #1c2842', overflow: 'hidden', position: 'relative' }}>
      <div style={{ position: 'absolute', top: '15px', left: '15px', zIndex: 10, color: '#00f2fe', fontFamily: 'Segoe UI', fontSize: '12px', fontWeight: 'bold', letterSpacing: '1px' }}>
        ⚛️ SINIR AĞI (THREE.JS 3D CANVAS)
      </div>
      <Canvas camera={{ position: [0, 0, 8] }}>
        <ambientLight intensity={0.5} />
        <NeuralNetworkParticles />
      </Canvas>
    </div>
  );
}

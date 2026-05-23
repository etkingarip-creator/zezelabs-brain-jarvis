import { useEffect, useRef } from 'react';

interface Node {
  x: number;
  y: number;
  z: number;
  vx: number;
  vy: number;
  dept: string;
  color: string;
  size: number;
  pulse: number;
}

const DEPT_COLORS: Record<string, string> = {
  zeze_prompt:   '#00f2fe',
  zeze_sec:      '#ef4444',
  zeze_guard:    '#db2777',
  zeze_rnd:      '#fbbf24',
  zeze_eng:      '#f59e0b',
  zeze_trading:  '#10b981',
  zeze_media:    '#a855f7',
};

const DEPTS = Object.keys(DEPT_COLORS);

export default function NeuralNetwork3D({ selectedDeptId }: { selectedDeptId: string }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const nodesRef = useRef<Node[]>([]);
  const animRef = useRef<number>(0);
  const tickRef = useRef<number>(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d')!;

    // Init nodes
    nodesRef.current = Array.from({ length: 48 }, (_, i) => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      z: Math.random(),
      vx: (Math.random() - 0.5) * 0.4,
      vy: (Math.random() - 0.5) * 0.4,
      dept: DEPTS[i % DEPTS.length],
      color: Object.values(DEPT_COLORS)[i % DEPTS.length],
      size: 3 + Math.random() * 4,
      pulse: Math.random() * Math.PI * 2,
    }));

    const resize = () => {
      canvas.width = canvas.offsetWidth;
      canvas.height = canvas.offsetHeight;
    };
    resize();
    window.addEventListener('resize', resize);

    const draw = () => {
      tickRef.current += 0.016;
      const t = tickRef.current;
      const W = canvas.width;
      const H = canvas.height;

      ctx.clearRect(0, 0, W, H);

      // Background gradient
      const bg = ctx.createRadialGradient(W/2, H/2, 0, W/2, H/2, Math.max(W, H));
      bg.addColorStop(0, '#0a1628');
      bg.addColorStop(1, '#03050f');
      ctx.fillStyle = bg;
      ctx.fillRect(0, 0, W, H);

      const nodes = nodesRef.current;

      // Move nodes
      nodes.forEach(n => {
        n.pulse += 0.04;
        n.x += n.vx;
        n.y += n.vy;
        if (n.x < 0 || n.x > W) n.vx *= -1;
        if (n.y < 0 || n.y > H) n.vy *= -1;
      });

      // Draw connections
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const a = nodes[i], b = nodes[j];
          const dx = a.x - b.x, dy = a.y - b.y;
          const dist = Math.sqrt(dx*dx + dy*dy);
          if (dist < 120) {
            const alpha = (1 - dist / 120) * 0.35;
            const isActive = a.dept === selectedDeptId || b.dept === selectedDeptId;
            ctx.beginPath();
            ctx.moveTo(a.x, a.y);
            ctx.lineTo(b.x, b.y);
            ctx.strokeStyle = isActive
              ? `${DEPT_COLORS[selectedDeptId]}${Math.floor(alpha * 255).toString(16).padStart(2,'0')}`
              : `#00f2fe${Math.floor(alpha * 100).toString(16).padStart(2,'0')}`;
            ctx.lineWidth = isActive ? 1.2 : 0.5;
            ctx.stroke();
          }
        }
      }

      // Draw nodes
      nodes.forEach(n => {
        const isSelected = n.dept === selectedDeptId;
        const pulseFactor = isSelected ? 1 + 0.4 * Math.sin(n.pulse) : 1;
        const r = n.size * pulseFactor;

        // Glow
        const glow = ctx.createRadialGradient(n.x, n.y, 0, n.x, n.y, r * 4);
        const c = isSelected ? n.color : '#00f2fe';
        glow.addColorStop(0, `${c}60`);
        glow.addColorStop(1, `${c}00`);
        ctx.beginPath();
        ctx.arc(n.x, n.y, r * 4, 0, Math.PI * 2);
        ctx.fillStyle = glow;
        ctx.fill();

        // Core
        const core = ctx.createRadialGradient(n.x - r*0.3, n.y - r*0.3, 0, n.x, n.y, r);
        core.addColorStop(0, '#ffffff');
        core.addColorStop(0.5, n.color);
        core.addColorStop(1, '#00000080');
        ctx.beginPath();
        ctx.arc(n.x, n.y, r, 0, Math.PI * 2);
        ctx.fillStyle = core;
        ctx.fill();
      });

      // Scanlines
      ctx.fillStyle = 'rgba(0,242,254,0.015)';
      for (let y = 0; y < H; y += 4) {
        ctx.fillRect(0, y, W, 1);
      }

      // HQ Title overlay
      ctx.font = 'bold 13px "Segoe UI"';
      ctx.fillStyle = '#00f2fe';
      ctx.textAlign = 'center';
      ctx.fillText('🏛️  ZEZELABS SİBER KARARGAH — CANLI AJAN AĞINIZ', W / 2, 28);
      ctx.textAlign = 'start';

      animRef.current = requestAnimationFrame(draw);
    };

    animRef.current = requestAnimationFrame(draw);
    return () => {
      cancelAnimationFrame(animRef.current);
      window.removeEventListener('resize', resize);
    };
  }, [selectedDeptId]);

  return (
    <canvas
      ref={canvasRef}
      style={{ width: '100%', height: '100%', display: 'block', borderRadius: '8px' }}
    />
  );
}

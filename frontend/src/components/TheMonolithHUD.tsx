import React, { useState, useEffect, useRef } from 'react';
import { useJarvisConnection } from '../hooks/useJarvisConnection';
import { useDepartments } from '../hooks/useDepartments';
import { useJarvisStore } from '../stores';
import { FLOOR_CATALOG } from '../data/floors';

export default function TheMonolithHUD() {
  const jarvis = useJarvisConnection();
  const { data: deptData, isLive } = useDepartments();

  const [input, setInput] = useState('');
  const [expandedFloor, setExpandedFloor] = useState<number | null>(null);

  // Critic Agent durum metni — GERÇEK jarvis.state geçişlerine tepki verir.
  // Skor değeri için gerçek bir telemetri kaynağı bağlanana kadar dürüstçe '—' gösterilir
  // (uydurma random skor YOK). Backend per-task critic skoru beslendiğinde criticScore set edilecek.
  const [criticScore, setCriticScore] = useState<number | '—'>('—');
  const [criticStatusText, setCriticStatusText] = useState('Görev bekleniyor.');
  const [criticBadgeText, setCriticBadgeText] = useState<string | null>(null);
  const [criticBadgeType, setCriticBadgeType] = useState<'ok' | 'warn' | null>(null);

  // CriticAgent yalnızca GERÇEK durum geçişlerine tepki verir (sahte skor üretmez)
  const prevStatusRef = useRef(jarvis.state);
  useEffect(() => {
    if (jarvis.state === 'thinking' && prevStatusRef.current !== 'thinking') {
      setCriticStatusText('CriticAgent çıktı kalitesini analiz ediyor...');
      setCriticBadgeText('Denetleniyor');
      setCriticBadgeType('warn');
    } else if (jarvis.state === 'idle' && prevStatusRef.current === 'thinking') {
      setCriticStatusText('Görev tamamlandı — sonucu sohbet panelinden inceleyin.');
      setCriticBadgeText('Tamamlandı');
      setCriticBadgeType('ok');
    }
    prevStatusRef.current = jarvis.state;
  }, [jarvis.state]);

  // Handle command submission
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || jarvis.connectionMode === 'offline') return;
    jarvis.sendMessage(input.trim());
    setInput('');
  };

  // Click chips handler
  const handleChipClick = (text: string) => {
    setInput(text);
  };

  // Dynamic HSL colors for each floor
  const getFloorColor = (floorId: number) => {
    const hue = 168 + (floorId - 1) * (300 - 168) / 16;
    return `hsl(${hue}, 75%, 62%)`;
  };

  // Filter pending approvals from message store
  const pendingApprovals = jarvis.messages.filter(
    msg => msg.action && msg.action.status === 'pending'
  );

  // Derive active tasks and completed tasks count
  const activeTasksCount = jarvis.tasks?.filter(t => t.status === 'running' || t.status === 'pending').length ?? 0;
  const completedTasksCount = jarvis.tasks?.filter(t => t.status === 'completed').length ?? 0;
  
  // Ort. critic skoru: gerçek kaynak bağlanana kadar dürüstçe '—' (sahte sabit yok)
  const averageCriticScore: number | string = '—';

  // Last user input display inside Brain panel
  const lastUserMsg = jarvis.messages
    .filter(m => m.role === 'user')
    .slice(-1)[0]?.text;

  // Active routing department info
  const activeAgentDept = useJarvisStore(state => state.activeAgentDept);
  const activeDeptId = activeAgentDept || jarvis.focusedDepartment || jarvis.activeDeptId;
  const activeDeptMeta = FLOOR_CATALOG.find(f => f.departmentId === activeDeptId);

  // SVG Concentric circle properties
  const CIRCLE_RADIUS = 32;
  const CIRCLE_CIRCUMFERENCE = 2 * Math.PI * CIRCLE_RADIUS; // ~201.06
  const gaugeOffset = typeof criticScore === 'number'
    ? CIRCLE_CIRCUMFERENCE - (CIRCLE_CIRCUMFERENCE * criticScore) / 100
    : CIRCLE_CIRCUMFERENCE;

  return (
    <div className="command-console-hud">
      <style>{`
        :root {
          --bg: #0a0e1a;
          --bg-deep: #060912;
          --glass: rgba(22, 29, 46, 0.52);
          --border: rgba(255,255,255,0.07);
          --border-strong: rgba(255,255,255,0.16);
          --text: #e8ecf4;
          --text-dim: #9aa4bd;
          --text-faint: #6e7893;
          --aurora-teal: #58e5c9;
          --aurora-violet: #9d7bff;
          --aurora-magenta: #f472b6;
          --ok: #4ade80;
          --warn: #fbbf24;
          --bad: #f87171;
          --radius: 16px;
        }

        .command-console-hud {
          position: relative;
          height: 100%;
          width: 100%;
          background: #0a0e1a;
          color: #e8ecf4;
          font-family: 'Inter', system-ui, sans-serif;
          overflow-y: auto;
          overflow-x: hidden;
          z-index: 1;
        }
        .command-console-hud::-webkit-scrollbar {
          width: 6px;
        }
        .command-console-hud::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.08);
          border-radius: 4px;
        }
        .command-console-hud::-webkit-scrollbar-thumb:hover {
          background: rgba(255, 255, 255, 0.15);
        }
        .command-console-hud * {
          box-sizing: border-box;
        }
        .command-console-hud .mono {
          font-family: 'JetBrains Mono', monospace;
        }
        .command-console-hud .dim {
          color: #9aa4bd;
        }
        .command-console-hud .aurora-bg {
          position: fixed; inset: 0; z-index: 0; pointer-events: none;
          overflow: hidden; background: #060912;
        }
        .command-console-hud .aurora-bg::before, 
        .command-console-hud .aurora-bg::after, 
        .command-console-hud .aurora-bg .blob {
          content: ''; position: absolute; border-radius: 50%;
          filter: blur(90px); opacity: 0.26; mix-blend-mode: screen;
        }
        .command-console-hud .aurora-bg::before {
          width: 50vw; height: 50vw; background: #9d7bff;
          top: -10%; left: -10%; animation: drift1 50s ease-in-out infinite alternate;
        }
        .command-console-hud .aurora-bg::after {
          width: 45vw; height: 45vw; background: #58e5c9;
          bottom: -15%; right: -5%; animation: drift2 60s ease-in-out infinite alternate;
        }
        .command-console-hud .aurora-bg .blob {
          width: 38vw; height: 38vw; background: #f472b6;
          top: 35%; left: 45%; opacity: 0.15;
          animation: drift3 70s ease-in-out infinite alternate;
        }
        @keyframes drift1 { to { transform: translate(8%, 10%) scale(1.1); } }
        @keyframes drift2 { to { transform: translate(-10%, -8%) scale(1.15); } }
        @keyframes drift3 { to { transform: translate(-6%, 12%) scale(0.92); } }

        .command-console-hud .noise {
          position: fixed; inset: 0; z-index: 0; pointer-events: none;
          opacity: 0.035; mix-blend-mode: overlay;
          background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='120'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
          background-size: 160px 160px;
        }

        .command-console-hud .app-content {
          position: relative; z-index: 1;
          max-width: 1280px; margin: 0 auto;
          padding: 18px 20px 32px;
          display: flex; flex-direction: column; gap: 18px;
          min-height: 100vh;
        }

        .command-console-hud .glass-panel {
          background: rgba(22, 29, 46, 0.52);
          border: 1px solid rgba(255, 255, 255, 0.07);
          border-radius: 16px;
          backdrop-filter: blur(18px);
          -webkit-backdrop-filter: blur(18px);
        }

        /* Topbar */
        .command-console-hud .topbar {
          display: flex; align-items: center; justify-content: space-between;
          gap: 24px; padding: 14px 22px; flex-wrap: wrap;
        }
        .command-console-hud .brand {
          font-family: 'Space Grotesk', sans-serif; font-weight: 700;
          font-size: 1.15rem; letter-spacing: 0.04em;
          display: flex; align-items: center; gap: 8px;
        }
        .command-console-hud .brand .mark { color: #9d7bff; font-size: 1.3rem; line-height: 1; }
        .command-console-hud .brand .core {
          color: #9aa4bd; font-weight: 500; font-size: 0.78em;
          letter-spacing: 0.18em; margin-left: 2px;
        }
        .command-console-hud .status { display: flex; align-items: center; gap: 8px; font-size: 0.82rem; color: #9aa4bd; }
        .command-console-hud .dot { width: 8px; height: 8px; border-radius: 50%; background: #4ade80; }
        .command-console-hud .dot.pulse { animation: pulseDot 2.2s ease-out infinite; }
        @keyframes pulseDot {
          0% { box-shadow: 0 0 0 0 rgba(74,222,128,0.55); }
          70% { box-shadow: 0 0 0 8px rgba(74,222,128,0); }
          100% { box-shadow: 0 0 0 0 rgba(74,222,128,0); }
        }
        .command-console-hud .token-usage { display: flex; align-items: center; gap: 10px; font-size: 0.74rem; }
        .command-console-hud .token-label { color: #6e7893; letter-spacing: 0.12em; font-weight: 600; }
        .command-console-hud .token-bar { width: 120px; height: 6px; border-radius: 4px; background: rgba(255,255,255,0.06); overflow: hidden; }
        .command-console-hud .token-fill {
          height: 100%; border-radius: 4px;
          background: linear-gradient(90deg, #58e5c9, #9d7bff);
          transition: width 0.6s ease;
        }
        .command-console-hud .token-val { color: #9aa4bd; }

        /* Hero */
        .command-console-hud .hero { padding: 32px 28px 26px; text-align: center; }
        .command-console-hud .hero .eyebrow {
          display: block; font-family: 'JetBrains Mono', monospace;
          font-size: 0.72rem; letter-spacing: 0.3em; text-transform: uppercase;
          color: #58e5c9; margin-bottom: 12px;
        }
        .command-console-hud .hero h1 {
          font-family: 'Space Grotesk', sans-serif; font-weight: 600;
          font-size: clamp(1.5rem, 4vw, 2.3rem); margin: 0 0 22px; letter-spacing: -0.01em;
          color: #e8ecf4;
        }
        .command-console-hud .hero h1 .accent {
          background: linear-gradient(90deg, #58e5c9, #9d7bff, #f472b6);
          -webkit-background-clip: text; background-clip: text; color: transparent;
        }
        .command-console-hud .command-bar {
          display: flex; align-items: center; gap: 10px;
          max-width: 680px; margin: 0 auto 18px;
          padding: 6px 6px 6px 18px; border-radius: 14px;
          background: rgba(10,14,26,0.6); border: 1px solid rgba(255,255,255,0.16);
          transition: border-color 0.2s ease, box-shadow 0.2s ease;
        }
        .command-console-hud .command-bar:focus-within {
          border-color: #9d7bff;
          box-shadow: 0 0 0 3px rgba(157,123,255,0.12);
        }
        .command-console-hud .prompt-caret { font-family: 'JetBrains Mono', monospace; color: #58e5c9; font-size: 1.05rem; user-select: none; }
        .command-console-hud .command-bar input {
          flex: 1; background: transparent; border: none; outline: none;
          color: #e8ecf4; font-size: 0.96rem; font-family: 'Inter', sans-serif; padding: 12px 0;
        }
        .command-console-hud .command-bar input::placeholder { color: #6e7893; }
        .command-console-hud .command-bar button {
          flex-shrink: 0; border: none; border-radius: 10px; padding: 11px 20px;
          font-size: 0.88rem; font-weight: 600; font-family: 'Inter', sans-serif;
          color: #0a0e1a; background: linear-gradient(135deg, #58e5c9, #9d7bff);
          cursor: pointer; transition: transform 0.15s ease, filter 0.15s ease;
        }
        .command-console-hud .command-bar button:hover { filter: brightness(1.08); }
        .command-console-hud .command-bar button:active { transform: scale(0.97); }
        .command-console-hud .command-bar button:disabled { opacity: 0.6; cursor: default; transform: none; }

        .command-console-hud .quick-chips { display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; }
        .command-console-hud .quick-chips button {
          border: 1px solid rgba(255,255,255,0.07); background: rgba(255,255,255,0.03);
          color: #9aa4bd; border-radius: 999px; padding: 8px 16px;
          font-size: 0.82rem; font-family: 'Inter', sans-serif; cursor: pointer;
          transition: border-color 0.15s ease, color 0.15s ease, background 0.15s ease;
        }
        .command-console-hud .quick-chips button:hover { border-color: rgba(255,255,255,0.16); color: #e8ecf4; background: rgba(255,255,255,0.06); }

        /* Main Grid */
        .command-console-hud .grid {
          display: grid;
          grid-template-columns: 1.3fr 1fr;
          grid-template-rows: auto auto auto;
          gap: 18px;
        }
        .command-console-hud .tower-panel { grid-column: 1; grid-row: 1 / span 3; display: flex; flex-direction: column; min-height: 0; }
        .command-console-hud .kpi-panel { grid-column: 2; grid-row: 1; }
        .command-console-hud .delegation-panel { grid-column: 2; grid-row: 2; display: flex; flex-direction: column; }
        .command-console-hud .approval-panel { grid-column: 2; grid-row: 3; }

        @media (max-width: 880px) {
          .command-console-hud .grid { grid-template-columns: 1fr; grid-template-rows: auto; }
          .command-console-hud .tower-panel { grid-column: auto; grid-row: auto; order: 4; }
          .command-console-hud .kpi-panel { grid-column: auto; grid-row: auto; order: 1; }
          .command-console-hud .approval-panel { grid-column: auto; grid-row: auto; order: 2; }
          .command-console-hud .delegation-panel { grid-column: auto; grid-row: auto; order: 3; }
          .command-console-hud .tower { max-height: 380px; }
        }

        .command-console-hud .panel-head {
          display: flex; align-items: baseline; justify-content: space-between;
          padding: 18px 22px 4px;
        }
        .command-console-hud .panel-head h2 {
          font-family: 'Space Grotesk', sans-serif; font-size: 0.94rem; font-weight: 600;
          letter-spacing: 0.06em; margin: 0; text-transform: uppercase;
          color: #e8ecf4;
        }
        .command-console-hud .panel-head .live-tag {
          font-size: 0.7rem; letter-spacing: 0.16em; color: #58e5c9;
          display: flex; align-items: center; gap: 6px; text-transform: uppercase;
        }
        .command-console-hud .panel-head .live-tag .dot { width: 6px; height: 6px; background: #58e5c9; }
        .command-console-hud .panel-head .sub { font-size: 0.7rem; color: #6e7893; }

        /* KPI summary */
        .command-console-hud .kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; padding: 6px 22px 20px; }
        @media (max-width: 480px) { .command-console-hud .kpi-grid { grid-template-columns: repeat(2, 1fr); } }
        .command-console-hud .kpi { display: flex; flex-direction: column; gap: 4px; }
        .command-console-hud .kpi .val { font-family: 'JetBrains Mono', monospace; font-size: 1.35rem; font-weight: 600; color: #e8ecf4; transition: color 0.3s ease; }
        .command-console-hud .kpi .lbl { font-size: 0.7rem; color: #6e7893; line-height: 1.4; }

        /* Tower */
        .command-console-hud .tower { display: flex; flex-direction: column; padding: 6px 14px 14px; flex: 1; min-height: 320px; max-height: 700px; overflow-y: auto; }
        .command-console-hud .tower::-webkit-scrollbar { width: 6px; }
        .command-console-hud .tower::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.08); border-radius: 4px; }

        .command-console-hud .floor {
          display: grid; grid-template-columns: 36px 1fr auto; align-items: center;
          gap: 12px; padding: 10px 12px; border-radius: 10px; border: 1px solid transparent;
          cursor: pointer; transition: background 0.18s ease, border-color 0.18s ease;
          width: 100%; background: none; font: inherit; color: inherit; text-align: left;
        }
        .command-console-hud .floor:hover { background: rgba(255,255,255,0.03); }
        .command-console-hud .floor.expanded, 
        .command-console-hud .floor.active-pulse { background: rgba(255,255,255,0.045); border-color: rgba(255,255,255,0.16); }
        .command-console-hud .floor.active-pulse { animation: floorPulse 1.4s ease-out infinite alternate; }
        @keyframes floorPulse {
          0%, 100% { box-shadow: 0 0 0 0 transparent; }
          50% { box-shadow: 0 0 22px -4px var(--floor-color, #58e5c9); }
        }
        .command-console-hud .floor .num { font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; color: #6e7893; text-align: right; }
        .command-console-hud .floor .info { min-width: 0; }
        .command-console-hud .floor .info .name { font-size: 0.88rem; font-weight: 500; color: #e8ecf4; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: block; }
        .command-console-hud .floor .info .id { font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; color: #6e7893; display: block; }
        .command-console-hud .floor .glow { width: 64px; height: 5px; border-radius: 3px; background: rgba(255,255,255,0.06); overflow: hidden; flex-shrink: 0; }
        .command-console-hud .floor .glow-fill { display: block; height: 100%; border-radius: 3px; transition: width 0.8s ease, background 0.8s ease; }

        .command-console-hud .floor-detail {
          padding: 4px 12px 12px 48px; font-size: 0.82rem;
          color: #9aa4bd; line-height: 1.5;
        }
        .command-console-hud .floor-detail .row { display: flex; gap: 18px; margin-top: 6px; font-size: 0.74rem; flex-wrap: wrap; }
        .command-console-hud .floor-detail .row span { display: inline-flex; align-items: baseline; }
        .command-console-hud .floor-detail .row span .label { color: #6e7893; margin-right: 4px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }

        /* Delegation panel */
        .command-console-hud .delegation-body { padding: 6px 22px 18px; min-height: 70px; font-size: 0.9rem; line-height: 1.6; }
        .command-console-hud .delegation-body .empty { color: #6e7893; font-size: 0.86rem; margin: 0; }
        .command-console-hud .delegation-body .route-line {
          display: flex; align-items: center; gap: 8px; font-family: 'JetBrains Mono', monospace;
          font-size: 0.78rem; color: #58e5c9; margin-bottom: 8px;
        }
        .command-console-hud .delegation-body .task-text { color: #e8ecf4; border-left: 2px solid rgba(255,255,255,0.16); padding-left: 12px; }

        .command-console-hud .critic-block, 
        .command-console-hud .memory-block { padding: 16px 22px; border-top: 1px solid rgba(255,255,255,0.07); }
        .command-console-hud .critic-block h3, 
        .command-console-hud .memory-block h3 {
          font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.14em;
          color: #6e7893; margin: 0 0 14px; font-weight: 600;
        }
        .command-console-hud .critic-row { display: flex; align-items: center; gap: 18px; }
        .command-console-hud .gauge circle { fill: none; stroke-width: 7; }
        .command-console-hud .gauge .gauge-bg { stroke: rgba(255,255,255,0.07); }
        .command-console-hud .gauge .gauge-fg {
          stroke: #58e5c9; stroke-linecap: round;
          transform: rotate(-90deg); transform-origin: 50% 50%;
          transition: stroke-dashoffset 1s cubic-bezier(.4,0,.2,1), stroke 0.6s ease;
        }
        .command-console-hud .gauge-wrap { position: relative; width: 76px; height: 76px; flex-shrink: 0; }
        .command-console-hud .gauge-score {
          position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
          font-family: 'JetBrains Mono', monospace; font-size: 1.4rem; font-weight: 600;
          color: #e8ecf4;
        }
        .command-console-hud .critic-status { font-size: 0.86rem; color: #9aa4bd; line-height: 1.5; }
        .command-console-hud .critic-status .badge {
          display: inline-block; margin-top: 4px; font-size: 0.72rem;
          font-family: 'JetBrains Mono', monospace; padding: 3px 8px; border-radius: 6px; background: rgba(255,255,255,0.05);
          font-weight: 600;
        }
        .command-console-hud .badge.ok { color: #4ade80; }
        .command-console-hud .badge.warn { color: #fbbf24; }

        .command-console-hud .memory-stats { display: flex; gap: 28px; }
        .command-console-hud .memory-stats > div { display: flex; flex-direction: column; gap: 4px; }
        .command-console-hud .memory-stats span { font-family: 'JetBrains Mono', monospace; font-size: 1.25rem; color: #9d7bff; font-weight: 600; }
        .command-console-hud .memory-stats label { font-size: 0.72rem; color: #6e7893; letter-spacing: 0.04em; text-transform: uppercase; }

        /* Approval queue */
        .command-console-hud .approval-list { display: flex; flex-direction: column; gap: 10px; padding: 6px 22px 18px; }
        .command-console-hud .approval-item {
          display: flex; align-items: center; justify-content: space-between; gap: 12px;
          padding: 12px 14px; border: 1px solid rgba(255,255,255,0.07); border-radius: 10px;
          background: rgba(255, 255, 255, 0.01);
          transition: all 0.35s ease;
        }
        .command-console-hud .approval-main .title { font-size: 0.86rem; margin-bottom: 4px; color: #e8ecf4; }
        .command-console-hud .approval-main .meta { font-size: 0.7rem; color: #6e7893; display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
        .command-console-hud .risk { font-size: 0.65rem; padding: 2px 7px; border-radius: 5px; letter-spacing: 0.05em; font-weight: 600; text-transform: uppercase; }
        .command-console-hud .risk-med { background: rgba(251,191,36,0.12); color: #fbbf24; }
        .command-console-hud .risk-low { background: rgba(74,222,128,0.12); color: #4ade80; }
        .command-console-hud .approval-actions { display: flex; gap: 8px; flex-shrink: 0; }
        .command-console-hud .approval-actions button {
          font-family: 'Inter', sans-serif; font-size: 0.78rem; padding: 7px 12px; border-radius: 8px;
          cursor: pointer; border: 1px solid rgba(255,255,255,0.16); background: rgba(255,255,255,0.03); color: #e8ecf4;
          transition: background 0.15s ease, border-color 0.15s ease, color 0.15s ease;
        }
        .command-console-hud .btn-approve:hover { border-color: #4ade80; color: #4ade80; background: rgba(74,222,128,0.05); }
        .command-console-hud .btn-reject:hover { border-color: #f87171; color: #f87171; background: rgba(248,113,113,0.05); }
        .command-console-hud .approval-empty { padding: 4px 22px 20px; font-size: 0.84rem; color: #6e7893; margin: 0; }

        /* Roadmap */
        .command-console-hud .roadmap { padding: 16px 22px; }
        .command-console-hud .roadmap-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-top: 12px; }
        @media (max-width: 700px) { .command-console-hud .roadmap-grid { grid-template-columns: 1fr 1fr; } }
        .command-console-hud .roadmap-item { border: 1px solid rgba(255,255,255,0.07); border-radius: 10px; padding: 12px 14px; font-size: 0.78rem; line-height: 1.5; background: rgba(255, 255, 255, 0.01); }
        .command-console-hud .roadmap-item .q { font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; letter-spacing: 0.14em; margin-bottom: 6px; display: inline-block; font-weight: 600; }
        .command-console-hud .roadmap-item.q1 .q { color: #58e5c9; }
        .command-console-hud .roadmap-item.q2 .q { color: #9d7bff; }
        .command-console-hud .roadmap-item.q3 .q { color: #f472b6; }
        .command-console-hud .roadmap-item.q4 .q { color: #9aa4bd; }
        .command-console-hud .roadmap-item .title { color: #e8ecf4; font-weight: 500; margin-bottom: 4px; }
        .command-console-hud .roadmap-item .desc { color: #6e7893; }
      `}</style>

      {/* Ambient aurora glow background blobs */}
      <div className="aurora-bg" aria-hidden="true">
        <div className="blob"></div>
      </div>
      <div className="noise" aria-hidden="true"></div>

      <div className="app-content">
        {/* Top bar header */}
        <header className="topbar glass-panel">
          <div className="brand">
            <span className="mark">◆</span> JARVIS ZOM <span className="core">CORE</span>
          </div>
          <div className="status">
            <span className={`dot ${isLive ? 'pulse' : ''}`} style={{ background: isLive ? '#4ade80' : '#f87171' }}></span>
            {isLive ? 'Çekirdek aktif — 17 departman çevrimiçi' : 'Bağlantı kesildi — Çevrimdışı mod'}
          </div>
          <div className="token-usage">
            <span className="token-label mono">AKTİF GÖREV</span>
            <div className="token-bar">
              <div className="token-fill" style={{ width: `${Math.min(100, activeTasksCount * 20)}%` }}></div>
            </div>
            <span className="token-val mono">{activeTasksCount} çalışıyor</span>
          </div>
        </header>

        {/* Command center hero prompt search */}
        <section className="hero glass-panel">
          <span className="eyebrow">Komuta Konsolu</span>
          <h1>Görevi tanımla, <span className="accent">kuleye devret.</span></h1>
          <form className="command-bar" onSubmit={handleSubmit}>
            <span className="prompt-caret">›</span>
            <input 
              id="commandInput"
              type="text" 
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="Bir görev tanımla — Jarvis ilgili departmana yönlendirsin..." 
              autoComplete="off"
              disabled={jarvis.connectionMode === 'offline'}
            />
            <button type="submit" disabled={!input.trim() || jarvis.connectionMode === 'offline'}>
              Gönder
            </button>
          </form>
          <div className="quick-chips">
            <button type="button" onClick={() => handleChipClick('Bitcoin için kısa vadeli arbitraj fırsatlarını tara')}>
              📈 Portföy analizi
            </button>
            <button type="button" onClick={() => handleChipClick('Yeni giriş ekranı için Aurora Glow temalı bir tasarım hazırla')}>
              🎨 Tasarım üret
            </button>
            <button type="button" onClick={() => handleChipClick('Bu hafta sosyal medyada paylaşılacak 3 içerik fikri çıkar')}>
              📣 İçerik fikri
            </button>
            <button type="button" onClick={() => handleChipClick('API anahtarlarında olası bir sızıntı var mı kontrol et')}>
              🛡️ Güvenlik taraması
            </button>
          </div>
        </section>

        {/* Main interactive grid */}
        <main className="grid">
          {/* Floor Monolith lists */}
          <section className="tower-panel glass-panel">
            <div className="panel-head">
              <h2>Kule — 17 Departman</h2>
              <span className="live-tag">
                <span className="dot pulse" style={{ background: '#58e5c9' }}></span> canlı
              </span>
            </div>
            <div className="tower">
              {FLOOR_CATALOG.map(floor => {
                const isExpanded = expandedFloor === floor.id;
                const isPulse = activeDeptId === floor.departmentId && jarvis.state === 'thinking';
                const color = getFloorColor(floor.id);
                const deptDetails = deptData?.departments[floor.departmentId];

                // Aktivite: yalnızca GERÇEK deptData'dan; canlı veri yoksa 0 (sahte drift yok)
                const activity = deptDetails
                  ? Math.min(100, Math.max(5, (deptDetails.active_agents * 25) + (deptDetails.queue_depth * 10) + (parseInt(deptDetails.system_usage.cpu) || 10)))
                  : 0;

                return (
                  <React.Fragment key={floor.id}>
                    <button
                      type="button"
                      className={`floor ${isExpanded ? 'expanded' : ''} ${isPulse ? 'active-pulse' : ''}`}
                      style={{ '--floor-color': color } as React.CSSProperties}
                      onClick={() => setExpandedFloor(isExpanded ? null : floor.id)}
                    >
                      <span className="num mono">K{floor.id}</span>
                      <span className="info">
                        <span className="name">{floor.name}</span>
                        <span className="id mono">{floor.departmentId}</span>
                      </span>
                      <span className="glow">
                        <span className="glow-fill" style={{ width: `${activity}%`, background: color }}></span>
                      </span>
                    </button>
                    {isExpanded && (
                      <div className="floor-detail">
                        <div>{floor.description}</div>
                        <div className="row mono">
                          <span>
                            <span className="label">durum </span>
                            {deptDetails?.status || (activity > 50 ? 'aktif' : 'bekliyor')}
                          </span>
                          <span>
                            <span className="label">yük </span>
                            %{activity}
                          </span>
                          {deptDetails && (
                            <>
                              <span>
                                <span className="label">ajanlar </span>
                                {deptDetails.active_agents}
                              </span>
                              <span>
                                <span className="label">kuyruk </span>
                                {deptDetails.queue_depth}
                              </span>
                              <span>
                                <span className="label">cpu </span>
                                {deptDetails.system_usage.cpu}
                              </span>
                            </>
                          )}
                        </div>
                      </div>
                    )}
                  </React.Fragment>
                );
              })}
            </div>
          </section>

          {/* Holding summary KPIs */}
          <section className="kpi-panel glass-panel">
            <div className="panel-head">
              <h2>Holding Özeti</h2>
              <span className="sub mono">son 24 saat</span>
            </div>
            <div className="kpi-grid">
              <div className="kpi">
                <span className="val">{activeTasksCount}</span>
                <span className="lbl">Aktif görev</span>
              </div>
              <div className="kpi">
                <span className="val">{completedTasksCount}</span>
                <span className="lbl">Tamamlanan</span>
              </div>
              <div className="kpi">
                <span className="val">{averageCriticScore}</span>
                <span className="lbl">Ort. critic skoru</span>
              </div>
              <div className="kpi">
                <span className="val">{pendingApprovals.length}</span>
                <span className="lbl">Onay bekleyen</span>
              </div>
            </div>
          </section>

          {/* Brain active routing delegation telemetry panel */}
          <section className="delegation-panel glass-panel">
            <div className="panel-head">
              <h2>Beyin — Aktif Delegasyon</h2>
            </div>
            <div className="delegation-body">
              {activeDeptMeta && jarvis.state === 'thinking' ? (
                <>
                  <div className="route-line">BEYİN ➔ K{activeDeptMeta.id} · {activeDeptMeta.departmentId}</div>
                  <div className="task-text">{lastUserMsg || 'Talimat işleniyor...'}</div>
                </>
              ) : (
                <p className="empty">
                  Henüz bir görev gönderilmedi. Komut çubuğuna bir görev yazın — Jarvis ilgili departmana yönlendirsin ve sonucu CriticAgent denetiminden geçirsin.
                </p>
              )}
            </div>

            <div className="critic-block">
              <h3>CriticAgent Denetimi</h3>
              <div className="critic-row">
                <div className="gauge-wrap">
                  <svg className="gauge" width="76" height="76" viewBox="0 0 76 76">
                    <circle className="gauge-bg" cx="38" cy="38" r="32"></circle>
                    <circle 
                      className="gauge-fg" 
                      cx="38" 
                      cy="38" 
                      r="32" 
                      strokeDasharray={CIRCLE_CIRCUMFERENCE} 
                      strokeDashoffset={gaugeOffset}
                      style={{
                        stroke: typeof criticScore === 'number' && criticScore >= 70 ? '#4ade80' : '#fbbf24'
                      }}
                    ></circle>
                  </svg>
                  <div className="gauge-score">{criticScore}</div>
                </div>
                <div className="critic-status">
                  <div>{criticStatusText}</div>
                  {criticBadgeText && (
                    <span className={`badge ${criticBadgeType === 'ok' ? 'ok' : 'warn'}`}>
                      {criticBadgeText}
                    </span>
                  )}
                </div>
              </div>
            </div>

            <div className="memory-block">
              <h3>Bellek Katmanı (SQLite FTS5)</h3>
              <div className="memory-stats">
                <div>
                  <span>{completedTasksCount || '—'}</span>
                  <label>işlenen görev</label>
                </div>
                <div>
                  <span>{jarvis.messages.length || '—'}</span>
                  <label>oturum kaydı</label>
                </div>
              </div>
            </div>
          </section>

          {/* Action approvals queue panel */}
          <section className="approval-panel glass-panel">
            <div className="panel-head">
              <h2>Onay Kuyruğu</h2>
              <span className="sub mono">insan onayı gerekli</span>
            </div>
            <div className="approval-list">
              {pendingApprovals.map(msg => {
                const action = msg.action!;
                const deptMeta = FLOOR_CATALOG.find(f => f.departmentId === msg.departmentId);
                const isLowRisk = action.description.toLowerCase().includes('limit') || action.description.toLowerCase().includes('düşük') || action.description.toLowerCase().includes('uyum');
                
                return (
                  <div className="approval-item" key={msg.id}>
                    <div className="approval-main">
                      <div className="title">{action.description || msg.text}</div>
                      <div className="meta mono">
                        {deptMeta ? `K${deptMeta.id} · ${msg.departmentId}` : 'ZOM CORE'} 
                        <span className={`risk ${isLowRisk ? 'risk-low' : 'risk-med'}`}>
                          {isLowRisk ? 'Düşük risk' : 'Orta risk'}
                        </span>
                      </div>
                    </div>
                    <div className="approval-actions">
                      <button 
                        type="button"
                        className="btn-approve" 
                        onClick={() => jarvis.sendActionResponse(action.id, true)}
                      >
                        Onayla
                      </button>
                      <button 
                        type="button"
                        className="btn-reject" 
                        onClick={() => jarvis.sendActionResponse(action.id, false)}
                      >
                        Reddet
                      </button>
                    </div>
                  </div>
                );
              })}
              {pendingApprovals.length === 0 && (
                <p className="approval-empty">Kuyruk temiz — onay bekleyen aksiyon yok.</p>
              )}
            </div>
          </section>
        </main>

        {/* Bottom Roadmap */}
        <section className="roadmap glass-panel">
          <div className="panel-head" style={{ paddingBottom: 0 }}>
            <h2>2026 Yol Haritası</h2>
          </div>
          <div className="roadmap-grid">
            <div className="roadmap-item q1">
              <span className="q mono">Q1 · HIZ &amp; BELLEK</span>
              <div className="title">Asenkron geçiş</div>
              <div className="desc">Senkron çağrıları asenkronlaştır, FTS5 sorgu süresini &lt;50ms'e indir.</div>
            </div>
            <div className="roadmap-item q2">
              <span className="q mono">Q2 · COGNITIVE PLUGINS</span>
              <div className="title">Departmanlar arası köprü</div>
              <div className="desc">Inter-agent delegasyon ve token bütçe limitörü devreye girer.</div>
            </div>
            <div className="roadmap-item q3">
              <span className="q mono">Q3 · OTONOM ÜRETİM</span>
              <div className="title">Sandbox test pipeline</div>
              <div className="desc">App Factory üretilen kodu izole ortamda otonom test eder.</div>
            </div>
            <div className="roadmap-item q4">
              <span className="q mono">Q4 · TAM ENTEGRASYON</span>
              <div className="title">Dağıtık holding</div>
              <div className="desc">17 departman, tek tıkla Docker Swarm / K8s ortamına deploy.</div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}

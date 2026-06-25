// KonvaCanvasView — Konva.js tabanlı yüksek performanslı canvas renderer
// DOM div absolute → Konva Stage/Layer/Shape/Transformer
// 60 FPS drag, resize, zoom. React.memo + Konva native events.

import React, { useRef, useCallback, useEffect, useState } from 'react';
import Konva from 'konva';
import {
  Stage,
  Layer,
  Rect,
  Circle,
  RegularPolygon,
  Text,
  Group,
  Transformer,
  Line,
} from 'react-konva';
import type { CanvasElement, CanvasConfig, ToolType } from '../../types/canvas';
import { Toolbar } from './Toolbar';

// ─── Types ────────────────────────────────────────────────────────────────────

interface KonvaCanvasViewProps {
  elements: CanvasElement[];
  canvasConfig: CanvasConfig;
  selectedId: string | null;
  activeTool: ToolType;
  zoom: number;
  isDark: boolean;
  isGenerating: boolean;
  snapGrid: number;
  onToolChange: (t: ToolType) => void;
  onZoomChange: (z: number) => void;
  onSelectId: (id: string | null) => void;
  onAddElement: (el: CanvasElement) => void;
  onCommitBulk: (els: CanvasElement[]) => void;
  onUpdateElement: (id: string, changes: Partial<CanvasElement>) => void;
}

// ─── Snap yardımcısı ──────────────────────────────────────────────────────────
function snap(v: number, grid: number): number {
  if (!grid) return v;
  return Math.round(v / grid) * grid;
}

// ─── Eleman renk çözümleyici ──────────────────────────────────────────────────
function resolveColor(el: CanvasElement): string {
  return el.background && !el.background.includes('gradient')
    ? el.background
    : el.fill;
}

// ─── Konva Shape Bileşeni ─────────────────────────────────────────────────────

interface ShapeNodeProps {
  element: CanvasElement;
  isSelected: boolean;
  isDark: boolean;
  snapGrid: number;
  activeTool: string;
  onSelect: (id: string) => void;
  onDragEnd: (id: string, x: number, y: number) => void;
  onTransformEnd: (id: string, x: number, y: number, w: number, h: number, rot: number) => void;
  onDblClick: (id: string) => void;
}

const ShapeNode = React.memo(function ShapeNode({
  element,
  isSelected,
  isDark,
  snapGrid,
  activeTool,
  onSelect,
  onDragEnd,
  onTransformEnd,
  onDblClick,
}: ShapeNodeProps) {
  const shapeRef = useRef<Konva.Shape | Konva.Group>(null);
  const isDraggable = activeTool === 'select' && !element.locked;
  const opacity = (element.opacity ?? 100) / 100;
  const rotation = element.rotation ?? 0;
  const fill = resolveColor(element);

  const commonProps = {
    id: element.id,
    x: element.x,
    y: element.y,
    width: element.width,
    height: element.height,
    opacity,
    rotation,
    draggable: isDraggable,
    onClick: () => { if (activeTool === 'select') onSelect(element.id); },
    onDblClick: () => onDblClick(element.id),
    onDragEnd: (e: Konva.KonvaEventObject<DragEvent>) => {
      const node = e.target;
      const x = snap(node.x(), snapGrid);
      const y = snap(node.y(), snapGrid);
      node.position({ x, y });
      onDragEnd(element.id, x, y);
    },
    onTransformEnd: (e: Konva.KonvaEventObject<Event>) => {
      const node = e.target;
      const scaleX = node.scaleX();
      const scaleY = node.scaleY();
      node.scaleX(1);
      node.scaleY(1);
      const newW = snap(Math.max(10, node.width() * scaleX), snapGrid);
      const newH = snap(Math.max(10, node.height() * scaleY), snapGrid);
      node.width(newW);
      node.height(newH);
      onTransformEnd(element.id, node.x(), node.y(), newW, newH, node.rotation());
    },
  };

  switch (element.type) {
    case 'rect':
      return (
        <Rect
          ref={shapeRef as React.RefObject<Konva.Rect>}
          {...commonProps}
          fill={fill}
          stroke={element.stroke !== 'transparent' ? element.stroke : undefined}
          strokeWidth={element.strokeWidth}
          cornerRadius={element.borderRadius ?? 0}
          shadowBlur={element.boxShadow ? 20 : 0}
          shadowColor={element.boxShadow ? '#6366f1' : undefined}
          shadowOpacity={element.boxShadow ? 0.4 : 0}
          shadowOffsetY={element.boxShadow ? 8 : 0}
        />
      );

    case 'circle':
      return (
        <Circle
          ref={shapeRef as React.RefObject<Konva.Circle>}
          id={element.id}
          x={element.x + element.width / 2}
          y={element.y + element.height / 2}
          radiusX={element.width / 2}
          radiusY={element.height / 2}
          width={element.width}
          height={element.height}
          fill={fill}
          stroke={element.stroke !== 'transparent' ? element.stroke : undefined}
          strokeWidth={element.strokeWidth}
          opacity={opacity}
          rotation={rotation}
          draggable={isDraggable}
          onClick={() => { if (activeTool === 'select') onSelect(element.id); }}
          onDblClick={() => onDblClick(element.id)}
          onDragEnd={(e: Konva.KonvaEventObject<DragEvent>) => {
            const node = e.target;
            onDragEnd(element.id, snap(node.x() - element.width / 2, snapGrid), snap(node.y() - element.height / 2, snapGrid));
          }}
          onTransformEnd={(e: Konva.KonvaEventObject<Event>) => {
            const node = e.target;
            const sx = node.scaleX(); const sy = node.scaleY();
            node.scaleX(1); node.scaleY(1);
            onTransformEnd(element.id, node.x() - (element.width * sx) / 2, node.y() - (element.height * sy) / 2, element.width * sx, element.height * sy, node.rotation());
          }}
        />
      );

    case 'triangle':
      return (
        <RegularPolygon
          ref={shapeRef as React.RefObject<Konva.RegularPolygon>}
          id={element.id}
          x={element.x + element.width / 2}
          y={element.y + element.height / 2}
          sides={3}
          radius={Math.min(element.width, element.height) / 2}
          fill={fill}
          stroke={element.stroke !== 'transparent' ? element.stroke : undefined}
          strokeWidth={element.strokeWidth}
          opacity={opacity}
          rotation={rotation}
          draggable={isDraggable}
          onClick={() => { if (activeTool === 'select') onSelect(element.id); }}
          onDblClick={() => onDblClick(element.id)}
          onDragEnd={(e: Konva.KonvaEventObject<DragEvent>) => {
            const node = e.target;
            onDragEnd(element.id, snap(node.x() - element.width / 2, snapGrid), snap(node.y() - element.height / 2, snapGrid));
          }}
          onTransformEnd={(e: Konva.KonvaEventObject<Event>) => {
            const node = e.target;
            const s = node.scaleX(); node.scaleX(1); node.scaleY(1);
            onTransformEnd(element.id, node.x() - (element.width * s) / 2, node.y() - (element.height * s) / 2, element.width * s, element.height * s, node.rotation());
          }}
        />
      );

    case 'text':
      return (
        <Text
          ref={shapeRef as React.RefObject<Konva.Text>}
          {...commonProps}
          text={element.text ?? ''}
          fontSize={element.fontSize ?? 16}
          fontStyle={element.fontWeight === 'bold' ? 'bold' : 'normal'}
          fontFamily={element.fontFamily ?? 'Inter, sans-serif'}
          fill={element.fill}
          align={element.textAlign ?? 'center'}
          verticalAlign="middle"
          wrap="word"
        />
      );

    case 'button-group':
      return (
        <Group {...commonProps}>
          {/* Primary button */}
          <Rect
            x={0}
            y={0}
            width={(element.width - 16) / 2}
            height={element.height}
            fill={fill}
            cornerRadius={element.borderRadius ?? 9999}
          />
          <Text
            x={0}
            y={0}
            width={(element.width - 16) / 2}
            height={element.height}
            text={element.textBtn1 ?? 'Button 1'}
            fontSize={13}
            fontStyle="bold"
            fontFamily="Inter, sans-serif"
            fill="#ffffff"
            align="center"
            verticalAlign="middle"
          />
          {/* Secondary button */}
          <Rect
            x={(element.width - 16) / 2 + 16}
            y={0}
            width={(element.width - 16) / 2}
            height={element.height}
            fill="transparent"
            stroke={element.stroke !== 'transparent' ? element.stroke : '#6366f1'}
            strokeWidth={1}
            cornerRadius={element.borderRadius ?? 9999}
          />
          <Text
            x={(element.width - 16) / 2 + 16}
            y={0}
            width={(element.width - 16) / 2}
            height={element.height}
            text={element.textBtn2 ?? 'Button 2'}
            fontSize={13}
            fontStyle="bold"
            fontFamily="Inter, sans-serif"
            fill={isDark ? '#ffffff' : '#0f172a'}
            align="center"
            verticalAlign="middle"
          />
        </Group>
      );

    case 'image':
      return (
        <Group {...commonProps}>
          <Rect
            x={0}
            y={0}
            width={element.width}
            height={element.height}
            fill="rgba(148,163,184,0.15)"
            stroke="#94a3b8"
            strokeWidth={1}
            dash={[6, 4]}
            cornerRadius={element.borderRadius ?? 8}
          />
          <Text
            x={0}
            y={0}
            width={element.width}
            height={element.height}
            text="🖼"
            fontSize={32}
            align="center"
            verticalAlign="middle"
          />
        </Group>
      );

    default:
      return null;
  }
});

// ─── Selection Transformer ────────────────────────────────────────────────────

function SelectionTransformer({
  selectedId,
  elements,
  stageRef,
}: {
  selectedId: string | null;
  elements: CanvasElement[];
  stageRef: React.RefObject<Konva.Stage>;
}) {
  const trRef = useRef<Konva.Transformer>(null);

  useEffect(() => {
    if (!trRef.current || !stageRef.current) return;
    if (!selectedId) {
      trRef.current.nodes([]);
      trRef.current.getLayer()?.batchDraw();
      return;
    }
    const node = stageRef.current.findOne(`#${selectedId}`);
    if (node) {
      trRef.current.nodes([node]);
      trRef.current.getLayer()?.batchDraw();
    }
  }, [selectedId, elements, stageRef]);

  return (
    <Transformer
      ref={trRef}
      rotateEnabled={true}
      enabledAnchors={['top-left', 'top-right', 'bottom-left', 'bottom-right', 'middle-left', 'middle-right', 'top-center', 'bottom-center']}
      boundBoxFunc={(oldBox, newBox) => {
        if (newBox.width < 10 || newBox.height < 10) return oldBox;
        return newBox;
      }}
      anchorStyleFunc={(anchor) => {
        anchor.cornerRadius(3);
        anchor.fill('#6366f1');
        anchor.stroke('#818cf8');
        anchor.strokeWidth(1.5);
        anchor.size({ width: 8, height: 8 });
      }}
      borderStroke="#6366f1"
      borderStrokeWidth={1.5}
      borderDash={[4, 3]}
    />
  );
}

// ─── Inline Text Editor Overlay ───────────────────────────────────────────────

function InlineTextEditor({
  element,
  zoom,
  canvasOffset,
  onFinish,
}: {
  element: CanvasElement;
  zoom: number;
  canvasOffset: { x: number; y: number };
  onFinish: (id: string, text: string) => void;
}) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (ref.current) {
      ref.current.focus();
      // Tüm metni seç
      const range = document.createRange();
      range.selectNodeContents(ref.current);
      window.getSelection()?.removeAllRanges();
      window.getSelection()?.addRange(range);
    }
  }, []);

  const style: React.CSSProperties = {
    position: 'absolute',
    left: canvasOffset.x + element.x * zoom,
    top: canvasOffset.y + element.y * zoom,
    width: element.width * zoom,
    height: element.height * zoom,
    fontSize: (element.fontSize ?? 16) * zoom,
    fontWeight: element.fontWeight ?? 'bold',
    fontFamily: element.fontFamily ?? 'Inter, sans-serif',
    color: element.fill,
    textAlign: (element.textAlign ?? 'center') as React.CSSProperties['textAlign'],
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '4px',
    background: 'rgba(99,102,241,0.08)',
    border: '2px solid #6366f1',
    borderRadius: 8,
    outline: 'none',
    zIndex: 100,
    transform: element.rotation ? `rotate(${element.rotation}deg)` : undefined,
    transformOrigin: 'center',
    cursor: 'text',
    lineHeight: 1.2,
    wordBreak: 'break-word',
  };

  return (
    <div
      ref={ref}
      contentEditable
      suppressContentEditableWarning
      style={style}
      onBlur={(e) => onFinish(element.id, e.currentTarget.textContent ?? '')}
      onKeyDown={(e) => {
        if (e.key === 'Escape') {
          e.currentTarget.blur();
        }
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          e.currentTarget.blur();
        }
        e.stopPropagation();
      }}
    >
      {element.text}
    </div>
  );
}

// ─── Ana KonvaCanvasView Bileşeni ─────────────────────────────────────────────

export function KonvaCanvasView({
  elements,
  canvasConfig,
  selectedId,
  activeTool,
  zoom,
  isDark,
  isGenerating,
  snapGrid,
  onToolChange,
  onZoomChange,
  onSelectId,
  onAddElement,
  onCommitBulk,
  onUpdateElement,
}: KonvaCanvasViewProps) {
  const stageRef = useRef<Konva.Stage>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [canvasOffset, setCanvasOffset] = useState({ x: 0, y: 0 });

  // Canvas merkezleme için offset hesapla
  useEffect(() => {
    if (!containerRef.current) return;
    const { offsetWidth: cw, offsetHeight: ch } = containerRef.current;
    const scaledW = canvasConfig.width * zoom;
    const scaledH = canvasConfig.height * zoom;
    setCanvasOffset({
      x: Math.max(0, (cw - scaledW) / 2),
      y: Math.max(0, (ch - scaledH) / 2),
    });
  }, [zoom, canvasConfig.width, canvasConfig.height]);

  // Zoom — mouse wheel
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    const handleWheel = (e: WheelEvent) => {
      if (!e.ctrlKey && !e.metaKey) return;
      e.preventDefault();
      const delta = e.deltaY > 0 ? 0.9 : 1.1;
      onZoomChange(Math.min(4, Math.max(0.1, zoom * delta)));
    };
    container.addEventListener('wheel', handleWheel, { passive: false });
    return () => container.removeEventListener('wheel', handleWheel);
  }, [zoom, onZoomChange]);

  // Stage tıklama → eleman ekle veya seçimi kaldır
  const handleStageClick = useCallback((e: Konva.KonvaEventObject<MouseEvent>) => {
    if (editingId) {
      setEditingId(null);
      return;
    }
    const stage = e.target.getStage();
    if (!stage) return;

    if (activeTool === 'select') {
      // Sahneye tıklandıysa (eleman değil) seçimi kaldır
      if (e.target === stage) {
        onSelectId(null);
      }
      return;
    }

    // Yeni eleman ekleme
    const pointer = stage.getPointerPosition();
    if (!pointer) return;
    // Stage koordinatlarına dönüştür (zoom + offset)
    const x = snap((pointer.x - canvasOffset.x) / zoom, snapGrid);
    const y = snap((pointer.y - canvasOffset.y) / zoom, snapGrid);

    const id = `el_${Date.now()}`;
    const maxZ = Math.max(0, ...elements.map(el => el.zIndex)) + 1;
    const base = {
      id, visible: true, locked: false, zIndex: maxZ,
      stroke: 'transparent', strokeWidth: 0,
      opacity: 100, borderRadius: 0, rotation: 0,
    };

    let newEl: CanvasElement | null = null;

    switch (activeTool) {
      case 'rect':
        newEl = { ...base, type: 'rect', name: `Dikdörtgen ${elements.length + 1}`, x: x - 50, y: y - 50, width: 100, height: 100, fill: '#3b82f6', stroke: '#2563eb', strokeWidth: 1.5, borderRadius: 8 };
        break;
      case 'circle':
        newEl = { ...base, type: 'circle', name: `Daire ${elements.length + 1}`, x: x - 50, y: y - 50, width: 100, height: 100, fill: '#10b981', stroke: '#059669', strokeWidth: 1.5 };
        break;
      case 'triangle':
        newEl = { ...base, type: 'triangle', name: `Üçgen ${elements.length + 1}`, x: x - 50, y: y - 50, width: 100, height: 100, fill: '#f59e0b', stroke: '#d97706', strokeWidth: 1.5 };
        break;
      case 'text':
        newEl = { ...base, type: 'text', name: `Metin ${elements.length + 1}`, x: x - 100, y: y - 20, width: 200, height: 40, fill: isDark ? '#ffffff' : '#0f172a', text: 'Yeni Metin', fontSize: 16, fontWeight: 'bold', textAlign: 'center' };
        break;
      case 'btn_group':
        newEl = { ...base, type: 'button-group', name: `Butonlar ${elements.length + 1}`, x: x - 150, y: y - 30, width: 300, height: 60, fill: '#4f46e5', stroke: '#7775a7', strokeWidth: 1, borderRadius: 9999, textBtn1: 'Birincil', textBtn2: 'İkincil' };
        break;
      case 'image':
        newEl = { ...base, type: 'image', name: `Görsel ${elements.length + 1}`, x: x - 100, y: y - 75, width: 200, height: 150, fill: '#94a3b8', stroke: '#64748b', strokeWidth: 1, borderRadius: 8 };
        break;
    }

    if (newEl) {
      onAddElement(newEl);
      onToolChange('select');
    }
  }, [activeTool, elements, zoom, canvasOffset, snapGrid, isDark, editingId, onAddElement, onToolChange, onSelectId]);

  // Drag end handler
  const handleDragEnd = useCallback((id: string, x: number, y: number) => {
    const next = elements.map(el => el.id === id ? { ...el, x, y } : el);
    onCommitBulk(next);
  }, [elements, onCommitBulk]);

  // Transform end handler
  const handleTransformEnd = useCallback((id: string, x: number, y: number, w: number, h: number, rot: number) => {
    const next = elements.map(el => el.id === id ? { ...el, x, y, width: w, height: h, rotation: rot } : el);
    onCommitBulk(next);
  }, [elements, onCommitBulk]);

  // Double click → inline edit (text tipi için)
  const handleDblClick = useCallback((id: string) => {
    const el = elements.find(e => e.id === id);
    if (el && el.type === 'text') {
      setEditingId(id);
    }
  }, [elements]);

  // Inline edit bitti
  const handleFinishEdit = useCallback((id: string, text: string) => {
    if (text !== elements.find(e => e.id === id)?.text) {
      onUpdateElement(id, { text });
    }
    setEditingId(null);
  }, [elements, onUpdateElement]);

  const visibleElements = [...elements]
    .filter(el => el.visible)
    .sort((a, b) => a.zIndex - b.zIndex);

  const editingElement = editingId ? elements.find(e => e.id === editingId) : null;

  // Workspace background rengi (canvasConfig.workspaceBg veya dark theme)
  const workspaceBg = canvasConfig.workspaceBg
    ?? (isDark ? '#0f172a' : '#f1f5f9');

  // Canvas fill/background
  const canvasBg = canvasConfig.background ?? canvasConfig.fill;

  // Gradient background için stage üstünde bir div overlay gerekir (Konva SVG fill kullanamaz)
  const isGradientBg = canvasBg.includes('gradient');

  return (
    <section
      ref={containerRef}
      className="flex-1 relative overflow-auto flex items-start justify-start select-none canvas-dot-grid"
      style={{ backgroundColor: workspaceBg, cursor: activeTool !== 'select' ? 'crosshair' : 'default' }}
      aria-label="Tasarım kanvası"
    >
      <Toolbar activeTool={activeTool} onToolChange={onToolChange} />

      {/* Konva Stage — tüm kanvası kaplayan */}
      <div
        className="relative"
        style={{
          marginLeft: canvasOffset.x,
          marginTop: canvasOffset.y,
        }}
      >
        {/* Gradient arka plan için CSS overlay (Konva fill desteği yok) */}
        {isGradientBg && (
          <div
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: canvasConfig.width * zoom,
              height: canvasConfig.height * zoom,
              background: canvasBg,
              borderRadius: 24,
              pointerEvents: 'none',
              zIndex: 0,
            }}
          />
        )}

        {/* Kanvas kutu gölgesi ve kenarlık için overlay */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: canvasConfig.width * zoom,
            height: canvasConfig.height * zoom,
            borderRadius: 24,
            boxShadow: canvasConfig.boxShadow ?? '0 25px 50px rgba(0,0,0,0.2)',
            border: `${canvasConfig.strokeWidth}px solid ${canvasConfig.stroke}`,
            pointerEvents: 'none',
            zIndex: 50,
          }}
        />

        {/* AI laser tarama efekti */}
        {isGenerating && (
          <div
            className="laser-scan-canvas"
            style={{
              position: 'absolute',
              zIndex: 60,
              width: canvasConfig.width * zoom,
              borderRadius: 24,
              overflow: 'hidden',
            }}
          />
        )}

        <Stage
          ref={stageRef}
          width={canvasConfig.width * zoom}
          height={canvasConfig.height * zoom}
          onClick={handleStageClick}
          style={{
            borderRadius: 24,
            overflow: 'hidden',
            display: 'block',
          }}
          scaleX={zoom}
          scaleY={zoom}
          listening={true}
        >
          {/* Arka plan layer */}
          <Layer>
            <Rect
              x={0}
              y={0}
              width={canvasConfig.width}
              height={canvasConfig.height}
              fill={isGradientBg ? '#ffffff' : canvasBg}
              opacity={isGradientBg ? 0 : 1}
            />
            {/* Dot grid */}
            {Array.from({ length: Math.ceil(canvasConfig.width / 24) }).map((_, xi) =>
              Array.from({ length: Math.ceil(canvasConfig.height / 24) }).map((_, yi) => (
                <Rect
                  key={`dot-${xi}-${yi}`}
                  x={xi * 24}
                  y={yi * 24}
                  width={1.2}
                  height={1.2}
                  fill={isDark ? 'rgba(51,65,85,0.5)' : 'rgba(203,213,225,0.6)'}
                  listening={false}
                />
              ))
            )}
          </Layer>

          {/* Element layer */}
          <Layer>
            {visibleElements.map(element => (
              editingId === element.id ? null : (
                <ShapeNode
                  key={element.id}
                  element={element}
                  isSelected={selectedId === element.id}
                  isDark={isDark}
                  snapGrid={snapGrid}
                  activeTool={activeTool}
                  onSelect={onSelectId}
                  onDragEnd={handleDragEnd}
                  onTransformEnd={handleTransformEnd}
                  onDblClick={handleDblClick}
                />
              )
            ))}
          </Layer>

          {/* Selection/Transform layer */}
          <Layer>
            <SelectionTransformer
              selectedId={editingId ? null : selectedId}
              elements={elements}
              stageRef={stageRef}
            />
          </Layer>
        </Stage>

        {/* Inline text editor overlay — Konva üstünde DOM */}
        {editingElement && editingElement.type === 'text' && (
          <InlineTextEditor
            element={editingElement}
            zoom={zoom}
            canvasOffset={{ x: 0, y: 0 }}
            onFinish={handleFinishEdit}
          />
        )}
      </div>

      {/* Zoom indicator */}
      <div className="absolute bottom-4 right-4 flex items-center gap-2 bg-black/40 backdrop-blur-md rounded-xl px-3 py-1.5 text-white text-xs font-mono z-50">
        <button
          onClick={() => onZoomChange(Math.max(0.1, zoom - 0.1))}
          className="hover:text-indigo-300 transition-colors px-1 cursor-pointer"
        >−</button>
        <span>{Math.round(zoom * 100)}%</span>
        <button
          onClick={() => onZoomChange(Math.min(4, zoom + 0.1))}
          className="hover:text-indigo-300 transition-colors px-1 cursor-pointer"
        >+</button>
        <button
          onClick={() => onZoomChange(1)}
          className="hover:text-indigo-300 transition-colors px-1 ml-1 cursor-pointer text-slate-400"
        >1:1</button>
      </div>
    </section>
  );
}

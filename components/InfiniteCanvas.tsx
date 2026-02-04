'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { TransformComponent, TransformWrapper } from 'react-zoom-pan-pinch';
import { CanvasNode, CanvasState, NodeType } from '../lib/types';
import { getImageRecord, loadCanvasState, saveCanvasState, saveImageRecord } from '../lib/storage';

const DEFAULT_NODE_SIZE = { width: 260, height: 180 };
const MIN_NODE_SIZE = { width: 160, height: 120 };

const createId = () => crypto.randomUUID();

const resizeImage = (file: File, maxSize: number) =>
  new Promise<{ blob: Blob; width: number; height: number }>((resolve, reject) => {
    const img = new Image();
    const url = URL.createObjectURL(file);
    img.onload = () => {
      const scale = Math.min(1, maxSize / Math.max(img.width, img.height));
      const width = Math.round(img.width * scale);
      const height = Math.round(img.height * scale);
      const canvas = document.createElement('canvas');
      canvas.width = width;
      canvas.height = height;
      const ctx = canvas.getContext('2d');
      if (!ctx) {
        URL.revokeObjectURL(url);
        reject(new Error('Canvas context missing'));
        return;
      }
      ctx.drawImage(img, 0, 0, width, height);
      canvas.toBlob(
        (blob) => {
          URL.revokeObjectURL(url);
          if (!blob) {
            reject(new Error('Image resize failed'));
            return;
          }
          resolve({ blob, width, height });
        },
        'image/jpeg',
        0.9
      );
    };
    img.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error('Image load failed'));
    };
    img.src = url;
  });

const createNode = (type: NodeType, overrides?: Partial<CanvasNode>): CanvasNode => ({
  id: createId(),
  type,
  x: 200,
  y: 200,
  width: DEFAULT_NODE_SIZE.width,
  height: DEFAULT_NODE_SIZE.height,
  title: type === 'task' ? 'New task' : type === 'prototype' ? 'Prototype' : 'File',
  body:
    type === 'task'
      ? 'Describe the task...'
      : type === 'prototype'
        ? 'Prototype concept...'
        : undefined,
  ...overrides
});

export default function InfiniteCanvas() {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [nodes, setNodes] = useState<CanvasNode[]>([]);
  const [transform, setTransform] = useState({ scale: 1, x: 0, y: 0 });
  const [dragState, setDragState] = useState<{
    id: string;
    offsetX: number;
    offsetY: number;
  } | null>(null);
  const [resizeState, setResizeState] = useState<{
    id: string;
    startX: number;
    startY: number;
    startWidth: number;
    startHeight: number;
  } | null>(null);
  const [initialStateLoaded, setInitialStateLoaded] = useState(false);
  const activeUrls = useRef<Set<string>>(new Set());

  const isInteracting = Boolean(dragState || resizeState);

  const storeState = useCallback(
    (nextNodes: CanvasNode[], nextTransform = transform) => {
      const state: CanvasState = { nodes: nextNodes, transform: nextTransform };
      saveCanvasState(state);
    },
    [transform]
  );

  useEffect(() => {
    const state = loadCanvasState();
    if (!state) {
      setNodes([
        createNode('task', { x: 160, y: 140, title: 'Kickoff' }),
        createNode('prototype', { x: 520, y: 200, title: 'Flow sketch' })
      ]);
      setInitialStateLoaded(true);
      return;
    }

    setTransform(state.transform ?? { scale: 1, x: 0, y: 0 });
    const restore = async () => {
      const restoredNodes = await Promise.all(
        state.nodes.map(async (node) => {
          if (!node.imageId) return node;
          const record = await getImageRecord(node.imageId);
          if (!record) return node;
          const imageUrl = URL.createObjectURL(record.blob);
          const thumbUrl = URL.createObjectURL(record.thumb);
          activeUrls.current.add(imageUrl);
          activeUrls.current.add(thumbUrl);
          return { ...node, imageUrl, thumbUrl };
        })
      );
      setNodes(restoredNodes);
      setInitialStateLoaded(true);
    };
    void restore();
  }, []);

  useEffect(() => {
    if (!initialStateLoaded) return;
    storeState(nodes, transform);
  }, [nodes, transform, initialStateLoaded, storeState]);

  useEffect(() => () => {
    activeUrls.current.forEach((url) => URL.revokeObjectURL(url));
  }, []);

  const handleAddNode = (type: NodeType) => {
    setNodes((prev) => [...prev, createNode(type, { x: 260 + prev.length * 40, y: 200 })]);
  };

  const screenToCanvas = (clientX: number, clientY: number) => {
    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return { x: 0, y: 0 };
    const localX = clientX - rect.left;
    const localY = clientY - rect.top;
    return {
      x: (localX - transform.x) / transform.scale,
      y: (localY - transform.y) / transform.scale
    };
  };

  const handlePointerDown = (event: React.PointerEvent<HTMLDivElement>, node: CanvasNode) => {
    if ((event.target as HTMLElement).dataset.resize === 'true') return;
    event.stopPropagation();
    const point = screenToCanvas(event.clientX, event.clientY);
    setDragState({ id: node.id, offsetX: point.x - node.x, offsetY: point.y - node.y });
  };

  const handleResizeDown = (event: React.PointerEvent<HTMLDivElement>, node: CanvasNode) => {
    event.stopPropagation();
    const point = screenToCanvas(event.clientX, event.clientY);
    setResizeState({
      id: node.id,
      startX: point.x,
      startY: point.y,
      startWidth: node.width,
      startHeight: node.height
    });
  };

  useEffect(() => {
    const handleMove = (event: PointerEvent) => {
      if (!dragState && !resizeState) return;
      const point = screenToCanvas(event.clientX, event.clientY);
      if (dragState) {
        setNodes((prev) =>
          prev.map((node) =>
            node.id === dragState.id
              ? {
                  ...node,
                  x: point.x - dragState.offsetX,
                  y: point.y - dragState.offsetY
                }
              : node
          )
        );
      }
      if (resizeState) {
        const nextWidth = Math.max(MIN_NODE_SIZE.width, resizeState.startWidth + point.x - resizeState.startX);
        const nextHeight = Math.max(
          MIN_NODE_SIZE.height,
          resizeState.startHeight + point.y - resizeState.startY
        );
        setNodes((prev) =>
          prev.map((node) =>
            node.id === resizeState.id
              ? {
                  ...node,
                  width: nextWidth,
                  height: nextHeight
                }
              : node
          )
        );
      }
    };
    const handleUp = () => {
      setDragState(null);
      setResizeState(null);
    };
    window.addEventListener('pointermove', handleMove);
    window.addEventListener('pointerup', handleUp);
    return () => {
      window.removeEventListener('pointermove', handleMove);
      window.removeEventListener('pointerup', handleUp);
    };
  }, [dragState, resizeState, transform]);

  const handleUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files ?? []);
    if (!files.length) return;
    const createdNodes: CanvasNode[] = [];

    for (const file of files) {
      const [resized, thumb] = await Promise.all([resizeImage(file, 1600), resizeImage(file, 400)]);
      const id = createId();
      await saveImageRecord({
        id,
        blob: resized.blob,
        thumb: thumb.blob,
        width: resized.width,
        height: resized.height,
        thumbWidth: thumb.width,
        thumbHeight: thumb.height,
        createdAt: Date.now()
      });
      const imageUrl = URL.createObjectURL(resized.blob);
      const thumbUrl = URL.createObjectURL(thumb.blob);
      activeUrls.current.add(imageUrl);
      activeUrls.current.add(thumbUrl);
      createdNodes.push(
        createNode('file', {
          title: file.name,
          imageId: id,
          imageUrl,
          thumbUrl,
          width: Math.min(DEFAULT_NODE_SIZE.width, resized.width),
          height: Math.min(DEFAULT_NODE_SIZE.height, resized.height)
        })
      );
    }

    setNodes((prev) => [...prev, ...createdNodes]);
    event.target.value = '';
  };

  const initialScale = useMemo(() => transform.scale, [transform.scale]);
  const initialPositionX = useMemo(() => transform.x, [transform.x]);
  const initialPositionY = useMemo(() => transform.y, [transform.y]);

  return (
    <main>
      <div className="toolbar">
        <h1>Infinite Canvas OS</h1>
        <button onClick={() => handleAddNode('task')}>Add Task</button>
        <button onClick={() => handleAddNode('file')}>Add File</button>
        <button onClick={() => handleAddNode('prototype')}>Add Prototype</button>
        <label>
          Upload image
          <input type="file" accept="image/*" multiple onChange={handleUpload} />
        </label>
        <span className="meta">Wheel to zoom, drag to pan. Nodes are draggable + resizable.</span>
      </div>
      <div className="canvas-shell" ref={containerRef}>
        <TransformWrapper
          initialScale={initialScale}
          initialPositionX={initialPositionX}
          initialPositionY={initialPositionY}
          minScale={0.2}
          maxScale={3}
          panning={{ disabled: isInteracting }}
          wheel={{ step: 0.08 }}
          onTransformed={(ref) => {
            setTransform({ scale: ref.state.scale, x: ref.state.positionX, y: ref.state.positionY });
          }}
        >
          <TransformComponent wrapperStyle={{ width: '100%', height: '100%' }}>
            <div className="canvas-surface">
              {nodes.map((node) => (
                <div
                  key={node.id}
                  className={`node ${dragState?.id === node.id ? 'dragging' : ''}`}
                  style={{
                    left: node.x,
                    top: node.y,
                    width: node.width,
                    height: node.height
                  }}
                  onPointerDown={(event) => handlePointerDown(event, node)}
                >
                  <header>{node.type}</header>
                  <strong>{node.title}</strong>
                  {node.body && <p>{node.body}</p>}
                  {node.thumbUrl && (
                    <img className="file-preview" src={node.thumbUrl} alt={node.title} />
                  )}
                  <div
                    className="resize-handle"
                    data-resize="true"
                    onPointerDown={(event) => handleResizeDown(event, node)}
                  />
                </div>
              ))}
            </div>
          </TransformComponent>
        </TransformWrapper>
      </div>
      <footer className="footer">Local-first MVP. Canvas + images persist in localStorage + IndexedDB.</footer>
    </main>
  );
}

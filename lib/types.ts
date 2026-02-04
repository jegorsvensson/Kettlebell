export type NodeType = 'task' | 'file' | 'prototype';

export interface CanvasNode {
  id: string;
  type: NodeType;
  x: number;
  y: number;
  width: number;
  height: number;
  title: string;
  body?: string;
  imageId?: string;
  imageUrl?: string;
  thumbUrl?: string;
}

export interface CanvasState {
  nodes: CanvasNode[];
  transform: {
    scale: number;
    x: number;
    y: number;
  };
}

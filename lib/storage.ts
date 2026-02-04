import { CanvasState } from './types';

const DB_NAME = 'infinite-canvas-db';
const DB_VERSION = 1;
const STORE_NAME = 'images';
const STATE_KEY = 'infinite-canvas-state';

export interface StoredImageRecord {
  id: string;
  blob: Blob;
  thumb: Blob;
  width: number;
  height: number;
  thumbWidth: number;
  thumbHeight: number;
  createdAt: number;
}

const openDb = (): Promise<IDBDatabase> =>
  new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME, { keyPath: 'id' });
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });

export const saveImageRecord = async (record: StoredImageRecord) => {
  const db = await openDb();
  await new Promise<void>((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readwrite');
    tx.objectStore(STORE_NAME).put(record);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
  db.close();
};

export const getImageRecord = async (
  id: string
): Promise<StoredImageRecord | undefined> => {
  const db = await openDb();
  const record = await new Promise<StoredImageRecord | undefined>((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readonly');
    const request = tx.objectStore(STORE_NAME).get(id);
    request.onsuccess = () => resolve(request.result as StoredImageRecord | undefined);
    request.onerror = () => reject(request.error);
  });
  db.close();
  return record;
};

export const saveCanvasState = (state: CanvasState) => {
  localStorage.setItem(STATE_KEY, JSON.stringify(state));
};

export const loadCanvasState = (): CanvasState | null => {
  const raw = localStorage.getItem(STATE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as CanvasState;
  } catch {
    return null;
  }
};

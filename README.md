# Infinite Canvas OS (MVP)

Local-first MVP inspired by Trello, Milanote, and Craft.io. Built with Next.js + React + TypeScript.

## Features

- Infinite canvas with pan + zoom.
- Node types: Task, File, Prototype.
- Drag + resize nodes.
- Image upload: client-side resize (max 1600px) and thumbnail (max 400px) stored in IndexedDB.
- Local persistence: canvas state in localStorage, images in IndexedDB.

## Getting started

```bash
npm install
npm run dev
```

Open <http://localhost:3000>.

## Notes

- Use your mouse wheel/trackpad to zoom, drag the background to pan.
- Uploaded images are stored locally in your browser only.

# Kettlebell – Infinite canvas för filer, tasks och prototyper

Det här är starten på ett konkret bygge av en kombinerad Trello/Milanote/Craft.io‑upplevelse: **en snabb, visuellt ren och oändlig canvas** där teams kan strukturera arbete, samla artefakter och klicka runt i prototyper – utan friktion.

## Varför vi bygger detta
Vi vill minska glappet mellan **planering (tasks)**, **inspiration (filer)** och **utförande (prototyper)**. En canvas gör att allt kan ligga visuellt intill varandra och snabbt flyttas om i takt med att arbetet utvecklas.

## Vad som byggs nu (MVP-start)
Fokus är att få en **användbar kärna** med:
1. **Infinite canvas** med snabb pan/zoom.
2. **Task cards** som kan placeras fritt på ytan.
3. **File cards** (bilder + pdf) med direkt preview.
4. **Direkt resize på upload** (dra hörn, presets).
5. **Frames/sections** för att skapa struktur.

## Interaktionsprinciper
- **Direkt manipulation:** allt är dragbart, resizebart och synligt.
- **Snabbhet först:** inga tunga paneler i MVP, endast det viktigaste.
- **Visuell struktur:** frames + färgkodning skapar ordning.

## Tekniskt upplägg (MVP)
- **Frontend:** React + Canvas‑lager (Konva/Fabric) eller DOM‑baserad canvas med CSS transforms.
- **Backend:** Supabase eller Firebase (auth + data + realtime).
- **Filer:** Cloudinary/S3 med automatiskt resize + thumbnails.
- **Realtid (senare):** WebSockets eller Supabase Realtime.

## Nästa leverabler (konkreta steg)
1. **Canvas-shell** med pan/zoom och grid.
2. **Card‑system** (task + file) som kan flyttas.
3. **Upload & resize‑flow** för bilder.
4. **Persistens** (spara position/size).
5. **Frame‑block** för gruppering och export.

Se vidare detaljer i:
- `docs/roadmap.md`
- `docs/user-stories.md`
- `docs/interaction-spec.md`


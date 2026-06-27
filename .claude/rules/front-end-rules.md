# Frontend Rules

## The UI is finished. Do not touch static/index.html.

The design, layout, and all JavaScript in static/index.html are complete.
Your job is exclusively to implement backend endpoints that match what the frontend already expects.

## How to work with the frontend

Before implementing any endpoint:
1. Grep static/index.html for the endpoint path (e.g. `/api/filing/reconcile`)
2. Read the fetch() call to find: HTTP method, request body shape, response fields the UI reads
3. Implement the Flask route to return exactly that shape — do not rename fields

## What the frontend uses
- Fonts: Google Fonts (Archivo, Inter, IBM Plex Mono, Source Serif 4)
- Theme: CSS custom properties with light/dark mode via data-theme attribute
- No external JS frameworks — plain fetch() for all API calls

## Forbidden
- Do not modify static/index.html for any reason
- Do not change response field names — the frontend is hardcoded to specific keys
- Do not add CORS configuration in JS — it is handled by Flask
- Do not add endpoints the frontend does not call

# RAG widget

Embeddable chat widget for the RAG service — a vanilla Web Component (`<rag-chat>`), isolated
by Shadow DOM, zero runtime dependencies, bundled by esbuild.

## Usage

```html
<rag-chat
  api-url="https://api.example.com"
  api-key="your-viewer-key"
  primary-color="#6C5CE7"
  position="bottom-right"
  lang="fr"
  top-k="4"
></rag-chat>
<script src="https://cdn.example.com/rag.min.js"></script>
```

### Attributes

| Attribute | Default | Description |
|---|---|---|
| `api-url` | `http://localhost:8000` | Base URL of the RAG API |
| `api-key` | — | Value sent as the `X-API-Key` header |
| `primary-color` | `#6C5CE7` | Accent color (`--primary`) |
| `position` | `bottom-right` | `bottom-right` or `bottom-left` |
| `lang` | `fr` | UI language (`fr`/`en`); RTL auto for `ar`/`he`/`fa`/`ur` |
| `top-k` | `4` | Number of reranked chunks requested |

The widget calls `POST {api-url}/rag/query` with `{ "question": "...", "top_k": N }` and renders
the `answer` plus collapsible `sources`. It surfaces `401`/`422` (auth), `429` (rate limit) and
network errors as inline messages.

## Security

`api-key` ships to the browser. Use a **read-only `viewer`** key — `/rag/query` only requires the
`read` permission. Never embed an `operator` (write) key client-side.

## Build

```bash
npm install
npm run build   # -> dist/rag.min.js (minified IIFE, no runtime deps)
npm run dev     # esbuild dev server; open the demo at the served index.html
```

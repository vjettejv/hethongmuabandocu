# Marketplace frontend

React 18 / Vite browser client for the canonical FastAPI/Django marketplace. Node/npm is build and test tooling. The production-style local container builds static assets and serves them through Nginx, which proxies HTTP and `/socket.io/` to the gateway.

```bash
npm ci
node tests/frontend-contracts.test.js
npm run build
npm run dev
```

Use the existing Node 18 toolchain. Start the backend with root Compose before host development. See the [root README](../README.md) for environment setup, architecture, API contracts and verification.

Private `.env*` files are excluded from the Docker context; `.env.example` is the documented example. Frontend build variables are public compiled configuration and must never contain backend signing keys, database credentials, or SMTP secrets.

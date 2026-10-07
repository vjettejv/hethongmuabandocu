# Marketplace frontend

React 18 / Vite browser client for the canonical FastAPI/Django marketplace. Node/npm is build and test tooling. The production-style local container builds static assets and serves them through Nginx, which proxies HTTP and `/socket.io/` to the gateway.

```bash
npm ci
node tests/frontend-contracts.test.js
npm run build
npm run dev
```

Use the existing Node 18 toolchain. Start the backend with root Compose before host development. See [root README](../README.md), [development guide](../docs/development.md), and [API guide](../docs/api.md) for environment setup and contracts.

Private `.env*` files are excluded from the Docker context; `.env.example` is the documented example. Frontend build variables are public compiled configuration and must never contain backend signing keys, database credentials, or SMTP secrets.

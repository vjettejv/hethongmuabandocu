const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const cors = require('cors');

const app = express();

app.use(cors());

// Health check
app.get('/health', (req, res) => res.status(200).send('Gateway OK'));

// Proxy Rules
const routes = {
    '/auth': process.env.AUTH_SERVICE_URL || 'http://localhost:3001',
    '/users': process.env.USER_SERVICE_URL || 'http://localhost:3002',
    '/posts': process.env.POST_SERVICE_URL || 'http://localhost:3003',
    '/categories': process.env.CATEGORY_SERVICE_URL || 'http://localhost:3004',
    '/messages': process.env.MESSAGE_SERVICE_URL || 'http://localhost:3005',
    '/notifications': process.env.NOTIFICATION_SERVICE_URL || 'http://localhost:3006',
    '/reviews': process.env.REVIEW_SERVICE_URL || 'http://localhost:3007',
    '/search': process.env.SEARCH_SERVICE_URL || 'http://localhost:3008',
    '/favorites': process.env.FAVORITE_SERVICE_URL || 'http://localhost:3009'
};

// Setup Proxies
for (const [path, target] of Object.entries(routes)) {
    app.use(path, createProxyMiddleware({
        target,
        changeOrigin: true,
        pathRewrite: { [`^${path}`]: '' }, // Strip the /service-name prefix
        onProxyReq: (proxyReq, req, res) => {
            // Forward client IP and other necessary headers
            proxyReq.setHeader('x-forwarded-for', req.ip || req.connection.remoteAddress);
        },
        onError: (err, req, res) => {
            console.error(`Error proxying to ${target}:`, err.message);
            if (!res.headersSent) {
               res.status(502).json({ error: 'Service Unavailable' });
            }
        }
    }));
}

// Special handling for uploads (Don't rewrite path)
app.use('/uploads', createProxyMiddleware({
    target: process.env.POST_SERVICE_URL || 'http://localhost:3003',
    changeOrigin: true,
    pathRewrite: (path, req) => req.originalUrl
}));



// Special handling for admin routes (Don't rewrite path)
app.use('/admin/posts', createProxyMiddleware({
    target: process.env.POST_SERVICE_URL || 'http://localhost:3003',
    changeOrigin: true,
    pathRewrite: (path, req) => {
        // Express strips '/admin/posts', so path is '/25'. We return the originalUrl.
        return req.originalUrl;
    }
}));

app.use('/admin/categories', createProxyMiddleware({
    target: process.env.CATEGORY_SERVICE_URL || 'http://localhost:3004',
    changeOrigin: true,
    pathRewrite: (path, req) => req.originalUrl
}));

// Special handling for Socket.io (WebSocket Proxy)
app.use('/socket.io', createProxyMiddleware({
    target: process.env.MESSAGE_SERVICE_URL || 'http://localhost:3005',
    ws: true,
    changeOrigin: true,
    pathRewrite: (path, req) => req.originalUrl
}));

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`API Gateway running on port ${PORT}`));

'use strict';
// Test transport sink only: proves the original Post create fetches Django Category.
const http = require('http');
const syncs = new Map();
http.createServer((req, res) => {
  const reply = (status, body) => {
    res.writeHead(status, {'Content-Type': 'application/json'});
    res.end(JSON.stringify(body));
  };
  if (req.method === 'GET' && req.url.startsWith('/sync/')) {
    const record = syncs.get(Number(req.url.slice(6)));
    reply(record ? 200 : 404, record || {});
    return;
  }
  if (req.method === 'POST' && req.url === '/sync') {
    const chunks = [];
    req.on('data', chunk => chunks.push(chunk));
    req.on('end', () => {
      try {
        const value = JSON.parse(Buffer.concat(chunks).toString());
        syncs.set(value.postId, {postId:value.postId, categoryId:value.categoryId,
                                categoryName:value.categoryName});
        reply(200, {});
      } catch (_) { reply(400, {}); }
    });
    return;
  }
  reply(404, {});
}).listen(3008, '0.0.0.0');

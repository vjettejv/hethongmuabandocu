'use strict';
// Isolated wire fixture; no marketplace write, upload or business implementation.
const http = require('http'), crypto = require('crypto');
http.createServer((req, res) => {
  if (req.url === '/uploads/fixture.bin') {
    const data = Buffer.from([0, 255, 1, 2, 3, 13, 10]);
    res.writeHead(200, {
      'Content-Type': 'application/octet-stream', 'Content-Length': data.length,
      'Cache-Control': 'public, max-age=60', 'ETag': '"fixture"',
      'Set-Cookie': ['a=1', 'b=2']
    });
    res.end(data);
    return;
  }
  const hash = crypto.createHash('sha256');
  let size = 0, chunks = 0;
  req.on('data', chunk => { hash.update(chunk); size += chunk.length; chunks++; });
  req.on('end', () => {
    res.writeHead(201, {'Content-Type':'application/json'});
    res.end(JSON.stringify({method:req.method, path:req.url, size, chunks,
      sha256:hash.digest('hex'), contentType:req.headers['content-type'],
      requestId:req.headers['x-request-id'], authorizationPresent:!!req.headers.authorization}));
  });
}).listen(3003, '0.0.0.0');

'use strict';
// Isolated HTTP capture/failure transport. Forward to unchanged real Node handlers.
const http = require('http');
let events = [], modes = {};
let pending = 0;
function json(res, status, body) {
  res.writeHead(status, {'Content-Type':'application/json'});
  res.end(JSON.stringify(body));
}
http.createServer(async (req, res) => {
  const path = new URL(req.url, 'http://fixture').pathname;
  const buffers=[];
  for await (const chunk of req) buffers.push(chunk);
  const body=Buffer.concat(buffers).toString();
  if (path==='/__events') return json(res,200,{events,pending});
  if (path==='/__control') {
    if (pending) return json(res,409,{error:'pending'});
    events=[]; modes=body?JSON.parse(body):{}; return json(res,200,{ok:true});
  }
  const key=path==='/category'?'CATEGORY':path==='/sync'?'SEARCH':
            path==='/notifications'?'MESSAGE':null;
  if (!key) return json(res,404,{});
  events.push({dependency:key,method:req.method,path,
    requestId:req.headers['x-request-id']||null,payload:body?JSON.parse(body):null});
  if (modes[key]==='failure') return json(res,503,{error:'synthetic outage'});
  if (modes[key]==='invalid') {res.writeHead(200);return res.end('invalid json');}
  pending++;
  try {
    const target=key==='CATEGORY'?process.env.CATEGORY_SERVICE_URL:
      process.env[key+'_SERVICE_URL']+path;
    const upstream=await fetch(target,{method:req.method,
      headers:{'Content-Type':'application/json','X-Request-ID':req.headers['x-request-id']||'fixture'},
      ...(body?{body}:{})});
    res.writeHead(upstream.status,{'Content-Type':'application/json'});
    res.end(await upstream.text());
  } catch (_) {json(res,502,{error:'fixture upstream unavailable'});}
  finally {pending--;}
}).listen(3010,'0.0.0.0');

'use strict';
// Test-only failure/capture transport forwarding to real Python dependencies.
const http=require('http');let events=[],modes={},pending=0;
const json=(res,status,body)=>{res.writeHead(status,{'Content-Type':'application/json'});res.end(JSON.stringify(body));};
http.createServer(async(req,res)=>{
  const path=new URL(req.url,'http://fixture').pathname;const chunks=[];
  for await(const part of req)chunks.push(part);const body=Buffer.concat(chunks).toString();
  if(path==='/__events')return json(res,200,{events,pending});
  if(path==='/__control'){if(pending)return json(res,409,{});events=[];modes=body?JSON.parse(body):{};return json(res,200,{ok:true});}
  const key=path.startsWith('/users/')?'USER':path.startsWith('/auth/')?'AUTH':path==='/email'?'NOTIFICATION':path==='/sync'?'SEARCH':null;
  if(!key)return json(res,404,{});
  events.push({dependency:key,path,method:req.method,requestId:req.headers['x-request-id']||null,payload:body?JSON.parse(body):null});
  if(modes[key]==='failure')return json(res,503,{error:'synthetic outage'});
  if(modes[key]==='invalid'){res.writeHead(200);return res.end('invalid');}
  if(modes[key]==='network'){req.socket.destroy();return;}
  pending++;
  try{
    if(modes[key]==='delay')await new Promise(resolve=>setTimeout(resolve,1200));
    let suffix=path.replace(/^\/(users|auth)/,'');
    const response=await fetch(process.env[key+'_SERVICE_URL']+suffix,{method:req.method,
      headers:{'Content-Type':'application/json','X-Request-ID':req.headers['x-request-id']||'phase6-fixture'},...(body?{body}:{})});
    res.writeHead(response.status,{'Content-Type':'application/json'});res.end(await response.text());
  }catch(_){json(res,502,{error:'fixture unavailable'});}finally{pending--;}
}).listen(3011,'0.0.0.0');

'use strict';
// Uses the unchanged frontend's installed Socket.IO 4.x client.
const {io}=require('../../do-cu-frontend/node_modules/socket.io-client');
const readline=require('readline');const sockets=new Map(),events=[];
function wait(check,timeout=10000){return new Promise((resolve,reject)=>{const start=Date.now();const tick=()=>{const value=check();if(value)return resolve(value);if(Date.now()-start>timeout)return reject(Error('socket fixture timeout'));setTimeout(tick,20);};tick();});}
async function command(input){
  if(input.command==='connect'){
    const socket=io(input.url,{autoConnect:false,reconnection:false,timeout:10000,transports:input.transports||['polling','websocket'],extraHeaders:{Origin:input.origin||'http://localhost'}});
    socket.on('receive_message',payload=>events.push({client:input.client,event:'receive_message',payload}));
    socket.on('receive_notification',payload=>events.push({client:input.client,event:'receive_notification',payload}));
    sockets.set(input.client,socket);
    await new Promise((resolve,reject)=>{socket.once('connect',resolve);socket.once('connect_error',()=>reject(Error('socket connect failed')));socket.connect();});
    if(input.upgrade)await wait(()=>socket.io.engine.transport.name==='websocket');
    socket.emit('join_user_room',input.userId);await new Promise(resolve=>setTimeout(resolve,150));
    return {transport:socket.io.engine.transport.name,connected:socket.connected};
  }
  if(input.command==='events')return {events:events.filter(item=>!input.client||item.client===input.client)};
  if(input.command==='wait')return await wait(()=>events.find(item=>item.client===input.client&&item.event===input.event&&(!input.id||item.payload.id===input.id)),input.timeout||10000);
  if(input.command==='clear'){events.length=0;return {ok:true};}
  if(input.command==='disconnect'){sockets.get(input.client)?.disconnect();sockets.delete(input.client);return {ok:true};}
  if(input.command==='close'){for(const socket of sockets.values())socket.disconnect();sockets.clear();return {ok:true};}
  throw Error('unknown socket command');
}
const rl=readline.createInterface({input:process.stdin});let pending=Promise.resolve();
rl.on('line',line=>{pending=pending.then(async()=>{try{const result=await command(JSON.parse(line));process.stdout.write(JSON.stringify({ok:true,result})+'\n');}catch(_){process.stdout.write(JSON.stringify({ok:false,error:'socket fixture operation failed'})+'\n');}});});
rl.on('close',()=>{for(const socket of sockets.values())socket.disconnect();process.exit(0);});

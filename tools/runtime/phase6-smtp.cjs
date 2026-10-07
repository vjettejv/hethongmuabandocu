'use strict';
// Local-only SMTP sink. Authentication is synthetic; no external delivery.
const net=require('net'),http=require('http');let messages=[],reject=false;
const server=net.createServer(socket=>{
  let buffer='',data=false,lines=[],envelope={from:null,to:[]},auth=0;
  socket.write('220 phase6.local ESMTP\r\n');
  socket.on('data',part=>{buffer+=part.toString();let at;
    while((at=buffer.indexOf('\r\n'))>=0){const line=buffer.slice(0,at);buffer=buffer.slice(at+2);
      if(data){if(line==='.'){
        data=false;if(reject)socket.write('554 synthetic delivery rejected\r\n');
        else{messages.push({...envelope,body:lines.join('\r\n')});socket.write('250 phase6 accepted\r\n');}
        lines=[];envelope={from:null,to:[]};
      }else lines.push(line.startsWith('..')?line.slice(1):line);continue;}
      if(auth){auth--;socket.write(auth?'334 UGFzc3dvcmQ6\r\n':'235 authentication accepted\r\n');continue;}
      if(/^EHLO|^HELO/i.test(line))socket.write('250-phase6.local\r\n250-AUTH PLAIN LOGIN\r\n250 SIZE 52428800\r\n');
      else if(/^AUTH LOGIN/i.test(line)){auth=2;socket.write('334 VXNlcm5hbWU6\r\n');}
      else if(/^AUTH /i.test(line))socket.write('235 authentication accepted\r\n');
      else if(/^MAIL FROM:/i.test(line)){envelope.from=line.slice(10).trim();socket.write('250 sender accepted\r\n');}
      else if(/^RCPT TO:/i.test(line)){envelope.to.push(line.slice(8).trim());socket.write('250 recipient accepted\r\n');}
      else if(/^DATA$/i.test(line)){data=true;socket.write('354 End with dot\r\n');}
      else if(/^QUIT$/i.test(line)){socket.end('221 bye\r\n');}
      else socket.write('250 OK\r\n');
    }
  });socket.on('error',()=>{});
});server.listen(2525,'0.0.0.0');
http.createServer(async(req,res)=>{const parts=[];for await(const p of req)parts.push(p);
  if(req.url==='/__control'){const body=JSON.parse(Buffer.concat(parts).toString()||'{}');messages=[];reject=!!body.reject;}
  res.writeHead(200,{'Content-Type':'application/json'});res.end(JSON.stringify({messages}));
}).listen(3012,'0.0.0.0');

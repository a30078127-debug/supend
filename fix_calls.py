f = open('ui/gui.py', encoding='utf-8')
c = f.read()
f.close()

# Исправление 1: sendCallSignal через трекер вместо P2P
old1 = """function sendCallSignal(peerId, data){
  cmd({cmd:'send', peer_id:peerId, text:CALL_PREFIX+JSON.stringify(data)});
}"""
new1 = """function sendCallSignal(peerId, data){
  // Сигналинг через WebSocket (трекер опросит Python)
  cmd({cmd:'call_signal', to:peerId, data:data});
}"""

# Исправление 2: буферизация ICE + правильный slice
old2 = """async function handleCallSignal(peerId, data){
  if(data.type==='offer'){
    incomingOffer=data;incomingPeerId=peerId;
    const p=peers[peerId];
    showIncomingCall(p||{id:peerId});
  } else if(data.type==='answer'){
    if(!pc)return;
    await pc.setRemoteDescription(new RTCSessionDescription(data.sdp));
    document.getElementById('callStatus').textContent='Соединяем...';
  } else if(data.type==='ice'){
    if(pc&&data.candidate)try{await pc.addIceCandidate(new RTCIceCandidate(data.candidate));}catch(e){}
  } else if(data.type==='decline'){
    toast('📵','Звонок отклонён','');endCall();
  } else if(data.type==='end'){
    endCall();
  }
}"""
new2 = """let iceCandidatesBuffer = [];

async function handleCallSignal(peerId, data){
  if(data.type==='offer'){
    incomingOffer=data;incomingPeerId=peerId;
    iceCandidatesBuffer=[];
    const p=peers[peerId];
    showIncomingCall(p||{id:peerId});
  } else if(data.type==='answer'){
    if(!pc)return;
    await pc.setRemoteDescription(new RTCSessionDescription(data.sdp));
    document.getElementById('callStatus').textContent='Соединяем...';
    for(const c of iceCandidatesBuffer){
      try{await pc.addIceCandidate(new RTCIceCandidate(c));}catch(e){}
    }
    iceCandidatesBuffer=[];
  } else if(data.type==='ice'){
    if(pc&&data.candidate){
      if(pc.remoteDescription){
        try{await pc.addIceCandidate(new RTCIceCandidate(data.candidate));}catch(e){}
      } else {
        iceCandidatesBuffer.push(data.candidate);
      }
    }
  } else if(data.type==='decline'){
    toast('📵','Звонок отклонён','');endCall();
  } else if(data.type==='end'){
    endCall();
  }
}"""

# Исправление 3: в acceptCall тоже применяем буфер после setRemoteDescription
old3 = """    await pc.setRemoteDescription(new RTCSessionDescription(incomingOffer.sdp));
    const answer=await pc.createAnswer();
    await pc.setLocalDescription(answer);
    sendCallSignal(callPeerId,{type:'answer',sdp:answer});"""
new3 = """    await pc.setRemoteDescription(new RTCSessionDescription(incomingOffer.sdp));
    for(const c of iceCandidatesBuffer){
      try{await pc.addIceCandidate(new RTCIceCandidate(c));}catch(e){}
    }
    iceCandidatesBuffer=[];
    const answer=await pc.createAnswer();
    await pc.setLocalDescription(answer);
    sendCallSignal(callPeerId,{type:'answer',sdp:answer});"""

ok1 = old1 in c
ok2 = old2 in c
ok3 = old3 in c
print(f"Замена 1 (sendCallSignal): {'найдено' if ok1 else 'НЕ НАЙДЕНО'}")
print(f"Замена 2 (handleCallSignal): {'найдено' if ok2 else 'НЕ НАЙДЕНО'}")
print(f"Замена 3 (acceptCall buffer): {'найдено' if ok3 else 'НЕ НАЙДЕНО'}")

if ok1: c = c.replace(old1, new1)
if ok2: c = c.replace(old2, new2)
if ok3: c = c.replace(old3, new3)

# Исправление 4: в Python части добавить обработку call_signal команды
old4 = "        elif c == 'send':"
new4 = """        elif c == 'call_signal':
            to_id = data.get('to', '')
            sig_data = data.get('data', {})
            if self.tracker and to_id:
                import json as _cj
                try:
                    await self.tracker.send_signal(self.node.peer_id, to_id, _cj.dumps(sig_data))
                except Exception as _ce:
                    logger.warning("call_signal error: %s", _ce)

        elif c == 'send':"""

ok4 = old4 in c
print(f"Замена 4 (Python call_signal): {'найдено' if ok4 else 'НЕ НАЙДЕНО'}")
if ok4: c = c.replace(old4, new4)

# Исправление 5: в run() добавить start_signal_listener
old5 = "        if self.tracker:\n            try:\n                await self.tracker.start_relay_listener(self.node.peer_id, self._on_relay_message)"
new5 = """        if self.tracker:
            try:
                await self.tracker.start_relay_listener(self.node.peer_id, self._on_relay_message)
            except Exception as e:
                logger.warning(\"Relay start error: %s\", e)
            try:
                await self.tracker.start_signal_listener(self.node.peer_id, self._on_call_signal)
            except Exception as e:
                logger.warning(\"Signal start error: %s\", e)"""

ok5 = old5 in c
print(f"Замена 5 (start_signal_listener): {'найдено' if ok5 else 'НЕ НАЙДЕНО'}")
if ok5: c = c.replace(old5, new5)

# Исправление 6: добавить _on_call_signal метод рядом с _on_relay_message
old6 = "    async def _on_message(self, peer_id, msg):"
new6 = """    async def _on_call_signal(self, from_id, data_str):
        import json as _csj
        try:
            data = _csj.loads(data_str) if isinstance(data_str, str) else data_str
            await self._broadcast({'type': 'call_signal', 'from': from_id, 'data': data})
        except Exception as e:
            logger.warning("_on_call_signal error: %s", e)

    async def _on_message(self, peer_id, msg):"""

ok6 = old6 in c
print(f"Замена 6 (_on_call_signal): {'найдено' if ok6 else 'НЕ НАЙДЕНО'}")
if ok6: c = c.replace(old6, new6)

# Исправление 7: в JS обработать call_signal от сервера
old7 = "  else if(ev.type==='error')toast('⚠️','Ошибка',ev.message);"
new7 = """  else if(ev.type==='call_signal'){
    const from=ev.from, data=ev.data;
    if(data&&from) handleCallSignal(from, data);
  }
  else if(ev.type==='error')toast('⚠️','Ошибка',ev.message);"""

ok7 = old7 in c
print(f"Замена 7 (JS call_signal handler): {'найдено' if ok7 else 'НЕ НАЙДЕНО'}")
if ok7: c = c.replace(old7, new7)

f = open('ui/gui.py', 'w', encoding='utf-8')
f.write(c)
f.close()
print('\nГотово! Все замены применены.')

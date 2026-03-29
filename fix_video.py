with open('ui/gui.py', encoding='utf-8') as f:
    c = f.read()

results = []

# ── 1. Кнопка маркетплейса — переносим выше (над кошельком и FAB) ─────────────
old1 = '    <!-- Market button -->\n    <div style="position:absolute;right:76px;bottom:76px;z-index:51">\n      <button onclick="openMarket()" title="Маркетплейс" style="width:52px;height:52px;border-radius:50%;background:linear-gradient(135deg,#f6d365,#fda085);border:none;display:flex;align-items:center;justify-content:center;cursor:pointer;box-shadow:0 4px 16px rgba(246,211,101,.4);font-size:22px;transition:transform .2s" onmouseover="this.style.transform=\'scale(1.08)\'" onmouseout="this.style.transform=\'scale(1)\'">🏪</button>\n    </div>'
new1 = '    <!-- Market button -->\n    <div style="position:absolute;right:16px;bottom:144px;z-index:51">\n      <button onclick="openMarket()" title="Маркетплейс" style="width:52px;height:52px;border-radius:50%;background:linear-gradient(135deg,#f6d365,#fda085);border:none;display:flex;align-items:center;justify-content:center;cursor:pointer;box-shadow:0 4px 16px rgba(246,211,101,.4);font-size:22px;transition:transform .2s" onmouseover="this.style.transform=\'scale(1.08)\'" onmouseout="this.style.transform=\'scale(1)\'">🏪</button>\n    </div>'
results.append(('market button above wallet', old1 in c))
if old1 in c: c = c.replace(old1, new1)

# ── 2. Добавить кнопку видеозвонка рядом с аудио ─────────────────────────────
old2 = '      <button class="call-ico-btn" id="callBtn" onclick="startCall()" title="Позвонить">'
new2 = '      <button class="call-ico-btn" id="videoCallBtn" onclick="startVideoCall()" title="Видеозвонок"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2" ry="2"/></svg></button>\n      <button class="call-ico-btn" id="callBtn" onclick="startCall()" title="Позвонить">'
results.append(('video call button', old2 in c))
if old2 in c: c = c.replace(old2, new2)

# ── 3. Добавить кнопку камеры и видео элементы в оверлей звонка ──────────────
old3 = '  <div style="display:flex;gap:16px;margin-top:10px">\n    <button id="callMicBtn" onclick="toggleCallMic()" title="Микрофон" style="width:56px;height:56px;border-radius:50%;background:#1ABC9C;border:none;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all .2s;box-shadow:0 4px 16px rgba(26,188,156,.4)"><svg id="micIcon" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="2" width="6" height="12" rx="3"/><path d="M5 10a7 7 0 0 0 14 0"/><line x1="12" y1="19" x2="12" y2="22"/><line x1="8" y1="22" x2="16" y2="22"/></svg></button>\n    <button onclick="endCall()" title="Завершить" style="width:56px;height:56px;border-radius:50%;background:#e53935;border:none;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all .2s;box-shadow:0 4px 16px rgba(229,57,53,.4)"><svg width="22" height="22" viewBox="0 0 24 24" fill="white"><path d="M10.68 13.31a16 16 0 0 0 3.41 2.6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 2 2 0 0 1-.45-2.11 12.84 12.84 0 0 0 .7-2.81 2 2 0 0 1-2-2v-3a2 2 0 0 1 1.72-2 12.84 12.84 0 0 0 .7-2.81 2 2 0 0 1 .45-2.11L3.07 2.07A19.79 19.79 0 0 0 0 10.7 2 2 0 0 0 2 12.88h3a2 2 0 0 0 1.72-2z"/></svg></button>\n  </div>\n  <audio id="remoteAudio" autoplay></audio>'
new3 = '''  <!-- Video containers -->
  <div id="videoContainer" style="display:none;width:100%;max-width:600px;position:relative;margin-bottom:12px">
    <video id="remoteVideo" autoplay playsinline style="width:100%;border-radius:16px;background:#000;max-height:300px;object-fit:cover"></video>
    <video id="localVideo" autoplay playsinline muted style="position:absolute;bottom:10px;right:10px;width:100px;border-radius:10px;background:#111;object-fit:cover;border:2px solid rgba(255,255,255,.3)"></video>
  </div>
  <div style="display:flex;gap:16px;margin-top:10px">
    <button id="callMicBtn" onclick="toggleCallMic()" title="Микрофон" style="width:56px;height:56px;border-radius:50%;background:#1ABC9C;border:none;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all .2s;box-shadow:0 4px 16px rgba(26,188,156,.4)"><svg id="micIcon" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="2" width="6" height="12" rx="3"/><path d="M5 10a7 7 0 0 0 14 0"/><line x1="12" y1="19" x2="12" y2="22"/><line x1="8" y1="22" x2="16" y2="22"/></svg></button>
    <button id="callCamBtn" onclick="toggleCallCam()" title="Камера" style="width:56px;height:56px;border-radius:50%;background:#1ABC9C;border:none;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all .2s;box-shadow:0 4px 16px rgba(26,188,156,.4)"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2"/></svg></button>
    <button onclick="endCall()" title="Завершить" style="width:56px;height:56px;border-radius:50%;background:#e53935;border:none;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all .2s;box-shadow:0 4px 16px rgba(229,57,53,.4)"><svg width="22" height="22" viewBox="0 0 24 24" fill="white"><path d="M10.68 13.31a16 16 0 0 0 3.41 2.6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 2 2 0 0 1-.45-2.11 12.84 12.84 0 0 0 .7-2.81 2 2 0 0 1-2-2v-3a2 2 0 0 1 1.72-2 12.84 12.84 0 0 0 .7-2.81 2 2 0 0 1 .45-2.11L3.07 2.07A19.79 19.79 0 0 0 0 10.7 2 2 0 0 0 2 12.88h3a2 2 0 0 0 1.72-2z"/></svg></button>
  </div>
  <audio id="remoteAudio" autoplay></audio>'''
results.append(('camera button + video elements', old3 in c))
if old3 in c: c = c.replace(old3, new3)

# ── 4. Добавить переменную isVideCall и функцию startVideoCall ────────────────
old4 = "async function startCall(){"
new4 = """let isVideoCall = false;
let isCamMuted = false;

async function startVideoCall(){
  isVideoCall = true;
  if(!active||activeType!=='peer')return;
  const p=peers[active];
  if(!p||!p.online){toast('⚠️','Пользователь не в сети','');return;}
  callPeerId=active;
  showCallOverlay(p, 'outgoing');
  document.getElementById('videoContainer').style.display='block';
  try{
    localStream=await navigator.mediaDevices.getUserMedia({audio:true,video:true});
    document.getElementById('localVideo').srcObject=localStream;
    pc=new RTCPeerConnection(RTC_CONFIG);
    localStream.getTracks().forEach(t=>pc.addTrack(t,localStream));
    pc.ontrack=e=>{
      const rv=document.getElementById('remoteVideo');
      const ra=document.getElementById('remoteAudio');
      if(e.streams&&e.streams[0]){
        if(e.track.kind==='video'){rv.srcObject=e.streams[0];}
        else{ra.srcObject=e.streams[0];}
      }else{
        if(e.track.kind==='video'){if(!rv.srcObject)rv.srcObject=new MediaStream();rv.srcObject.addTrack(e.track);}
        else{if(!ra.srcObject)ra.srcObject=new MediaStream();ra.srcObject.addTrack(e.track);}
      }
      rv.play().catch(()=>{});ra.play().catch(()=>{});
    };
    pc.onicecandidate=e=>{if(e.candidate)sendCallSignal(callPeerId,{type:'ice',candidate:e.candidate});};
    pc.onconnectionstatechange=()=>{
      if(pc.connectionState==='connected')startCallTimer();
      if(pc.connectionState==='disconnected'||pc.connectionState==='failed')endCall();
    };
    const offer=await pc.createOffer();
    await pc.setLocalDescription(offer);
    sendCallSignal(callPeerId,{type:'offer',sdp:offer,video:true});
    document.getElementById('callStatus').textContent='Ждём ответа...';
  }catch(err){
    toast('⚠️','Нет доступа к камере','');
    endCall();
  }
}

async function startCall(){"""
results.append(('startVideoCall function', old4 in c))
if old4 in c: c = c.replace(old4, new4)

# ── 5. В handleCallSignal показываем видео если offer содержит video:true ─────
old5 = "  if(data.type==='offer'){\n    incomingOffer=data;incomingPeerId=peerId;\n    iceCandidatesBuffer=[];\n    const p=peers[peerId];\n    showIncomingCall(p||{id:peerId});"
new5 = "  if(data.type==='offer'){\n    incomingOffer=data;incomingPeerId=peerId;\n    isVideoCall=!!data.video;\n    iceCandidatesBuffer=[];\n    const p=peers[peerId];\n    showIncomingCall(p||{id:peerId});\n    if(isVideoCall)document.getElementById('videoContainer').style.display='block';"
results.append(('handle video offer', old5 in c))
if old5 in c: c = c.replace(old5, new5)

# ── 6. В acceptCall добавить видео поток если видеозвонок ─────────────────────
old6 = "    localStream=await navigator.mediaDevices.getUserMedia({audio:true});\n    pc=new RTCPeerConnection(RTC_CONFIG);\n    localStream.getTracks().forEach(t=>pc.addTrack(t,localStream));\n    pc.ontrack=e=>{const a=document.getElementById('remoteAudio');if(e.streams&&e.streams[0]){a.srcObject=e.streams[0];}else{if(!a.srcObject){a.srcObject=new MediaStream();}a.srcObject.addTrack(e.track);}a.play().catch(()=>{});};"
new6 = """    localStream=await navigator.mediaDevices.getUserMedia(isVideoCall?{audio:true,video:true}:{audio:true});
    if(isVideoCall){document.getElementById('localVideo').srcObject=localStream;}
    pc=new RTCPeerConnection(RTC_CONFIG);
    localStream.getTracks().forEach(t=>pc.addTrack(t,localStream));
    pc.ontrack=e=>{
      const rv=document.getElementById('remoteVideo');
      const ra=document.getElementById('remoteAudio');
      if(e.streams&&e.streams[0]){
        if(e.track.kind==='video'){rv.srcObject=e.streams[0];}
        else{ra.srcObject=e.streams[0];}
      }else{
        if(e.track.kind==='video'){if(!rv.srcObject)rv.srcObject=new MediaStream();rv.srcObject.addTrack(e.track);}
        else{if(!ra.srcObject)ra.srcObject=new MediaStream();ra.srcObject.addTrack(e.track);}
      }
      rv.play().catch(()=>{});ra.play().catch(()=>{});
    };"""
results.append(('acceptCall video stream', old6 in c))
if old6 in c: c = c.replace(old6, new6)

# ── 7. В endCall сбрасываем видео ────────────────────────────────────────────
old7 = "  document.getElementById('callOverlay').classList.remove('show');\n  document.getElementById('remoteAudio').srcObject=null;"
new7 = "  document.getElementById('callOverlay').classList.remove('show');\n  document.getElementById('remoteAudio').srcObject=null;\n  document.getElementById('remoteVideo').srcObject=null;\n  document.getElementById('localVideo').srcObject=null;\n  document.getElementById('videoContainer').style.display='none';\n  isVideoCall=false;isCamMuted=false;"
results.append(('endCall reset video', old7 in c))
if old7 in c: c = c.replace(old7, new7)

# ── 8. Функция toggleCallCam ─────────────────────────────────────────────────
old8 = "function startCallTimer(){"
new8 = """function toggleCallCam(){
  if(!localStream)return;
  isCamMuted=!isCamMuted;
  localStream.getVideoTracks().forEach(t=>t.enabled=!isCamMuted);
  const btn=document.getElementById('callCamBtn');
  if(isCamMuted){
    btn.style.background='#fff';
    btn.style.boxShadow='0 4px 16px rgba(0,0,0,.15)';
    btn.innerHTML='<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#9e9e9e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2"/><line x1="2" y1="2" x2="22" y2="22" stroke="#e53935" stroke-width="2.5"/></svg>';
  }else{
    btn.style.background='#1ABC9C';
    btn.style.boxShadow='0 4px 16px rgba(26,188,156,.4)';
    btn.innerHTML='<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2"/></svg>';
  }
}

function startCallTimer(){"""
results.append(('toggleCallCam function', old8 in c))
if old8 in c: c = c.replace(old8, new8)

with open('ui/gui.py', 'w', encoding='utf-8') as f:
    f.write(c)

print()
for name, found in results:
    print(f"  {'✓' if found else '✗ НЕ НАЙДЕНО'}  {name}")
print('\nГотово!')

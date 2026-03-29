with open('ui/gui.py', encoding='utf-8') as f:
    c = f.read()

results = []

# ── 1. Переместить pinnedBar под chat-head ────────────────────────────────────
old1 = '  <main class="chat">\n    <!-- Pinned message bar -->\n    <div class="pinned-bar" id="pinnedBar" onclick="scrollToPinned()">\n      <span class="pinned-bar-icon">📌</span>\n      <div><div style="font-size:10px;font-weight:700;color:#f0b90b;margin-bottom:1px">Закреплённое сообщение</div><div class="pinned-bar-text" id="pinnedBarText"></div></div>\n    </div>\n    <div class="chat-head" id="chatHead" style="display:none">'
new1 = '  <main class="chat">\n    <div class="chat-head" id="chatHead" style="display:none">'
results.append(('remove pinnedBar before chat-head', old1 in c))
if old1 in c: c = c.replace(old1, new1)

# ── 2. Добавить pinnedBar + mentionPopup после chat-head ─────────────────────
old2 = '    <!-- Search bar -->'
new2 = '''    <!-- Pinned message bar -->
    <div class="pinned-bar" id="pinnedBar" oncontextmenu="showPinnedCtx(event)">
      <div onclick="scrollToPinned()" style="display:flex;align-items:center;gap:10px;flex:1;cursor:pointer">
        <span class="pinned-bar-icon">📌</span>
        <div><div style="font-size:10px;font-weight:700;color:#f0b90b;margin-bottom:1px">Закреплённое сообщение</div><div class="pinned-bar-text" id="pinnedBarText"></div></div>
      </div>
    </div>
    <!-- Mention popup -->
    <div id="mentionPopup" style="display:none;position:absolute;bottom:80px;left:16px;right:16px;background:#fff;border:1px solid #e0e0e0;border-radius:12px;box-shadow:0 4px 20px rgba(0,0,0,.12);z-index:100;max-height:160px;overflow-y:auto"></div>
    <!-- Search bar -->'''
results.append(('add pinnedBar after chat-head + mentionPopup', old2 in c))
if old2 in c: c = c.replace(old2, new2)

# ── 3. Контекстное меню — добавить Открепить и убрать ограничение группы ─────
old3 = '  <div class="ctx-item" id="ctxPinBtn" onclick="pinMsg()">📌 Закрепить</div>'
new3 = '  <div class="ctx-item" id="ctxPinBtn" onclick="pinMsg()">📌 Закрепить</div>\n  <div class="ctx-item" id="ctxUnpinBtn" onclick="unpinMsg()" style="display:none">📌 Открепить</div>'
results.append(('add unpin button to context menu', old3 in c))
if old3 in c: c = c.replace(old3, new3)

# ── 4. showMsgCtx — показывать pin для всех чатов, показывать unpin если закреплено ──
old4 = '  document.getElementById(\'ctxEditBtn\').style.display=isOwn?\'block\':\'none\';\n  document.getElementById(\'ctxPinBtn\').style.display=activeType===\'group\'?\'block\':\'none\';'
new4 = """  document.getElementById('ctxEditBtn').style.display=isOwn?'block':'none';
  document.getElementById('ctxPinBtn').style.display='block';
  const pinnedId=activeType==='group'?groups[active]?.pinnedMsgId:peers[active]?.pinnedMsgId;
  const isPin=pinnedId==msgId;
  document.getElementById('ctxPinBtn').style.display=isPin?'none':'block';
  document.getElementById('ctxUnpinBtn').style.display=isPin?'block':'none';"""
results.append(('showMsgCtx pin/unpin visibility', old4 in c))
if old4 in c: c = c.replace(old4, new4)

# ── 5. pinMsg — работает и в переписке ───────────────────────────────────────
old5 = "function pinMsg(){\n  hideMsgCtx();\n  if(!ctxMsgId||activeType!=='group')return;\n  const g=groups[active];if(!g)return;\n  const msg=g.messages.find(m=>m.id==ctxMsgId);if(!msg)return;\n  g.pinnedMsgId=ctxMsgId;g.pinnedMsgText=msg.text||'[медиа]';\n  updatePinnedBar();\n  const payload=JSON.stringify({type:'pin',msgId:ctxMsgId,text:msg.text||'[медиа]'});\n  Object.keys(g.members).filter(pid=>pid!==myId&&peers[pid]?.online).forEach(pid=>cmd({cmd:'send',peer_id:pid,text:'__MSGACT__'+payload}));\n  toast('📌','Сообщение закреплено','');\n}"
new5 = """function pinMsg(){
  hideMsgCtx();
  if(!ctxMsgId||!active)return;
  const store=activeType==='group'?groups[active]:peers[active];if(!store)return;
  const msg=store.messages.find(m=>m.id==ctxMsgId);if(!msg)return;
  store.pinnedMsgId=ctxMsgId;store.pinnedMsgText=msg.text||'[медиа]';
  updatePinnedBar();
  const payload=JSON.stringify({type:'pin',msgId:ctxMsgId,text:msg.text||'[медиа]'});
  if(activeType==='group'){
    const g=groups[active];
    Object.keys(g.members).filter(pid=>pid!==myId&&peers[pid]?.online).forEach(pid=>cmd({cmd:'send',peer_id:pid,text:'__MSGACT__'+payload}));
  } else {
    cmd({cmd:'send',peer_id:active,text:'__MSGACT__'+payload});
  }
  toast('📌','Сообщение закреплено','');
}

function unpinMsg(){
  hideMsgCtx();
  if(!active)return;
  const store=activeType==='group'?groups[active]:peers[active];if(!store)return;
  store.pinnedMsgId=null;store.pinnedMsgText='';
  updatePinnedBar();
  const payload=JSON.stringify({type:'unpin'});
  if(activeType==='group'){
    const g=groups[active];
    Object.keys(g.members).filter(pid=>pid!==myId&&peers[pid]?.online).forEach(pid=>cmd({cmd:'send',peer_id:pid,text:'__MSGACT__'+payload}));
  } else {
    cmd({cmd:'send',peer_id:active,text:'__MSGACT__'+payload});
  }
  toast('','Сообщение откреплено','');
}

function showPinnedCtx(e){
  e.preventDefault();
  // Show unpin option
  ctxMsgId=null;
  const m=document.getElementById('msgCtx');
  document.getElementById('ctxPinBtn').style.display='none';
  document.getElementById('ctxUnpinBtn').style.display='block';
  document.getElementById('ctxEditBtn').style.display='none';
  let x=e.clientX,y=e.clientY;
  if(x+200>window.innerWidth)x=window.innerWidth-210;
  m.style.left=x+'px';m.style.top=y+'px';m.classList.add('show');
  setTimeout(()=>document.addEventListener('click',hideMsgCtx,{once:true}),50);
}"""
results.append(('pinMsg works in peer chat + unpinMsg', old5 in c))
if old5 in c: c = c.replace(old5, new5)

# ── 6. updatePinnedBar — работает и в переписке ──────────────────────────────
old6 = "function updatePinnedBar(){\n  if(activeType!=='group')return;\n  const g=groups[active];\n  const bar=document.getElementById('pinnedBar');\n  if(g?.pinnedMsgId){\n    document.getElementById('pinnedBarText').textContent=g.pinnedMsgText||'';\n    bar.classList.add('show');\n  } else {\n    bar.classList.remove('show');\n  }\n}"
new6 = """function updatePinnedBar(){
  const store=activeType==='group'?groups[active]:peers[active];
  const bar=document.getElementById('pinnedBar');
  if(store?.pinnedMsgId){
    document.getElementById('pinnedBarText').textContent=store.pinnedMsgText||'';
    bar.classList.add('show');
  } else {
    bar.classList.remove('show');
  }
}"""
results.append(('updatePinnedBar works in peer chat', old6 in c))
if old6 in c: c = c.replace(old6, new6)

# ── 7. __MSGACT__ unpin handler ───────────────────────────────────────────────
old7 = "      } else if(d.type==='pin'){\n        const g=Object.values(groups).find(g=>g.members&&g.members[id]);\n        if(g){g.pinnedMsgId=d.msgId;g.pinnedMsgText=d.text;updatePinnedBar();}\n        toast('📌','Сообщение закреплено','');"
new7 = """      } else if(d.type==='pin'){
        const g=Object.values(groups).find(g=>g.members&&g.members[id]);
        if(g){g.pinnedMsgId=d.msgId;g.pinnedMsgText=d.text;updatePinnedBar();}
        else if(peers[id]){peers[id].pinnedMsgId=d.msgId;peers[id].pinnedMsgText=d.text;updatePinnedBar();}
        toast('📌','Сообщение закреплено','');
      } else if(d.type==='unpin'){
        const g=Object.values(groups).find(g=>g.members&&g.members[id]);
        if(g){g.pinnedMsgId=null;g.pinnedMsgText='';updatePinnedBar();}
        else if(peers[id]){peers[id].pinnedMsgId=null;peers[id].pinnedMsgText='';updatePinnedBar();}
        toast('','Сообщение откреплено','');"""
results.append(('unpin handler in __MSGACT__', old7 in c))
if old7 in c: c = c.replace(old7, new7)

# ── 8. msgInp — добавить oninput для @упоминаний ─────────────────────────────
old8 = '<textarea class="msg-inp" id="msgInp" rows="1" placeholder="Сообщение..." onkeydown="inpKey(event)" oninput="autoH(this)"></textarea>'
new8 = '<textarea class="msg-inp" id="msgInp" rows="1" placeholder="Сообщение..." onkeydown="inpKey(event)" oninput="autoH(this);handleMentionInput(this)"></textarea>'
results.append(('msgInp mention handler', old8 in c))
if old8 in c: c = c.replace(old8, new8)

# ── 9. Добавить JS для @упоминаний ───────────────────────────────────────────
old9 = "function renderMentions(text){"
new9 = """// ── @ Mentions ────────────────────────────────
function handleMentionInput(inp){
  const val=inp.value;
  const pos=inp.selectionStart;
  const before=val.slice(0,pos);
  const match=before.match(/@(\\w*)$/);
  if(!match){hideMentionPopup();return;}
  const query=match[1].toLowerCase();
  // Collect users from peers
  const candidates=Object.values(peers).filter(p=>p.username&&p.username.toLowerCase().startsWith(query));
  if(candidates.length===0){hideMentionPopup();return;}
  showMentionPopup(candidates,match[0],pos);
}

function showMentionPopup(candidates,trigger,pos){
  const popup=document.getElementById('mentionPopup');
  popup.innerHTML='';
  candidates.slice(0,6).forEach(p=>{
    const item=document.createElement('div');
    item.style.cssText='padding:10px 14px;cursor:pointer;display:flex;align-items:center;gap:10px;border-bottom:1px solid #f0f0f0';
    item.innerHTML=`<div style="width:28px;height:28px;border-radius:50%;background:#1ABC9C;display:flex;align-items:center;justify-content:center;color:#fff;font-size:12px;font-weight:700">${p.username[0].toUpperCase()}</div><span style="font-size:13px;font-weight:600;color:#1ABC9C">@${p.username}</span>`;
    item.onmouseover=()=>item.style.background='#f8f8f8';
    item.onmouseout=()=>item.style.background='none';
    item.onclick=()=>insertMention(p.username,trigger,pos);
    popup.appendChild(item);
  });
  popup.style.display='block';
}

function hideMentionPopup(){
  document.getElementById('mentionPopup').style.display='none';
}

function insertMention(username,trigger,pos){
  const inp=document.getElementById('msgInp');
  const val=inp.value;
  const before=val.slice(0,pos-trigger.length);
  const after=val.slice(pos);
  inp.value=before+'@'+username+' '+after;
  inp.selectionStart=inp.selectionEnd=before.length+username.length+2;
  inp.focus();
  hideMentionPopup();
  autoH(inp);
}

function renderMentions(text){"""
results.append(('mention JS functions', old9 in c))
if old9 in c: c = c.replace(old9, new9)

# ── 10. В mkBubble рендерить @упоминания с цветом ────────────────────────────
old10 = "  bubble.appendChild(document.createTextNode(m.text||''));\n    if(m.origText){const od=document.createElement('div');od.className='translate-orig';od.textContent='Оригинал: '+m.origText;bubble.appendChild(od)}"
new10 = """  const textNode=document.createElement('span');
    textNode.innerHTML=renderMentions(esc(m.text||''));
    bubble.appendChild(textNode);
    if(m.origText){const od=document.createElement('div');od.className='translate-orig';od.textContent='Оригинал: '+m.origText;bubble.appendChild(od)}"""
results.append(('render mentions in bubble', old10 in c))
if old10 in c: c = c.replace(old10, new10)

with open('ui/gui.py', 'w', encoding='utf-8') as f:
    f.write(c)

print()
for name, found in results:
    print(f"  {'✓' if found else '✗ НЕ НАЙДЕНО'}  {name}")
print('\nГотово!')

with open('ui/gui.py', encoding='utf-8') as f:
    c = f.read()

results = []

# ── 1. CSS для новых функций ──────────────────────────────────────────────────
old1 = '.bubble{padding:9px 14px;font-size:14px;line-height:1.5;word-break:break-word;cursor:pointer}'
new1 = '''.bubble{padding:9px 14px;font-size:14px;line-height:1.5;word-break:break-word;cursor:pointer}
.reactions-row{display:flex;flex-wrap:wrap;gap:4px;margin-top:4px}
.reaction-chip{background:rgba(26,188,156,.12);border:1px solid rgba(26,188,156,.25);border-radius:12px;padding:2px 8px;font-size:13px;cursor:pointer;display:flex;align-items:center;gap:3px;transition:background .15s}
.reaction-chip:hover,.reaction-chip.mine{background:rgba(26,188,156,.28);border-color:#1ABC9C}
.reaction-chip span{font-size:11px;color:#1ABC9C;font-weight:600}
.reply-preview{background:rgba(26,188,156,.1);border-left:3px solid #1ABC9C;padding:6px 10px;border-radius:0 8px 8px 0;margin-bottom:6px;cursor:pointer}
.reply-preview-name{font-size:11px;font-weight:700;color:#1ABC9C;margin-bottom:2px}
.reply-preview-text{font-size:12px;color:rgba(0,0,0,.5);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:240px}
.msg-row.out .reply-preview-text{color:rgba(255,255,255,.6)}
.msg-row.out .reply-preview{background:rgba(255,255,255,.15);border-left-color:rgba(255,255,255,.6)}
.msg-row.out .reply-preview-name{color:rgba(255,255,255,.8)}
.reply-bar{display:none;padding:8px 14px;background:#f0fdf8;border-top:1px solid #e0f5ef;align-items:center;gap:10px}
.reply-bar.show{display:flex}
.reply-bar-text{flex:1;font-size:13px;color:#333;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.reply-bar-name{font-size:11px;font-weight:700;color:#1ABC9C}
.reply-bar-cancel{background:none;border:none;color:#999;cursor:pointer;font-size:18px;padding:0 4px}
.mention{color:#1ABC9C;font-weight:600;cursor:pointer}
.pinned-bar{display:none;padding:8px 14px;background:#fff9e6;border-bottom:1px solid #ffe58a;align-items:center;gap:10px;cursor:pointer}
.pinned-bar.show{display:flex}
.pinned-bar-icon{color:#f0b90b;font-size:16px}
.pinned-bar-text{flex:1;font-size:13px;color:#333;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.search-bar{display:none;padding:8px 14px;background:#f8f8f8;border-bottom:1px solid #eee;align-items:center;gap:8px}
.search-bar.show{display:flex}
.search-inp{flex:1;border:1px solid #ddd;border-radius:20px;padding:6px 14px;font-size:13px;outline:none;font-family:\'Inter\',sans-serif}
.search-nav{background:none;border:none;color:#999;cursor:pointer;font-size:16px;padding:4px 6px}
.search-nav:hover{color:#1ABC9C}
.msg-highlight{background:rgba(26,188,156,.25)!important}
.edited-mark{font-size:10px;color:rgba(0,0,0,.35);margin-left:4px}
.msg-row.out .edited-mark{color:rgba(255,255,255,.5)}'''
results.append(('CSS new features', old1 in c))
if old1 in c: c = c.replace(old1, new1)

# ── 2. Контекстное меню — добавить реакции, ответ, редактировать, удалить для всех, закрепить ──
old2 = '<div class="ctx-menu" id="msgCtx">\n  <div class="ctx-item danger" onclick="delMsg()">🗑 Удалить</div>\n  <div class="ctx-item" onclick="showTrans()">🌐 Перевести</div>\n</div>'
new2 = '''<div class="ctx-menu" id="msgCtx">
  <div style="display:flex;gap:6px;padding:6px 10px;border-bottom:1px solid #f0f0f0">
    <span onclick="addReaction('👍')" style="font-size:20px;cursor:pointer;padding:2px 4px;border-radius:6px;transition:background .15s" onmouseover="this.style.background='#f0f0f0'" onmouseout="this.style.background='none'">👍</span>
    <span onclick="addReaction('❤️')" style="font-size:20px;cursor:pointer;padding:2px 4px;border-radius:6px;transition:background .15s" onmouseover="this.style.background='#f0f0f0'" onmouseout="this.style.background='none'">❤️</span>
    <span onclick="addReaction('😂')" style="font-size:20px;cursor:pointer;padding:2px 4px;border-radius:6px;transition:background .15s" onmouseover="this.style.background='#f0f0f0'" onmouseout="this.style.background='none'">😂</span>
    <span onclick="addReaction('😮')" style="font-size:20px;cursor:pointer;padding:2px 4px;border-radius:6px;transition:background .15s" onmouseover="this.style.background='#f0f0f0'" onmouseout="this.style.background='none'">😮</span>
    <span onclick="addReaction('👎')" style="font-size:20px;cursor:pointer;padding:2px 4px;border-radius:6px;transition:background .15s" onmouseover="this.style.background='#f0f0f0'" onmouseout="this.style.background='none'">👎</span>
  </div>
  <div class="ctx-item" onclick="replyToMsg()">↩ Ответить</div>
  <div class="ctx-item" id="ctxEditBtn" onclick="editMsg()">✏️ Редактировать</div>
  <div class="ctx-item" id="ctxPinBtn" onclick="pinMsg()">📌 Закрепить</div>
  <div class="ctx-item" onclick="showTrans()">🌐 Перевести</div>
  <div class="ctx-item danger" onclick="delMsgForAll()">🗑 Удалить для всех</div>
</div>'''
results.append(('context menu with reactions', old2 in c))
if old2 in c: c = c.replace(old2, new2)

# ── 3. Добавить reply-bar, search-bar, pinned-bar в chat area ────────────────
old3 = '    <div class="peer-list" id="peerList"></div>'
new3 = '''    <div class="peer-list" id="peerList"></div>
    <!-- Search bar -->
    <div class="search-bar" id="searchBar">
      <input class="search-inp" id="searchInp" placeholder="Поиск по чату..." oninput="doSearch(this.value)" onkeydown="if(event.key===\'Escape\')closeSearch()">
      <button class="search-nav" onclick="searchNav(-1)">▲</button>
      <button class="search-nav" onclick="searchNav(1)">▼</button>
      <span id="searchCount" style="font-size:12px;color:#999;min-width:40px"></span>
      <button class="search-nav" onclick="closeSearch()">✕</button>
    </div>'''
results.append(('search bar in sidebar', old3 in c))
if old3 in c: c = c.replace(old3, new3)

# ── 4. Добавить pinned-bar и reply-bar в chat area ───────────────────────────
old4 = '    <div class="chat-head" id="chatHead" style="display:none">'
new4 = '''    <!-- Pinned message bar -->
    <div class="pinned-bar" id="pinnedBar" onclick="scrollToPinned()">
      <span class="pinned-bar-icon">📌</span>
      <div><div style="font-size:10px;font-weight:700;color:#f0b90b;margin-bottom:1px">Закреплённое сообщение</div><div class="pinned-bar-text" id="pinnedBarText"></div></div>
    </div>
    <div class="chat-head" id="chatHead" style="display:none">'''
results.append(('pinned bar in chat', old4 in c))
if old4 in c: c = c.replace(old4, new4)

# ── 5. Добавить reply-bar перед полем ввода ──────────────────────────────────
old5 = '    <div class="inp-area" id="inpArea" style="display:none">'
new5 = '''    <!-- Reply bar -->
    <div class="reply-bar" id="replyBar">
      <div style="flex:1;min-width:0">
        <div class="reply-bar-name" id="replyBarName"></div>
        <div class="reply-bar-text" id="replyBarText"></div>
      </div>
      <button class="reply-bar-cancel" onclick="cancelReply()">✕</button>
    </div>
    <div class="inp-area" id="inpArea" style="display:none">'''
results.append(('reply bar before input', old5 in c))
if old5 in c: c = c.replace(old5, new5)

# ── 6. Добавить кнопку поиска в chat-head ────────────────────────────────────
old6 = '      <button class="call-ico-btn" id="videoCallBtn" onclick="startVideoCall()" title="Видеозвонок">'
new6 = '      <button class="call-ico-btn" onclick="openSearch()" title="Поиск"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg></button>\n      <button class="call-ico-btn" id="videoCallBtn" onclick="startVideoCall()" title="Видеозвонок">'
results.append(('search button in chat head', old6 in c))
if old6 in c: c = c.replace(old6, new6)

# ── 7. mkBubble — добавить reply preview, реакции, edited mark ───────────────
old7 = '  bubble.oncontextmenu=e=>showMsgCtx(e,m.id,wrap);\n  const meta=document.createElement(\'div\');meta.className=\'m-meta\';\n  meta.innerHTML=`<span>${m.time}</span>${m.out?\'<span class="m-tick">✓✓</span>\':\'\'}`;\n  wrap.appendChild(bubble);wrap.appendChild(meta);'
new7 = '''  // Reply preview
  if(m.replyTo){
    const rp=document.createElement('div');rp.className='reply-preview';
    rp.innerHTML=`<div class="reply-preview-name">${esc(m.replyToName||'')}</div><div class="reply-preview-text">${esc(m.replyToText||'')}</div>`;
    rp.onclick=e=>{e.stopPropagation();scrollToMsg(m.replyTo)};
    wrap.insertBefore(rp,bubble);
  }
  bubble.oncontextmenu=e=>showMsgCtx(e,m.id,wrap);
  // Reactions row
  const reactRow=document.createElement('div');reactRow.className='reactions-row';reactRow.id='react_'+m.id;
  renderReactRow(m,reactRow);
  const meta=document.createElement('div');meta.className='m-meta';
  meta.innerHTML=`<span>${m.time}</span>${m.edited?'<span class="edited-mark">изм.</span>':''}${m.out?'<span class="m-tick">✓✓</span>':''}`;
  wrap.appendChild(bubble);wrap.appendChild(reactRow);wrap.appendChild(meta);'''
results.append(('mkBubble reply+reactions+edited', old7 in c))
if old7 in c: c = c.replace(old7, new7)

# ── 8. showMsgCtx — показывать/скрывать кнопки редактирования и закрепления ──
old8 = "function showMsgCtx(e,msgId,wrap){\n  e.preventDefault();e.stopPropagation();ctxMsgId=msgId;ctxMsgEl=wrap;\n  const m=document.getElementById('msgCtx');\n  let x=e.clientX,y=e.clientY;\n  if(x+200>window.innerWidth)x=window.innerWidth-210;\n  if(y+80>window.innerHeight)y=window.innerHeight-90;\n  m.style.left=x+'px';m.style.top=y+'px';m.classList.add('show');\n  document.getElementById('transPanel').classList.remove('show');\n  setTimeout(()=>document.addEventListener('click',hideMsgCtx,{once:true}),50);\n}"
new8 = """function showMsgCtx(e,msgId,wrap){
  e.preventDefault();e.stopPropagation();ctxMsgId=msgId;ctxMsgEl=wrap;
  const m=document.getElementById('msgCtx');
  // Show/hide edit button (only for own messages)
  const store=activeType==='group'?groups[active]:peers[active];
  const msg=store?.messages?.find(x=>x.id==msgId);
  const isOwn=msg?.out||msg?.from===myId;
  document.getElementById('ctxEditBtn').style.display=isOwn?'block':'none';
  document.getElementById('ctxPinBtn').style.display=activeType==='group'?'block':'none';
  let x=e.clientX,y=e.clientY;
  if(x+200>window.innerWidth)x=window.innerWidth-210;
  if(y+160>window.innerHeight)y=window.innerHeight-170;
  m.style.left=x+'px';m.style.top=y+'px';m.classList.add('show');
  document.getElementById('transPanel').classList.remove('show');
  setTimeout(()=>document.addEventListener('click',hideMsgCtx,{once:true}),50);
}"""
results.append(('showMsgCtx with edit/pin visibility', old8 in c))
if old8 in c: c = c.replace(old8, new8)

# ── 9. Добавить все новые JS функции после delMsg ────────────────────────────
old9 = "function showTrans(){"
new9 = """// ── Reactions ─────────────────────────────────
function renderReactRow(m,row){
  if(!m.reactions)return;
  row.innerHTML='';
  Object.entries(m.reactions).forEach(([emoji,users])=>{
    if(!users||users.length===0)return;
    const chip=document.createElement('div');chip.className='reaction-chip'+(users.includes(myId)?' mine':'');
    chip.innerHTML=emoji+'<span>'+users.length+'</span>';
    chip.onclick=e=>{e.stopPropagation();addReactionDirect(m.id,emoji)};
    row.appendChild(chip);
  });
}

function addReaction(emoji){
  hideMsgCtx();
  addReactionDirect(ctxMsgId,emoji);
}

function addReactionDirect(msgId,emoji){
  if(!active)return;
  const store=activeType==='group'?groups[active]:peers[active];if(!store)return;
  const msg=store.messages.find(m=>m.id==msgId);if(!msg)return;
  if(!msg.reactions)msg.reactions={};
  if(!msg.reactions[emoji])msg.reactions[emoji]=[];
  const idx=msg.reactions[emoji].indexOf(myId);
  if(idx>=0)msg.reactions[emoji].splice(idx,1);
  else msg.reactions[emoji].push(myId);
  // Update UI
  const row=document.getElementById('react_'+msgId);
  if(row)renderReactRow(msg,row);
  // Send to peers
  const payload=JSON.stringify({type:'reaction',msgId,emoji,userId:myId});
  if(activeType==='peer')cmd({cmd:'send',peer_id:active,text:'__REACT__'+payload});
  else if(activeType==='group'){
    const g=groups[active];
    Object.keys(g.members).filter(pid=>pid!==myId&&peers[pid]?.online).forEach(pid=>cmd({cmd:'send',peer_id:pid,text:'__REACT__'+payload}));
  }
}

// ── Reply ──────────────────────────────────────
let replyToId=null,replyToText='',replyToName='';

function replyToMsg(){
  hideMsgCtx();
  if(!ctxMsgId||!active)return;
  const store=activeType==='group'?groups[active]:peers[active];if(!store)return;
  const msg=store.messages.find(m=>m.id==ctxMsgId);if(!msg)return;
  replyToId=ctxMsgId;
  replyToText=msg.text||'[медиа]';
  replyToName=msg.out?myU||'Вы':(msg.fromName||dn(peers[active])||'');
  document.getElementById('replyBarName').textContent=replyToName;
  document.getElementById('replyBarText').textContent=replyToText;
  document.getElementById('replyBar').classList.add('show');
  document.getElementById('msgInp').focus();
}

function cancelReply(){
  replyToId=null;replyToText='';replyToName='';
  document.getElementById('replyBar').classList.remove('show');
}

// ── Edit message ───────────────────────────────
let editingMsgId=null;

function editMsg(){
  hideMsgCtx();
  if(!ctxMsgId||!active)return;
  const store=activeType==='group'?groups[active]:peers[active];if(!store)return;
  const msg=store.messages.find(m=>m.id==ctxMsgId);if(!msg||msg.type!=='text')return;
  editingMsgId=ctxMsgId;
  const inp=document.getElementById('msgInp');
  inp.value=msg.text;inp.focus();
  document.getElementById('replyBarName').textContent='Редактирование';
  document.getElementById('replyBarText').textContent=msg.text;
  document.getElementById('replyBar').classList.add('show');
}

// ── Delete for all ─────────────────────────────
function delMsgForAll(){
  hideMsgCtx();
  if(!ctxMsgEl||!active)return;
  const store=activeType==='group'?groups[active]:peers[active];if(!store)return;
  store.messages=store.messages.filter(m=>m.id!=ctxMsgId);
  ctxMsgEl.closest('.msg-row')?.remove();
  const payload=JSON.stringify({type:'delete',msgId:ctxMsgId});
  if(activeType==='peer')cmd({cmd:'send',peer_id:active,text:'__MSGACT__'+payload});
  else if(activeType==='group'){
    const g=groups[active];
    Object.keys(g.members).filter(pid=>pid!==myId&&peers[pid]?.online).forEach(pid=>cmd({cmd:'send',peer_id:pid,text:'__MSGACT__'+payload}));
  }
}

// ── Pin message ────────────────────────────────
function pinMsg(){
  hideMsgCtx();
  if(!ctxMsgId||activeType!=='group')return;
  const g=groups[active];if(!g)return;
  const msg=g.messages.find(m=>m.id==ctxMsgId);if(!msg)return;
  g.pinnedMsgId=ctxMsgId;g.pinnedMsgText=msg.text||'[медиа]';
  updatePinnedBar();
  const payload=JSON.stringify({type:'pin',msgId:ctxMsgId,text:msg.text||'[медиа]'});
  Object.keys(g.members).filter(pid=>pid!==myId&&peers[pid]?.online).forEach(pid=>cmd({cmd:'send',peer_id:pid,text:'__MSGACT__'+payload}));
  toast('📌','Сообщение закреплено','');
}

function updatePinnedBar(){
  if(activeType!=='group')return;
  const g=groups[active];
  const bar=document.getElementById('pinnedBar');
  if(g?.pinnedMsgId){
    document.getElementById('pinnedBarText').textContent=g.pinnedMsgText||'';
    bar.classList.add('show');
  } else {
    bar.classList.remove('show');
  }
}

function scrollToPinned(){
  if(activeType!=='group')return;
  const g=groups[active];if(!g?.pinnedMsgId)return;
  scrollToMsg(g.pinnedMsgId);
}

function scrollToMsg(msgId){
  document.querySelectorAll('.msg-row').forEach(row=>{
    row.classList.remove('msg-highlight');
  });
  const rows=document.querySelectorAll('.msg-row');
  const store=activeType==='group'?groups[active]:peers[active];if(!store)return;
  const idx=store.messages.findIndex(m=>m.id==msgId);
  if(idx>=0&&rows[idx]){
    rows[idx].scrollIntoView({behavior:'smooth',block:'center'});
    rows[idx].classList.add('msg-highlight');
    setTimeout(()=>rows[idx].classList.remove('msg-highlight'),2000);
  }
}

// ── Search ─────────────────────────────────────
let searchResults=[],searchIdx=0;

function openSearch(){
  document.getElementById('searchBar').classList.add('show');
  document.getElementById('searchInp').focus();
}

function closeSearch(){
  document.getElementById('searchBar').classList.remove('show');
  document.getElementById('searchInp').value='';
  document.querySelectorAll('.msg-highlight').forEach(el=>el.classList.remove('msg-highlight'));
  searchResults=[];searchIdx=0;
  document.getElementById('searchCount').textContent='';
}

function doSearch(q){
  document.querySelectorAll('.msg-highlight').forEach(el=>el.classList.remove('msg-highlight'));
  if(!q){searchResults=[];document.getElementById('searchCount').textContent='';return;}
  const store=activeType==='group'?groups[active]:peers[active];if(!store)return;
  const rows=document.querySelectorAll('#msgs .msg-row');
  searchResults=[];
  store.messages.forEach((m,i)=>{
    if(m.text&&m.text.toLowerCase().includes(q.toLowerCase())&&rows[i]){
      searchResults.push(rows[i]);
    }
  });
  searchIdx=0;
  if(searchResults.length>0){
    searchResults[0].classList.add('msg-highlight');
    searchResults[0].scrollIntoView({behavior:'smooth',block:'center'});
    document.getElementById('searchCount').textContent='1/'+searchResults.length;
  } else {
    document.getElementById('searchCount').textContent='0';
  }
}

function searchNav(dir){
  if(!searchResults.length)return;
  searchResults[searchIdx].classList.remove('msg-highlight');
  searchIdx=(searchIdx+dir+searchResults.length)%searchResults.length;
  searchResults[searchIdx].classList.add('msg-highlight');
  searchResults[searchIdx].scrollIntoView({behavior:'smooth',block:'center'});
  document.getElementById('searchCount').textContent=(searchIdx+1)+'/'+searchResults.length;
}

// ── Mentions in groups ─────────────────────────
function renderMentions(text){
  return text.replace(/@(\\w+)/g,(match,name)=>`<span class="mention" onclick="openMentionedUser('${name}')">${match}</span>`);
}
function openMentionedUser(name){
  const pid=Object.keys(peers).find(id=>peers[id].username&&peers[id].username.toLowerCase()===name.toLowerCase());
  if(pid)openChat(pid,'peer');
}

function showTrans(){"""
results.append(('new JS functions', old9 in c))
if old9 in c: c = c.replace(old9, new9)

# ── 10. В send message — добавить replyTo и editingMsgId ─────────────────────
old10 = "function sendMsg(){\n  const inp=document.getElementById('msgInp');\n  const text=inp.value.trim();if(!text||!active)return;"
new10 = """function sendMsg(){
  const inp=document.getElementById('msgInp');
  const text=inp.value.trim();if(!text||!active)return;
  // Handle edit
  if(editingMsgId){
    const store=activeType==='group'?groups[active]:peers[active];
    const msg=store?.messages?.find(m=>m.id==editingMsgId);
    if(msg){
      msg.text=text;msg.edited=true;
      // Update bubble
      document.querySelectorAll('.msg-row').forEach((row,i)=>{
        if(store.messages[i]?.id==editingMsgId){
          const b=row.querySelector('.bubble');
          if(b){let tn=null;for(const n of b.childNodes){if(n.nodeType===3){tn=n;break}}if(tn)tn.textContent=text;}
          const meta=row.querySelector('.m-meta');
          if(meta&&!meta.querySelector('.edited-mark')){const em=document.createElement('span');em.className='edited-mark';em.textContent='изм.';meta.insertBefore(em,meta.lastChild);}
        }
      });
      const payload=JSON.stringify({type:'edit',msgId:editingMsgId,text});
      if(activeType==='peer')cmd({cmd:'send',peer_id:active,text:'__MSGACT__'+payload});
      else if(activeType==='group'){
        const g=groups[active];
        Object.keys(g.members).filter(pid=>pid!==myId&&peers[pid]?.online).forEach(pid=>cmd({cmd:'send',peer_id:pid,text:'__MSGACT__'+payload}));
      }
    }
    editingMsgId=null;cancelReply();inp.value='';autoH(inp);return;
  }"""
results.append(('sendMsg with edit support', old10 in c))
if old10 in c: c = c.replace(old10, new10)

# ── 11. В sendMsg добавить replyTo к сообщению ───────────────────────────────
old11 = "  const now=new Date().toTimeString().slice(0,5);\n  const m={id:Date.now()+'_out',text,out:true,time:now,type:'text'};"
new11 = """  const now=new Date().toTimeString().slice(0,5);
  const m={id:Date.now()+'_out',text,out:true,time:now,type:'text'};
  if(replyToId){m.replyTo=replyToId;m.replyToText=replyToText;m.replyToName=replyToName;cancelReply();}"""
results.append(('sendMsg with replyTo', old11 in c))
if old11 in c: c = c.replace(old11, new11)

# ── 12. В handle — обработать __REACT__, __MSGACT__ ──────────────────────────
old12 = "  if(handleExchangeMsg(id,txt)) return;"
new12 = """  if(handleExchangeMsg(id,txt)) return;
  if(txt.startsWith('__REACT__')){
    try{
      const d=JSON.parse(txt.slice(9));
      const store=peers[id]?peers[id]:Object.values(groups).find(g=>g.members&&g.members[id]);
      if(store&&store.messages){
        const msg=store.messages.find(m=>m.id==d.msgId);
        if(msg){
          if(!msg.reactions)msg.reactions={};
          if(!msg.reactions[d.emoji])msg.reactions[d.emoji]=[];
          const idx=msg.reactions[d.emoji].indexOf(d.userId);
          if(idx>=0)msg.reactions[d.emoji].splice(idx,1);else msg.reactions[d.emoji].push(d.userId);
          const row=document.getElementById('react_'+d.msgId);
          if(row)renderReactRow(msg,row);
        }
      }
    }catch(e){}
    return;
  }
  if(txt.startsWith('__MSGACT__')){
    try{
      const d=JSON.parse(txt.slice(10));
      const findStore=()=>{
        if(peers[id])return{store:peers[id],type:'peer'};
        const g=Object.values(groups).find(g=>g.members&&g.members[id]);
        return g?{store:g,type:'group'}:{};
      };
      const {store,type}=findStore();
      if(!store)return;
      if(d.type==='delete'){
        store.messages=store.messages.filter(m=>m.id!=d.msgId);
        if(active===(type==='peer'?id:Object.keys(groups).find(k=>groups[k]===store))&&activeType===type){
          document.querySelectorAll('.msg-row').forEach((row,i)=>{
            if(!store.messages[i])row.remove();
          });
          const area=document.getElementById('msgs');
          area.innerHTML='<div class="date-sep">СЕГОДНЯ</div>';
          store.messages.forEach(m=>area.appendChild(mkBubble(m,type)));
        }
      } else if(d.type==='edit'){
        const msg=store.messages.find(m=>m.id==d.msgId);
        if(msg){msg.text=d.text;msg.edited=true;}
        const gid=Object.keys(groups).find(k=>groups[k]===store)||id;
        if(active===gid||active===id){
          document.querySelectorAll('.msg-row').forEach((row,i)=>{
            if(store.messages[i]?.id==d.msgId){
              const b=row.querySelector('.bubble');
              if(b){let tn=null;for(const n of b.childNodes){if(n.nodeType===3){tn=n;break}}if(tn)tn.textContent=d.text;}
              const meta=row.querySelector('.m-meta');
              if(meta&&!meta.querySelector('.edited-mark')){const em=document.createElement('span');em.className='edited-mark';em.textContent='изм.';meta.insertBefore(em,meta.lastChild);}
            }
          });
        }
      } else if(d.type==='pin'){
        const g=Object.values(groups).find(g=>g.members&&g.members[id]);
        if(g){g.pinnedMsgId=d.msgId;g.pinnedMsgText=d.text;updatePinnedBar();}
        toast('📌','Сообщение закреплено','');
      }
    }catch(e){}
    return;
  }"""
results.append(('handle __REACT__ and __MSGACT__', old12 in c))
if old12 in c: c = c.replace(old12, new12)

# ── 13. openChat — сбросить reply и обновить pinned bar ──────────────────────
old13 = "function openChat(id,type){"
new13 = """function openChat(id,type){
  cancelReply();editingMsgId=null;closeSearch();"""
results.append(('openChat reset reply/edit/search', old13 in c))
if old13 in c: c = c.replace(old13, new13)

# ── 14. Обновить pinnedBar при открытии чата ─────────────────────────────────
old14 = "  document.getElementById('msgs').innerHTML='<div class=\"date-sep\">СЕГОДНЯ</div>';"
new14 = """  document.getElementById('msgs').innerHTML='<div class="date-sep">СЕГОДНЯ</div>';
  setTimeout(updatePinnedBar,50);"""
results.append(('updatePinnedBar on openChat', old14 in c))
if old14 in c: c = c.replace(old14, new14)

with open('ui/gui.py', 'w', encoding='utf-8') as f:
    f.write(c)

print()
for name, found in results:
    print(f"  {'✓' if found else '✗ НЕ НАЙДЕНО'}  {name}")
print('\nГотово!')

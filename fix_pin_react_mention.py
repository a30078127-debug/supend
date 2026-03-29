with open('ui/gui.py', encoding='utf-8') as f:
    c = f.read()

results = []

# ── 1. Убрать pinnedBar из aside (сейчас в списке чатов) ─────────────────────
old1 = '    <!-- Pinned message bar -->\n    <div class="pinned-bar" id="pinnedBar" oncontextmenu="showPinnedCtx(event)">\n      <div onclick="scrollToPinned()" style="display:flex;align-items:center;gap:10px;flex:1;cursor:pointer">\n        <span class="pinned-bar-icon">📌</span>\n        <div><div style="font-size:10px;font-weight:700;color:#f0b90b;margin-bottom:1px">Закреплённое сообщение</div><div class="pinned-bar-text" id="pinnedBarText"></div></div>\n      </div>\n    </div>\n    <!-- Mention popup -->'
new1 = '    <!-- Mention popup -->'
results.append(('remove pinnedBar from aside', old1 in c))
if old1 in c: c = c.replace(old1, new1)

# ── 2. Добавить pinnedBar в main после chat-head ──────────────────────────────
old2 = '  <main class="chat">\n    <div class="chat-head" id="chatHead" style="display:none">'
new2 = '  <main class="chat">\n    <div class="chat-head" id="chatHead" style="display:none">'
# Find closing of chat-head div to insert after it
old2b = '      <button class="ico-btn" onclick="doDisconn()"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18.36 6.64a9 9 0 1 1-12.73 0"/><line x1="12" y1="2" x2="12" y2="12"/></svg></button>\n    </div>'
new2b = '      <button class="ico-btn" onclick="doDisconn()"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18.36 6.64a9 9 0 1 1-12.73 0"/><line x1="12" y1="2" x2="12" y2="12"/></svg></button>\n    </div>\n    <!-- Pinned message bar -->\n    <div class="pinned-bar" id="pinnedBar" oncontextmenu="showPinnedCtx(event)">\n      <div onclick="scrollToPinned()" style="display:flex;align-items:center;gap:10px;flex:1;cursor:pointer">\n        <span class="pinned-bar-icon">📌</span>\n        <div><div style="font-size:10px;font-weight:700;color:#f0b90b;margin-bottom:1px">Закреплённое сообщение</div><div class="pinned-bar-text" id="pinnedBarText"></div></div>\n      </div>\n    </div>'
results.append(('add pinnedBar after chat-head close', old2b in c))
if old2b in c: c = c.replace(old2b, new2b)

# ── 3. Реакции — один пользователь одна реакция на сообщение ─────────────────
old3 = """function addReactionDirect(msgId,emoji){
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
}"""
new3 = """function addReactionDirect(msgId,emoji){
  if(!active)return;
  const store=activeType==='group'?groups[active]:peers[active];if(!store)return;
  const msg=store.messages.find(m=>m.id==msgId);if(!msg)return;
  if(!msg.reactions)msg.reactions={};
  // Remove old reaction from this user (one reaction per user per message)
  let oldEmoji=null;
  Object.keys(msg.reactions).forEach(e=>{
    const idx=msg.reactions[e].indexOf(myId);
    if(idx>=0){oldEmoji=e;msg.reactions[e].splice(idx,1);}
  });
  // Toggle: if clicking same emoji — just remove, else add new
  if(oldEmoji!==emoji){
    if(!msg.reactions[emoji])msg.reactions[emoji]=[];
    msg.reactions[emoji].push(myId);
  }
  // Update UI
  const row=document.getElementById('react_'+msgId);
  if(row)renderReactRow(msg,row);
  // Send to peers
  const payload=JSON.stringify({type:'reaction',msgId,emoji,userId:myId,oldEmoji});
  if(activeType==='peer')cmd({cmd:'send',peer_id:active,text:'__REACT__'+payload});
  else if(activeType==='group'){
    const g=groups[active];
    Object.keys(g.members).filter(pid=>pid!==myId&&peers[pid]?.online).forEach(pid=>cmd({cmd:'send',peer_id:pid,text:'__REACT__'+payload}));
  }
}"""
results.append(('one reaction per user', old3 in c))
if old3 in c: c = c.replace(old3, new3)

# ── 4. Обновить __REACT__ handler — учитывать oldEmoji ───────────────────────
old4 = """          const msg=store.messages.find(m=>m.id==d.msgId);
        if(msg){
          if(!msg.reactions)msg.reactions={};
          if(!msg.reactions[d.emoji])msg.reactions[d.emoji]=[];
          const idx=msg.reactions[d.emoji].indexOf(d.userId);
          if(idx>=0)msg.reactions[d.emoji].splice(idx,1);else msg.reactions[d.emoji].push(d.userId);
          const row=document.getElementById('react_'+d.msgId);
          if(row)renderReactRow(msg,row);
        }"""
new4 = """          const msg=store.messages.find(m=>m.id==d.msgId);
        if(msg){
          if(!msg.reactions)msg.reactions={};
          // Remove old reaction
          if(d.oldEmoji&&msg.reactions[d.oldEmoji]){
            const oi=msg.reactions[d.oldEmoji].indexOf(d.userId);
            if(oi>=0)msg.reactions[d.oldEmoji].splice(oi,1);
          }
          // Remove from all (safety)
          Object.keys(msg.reactions).forEach(e=>{
            const i=msg.reactions[e].indexOf(d.userId);
            if(i>=0)msg.reactions[e].splice(i,1);
          });
          // Add new if not toggling same
          if(!d.oldEmoji||d.oldEmoji!==d.emoji){
            if(!msg.reactions[d.emoji])msg.reactions[d.emoji]=[];
            msg.reactions[d.emoji].push(d.userId);
          }
          const row=document.getElementById('react_'+d.msgId);
          if(row)renderReactRow(msg,row);
        }"""
results.append(('__REACT__ handler with oldEmoji', old4 in c))
if old4 in c: c = c.replace(old4, new4)

# ── 5. Упоминания — белый фон + цветной текст ────────────────────────────────
old5 = "function renderMentions(text){\n  return text.replace(/@(\\w+)/g,(match,name)=>`<span class=\"mention\" onclick=\"openMentionedUser('${name}')\">${match}</span>`);\n}"
new5 = """function renderMentions(text){
  return text.replace(/@(\\w+)/g,(match,name)=>`<span class="mention" onclick="openMentionedUser('${name}')" style="color:#1ABC9C;font-weight:700;cursor:pointer;background:rgba(26,188,156,.08);padding:0 3px;border-radius:4px">${match}</span>`);
}

function hasMention(text){
  return /@\\w+/.test(text);
}"""
results.append(('renderMentions with styled span', old5 in c))
if old5 in c: c = c.replace(old5, new5)

# ── 6. mkBubble — если есть упоминание, белый фон у bubble ──────────────────
old6 = "  const textNode=document.createElement('span');\n    textNode.innerHTML=renderMentions(esc(m.text||''));\n    bubble.appendChild(textNode);"
new6 = """  const textNode=document.createElement('span');
    textNode.innerHTML=renderMentions(esc(m.text||''));
    bubble.appendChild(textNode);
    // White bubble for messages with mentions
    if(hasMention(m.text||'')){
      bubble.style.background='#fff';
      bubble.style.color='#111';
    }"""
results.append(('white bubble for mentions', old6 in c))
if old6 in c: c = c.replace(old6, new6)

with open('ui/gui.py', 'w', encoding='utf-8') as f:
    f.write(c)

print()
for name, found in results:
    print(f"  {'✓' if found else '✗ НЕ НАЙДЕНО'}  {name}")
print('\nГотово!')

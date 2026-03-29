with open('ui/gui.py', encoding='utf-8') as f:
    c = f.read()

results = []

# ── 1. doSend — добавить edit и replyTo ──────────────────────────────────────
old1 = """function doSend(){
  const inp=document.getElementById('msgInp');const text=inp.value.trim();
  if(!text||!active)return;
  const now=new Date().toTimeString().slice(0,5);
  if(activeType==='peer'){
    cmd({cmd:'send',peer_id:active,text});
    playSendSound();
    earnCoins(text, undefined, 'За сообщение ('+text.length+' симв.)');
    const m={id:Date.now()+'_out',text,out:true,time:now,type:'text'};
    peers[active].messages.push(m);peers[active].lastMsg=text;peers[active].lastTime=now;
    appendBubble(m,'peer');
  } else if(activeType==='group'){
    const g=groups[active];if(!g)return;
    const gm={gid:active,gn:g.name,ga:g.avatar,from:myU,msg:text,members:g.members};
    const payload=GP+JSON.stringify(gm);
    Object.keys(g.members).filter(pid=>pid!==myId&&peers[pid]?.online).forEach(pid=>cmd({cmd:'send',peer_id:pid,text:payload}));
    earnCoins(text);
    const m={id:Date.now()+'_out',text,out:true,time:now,type:'text'};
    g.messages.push(m);g.lastMsg=text;g.lastTime=now;
    appendBubble(m,'group');
  }
  scrollMsgs();renderList();
  inp.value='';inp.style.height='auto';
}"""
new1 = """function doSend(){
  const inp=document.getElementById('msgInp');const text=inp.value.trim();
  if(!text||!active)return;
  // Handle edit
  if(editingMsgId){
    const store=activeType==='group'?groups[active]:peers[active];
    const msg=store?.messages?.find(m=>m.id==editingMsgId);
    if(msg){
      msg.text=text;msg.edited=true;
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
    editingMsgId=null;cancelReply();inp.value='';inp.style.height='auto';return;
  }
  const now=new Date().toTimeString().slice(0,5);
  if(activeType==='peer'){
    cmd({cmd:'send',peer_id:active,text});
    playSendSound();
    earnCoins(text, undefined, 'За сообщение ('+text.length+' симв.)');
    const m={id:Date.now()+'_out',text,out:true,time:now,type:'text'};
    if(replyToId){m.replyTo=replyToId;m.replyToText=replyToText;m.replyToName=replyToName;cancelReply();}
    peers[active].messages.push(m);peers[active].lastMsg=text;peers[active].lastTime=now;
    appendBubble(m,'peer');
  } else if(activeType==='group'){
    const g=groups[active];if(!g)return;
    const m={id:Date.now()+'_out',text,out:true,time:now,type:'text'};
    if(replyToId){m.replyTo=replyToId;m.replyToText=replyToText;m.replyToName=replyToName;cancelReply();}
    const gm={gid:active,gn:g.name,ga:g.avatar,from:myU,msg:text,members:g.members,replyTo:m.replyTo,replyToText:m.replyToText,replyToName:m.replyToName,msgId:m.id};
    const payload=GP+JSON.stringify(gm);
    Object.keys(g.members).filter(pid=>pid!==myId&&peers[pid]?.online).forEach(pid=>cmd({cmd:'send',peer_id:pid,text:payload}));
    earnCoins(text);
    g.messages.push(m);g.lastMsg=text;g.lastTime=now;
    appendBubble(m,'group');
  }
  scrollMsgs();renderList();
  inp.value='';inp.style.height='auto';
}"""
results.append(('doSend with edit and reply', old1 in c))
if old1 in c: c = c.replace(old1, new1)

# ── 2. updatePinnedBar — вызов при рендере чата ──────────────────────────────
old2 = "  document.getElementById('msgs').innerHTML='<div class=\"date-sep\">СЕГОДНЯ</div>';"
new2 = "  document.getElementById('msgs').innerHTML='<div class=\"date-sep\">СЕГОДНЯ</div>';\n  setTimeout(updatePinnedBar,50);"
results.append(('updatePinnedBar on openChat', old2 in c))
if old2 in c: c = c.replace(old2, new2)

# ── 3. В группах передавать replyTo в входящем сообщении ─────────────────────
old3 = "          const m={id:Date.now()+'_gm',text:gm.msg,out:false,time:ev.time,type:'text',from:id,fromName:gm.from||shortId(id)};"
new3 = "          const m={id:gm.msgId||Date.now()+'_gm',text:gm.msg,out:false,time:ev.time,type:'text',from:id,fromName:gm.from||shortId(id),replyTo:gm.replyTo,replyToText:gm.replyToText,replyToName:gm.replyToName};"
results.append(('group message with replyTo', old3 in c))
if old3 in c: c = c.replace(old3, new3)

with open('ui/gui.py', 'w', encoding='utf-8') as f:
    f.write(c)

print()
for name, found in results:
    print(f"  {'✓' if found else '✗ НЕ НАЙДЕНО'}  {name}")
print('\nГотово!')

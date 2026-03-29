with open('ui/gui.py', encoding='utf-8') as f:
    c = f.read()

results = []

# ── 1. sendProfile — передавать registeredAt ─────────────────────────────────
old1 = "function sendProfile(peerId){cmd({cmd:'send',peer_id:peerId,text:PP+JSON.stringify({u:myU,b:myBio,a:myAv})})}"
new1 = "function sendProfile(peerId){cmd({cmd:'send',peer_id:peerId,text:PP+JSON.stringify({u:myU,b:myBio,a:myAv,r:profileData.registeredAt||''})})}"
results.append(('sendProfile with registeredAt', old1 in c))
if old1 in c: c = c.replace(old1, new1)

# ── 2. При получении профиля сохранять registeredAt ──────────────────────────
old2 = "if(prof.avatar)p.avatar=prof.avatar;\n        if(prof.registeredAt)p.registeredAt=prof.registeredAt;"
new2 = "if(prof.avatar)p.avatar=prof.avatar;\n        if(prof.r)p.registeredAt=prof.r;"
results.append(('receive profile registeredAt', old2 in c))
if old2 in c: c = c.replace(old2, new2)

# Also try alternate form
if not results[-1][1]:
    old2b = "if(prof.avatar)p.avatar=prof.avatar;"
    new2b = "if(prof.avatar)p.avatar=prof.avatar;\n        if(prof.r)p.registeredAt=prof.r;"
    found2b = old2b in c
    results[-1] = ('receive profile registeredAt', found2b)
    if found2b: c = c.replace(old2b, new2b, 1)

# ── 3. openMentionedUser — показывать профиль, не переходить в чат ───────────
old3 = "function openMentionedUser(name){\n  const pid=Object.keys(peers).find(id=>peers[id].username&&peers[id].username.toLowerCase()===name.toLowerCase());\n  if(pid)openChat(pid,'peer');\n}"
new3 = """function openMentionedUser(name){
  const pid=Object.keys(peers).find(id=>peers[id].username&&peers[id].username.toLowerCase()===name.toLowerCase());
  if(!pid){toast('🔍','Пользователь не найден','@'+name);return;}
  const p=peers[pid];
  const av=document.getElementById('peerProfAv');
  if(p.avatar){av.innerHTML=`<img src="${p.avatar}">`}else{av.innerHTML='';av.textContent=lbl(p.id);av.style.background=avc(p.id);}
  document.getElementById('peerProfLogin').textContent=p.username?'@'+p.username:shortId(p.id);
  document.getElementById('peerProfKey').textContent=p.id;
  const bw=document.getElementById('peerBioWrap');
  if(p.bio){bw.style.display='block';document.getElementById('peerProfBio').textContent=p.bio}else bw.style.display='none';
  const rw=document.getElementById('peerRegWrap');
  if(p.registeredAt){rw.style.display='block';document.getElementById('peerProfDate').textContent=p.registeredAt}else rw.style.display='none';
  // Add "Write" button
  const modal=document.getElementById('peerProfModal');
  let writeBtn=modal.querySelector('.mention-write-btn');
  if(!writeBtn){
    writeBtn=document.createElement('button');
    writeBtn.className='modal-btn mention-write-btn';
    writeBtn.style.cssText='background:#1ABC9C;color:#fff;margin-top:8px';
    modal.querySelector('.modal').appendChild(writeBtn);
  }
  writeBtn.textContent='Написать @'+(p.username||shortId(p.id));
  writeBtn.onclick=()=>{closeM('peerProfModal');openChat(pid,'peer');};
  modal.classList.add('show');
}"""
results.append(('openMentionedUser shows profile', old3 in c))
if old3 in c: c = c.replace(old3, new3)

# ── 4. scrollToPinned — работать и в переписке ───────────────────────────────
old4 = "function scrollToPinned(){\n  if(activeType!=='group')return;\n  const g=groups[active];if(!g?.pinnedMsgId)return;\n  scrollToMsg(g.pinnedMsgId);\n}"
new4 = """function scrollToPinned(){
  const store=activeType==='group'?groups[active]:peers[active];
  if(!store?.pinnedMsgId)return;
  scrollToMsg(store.pinnedMsgId);
}"""
results.append(('scrollToPinned works in peer chat', old4 in c))
if old4 in c: c = c.replace(old4, new4)

# ── 5. ЧС — блокировать входящие сообщения ───────────────────────────────────
# Find the place where incoming messages are processed and add blacklist check
old5 = "    const m={id:Date.now()+'_r',text:txt,out:false,time:ev.time,type:'text',from:id};"
new5 = "    if(blacklist.has(id))return; // blocked\n    const m={id:Date.now()+'_r',text:txt,out:false,time:ev.time,type:'text',from:id};"
results.append(('block incoming messages from blacklist', old5 in c))
if old5 in c: c = c.replace(old5, new5)

# ── 6. Реакции — отправлять при ответе собеседника (уже работает через __REACT__)
# The issue is reactions from others aren't shown — check if renderReactRow uses msg.reactions correctly
# The real fix: when receiving reaction, find the right store (peer or group)
old6 = "      if(store&&store.messages){\n        const msg=store.messages.find(m=>m.id==d.msgId);\n        if(msg){\n          if(!msg.reactions)msg.reactions={};\n          // Remove old reaction from this user\n          Object.keys(msg.reactions).forEach(e=>{\n            const i=msg.reactions[e].indexOf(d.userId);\n            if(i>=0)msg.reactions[e].splice(i,1);\n          });\n          // Add new if not toggling same\n          if(!d.oldEmoji||d.oldEmoji!==d.emoji){\n            if(!msg.reactions[d.emoji])msg.reactions[d.emoji]=[];\n            msg.reactions[d.emoji].push(d.userId);\n          }\n          const row=document.getElementById('react_'+d.msgId);\n          if(row)renderReactRow(msg,row);\n        }\n      }"
new6 = """      // Search in peers and groups
      let foundMsg=null;
      if(peers[id]){
        foundMsg=peers[id].messages?.find(m=>m.id==d.msgId);
      }
      if(!foundMsg){
        Object.values(groups).forEach(g=>{
          if(g.members&&g.members[id]){
            const m=g.messages?.find(m=>m.id==d.msgId);
            if(m)foundMsg=m;
          }
        });
      }
      if(foundMsg){
        if(!foundMsg.reactions)foundMsg.reactions={};
        Object.keys(foundMsg.reactions).forEach(e=>{
          const i=foundMsg.reactions[e].indexOf(d.userId);
          if(i>=0)foundMsg.reactions[e].splice(i,1);
        });
        if(!d.oldEmoji||d.oldEmoji!==d.emoji){
          if(!foundMsg.reactions[d.emoji])foundMsg.reactions[d.emoji]=[];
          foundMsg.reactions[d.emoji].push(d.userId);
        }
        const row=document.getElementById('react_'+d.msgId);
        if(row)renderReactRow(foundMsg,row);
      }"""
results.append(('reactions visible to all', old6 in c))
if old6 in c: c = c.replace(old6, new6)

# ── 7. Пeerprofile — кнопка "Написать" ───────────────────────────────────────
old7 = '    <div class="modal-field"><div class="modal-label">Peer ID</div><div class="modal-value mono" id="peerProfKey">–</div></div>\n  </div>\n</div>\n\n<!-- Create Group Modal -->'
new7 = '    <div class="modal-field"><div class="modal-label">Peer ID</div><div class="modal-value mono" id="peerProfKey">–</div></div>\n    <button class="modal-btn" id="peerWriteBtn" onclick="writeToPeer()" style="margin-top:8px">✉️ Написать</button>\n  </div>\n</div>\n\n<!-- Create Group Modal -->'
results.append(('write button in peer profile', old7 in c))
if old7 in c: c = c.replace(old7, new7)

# ── 8. openPeerProfile — сохранять peerId для кнопки написать ────────────────
old8 = "function openPeerProfile(){\n  if(!active||activeType!=='peer')return;const p=peers[active];if(!p)return;"
new8 = """let viewingPeerId=null;
function openPeerProfile(){
  if(!active||activeType!=='peer')return;const p=peers[active];if(!p)return;
  viewingPeerId=active;"""
results.append(('openPeerProfile saves viewingPeerId', old8 in c))
if old8 in c: c = c.replace(old8, new8)

# ── 9. Добавить writeToPeer функцию ──────────────────────────────────────────
old9 = "function closeM(id){document.getElementById(id).classList.remove('show')}"
new9 = """function writeToPeer(){
  closeM('peerProfModal');
  if(viewingPeerId)openChat(viewingPeerId,'peer');
}
function closeM(id){document.getElementById(id).classList.remove('show')}"""
results.append(('writeToPeer function', old9 in c))
if old9 in c: c = c.replace(old9, new9)

with open('ui/gui.py', 'w', encoding='utf-8') as f:
    f.write(c)

print()
for name, found in results:
    print(f"  {'✓' if found else '✗ НЕ НАЙДЕНО'}  {name}")
print('\nГотово!')

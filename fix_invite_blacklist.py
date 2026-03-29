with open('ui/gui.py', encoding='utf-8') as f:
    c = f.read()

results = []

# ── 1. Добавить поле кода приглашения в regPage2 ─────────────────────────────
old1 = '      <div class="inp-group"><div class="inp-label">О себе (необязательно)</div><textarea class="tg-textarea" id="r2Bio" placeholder="Расскажи о себе..."></textarea></div>\n      <div class="auth-error" id="r2Err"></div>\n      <button class="btn-primary" onclick="doReg2()">Зарегистрироваться</button>'
new1 = '      <div class="inp-group"><div class="inp-label">О себе (необязательно)</div><textarea class="tg-textarea" id="r2Bio" placeholder="Расскажи о себе..."></textarea></div>\n      <div class="inp-group"><div class="inp-label">Код приглашения (необязательно)</div><input class="tg-input" id="r2InvCode" type="text" placeholder="Введи код друга — получи 100 SUP" maxlength="12" autocomplete="off" style="text-transform:uppercase"></div>\n      <div class="auth-error" id="r2Err"></div>\n      <button class="btn-primary" onclick="doReg2()">Зарегистрироваться</button>'
results.append(('invite code field in regPage2', old1 in c))
if old1 in c: c = c.replace(old1, new1)

# ── 2. doReg2 — передавать код приглашения ────────────────────────────────────
old2 = "function doReg2(){\n  const bio=document.getElementById('r2Bio').value.trim();\n  const pass=document.getElementById('r1Pass').value;\n  cmd({cmd:'register',username:reg1Login,password:pass,bio,avatar:regAvData});\n}"
new2 = """function doReg2(){
  const bio=document.getElementById('r2Bio').value.trim();
  const pass=document.getElementById('r1Pass').value;
  const invCode=document.getElementById('r2InvCode')?.value.trim().toUpperCase()||'';
  cmd({cmd:'register',username:reg1Login,password:pass,bio,avatar:regAvData,invCode});
}"""
results.append(('doReg2 with invCode', old2 in c))
if old2 in c: c = c.replace(old2, new2)

# ── 3. register_ok — проверить код и начислить бонус ─────────────────────────
old3 = "  else if(ev.type==='register_ok'){\n    myU=ev.username;myBio=ev.bio||'';myAv=ev.avatar||'';\n    updMyAv();\n    document.getElementById('myUname').textContent='@'+ev.username;\n    document.getElementById('myBioPrev').textContent=myBio||'нажми чтобы открыть профиль';\n    document.getElementById('regPage2').classList.add('hidden');\n    document.getElementById('app').classList.add('visible');\n    toast('🎉','Аккаунт создан!','@'+ev.username);\n  }"
new3 = """  else if(ev.type==='register_ok'){
    myU=ev.username;myBio=ev.bio||'';myAv=ev.avatar||'';
    updMyAv();
    document.getElementById('myUname').textContent='@'+ev.username;
    document.getElementById('myBioPrev').textContent=myBio||'нажми чтобы открыть профиль';
    document.getElementById('regPage2').classList.add('hidden');
    document.getElementById('app').classList.add('visible');
    toast('🎉','Аккаунт создан!','@'+ev.username);
    // Process invite code
    if(ev.invCode){
      walletData.balance+=100;
      walletData.txHistory.unshift({amount:100,desc:'🎁 Бонус за регистрацию по коду',time:new Date().toTimeString().slice(0,5)});
      saveWallet();updateWalletUI();
      toast('🎁','Бонус получен!','+100 SUP за код приглашения');
      // Notify referrer
      cmd({cmd:'ref_activated',invCode:ev.invCode});
    }
  }"""
results.append(('register_ok with invCode bonus', old3 in c))
if old3 in c: c = c.replace(old3, new3)

# ── 4. Python — обработать invCode при регистрации ───────────────────────────
old4 = "            await self._broadcast({'type': 'register_ok', 'username': username, 'bio': bio, 'avatar': avatar})"
new4 = "            inv_code = data.get('invCode', '')\n                    await self._broadcast({'type': 'register_ok', 'username': username, 'bio': bio, 'avatar': avatar, 'invCode': inv_code})"
results.append(('Python register_ok with invCode', old4 in c))
if old4 in c: c = c.replace(old4, new4)

# ── 5. Python — обработать ref_activated ─────────────────────────────────────
old5 = "        elif c == 'ref_used':"
new5 = """        elif c == 'ref_activated':
            inv_code = data.get('invCode', '').upper()
            if inv_code and self.node:
                for pid in self.node.peers:
                    if pid.upper().startswith(inv_code[:12]):
                        await self._broadcast({'type': 'ref_reward'})
                        break

        elif c == 'ref_used':"""
results.append(('Python ref_activated handler', old5 in c))
if old5 in c: c = c.replace(old5, new5)

# ── 6. ref_reward JS — обновить inviteCount ───────────────────────────────────
old6 = "  else if(ev.type==='ref_reward'){\n    // Someone used our ref link — give reward\n    profileData.inviteCount=(profileData.inviteCount||0)+1;\n    walletData.balance+=200;\n    walletData.txHistory.unshift({amount:200,desc:'🎁 Реферальный бонус',time:new Date().toTimeString().slice(0,5)});\n    try{localStorage.setItem('sup_profile',JSON.stringify(profileData))}catch(e){}\n    saveWallet();updateWalletUI();\n    toast('🎁','Реферальный бонус!','Новый пользователь присоединился. +200 SUP');\n  }"
new6 = """  else if(ev.type==='ref_reward'){
    profileData.inviteCount=(profileData.inviteCount||0)+1;
    walletData.balance+=200;
    walletData.txHistory.unshift({amount:200,desc:'🎁 Реферальный бонус',time:new Date().toTimeString().slice(0,5)});
    try{localStorage.setItem('sup_profile',JSON.stringify(profileData))}catch(e){}
    saveWallet();updateWalletUI();
    toast('🎁','Реферальный бонус!','Новый пользователь зарегистрировался по твоему коду. +200 SUP');
  }"""
results.append(('ref_reward JS updated', old6 in c))
if old6 in c: c = c.replace(old6, new6)

# ── 7. Показывать код (не ссылку) в профиле ──────────────────────────────────
old7 = "  // Ref link\n  const refCode=myId.slice(0,12);\n  document.getElementById('myRefLink').textContent='supend://ref/'+refCode;"
new7 = "  // Ref code\n  const refCode=myId.slice(0,12).toUpperCase();\n  document.getElementById('myRefLink').textContent=refCode;"
results.append(('show ref code not link', old7 in c))
if old7 in c: c = c.replace(old7, new7)

old8 = "  const refCode=myId.slice(0,12);\n  const link='supend://ref/'+refCode;\n  navigator.clipboard?.writeText(link).catch(()=>{});\n  toast('📋','Ссылка скопирована','Поделись с друзьями!');"
new8 = "  const refCode=myId.slice(0,12).toUpperCase();\n  navigator.clipboard?.writeText(refCode).catch(()=>{});\n  toast('📋','Код скопирован','Поделись с друзьями!');"
results.append(('copyRefLink copies code', old8 in c))
if old8 in c: c = c.replace(old8, new8)

# ── 8. Обновить label в профиле с ссылки на код ──────────────────────────────
old9 = '      <div style="font-size:11px;color:#999;margin-top:4px">Поделись ссылкой — получи 200 SUP за каждого приглашённого</div>'
new9 = '      <div style="font-size:11px;color:#999;margin-top:4px">Поделись кодом — получи 200 SUP. Друг получит 100 SUP при регистрации</div>'
results.append(('update ref label', old9 in c))
if old9 in c: c = c.replace(old9, new9)

old10 = '      <div class="modal-label">Реферальная ссылка</div>'
new10 = '      <div class="modal-label">Код приглашения</div>'
results.append(('rename ref field label', old10 in c))
if old10 in c: c = c.replace(old10, new10)

# ── 9. Чёрный список — добавить кнопку в peerCtx ────────────────────────────
old11 = '<div class="ctx-menu" id="peerCtx">\n  <div class="ctx-item" onclick="ctxCustomize()">🎨 Кастомизация</div>\n  <div class="ctx-item" onclick="ctxClearHist()">🧹 Удалить историю</div>\n  <div class="ctx-item" onclick="ctxSel()">✓ Выбрать</div>\n  <div class="ctx-item danger" onclick="ctxDelChat()">🗑 Удалить чат</div>\n</div>'
new11 = '''<div class="ctx-menu" id="peerCtx">
  <div class="ctx-item" onclick="ctxCustomize()">🎨 Кастомизация</div>
  <div class="ctx-item" onclick="ctxClearHist()">🧹 Удалить историю</div>
  <div class="ctx-item" onclick="ctxSel()">✓ Выбрать</div>
  <div class="ctx-item danger" onclick="ctxDelChat()">🗑 Удалить чат</div>
  <div class="ctx-item danger" id="ctxBlockBtn" onclick="ctxToggleBlock()">🔒 Добавить в ЧС</div>
</div>'''
results.append(('blacklist button in peerCtx', old11 in c))
if old11 in c: c = c.replace(old11, new11)

# ── 10. showPeerCtx — обновить текст кнопки блокировки ──────────────────────
old12 = "function showPeerCtx(e,id){\n  e.preventDefault();e.stopPropagation();ctxTgt=id;\n  const m=document.getElementById('peerCtx');"
new12 = """function showPeerCtx(e,id){
  e.preventDefault();e.stopPropagation();ctxTgt=id;
  const m=document.getElementById('peerCtx');
  const isBlocked=blacklist.has(id);
  const btn=document.getElementById('ctxBlockBtn');
  if(btn)btn.textContent=isBlocked?'🔓 Убрать из ЧС':'🔒 Добавить в ЧС';"""
results.append(('showPeerCtx with block status', old12 in c))
if old12 in c: c = c.replace(old12, new12)

# ── 11. Добавить blacklist переменную и функции ───────────────────────────────
old13 = "function ctxDelChat(){"
new13 = """// ── Blacklist ──────────────────────────────────
let blacklist = new Set(JSON.parse(localStorage.getItem('sup_blacklist')||'[]'));

function saveBlacklist(){
  try{localStorage.setItem('sup_blacklist',JSON.stringify([...blacklist]))}catch(e){}
}

function ctxToggleBlock(){
  hidePeerCtx();
  if(!ctxTgt)return;
  if(blacklist.has(ctxTgt)){
    blacklist.delete(ctxTgt);
    saveBlacklist();
    renderList();
    toast('🔓','Убран из чёрного списка','');
  } else {
    blacklist.add(ctxTgt);
    saveBlacklist();
    renderList();
    toast('🔒','Добавлен в чёрный список','Пользователь не сможет писать тебе');
  }
}

function ctxDelChat(){"""
results.append(('blacklist variable and functions', old13 in c))
if old13 in c: c = c.replace(old13, new13)

# ── 12. В renderList — показывать замок у заблокированных ────────────────────
old14 = "function mkP(id,h,p){return{id,host:h,port:p,username:'',online:true,messages:[],lastMsg:'',lastTime:'',unread:0,avatar:'',bio:''}}"
new14 = "function mkP(id,h,p){return{id,host:h,port:p,username:'',online:true,messages:[],lastMsg:'',lastTime:'',unread:0,avatar:'',bio:'',registeredAt:''}}"
results.append(('mkP with registeredAt', old14 in c))
if old14 in c: c = c.replace(old14, new14)

# ── 13. В peer list item — добавить иконку замка ─────────────────────────────
old15 = "oncontextmenu=\"showPeerCtx(event,'${id}')\">"
new15 = "oncontextmenu=\"showPeerCtx(event,'${id}')\">\n      ${blacklist.has(id)?'<span style=\"font-size:12px;margin-right:4px\" title=\"В чёрном списке\">🔒</span>':''}"
results.append(('lock icon in peer list', old15 in c))
if old15 in c: c = c.replace(old15, new15)

# ── 14. В inpArea — показывать "заблокирован" вместо поля ввода ──────────────
old16 = "function openChat(id,type){\n  cancelReply();editingMsgId=null;closeSearch();"
new16 = """function openChat(id,type){
  cancelReply();editingMsgId=null;closeSearch();
  // Update input area based on blacklist
  setTimeout(()=>{
    const inpArea=document.getElementById('inpArea');
    let blockedBar=document.getElementById('blockedBar');
    if(type==='peer'&&blacklist.has(id)){
      if(inpArea)inpArea.style.display='none';
      if(!blockedBar){
        blockedBar=document.createElement('div');
        blockedBar.id='blockedBar';
        blockedBar.style.cssText='padding:14px 20px;background:#f8f8f8;border-top:1px solid #eee;text-align:center;color:#999;font-size:13px';
        blockedBar.textContent='Вы не можете писать этому пользователю';
        inpArea?.parentNode?.insertBefore(blockedBar,inpArea);
      }
      blockedBar.style.display='block';
    } else {
      if(inpArea)inpArea.style.display='flex';
      if(blockedBar)blockedBar.style.display='none';
    }
  },50);"""
results.append(('openChat blacklist check', old16 in c))
if old16 in c: c = c.replace(old16, new16)

with open('ui/gui.py', 'w', encoding='utf-8') as f:
    f.write(c)

print()
for name, found in results:
    print(f"  {'✓' if found else '✗ НЕ НАЙДЕНО'}  {name}")
print('\nГотово!')

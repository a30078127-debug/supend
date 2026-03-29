with open('ui/gui.py', encoding='utf-8') as f:
    c = f.read()

results = []

# ── 1. ctxToggleBlock — обновлять поле ввода сразу при блокировке ────────────
old1 = """function ctxToggleBlock(){
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
}"""
new1 = """function ctxToggleBlock(){
  hidePeerCtx();
  if(!ctxTgt)return;
  if(blacklist.has(ctxTgt)){
    blacklist.delete(ctxTgt);
    saveBlacklist();
    renderList();
    // If currently viewing this chat — restore input
    if(active===ctxTgt&&activeType==='peer') updateBlockedBar(ctxTgt);
    toast('🔓','Убран из чёрного списка','');
  } else {
    blacklist.add(ctxTgt);
    saveBlacklist();
    renderList();
    // If currently viewing this chat — show blocked bar
    if(active===ctxTgt&&activeType==='peer') updateBlockedBar(ctxTgt);
    toast('🔒','Добавлен в чёрный список','');
  }
}

function updateBlockedBar(peerId){
  const inpArea=document.getElementById('inpArea');
  let bar=document.getElementById('blockedBar');
  if(blacklist.has(peerId)){
    if(inpArea)inpArea.style.display='none';
    if(!bar){
      bar=document.createElement('div');
      bar.id='blockedBar';
      bar.style.cssText='padding:14px 20px;background:#fff0f0;border-top:2px solid #ffcccc;text-align:center;color:#e53935;font-size:13px;font-weight:600';
      bar.textContent='Вы не можете писать этому пользователю';
      inpArea?.parentNode?.insertBefore(bar,inpArea);
    }
    bar.style.display='block';
  } else {
    if(inpArea)inpArea.style.display='flex';
    if(bar)bar.style.display='none';
  }
}"""
results.append(('ctxToggleBlock with instant UI update', old1 in c))
if old1 in c: c = c.replace(old1, new1)

# ── 2. openChat — использовать updateBlockedBar ───────────────────────────────
old2 = """  // Update input area based on blacklist
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
new2 = """  // Update input area based on blacklist
  setTimeout(()=>{ if(type==='peer') updateBlockedBar(id); else { const inpArea=document.getElementById('inpArea');if(inpArea)inpArea.style.display='flex';const bar=document.getElementById('blockedBar');if(bar)bar.style.display='none'; }},50);"""
results.append(('openChat uses updateBlockedBar', old2 in c))
if old2 in c: c = c.replace(old2, new2)

# ── 3. Закреплённое сообщение — pinnedBar показывать только для текущего чата ─
# updatePinnedBar already uses activeType and active correctly
# The problem is that pinnedBar stays shown when switching chats
# Fix: hide pinnedBar when chat is opened before setTimeout
old3 = "function openChat(id,type){\n  cancelReply();editingMsgId=null;closeSearch();"
new3 = """function openChat(id,type){
  cancelReply();editingMsgId=null;closeSearch();
  document.getElementById('pinnedBar').classList.remove('show'); // hide until updated"""
results.append(('hide pinnedBar on openChat', old3 in c))
if old3 in c: c = c.replace(old3, new3)

# ── 4. Ответ на сообщение — проблема в том что replyData теряется ────────────
# В group чате replyToId вызывает cancelReply() ПОСЛЕ создания m, но ДО append
# Проверим: replyToId используется в replyData ДО cancelReply — это правильно
# Проблема: в peer чате cancelReply() вызывается, но replyData уже создан — ОК
# Скорее всего проблема в mkBubble — reply-preview вставляется перед bubble
# но bubble может быть другим элементом. Проверим порядок вставки.

# На самом деле проблема может быть в том что replyBar.show остаётся
# и при следующей отправке editingMsgId проверяется первым

# Простое исправление: в cancelReply() также сбрасывать editingMsgId
old4 = "function cancelReply(){\n  replyToId=null;replyToText='';replyToName='';\n  document.getElementById('replyBar').classList.remove('show');\n}"
new4 = """function cancelReply(){
  replyToId=null;replyToText='';replyToName='';
  editingMsgId=null;
  document.getElementById('replyBar').classList.remove('show');
}"""
results.append(('cancelReply resets editingMsgId', old4 in c))
if old4 in c: c = c.replace(old4, new4)

# ── 5. В doSend — проверить что editingMsgId не мешает reply ─────────────────
# editingMsgId проверяется первым — если он установлен, то reply не работает
# Нужно очищать editingMsgId при нажатии "Ответить"
old5 = "function replyToMsg(){\n  hideMsgCtx();\n  if(!ctxMsgId||!active)return;\n  const store=activeType==='group'?groups[active]:peers[active];if(!store)return;\n  const msg=store.messages.find(m=>m.id==ctxMsgId);if(!msg)return;\n  replyToId=ctxMsgId;"
new5 = """function replyToMsg(){
  hideMsgCtx();
  if(!ctxMsgId||!active)return;
  const store=activeType==='group'?groups[active]:peers[active];if(!store)return;
  const msg=store.messages.find(m=>m.id==ctxMsgId);if(!msg)return;
  editingMsgId=null; // clear edit mode
  replyToId=ctxMsgId;"""
results.append(('replyToMsg clears editingMsgId', old5 in c))
if old5 in c: c = c.replace(old5, new5)

with open('ui/gui.py', 'w', encoding='utf-8') as f:
    f.write(c)

print()
for name, found in results:
    print(f"  {'v' if found else 'X НЕ НАЙДЕНО'}  {name}")
print('\nГотово!')

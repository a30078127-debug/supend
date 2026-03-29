with open('ui/gui.py', encoding='utf-8') as f:
    c = f.read()

results = []

# ── 1. showPeerCtx — менять стиль кнопки (красная/обычная) ──────────────────
old1 = "  const isBlocked=blacklist.has(id);\n  const btn=document.getElementById('ctxBlockBtn');\n  if(btn)btn.textContent=isBlocked?'🔓 Убрать из ЧС':'🔒 Добавить в ЧС';"
new1 = "  const isBlocked=blacklist.has(id);\n  const btn=document.getElementById('ctxBlockBtn');\n  if(btn){\n    btn.textContent=isBlocked?'🔓 Убрать из ЧС':'🔒 Добавить в ЧС';\n    btn.className=isBlocked?'ctx-item':'ctx-item danger';\n  }"
results.append(('showPeerCtx button style', old1 in c))
if old1 in c: c = c.replace(old1, new1)

# ── 2. openChat — убрать принудительное display='flex' для inpArea ───────────
# Проблема: inpArea.style.display='flex' на строке 2649 перекрывает updateBlockedBar
old2 = "  document.getElementById('chatHead').style.display='flex';\n  document.getElementById('emptyState').style.display='none';\n  document.getElementById('msgs').style.display='flex';\n  document.getElementById('inpArea').style.display='flex';"
new2 = "  document.getElementById('chatHead').style.display='flex';\n  document.getElementById('emptyState').style.display='none';\n  document.getElementById('msgs').style.display='flex';\n  // inpArea visibility is controlled by updateBlockedBar"
results.append(('openChat remove inpArea force show', old2 in c))
if old2 in c: c = c.replace(old2, new2)

# ── 3. updateBlockedBar — показывать inpArea для не заблокированных ──────────
old3 = "function updateBlockedBar(peerId){\n  const inpArea=document.getElementById('inpArea');\n  let bar=document.getElementById('blockedBar');\n  if(blacklist.has(peerId)){\n    if(inpArea)inpArea.style.display='none';\n    if(!bar){\n      bar=document.createElement('div');\n      bar.id='blockedBar';\n      bar.style.cssText='padding:14px 20px;background:#fff0f0;border-top:2px solid #ffcccc;text-align:center;color:#e53935;font-size:13px;font-weight:600';\n      bar.textContent='Вы не можете писать этому пользователю';\n      inpArea?.parentNode?.insertBefore(bar,inpArea);\n    }\n    bar.style.display='block';\n  } else {\n    if(inpArea)inpArea.style.display='flex';\n    if(bar)bar.style.display='none';\n  }\n}"
new3 = """function updateBlockedBar(peerId){
  const inpArea=document.getElementById('inpArea');
  let bar=document.getElementById('blockedBar');
  if(blacklist.has(peerId)){
    if(inpArea)inpArea.style.display='none';
    if(!bar){
      bar=document.createElement('div');
      bar.id='blockedBar';
      bar.style.cssText='padding:16px 20px;background:#fff0f0;border-top:2px solid #ffcccc;text-align:center;color:#e53935;font-size:13px;font-weight:600;flex-shrink:0';
      bar.textContent='🚫 Вы не можете писать этому пользователю';
      const chat=document.querySelector('.chat');
      if(chat)chat.appendChild(bar);
    }
    bar.style.display='block';
  } else {
    if(inpArea)inpArea.style.display='flex';
    if(bar)bar.style.display='none';
  }
}"""
results.append(('updateBlockedBar improved', old3 in c))
if old3 in c: c = c.replace(old3, new3)

# ── 4. openChat setTimeout — вызывать updateBlockedBar раньше ────────────────
old4 = "  setTimeout(()=>{ if(type==='peer') updateBlockedBar(id); else { const inpArea=document.getElementById('inpArea');if(inpArea)inpArea.style.display='flex';const bar=document.getElementById('blockedBar');if(bar)bar.style.display='none'; }},50);"
new4 = "  // Show inpArea by default, then check blacklist\n  const _ia=document.getElementById('inpArea');\n  if(_ia)_ia.style.display='flex';\n  const _bb=document.getElementById('blockedBar');\n  if(_bb)_bb.style.display='none';\n  setTimeout(()=>{ if(type==='peer') updateBlockedBar(id); else { const inpArea=document.getElementById('inpArea');if(inpArea)inpArea.style.display='flex';const bar=document.getElementById('blockedBar');if(bar)bar.style.display='none'; }},10);"
results.append(('openChat show inpArea first then check blacklist', old4 in c))
if old4 in c: c = c.replace(old4, new4)

with open('ui/gui.py', 'w', encoding='utf-8') as f:
    f.write(c)

print()
for name, found in results:
    print(f"  {'v' if found else 'X НЕ НАЙДЕНО'}  {name}")
print('\nГотово!')

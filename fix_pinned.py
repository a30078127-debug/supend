with open('ui/gui.py', encoding='utf-8') as f:
    c = f.read()

results = []

# ── 1. openChat — обновлять pinnedBar ПОСЛЕ установки active ─────────────────
old1 = "function openChat(id,type){\n  cancelReply();editingMsgId=null;closeSearch();\n  document.getElementById('pinnedBar').classList.remove('show'); // hide until updated\n  // Update input area based on blacklist\n  setTimeout(()=>{ if(type==='peer') updateBlockedBar(id); else { const inpArea=document.getElementById('inpArea');if(inpArea)inpArea.style.display='flex';const bar=document.getElementById('blockedBar');if(bar)bar.style.display='none'; }},50);\n  active=id;activeType=type||'peer';"
new1 = "function openChat(id,type){\n  cancelReply();editingMsgId=null;closeSearch();\n  document.getElementById('pinnedBar').classList.remove('show'); // hide until updated\n  active=id;activeType=type||'peer';\n  // Update input area based on blacklist\n  setTimeout(()=>{ if(type==='peer') updateBlockedBar(id); else { const inpArea=document.getElementById('inpArea');if(inpArea)inpArea.style.display='flex';const bar=document.getElementById('blockedBar');if(bar)bar.style.display='none'; }},50);\n  // Update pinned bar AFTER active is set\n  setTimeout(updatePinnedBar,30);"
results.append(('openChat update pinnedBar after active set', old1 in c))
if old1 in c: c = c.replace(old1, new1)

# ── 2. Убрать дублирующий setTimeout(updatePinnedBar) который был раньше ─────
old2 = "  setTimeout(updatePinnedBar,50);\n  // Update pinned bar AFTER active is set\n  setTimeout(updatePinnedBar,30);"
new2 = "  // Update pinned bar AFTER active is set\n  setTimeout(updatePinnedBar,30);"
results.append(('remove duplicate updatePinnedBar timeout', old2 in c))
if old2 in c: c = c.replace(old2, new2)

# ── 3. Убрать старый setTimeout(updatePinnedBar,50) в области рендера сообщений
old3 = "  document.getElementById('msgs').innerHTML='<div class=\"date-sep\">СЕГОДНЯ</div>';\n  setTimeout(updatePinnedBar,50);"
new3 = "  document.getElementById('msgs').innerHTML='<div class=\"date-sep\">СЕГОДНЯ</div>';"
results.append(('remove old updatePinnedBar timeout from render', old3 in c))
if old3 in c: c = c.replace(old3, new3)

# ── 4. В active=id строке убрать дубль (active уже устанавливается выше) ─────
old4 = "  active=id;activeType=type||'peer';\n  const store=type==='group'?groups[id]:peers[id];if(!store)return;"
new4 = "  const store=type==='group'?groups[id]:peers[id];if(!store)return;"
results.append(('remove duplicate active=id assignment', old4 in c))
if old4 in c: c = c.replace(old4, new4)

# ── 5. __MSGACT__ pin для peer — правильно находить peer ─────────────────────
old5 = "      } else if(d.type==='pin'){\n        const g=Object.values(groups).find(g=>g.members&&g.members[id]);\n        if(g){g.pinnedMsgId=d.msgId;g.pinnedMsgText=d.text;updatePinnedBar();}\n        else if(peers[id]){peers[id].pinnedMsgId=d.msgId;peers[id].pinnedMsgText=d.text;updatePinnedBar();}\n        toast('📌','Сообщение закреплено','');\n      } else if(d.type==='unpin'){\n        const g=Object.values(groups).find(g=>g.members&&g.members[id]);\n        if(g){g.pinnedMsgId=null;g.pinnedMsgText='';updatePinnedBar();}\n        else if(peers[id]){peers[id].pinnedMsgId=null;peers[id].pinnedMsgText='';updatePinnedBar();}\n        toast('','Сообщение откреплено','');"
new5 = """      } else if(d.type==='pin'){
        const g=Object.values(groups).find(g=>g.members&&g.members[id]);
        if(g){g.pinnedMsgId=d.msgId;g.pinnedMsgText=d.text;}
        else if(peers[id]){peers[id].pinnedMsgId=d.msgId;peers[id].pinnedMsgText=d.text;}
        // Only update bar if this is the active chat
        const pinnedStore=g||peers[id];
        if((g&&active===Object.keys(groups).find(k=>groups[k]===g))||(peers[id]&&active===id)) updatePinnedBar();
        toast('📌','Сообщение закреплено','');
      } else if(d.type==='unpin'){
        const g2=Object.values(groups).find(g=>g.members&&g.members[id]);
        if(g2){g2.pinnedMsgId=null;g2.pinnedMsgText='';}
        else if(peers[id]){peers[id].pinnedMsgId=null;peers[id].pinnedMsgText='';}
        if(active===id||(g2&&active===Object.keys(groups).find(k=>groups[k]===g2))) updatePinnedBar();
        toast('','Сообщение откреплено','');"""
results.append(('__MSGACT__ pin/unpin update bar only for active chat', old5 in c))
if old5 in c: c = c.replace(old5, new5)

with open('ui/gui.py', 'w', encoding='utf-8') as f:
    f.write(c)

print()
for name, found in results:
    print(f"  {'v' if found else 'X НЕ НАЙДЕНО'}  {name}")
print('\nГотово!')

import re

with open('ui/gui.py', encoding='utf-8') as f:
    c = f.read()

results = []

# ── 1. Иконка кошелька (заменяем SVG на иконку кошелька из картинки) ─────────
old1 = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><path d="M20 12V22H4V12"/><path d="M22 7H2v5h20V7z"/><path d="M12 22V7"/><path d="M12 7H7.5a2.5 2.5 0 0 1 0-5C11 2 12 7 12 7z"/><path d="M12 7h4.5a2.5 2.5 0 0 0 0-5C13 2 12 7 12 7z"/></svg>'
new1 = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="5" width="20" height="14" rx="3"/><path d="M16 12a1 1 0 1 0 2 0 1 1 0 0 0-2 0z" fill="white" stroke="none"/><path d="M2 10h20"/></svg>'
results.append(('wallet icon', old1 in c))
if old1 in c: c = c.replace(old1, new1)

# ── 2. Маркетплейс кнопку опускаем на уровень с кошельком (bottom:140px→bottom:76px, убираем отдельный div) ─────
old2 = '    <!-- Market button -->\n    <div style="position:absolute;right:16px;bottom:200px;z-index:51">\n      <button onclick="openMarket()" title="Маркетплейс" style="width:52px;height:52px;border-radius:50%;background:linear-gradient(135deg,#f6d365,#fda085);border:none;display:flex;align-items:center;justify-content:center;cursor:pointer;box-shadow:0 4px 16px rgba(246,211,101,.4);font-size:22px;transition:transform .2s" onmouseover="this.style.transform=\'scale(1.08)\'" onmouseout="this.style.transform=\'scale(1)\'">🏪</button>\n    </div>'
new2 = '    <!-- Market button -->\n    <div style="position:absolute;right:76px;bottom:76px;z-index:51">\n      <button onclick="openMarket()" title="Маркетплейс" style="width:52px;height:52px;border-radius:50%;background:linear-gradient(135deg,#f6d365,#fda085);border:none;display:flex;align-items:center;justify-content:center;cursor:pointer;box-shadow:0 4px 16px rgba(246,211,101,.4);font-size:22px;transition:transform .2s" onmouseover="this.style.transform=\'scale(1.08)\'" onmouseout="this.style.transform=\'scale(1)\'">🏪</button>\n    </div>'
results.append(('market button position', old2 in c))
if old2 in c: c = c.replace(old2, new2)

# ── 3. Группа — создатель становится owner, добавляем owner поле ──────────────
old3 = "  groups[gid]={id:gid,name,avatar:groupAvData,members,messages:[],lastMsg:'',lastTime:'',unread:0,isAdmin:true};"
new3 = "  groups[gid]={id:gid,name,avatar:groupAvData,members,messages:[],lastMsg:'',lastTime:'',unread:0,isAdmin:true,owner:myId};"
results.append(('group owner field', old3 in c))
if old3 in c: c = c.replace(old3, new3)

# ── 4. При создании группы creator получает role:'owner' ──────────────────────
old4 = "  members[myId]={username:myU,avatar:myAv,role:'admin'};"
new4 = "  members[myId]={username:myU,avatar:myAv,role:'owner'};"
results.append(('creator role owner', old4 in c))
if old4 in c: c = c.replace(old4, new4)

# ── 5. Контекстное меню участника группы (правая кнопка мыши) ────────────────
old5 = "    if(!isMe){div.style.cursor='pointer';div.onclick=()=>{closeM('groupInfoModal');if(peers[pid])openChat(pid,'peer')}}"
new5 = """    if(!isMe){
      div.style.cursor='pointer';
      div.onclick=()=>{closeM('groupInfoModal');if(peers[pid])openChat(pid,'peer')};
      const g2=groups[gid];
      const amOwner=g2&&g2.owner===myId;
      const amAdmin=g2&&(g2.owner===myId||(g2.members[myId]&&g2.members[myId].role==='admin'));
      if(amAdmin){
        div.oncontextmenu=e=>{
          e.preventDefault();e.stopPropagation();
          showMemberCtx(e,pid,gid,amOwner,m);
        };
      }
    }"""
results.append(('member context menu handler', old5 in c))
if old5 in c: c = c.replace(old5, new5)

# ── 6. Добавить HTML контекстного меню участника и модала прав ────────────────
old6 = '<div class="modal-overlay" id="groupInfoModal">'
new6 = '''<!-- Member context menu -->
<div id="memberCtxMenu" style="display:none;position:fixed;z-index:999;background:#1e1e2e;border:1px solid rgba(255,255,255,.12);border-radius:12px;padding:6px;box-shadow:0 8px 32px rgba(0,0,0,.5);min-width:180px">
  <div id="memberCtxKick" onclick="memberCtxKick()" style="padding:10px 14px;color:#ff5555;font-size:13px;font-weight:600;cursor:pointer;border-radius:8px;display:flex;align-items:center;gap:8px" onmouseover="this.style.background='rgba(255,85,85,.1)'" onmouseout="this.style.background='none'">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><line x1="17" y1="11" x2="23" y2="11"/></svg>
    Удалить из группы
  </div>
  <div id="memberCtxAdmin" onclick="memberCtxMakeAdmin()" style="padding:10px 14px;color:#1ABC9C;font-size:13px;font-weight:600;cursor:pointer;border-radius:8px;display:flex;align-items:center;gap:8px" onmouseover="this.style.background='rgba(26,188,156,.1)'" onmouseout="this.style.background='none'">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
    Назначить администратора
  </div>
</div>

<!-- Admin rights modal -->
<div class="modal-overlay" id="adminRightsModal">
  <div class="modal-box" style="max-width:400px">
    <button class="modal-close" onclick="closeM('adminRightsModal')">×</button>
    <div class="modal-title">Права администратора</div>
    <div style="padding:4px 0 16px;color:rgba(255,255,255,.5);font-size:13px">Выберите что может делать этот администратор</div>
    <div style="display:flex;flex-direction:column;gap:12px;margin-bottom:24px">
      <label style="display:flex;align-items:center;gap:12px;cursor:pointer">
        <input type="checkbox" id="ar_avatar" checked style="width:18px;height:18px;accent-color:#1ABC9C">
        <span style="color:#fff;font-size:14px">Менять аватарку группы</span>
      </label>
      <label style="display:flex;align-items:center;gap:12px;cursor:pointer">
        <input type="checkbox" id="ar_name" checked style="width:18px;height:18px;accent-color:#1ABC9C">
        <span style="color:#fff;font-size:14px">Менять название и описание</span>
      </label>
      <label style="display:flex;align-items:center;gap:12px;cursor:pointer">
        <input type="checkbox" id="ar_add" checked style="width:18px;height:18px;accent-color:#1ABC9C">
        <span style="color:#fff;font-size:14px">Добавлять участников</span>
      </label>
      <label style="display:flex;align-items:center;gap:12px;cursor:pointer">
        <input type="checkbox" id="ar_admin" style="width:18px;height:18px;accent-color:#1ABC9C">
        <span style="color:#fff;font-size:14px">Назначать администраторов</span>
      </label>
    </div>
    <button onclick="confirmMakeAdmin()" style="width:100%;padding:12px;background:#1ABC9C;border:none;border-radius:12px;color:#fff;font-size:14px;font-weight:700;cursor:pointer">Назначить</button>
  </div>
</div>

<div class="modal-overlay" id="groupInfoModal">'''
results.append(('member ctx html + admin rights modal', old6 in c))
if old6 in c: c = c.replace(old6, new6)

# ── 7. Добавить JS функции для контекстного меню участника ───────────────────
old7 = "// ── Emoji ─────────────────────────────────────"
new7 = """// ── Member context menu ──────────────────────
let memberCtxPid=null, memberCtxGid=null;

function showMemberCtx(e, pid, gid, isOwner, member){
  memberCtxPid=pid; memberCtxGid=gid;
  const menu=document.getElementById('memberCtxMenu');
  // Show/hide admin button based on owner status
  document.getElementById('memberCtxAdmin').style.display=isOwner?'flex':'none';
  // Update admin button text based on current role
  const isAdmin=member.role==='admin'||member.role==='owner';
  document.getElementById('memberCtxAdmin').innerHTML=isAdmin
    ? '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg> Снять администратора'
    : '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg> Назначить администратора';
  menu.style.display='block';
  menu.style.left=Math.min(e.clientX, window.innerWidth-200)+'px';
  menu.style.top=Math.min(e.clientY, window.innerHeight-120)+'px';
  setTimeout(()=>document.addEventListener('click',()=>menu.style.display='none',{once:true}),50);
}

function memberCtxKick(){
  const menu=document.getElementById('memberCtxMenu');
  menu.style.display='none';
  if(!memberCtxPid||!memberCtxGid)return;
  const g=groups[memberCtxGid];if(!g)return;
  const name=g.members[memberCtxPid]?.username||shortId(memberCtxPid);
  if(!confirm('Удалить @'+name+' из группы?'))return;
  delete g.members[memberCtxPid];
  // Notify kicked member
  if(peers[memberCtxPid])cmd({cmd:'send',peer_id:memberCtxPid,text:GP+JSON.stringify({type:'kick',gid:memberCtxGid,by:myId})});
  openGroupInfo(memberCtxGid);
  toast('👋','Участник удалён','@'+name);
}

function memberCtxMakeAdmin(){
  const menu=document.getElementById('memberCtxMenu');
  menu.style.display='none';
  if(!memberCtxPid||!memberCtxGid)return;
  const g=groups[memberCtxGid];if(!g)return;
  const m=g.members[memberCtxPid];if(!m)return;
  // If already admin — remove
  if(m.role==='admin'){
    m.role='member';
    openGroupInfo(memberCtxGid);
    toast('✅','Права сняты','@'+m.username);
    return;
  }
  // Show rights modal
  document.getElementById('adminRightsModal').classList.add('show');
}

function confirmMakeAdmin(){
  if(!memberCtxPid||!memberCtxGid)return;
  const g=groups[memberCtxGid];if(!g)return;
  const m=g.members[memberCtxPid];if(!m)return;
  m.role='admin';
  m.adminRights={
    avatar:document.getElementById('ar_avatar').checked,
    name:document.getElementById('ar_name').checked,
    add:document.getElementById('ar_add').checked,
    admin:document.getElementById('ar_admin').checked,
  };
  closeM('adminRightsModal');
  openGroupInfo(memberCtxGid);
  toast('🛡️','Администратор назначен','@'+m.username);
}

// ── Emoji ─────────────────────────────────────"""
results.append(('member ctx js functions', old7 in c))
if old7 in c: c = c.replace(old7, new7)

# ── 8. Роль owner отображается как Владелец ───────────────────────────────────
old8 = "${m.role==='admin'?'Администратор':'Участник'}"
new8 = "${m.role==='owner'?'Владелец':m.role==='admin'?'Администратор':'Участник'}"
results.append(('owner role display', old8 in c))
if old8 in c: c = c.replace(old8, new8)

with open('ui/gui.py', 'w', encoding='utf-8') as f:
    f.write(c)

print()
for name, found in results:
    print(f"  {'✓' if found else '✗ НЕ НАЙДЕНО'}  {name}")
print('\nГотово!')

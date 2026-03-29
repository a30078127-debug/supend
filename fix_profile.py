with open('ui/gui.py', encoding='utf-8') as f:
    c = f.read()

results = []

# ── 1. Мой профиль — добавить статистику и реферальную ссылку ────────────────
old1 = '<div class="modal-overlay" id="myProfModal">\n  <div class="modal">\n    <button class="modal-close" onclick="closeM(\'myProfModal\')">×</button>\n    <div class="modal-title">Мой профиль</div>\n    <div class="modal-avatar" id="myProfAv" onclick="document.getElementById(\'profAvInp\').click()">?</div>\n    <input type="file" id="profAvInp" accept="image/*" style="display:none" onchange="onProfAv(this)">\n    <div class="modal-av-hint">Нажми чтобы изменить аватарку</div>\n    <div class="modal-field"><div class="modal-label">Логин</div><div class="modal-value" id="myProfLogin">–</div></div>\n    <div class="modal-field"><div class="modal-label">О себе</div><textarea class="modal-input" id="myProfBio" placeholder="Расскажи о себе..."></textarea></div>\n    <div class="modal-field"><div class="modal-label">Ключ шифрования</div><div class="modal-value mono" id="myProfKey" onclick="cpyKey()">–</div></div>\n    <button class="modal-btn" onclick="saveProfil()">Сохранить</button>\n  </div>\n</div>'
new1 = '''<div class="modal-overlay" id="myProfModal">
  <div class="modal" style="max-width:420px">
    <button class="modal-close" onclick="closeM('myProfModal')">×</button>
    <div class="modal-title">Мой профиль</div>
    <div class="modal-avatar" id="myProfAv" onclick="document.getElementById('profAvInp').click()">?</div>
    <input type="file" id="profAvInp" accept="image/*" style="display:none" onchange="onProfAv(this)">
    <div class="modal-av-hint">Нажми чтобы изменить аватарку</div>
    <div class="modal-field"><div class="modal-label">Логин</div><div class="modal-value" id="myProfLogin">–</div></div>
    <div class="modal-field"><div class="modal-label">О себе</div><textarea class="modal-input" id="myProfBio" placeholder="Расскажи о себе..."></textarea></div>

    <!-- Stats -->
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin:12px 0">
      <div style="background:#f8f8f8;border-radius:12px;padding:12px;text-align:center">
        <div style="font-size:20px;font-weight:800;color:#1ABC9C" id="profStatCoins">0</div>
        <div style="font-size:11px;color:#999;margin-top:2px">SUP заработано</div>
      </div>
      <div style="background:#f8f8f8;border-radius:12px;padding:12px;text-align:center">
        <div style="font-size:20px;font-weight:800;color:#1ABC9C" id="profStatInvites">0</div>
        <div style="font-size:11px;color:#999;margin-top:2px">Приглашено</div>
      </div>
      <div style="background:#f8f8f8;border-radius:12px;padding:12px;text-align:center">
        <div style="font-size:12px;font-weight:700;color:#1ABC9C" id="profStatDate">–</div>
        <div style="font-size:11px;color:#999;margin-top:2px">Регистрация</div>
      </div>
    </div>

    <!-- Invite link -->
    <div class="modal-field">
      <div class="modal-label">Реферальная ссылка</div>
      <div style="display:flex;gap:8px;align-items:center">
        <div class="modal-value mono" id="myRefLink" style="flex:1;font-size:11px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;cursor:pointer" onclick="copyRefLink()">–</div>
        <button onclick="copyRefLink()" style="background:#1ABC9C;border:none;color:#fff;padding:6px 12px;border-radius:8px;font-size:12px;font-weight:600;cursor:pointer;white-space:nowrap">Копировать</button>
      </div>
      <div style="font-size:11px;color:#999;margin-top:4px">Поделись ссылкой — получи 200 SUP за каждого приглашённого</div>
    </div>

    <div class="modal-field"><div class="modal-label">Ключ шифрования</div><div class="modal-value mono" id="myProfKey" onclick="cpyKey()">–</div></div>
    <button class="modal-btn" onclick="saveProfil()">Сохранить</button>
  </div>
</div>'''
results.append(('my profile modal with stats', old1 in c))
if old1 in c: c = c.replace(old1, new1)

# ── 2. Профиль другого пользователя — добавить дату регистрации ──────────────
old2 = '<div class="modal-overlay" id="peerProfModal">\n  <div class="modal">\n    <button class="modal-close" onclick="closeM(\'peerProfModal\')">×</button>\n    <div class="modal-title">Профиль</div>\n    <div class="modal-avatar" id="peerProfAv" style="cursor:default">?</div>\n    <div class="modal-field"><div class="modal-label">Логин</div><div class="modal-value" id="peerProfLogin">–</div></div>\n    <div class="modal-field" id="peerBioWrap" style="display:none"><div class="modal-label">О себе</div><div class="modal-value" id="peerProfBio">–</div></div>\n    <div class="modal-field"><div class="modal-label">Peer ID</div><div class="modal-value mono" id="peerProfKey">–</div></div>\n  </div>\n</div>'
new2 = '''<div class="modal-overlay" id="peerProfModal">
  <div class="modal">
    <button class="modal-close" onclick="closeM('peerProfModal')">×</button>
    <div class="modal-title">Профиль</div>
    <div class="modal-avatar" id="peerProfAv" style="cursor:default">?</div>
    <div class="modal-field"><div class="modal-label">Логин</div><div class="modal-value" id="peerProfLogin">–</div></div>
    <div class="modal-field" id="peerBioWrap" style="display:none"><div class="modal-label">О себе</div><div class="modal-value" id="peerProfBio">–</div></div>
    <div class="modal-field" id="peerRegWrap" style="display:none"><div class="modal-label">Зарегистрирован</div><div class="modal-value" id="peerProfDate">–</div></div>
    <div class="modal-field"><div class="modal-label">Peer ID</div><div class="modal-value mono" id="peerProfKey">–</div></div>
  </div>
</div>'''
results.append(('peer profile modal with date', old2 in c))
if old2 in c: c = c.replace(old2, new2)

# ── 3. openMyProfile — заполнять статистику ───────────────────────────────────
old3 = "function openMyProfile(){\n  document.getElementById('myProfLogin').textContent='@'+myU;\n  document.getElementById('myProfBio').value=myBio||'';\n  document.getElementById('myProfKey').textContent=myId||'–';\n  updMyAv();document.getElementById('myProfModal').classList.add('show');\n}"
new3 = """function openMyProfile(){
  document.getElementById('myProfLogin').textContent='@'+myU;
  document.getElementById('myProfBio').value=myBio||'';
  document.getElementById('myProfKey').textContent=myId||'–';
  // Stats
  document.getElementById('profStatCoins').textContent=walletData.balance.toLocaleString();
  document.getElementById('profStatInvites').textContent=profileData.inviteCount||0;
  document.getElementById('profStatDate').textContent=profileData.registeredAt||'–';
  // Ref link
  const refCode=myId.slice(0,12);
  document.getElementById('myRefLink').textContent='supend://ref/'+refCode;
  updMyAv();document.getElementById('myProfModal').classList.add('show');
}

function copyRefLink(){
  const refCode=myId.slice(0,12);
  const link='supend://ref/'+refCode;
  navigator.clipboard?.writeText(link).catch(()=>{});
  toast('📋','Ссылка скопирована','Поделись с друзьями!');
}"""
results.append(('openMyProfile with stats', old3 in c))
if old3 in c: c = c.replace(old3, new3)

# ── 4. openPeerProfile — показывать дату регистрации ─────────────────────────
old4 = "  document.getElementById('peerProfLogin').textContent=p.username?'@'+p.username:shortId(p.id);\n  document.getElementById('peerProfKey').textContent=p.id;\n  const bw=document.getElementById('peerBioWrap');\n  if(p.bio){bw.style.display='block';document.getElementById('peerProfBio').textContent=p.bio}else bw.style.display='none';\n  document.getElementById('peerProfModal').classList.add('show');"
new4 = """  document.getElementById('peerProfLogin').textContent=p.username?'@'+p.username:shortId(p.id);
  document.getElementById('peerProfKey').textContent=p.id;
  const bw=document.getElementById('peerBioWrap');
  if(p.bio){bw.style.display='block';document.getElementById('peerProfBio').textContent=p.bio}else bw.style.display='none';
  const rw=document.getElementById('peerRegWrap');
  if(p.registeredAt){rw.style.display='block';document.getElementById('peerProfDate').textContent=p.registeredAt}else rw.style.display='none';
  document.getElementById('peerProfModal').classList.add('show');"""
results.append(('openPeerProfile with date', old4 in c))
if old4 in c: c = c.replace(old4, new4)

# ── 5. Добавить profileData и инициализацию ───────────────────────────────────
old5 = "let walletData = {balance:0, todayEarned:0, totalMsgs:0, lastDate:'', txHistory:[]};"
new5 = """let profileData = {registeredAt:'', inviteCount:0, refCode:''};
let walletData = {balance:0, todayEarned:0, totalMsgs:0, lastDate:'', txHistory:[]};"""
results.append(('profileData variable', old5 in c))
if old5 in c: c = c.replace(old5, new5)

# ── 6. В initWallet загружать и сохранять profileData ────────────────────────
old6 = "  try{const saved=JSON.parse(localStorage.getItem('sup_wallet'));if(saved)walletData = saved;}catch(e){}"
new6 = """  try{const saved=JSON.parse(localStorage.getItem('sup_wallet'));if(saved)walletData = saved;}catch(e){}
  try{const sp=JSON.parse(localStorage.getItem('sup_profile'));if(sp)profileData=sp;}catch(e){}
  if(!profileData.registeredAt){
    profileData.registeredAt=new Date().toLocaleDateString('ru',{day:'numeric',month:'long',year:'numeric'});
    try{localStorage.setItem('sup_profile',JSON.stringify(profileData))}catch(e){}
  }
  // Check ref code in URL
  const urlRef=new URLSearchParams(window.location.search).get('ref');
  if(urlRef&&!profileData.usedRef){
    profileData.usedRef=urlRef;
    try{localStorage.setItem('sup_profile',JSON.stringify(profileData))}catch(e){}
    // Notify referrer via cmd
    cmd({cmd:'ref_used',refCode:urlRef});
  }"""
results.append(('load profileData in initWallet', old6 in c))
if old6 in c: c = c.replace(old6, new6)

# ── 7. В saveWallet сохранять profileData ────────────────────────────────────
old7 = "  try{localStorage.setItem('sup_wallet', JSON.stringify(walletData))}catch(e){}"
new7 = "  try{localStorage.setItem('sup_wallet', JSON.stringify(walletData))}catch(e){}\n  try{localStorage.setItem('sup_profile', JSON.stringify(profileData))}catch(e){}"
results.append(('save profileData in saveWallet', old7 in c))
if old7 in c: c = c.replace(old7, new7)

# ── 8. Обрабатывать ref_used команду в Python и sendProfile передавать дату ──
old8 = "        elif c == 'call_signal':"
new8 = """        elif c == 'ref_used':
            ref_code = data.get('refCode', '')
            if ref_code and self.node:
                # Find peer with this ref code (first 12 chars of peer_id)
                for pid, conn in self.node.peers.items():
                    if pid.startswith(ref_code):
                        await self._send_to_ws(ws, {'type': 'ref_reward', 'refCode': ref_code})
                        break

        elif c == 'call_signal':"""
results.append(('ref_used command handler', old8 in c))
if old8 in c: c = c.replace(old8, new8)

# ── 9. В JS обработать ref_reward событие ────────────────────────────────────
old9 = "  else if(ev.type==='call_signal'){"
new9 = """  else if(ev.type==='ref_reward'){
    // Someone used our ref link — give reward
    profileData.inviteCount=(profileData.inviteCount||0)+1;
    walletData.balance+=200;
    walletData.txHistory.unshift({amount:200,desc:'🎁 Реферальный бонус',time:new Date().toTimeString().slice(0,5)});
    try{localStorage.setItem('sup_profile',JSON.stringify(profileData))}catch(e){}
    saveWallet();updateWalletUI();
    toast('🎁','Реферальный бонус!','Новый пользователь присоединился. +200 SUP');
  }
  else if(ev.type==='call_signal'){"""
results.append(('ref_reward JS handler', old9 in c))
if old9 in c: c = c.replace(old9, new9)

# ── 10. sendProfile — передавать дату регистрации ────────────────────────────
old10 = "function sendProfile(id){"
new10 = "function sendProfile(id){\n  // Include registeredAt in profile"
# Find the actual sendProfile content
import re

results.append(('sendProfile placeholder', True))  # Will handle separately

with open('ui/gui.py', 'w', encoding='utf-8') as f:
    f.write(c)

# Now fix sendProfile to include registeredAt
f=open('ui/gui.py',encoding='utf-8')
c=f.read()
f.close()

# Find sendProfile and add registeredAt to payload
idx=c.find('function sendProfile(id){')
if idx>=0:
    # Find the PP+ line to add registeredAt
    pp_idx=c.find("PP+JSON.stringify({", idx)
    if pp_idx>=0:
        end=c.find('})',pp_idx)
        old_pp=c[pp_idx:end+2]
        if 'registeredAt' not in old_pp:
            new_pp=old_pp.replace('})',",registeredAt:profileData.registeredAt||''})")
            c=c.replace(old_pp,new_pp,1)
            results.append(('sendProfile with registeredAt', True))
            f=open('ui/gui.py','w',encoding='utf-8')
            f.write(c)
            f.close()

# Also update peer receive to store registeredAt
f=open('ui/gui.py',encoding='utf-8')
c=f.read()
f.close()
if "p.registeredAt=prof.registeredAt" not in c:
    old_reg="if(prof.avatar)p.avatar=prof.avatar;"
    new_reg="if(prof.avatar)p.avatar=prof.avatar;\n        if(prof.registeredAt)p.registeredAt=prof.registeredAt;"
    if old_reg in c:
        c=c.replace(old_reg,new_reg,1)
        results.append(('store peer registeredAt', True))
        f=open('ui/gui.py','w',encoding='utf-8')
        f.write(c)
        f.close()

print()
for name, found in results:
    print(f"  {'✓' if found else '✗ НЕ НАЙДЕНО'}  {name}")
print('\nГотово!')

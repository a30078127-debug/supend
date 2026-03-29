with open('ui/gui.py', encoding='utf-8') as f:
    c = f.read()

results = []

# ── 1. Wallet button — добавляем всплывающее меню вместо прямого открытия ────
old1 = '    <!-- Wallet button -->\n    <div style="position:absolute;right:16px;bottom:76px;z-index:50">\n      <button class="wallet-btn" onclick="openWallet()" title="SUP Кошелёк">\n        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="5" width="20" height="14" rx="3"/><path d="M16 12a1 1 0 1 0 2 0 1 1 0 0 0-2 0z" fill="white" stroke="none"/><path d="M2 10h20"/></svg>\n      </button>\n    </div>'
new1 = '''    <!-- Wallet button -->
    <div style="position:absolute;right:16px;bottom:76px;z-index:50">
      <div id="walletMenuPop" style="display:none;position:absolute;bottom:60px;right:0;background:#1a1a2e;border:1px solid rgba(255,255,255,.12);border-radius:14px;padding:6px;box-shadow:0 8px 32px rgba(0,0,0,.6);min-width:190px">
        <div onclick="openWallet();hideWalletMenu()" style="padding:11px 14px;color:#fff;font-size:13px;font-weight:600;cursor:pointer;border-radius:8px;display:flex;align-items:center;gap:10px" onmouseover="this.style.background='rgba(255,255,255,.08)'" onmouseout="this.style.background='none'">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#1ABC9C" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="5" width="20" height="14" rx="3"/><path d="M16 12a1 1 0 1 0 2 0 1 1 0 0 0-2 0z" fill="#1ABC9C" stroke="none"/><path d="M2 10h20"/></svg>
          Открыть кошелёк
        </div>
        <div onclick="openExchange();hideWalletMenu()" style="padding:11px 14px;color:#fff;font-size:13px;font-weight:600;cursor:pointer;border-radius:8px;display:flex;align-items:center;gap:10px" onmouseover="this.style.background='rgba(255,255,255,.08)'" onmouseout="this.style.background='none'">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#f0b90b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 3H5a2 2 0 0 0-2 2v3"/><path d="M21 8V5a2 2 0 0 0-2-2h-3"/><path d="M3 16v3a2 2 0 0 0 2 2h3"/><path d="M16 21h3a2 2 0 0 0 2-2v-3"/></svg>
          P2P Обменник
        </div>
      </div>
      <button class="wallet-btn" onclick="toggleWalletMenu()" title="SUP Кошелёк">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="5" width="20" height="14" rx="3"/><path d="M16 12a1 1 0 1 0 2 0 1 1 0 0 0-2 0z" fill="white" stroke="none"/><path d="M2 10h20"/></svg>
      </button>
    </div>'''
results.append(('wallet menu popup', old1 in c))
if old1 in c: c = c.replace(old1, new1)

# ── 2. Добавить HTML страницы обменника перед закрытием body ─────────────────
old2 = '</body>\n</html>'
new2 = '''<!-- P2P Exchange Page -->
<div id="exchangePage" style="display:none;position:fixed;inset:0;z-index:150;background:#0b0e11;flex-direction:column;overflow:hidden">

  <!-- Header -->
  <div style="background:#0b0e11;border-bottom:1px solid #1e2329;padding:0 24px;height:56px;display:flex;align-items:center;justify-content:space-between;flex-shrink:0">
    <div style="display:flex;align-items:center;gap:16px">
      <button onclick="closeExchange()" style="background:none;border:none;color:#848e9c;cursor:pointer;display:flex;align-items:center;gap:6px;font-size:13px;font-weight:500;padding:6px 0" onmouseover="this.style.color='#fff'" onmouseout="this.style.color='#848e9c'">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>
        Назад
      </button>
      <div style="width:1px;height:20px;background:#1e2329"></div>
      <div style="font-size:16px;font-weight:700;color:#fff">P2P Обменник</div>
      <div style="background:#f0b90b;color:#000;font-size:10px;font-weight:800;padding:2px 7px;border-radius:4px;letter-spacing:.05em">SUP</div>
    </div>
    <button onclick="showCreateOrder()" style="background:#f0b90b;border:none;color:#000;font-size:13px;font-weight:700;padding:8px 18px;border-radius:8px;cursor:pointer;transition:opacity .2s" onmouseover="this.style.opacity='.85'" onmouseout="this.style.opacity='1'">+ Создать ордер</button>
  </div>

  <!-- Tabs -->
  <div style="background:#0b0e11;border-bottom:1px solid #1e2329;padding:0 24px;display:flex;align-items:center;gap:0;flex-shrink:0">
    <button id="tabBuy" onclick="switchExTab('buy')" style="padding:14px 20px;background:none;border:none;border-bottom:2px solid #f0b90b;color:#f0b90b;font-size:14px;font-weight:600;cursor:pointer;font-family:'Inter',sans-serif">Купить SUP</button>
    <button id="tabSell" onclick="switchExTab('sell')" style="padding:14px 20px;background:none;border:none;border-bottom:2px solid transparent;color:#848e9c;font-size:14px;font-weight:600;cursor:pointer;font-family:'Inter',sans-serif">Продать SUP</button>
    <button id="tabMy" onclick="switchExTab('my')" style="padding:14px 20px;background:none;border:none;border-bottom:2px solid transparent;color:#848e9c;font-size:14px;font-weight:600;cursor:pointer;font-family:'Inter',sans-serif">Мои ордера</button>
  </div>

  <!-- Orders table header -->
  <div style="padding:0 24px;background:#0b0e11;flex-shrink:0">
    <div style="display:grid;grid-template-columns:2fr 1.5fr 1.5fr 2fr 1fr;gap:12px;padding:12px 0;border-bottom:1px solid #1e2329">
      <div style="font-size:12px;color:#848e9c;font-weight:500">Продавец</div>
      <div style="font-size:12px;color:#848e9c;font-weight:500">Цена</div>
      <div style="font-size:12px;color:#848e9c;font-weight:500">Доступно</div>
      <div style="font-size:12px;color:#848e9c;font-weight:500">Способ оплаты</div>
      <div style="font-size:12px;color:#848e9c;font-weight:500"></div>
    </div>
  </div>

  <!-- Orders list -->
  <div id="exchangeOrdersList" style="flex:1;overflow-y:auto;padding:0 24px">
    <div id="exchangeEmpty" style="text-align:center;padding:60px 20px;color:#848e9c">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="margin-bottom:12px;opacity:.4"><rect x="2" y="5" width="20" height="14" rx="3"/><path d="M2 10h20"/></svg>
      <div style="font-size:14px">Ордеров пока нет</div>
      <div style="font-size:12px;margin-top:4px;opacity:.6">Будьте первым — создайте ордер</div>
    </div>
  </div>
</div>

<!-- Create Order Modal -->
<div id="createOrderModal" style="display:none;position:fixed;inset:0;z-index:200;background:rgba(0,0,0,.7);align-items:center;justify-content:center">
  <div style="background:#161a1e;border:1px solid #1e2329;border-radius:16px;padding:28px;width:100%;max-width:420px;max-height:90vh;overflow-y:auto">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:24px">
      <div style="font-size:18px;font-weight:700;color:#fff">Создать ордер на продажу</div>
      <button onclick="hideCreateOrder()" style="background:rgba(255,255,255,.08);border:none;color:#848e9c;width:32px;height:32px;border-radius:8px;cursor:pointer;font-size:18px;display:flex;align-items:center;justify-content:center">×</button>
    </div>

    <div style="margin-bottom:16px">
      <div style="font-size:12px;color:#848e9c;margin-bottom:6px;font-weight:500">КОЛИЧЕСТВО SUP</div>
      <div style="position:relative">
        <input id="orderAmount" type="number" placeholder="Например: 1000" style="width:100%;background:#0b0e11;border:1px solid #2b3139;border-radius:8px;padding:12px 60px 12px 14px;color:#fff;font-size:14px;font-family:'Inter',sans-serif;box-sizing:border-box;outline:none" onfocus="this.style.borderColor='#f0b90b'" onblur="this.style.borderColor='#2b3139'">
        <span style="position:absolute;right:14px;top:50%;transform:translateY(-50%);color:#848e9c;font-size:13px;font-weight:600">SUP</span>
      </div>
    </div>

    <div style="margin-bottom:16px">
      <div style="font-size:12px;color:#848e9c;margin-bottom:6px;font-weight:500">ЦЕНА (РУБ)</div>
      <div style="position:relative">
        <input id="orderPrice" type="number" placeholder="Например: 100" style="width:100%;background:#0b0e11;border:1px solid #2b3139;border-radius:8px;padding:12px 60px 12px 14px;color:#fff;font-size:14px;font-family:'Inter',sans-serif;box-sizing:border-box;outline:none" onfocus="this.style.borderColor='#f0b90b'" onblur="this.style.borderColor='#2b3139'">
        <span style="position:absolute;right:14px;top:50%;transform:translateY(-50%);color:#848e9c;font-size:13px;font-weight:600">₽</span>
      </div>
    </div>

    <div style="margin-bottom:16px">
      <div style="font-size:12px;color:#848e9c;margin-bottom:6px;font-weight:500">СПОСОБ ОПЛАТЫ</div>
      <select id="orderBank" onchange="onBankChange()" style="width:100%;background:#0b0e11;border:1px solid #2b3139;border-radius:8px;padding:12px 14px;color:#fff;font-size:14px;font-family:'Inter',sans-serif;outline:none;cursor:pointer" onfocus="this.style.borderColor='#f0b90b'" onblur="this.style.borderColor='#2b3139'">
        <option value="">Выберите банк</option>
        <option value="Сбербанк">Сбербанк</option>
        <option value="Тинькофф">Тинькофф (Т-Банк)</option>
        <option value="ВТБ">ВТБ</option>
        <option value="Альфа-Банк">Альфа-Банк</option>
        <option value="Газпромбанк">Газпромбанк</option>
        <option value="Росбанк">Росбанк</option>
        <option value="Россельхозбанк">Россельхозбанк</option>
        <option value="Открытие">Банк Открытие</option>
        <option value="Райффайзен">Райффайзен</option>
        <option value="СБП">СБП (по номеру телефона)</option>
      </select>
    </div>

    <div id="cardInputWrap" style="margin-bottom:16px;display:none">
      <div style="font-size:12px;color:#848e9c;margin-bottom:6px;font-weight:500">НОМЕР КАРТЫ / ТЕЛЕФОНА</div>
      <input id="orderCard" type="text" placeholder="0000 0000 0000 0000" maxlength="19" oninput="fmtCard(this)" style="width:100%;background:#0b0e11;border:1px solid #2b3139;border-radius:8px;padding:12px 14px;color:#fff;font-size:14px;font-family:'Inter',sans-serif;box-sizing:border-box;outline:none;letter-spacing:.05em" onfocus="this.style.borderColor='#f0b90b'" onblur="this.style.borderColor='#2b3139'">
    </div>

    <button onclick="submitOrder()" style="width:100%;background:#f0b90b;border:none;border-radius:8px;padding:14px;color:#000;font-size:14px;font-weight:700;cursor:pointer;font-family:'Inter',sans-serif;margin-top:8px;transition:opacity .2s" onmouseover="this.style.opacity='.85'" onmouseout="this.style.opacity='1'">Опубликовать ордер</button>
  </div>
</div>

<!-- Deal Chat Modal -->
<div id="dealModal" style="display:none;position:fixed;inset:0;z-index:200;background:rgba(0,0,0,.7);align-items:center;justify-content:center">
  <div style="background:#161a1e;border:1px solid #1e2329;border-radius:16px;width:100%;max-width:480px;height:80vh;display:flex;flex-direction:column">
    <div style="padding:20px 20px 16px;border-bottom:1px solid #1e2329;display:flex;align-items:center;justify-content:space-between;flex-shrink:0">
      <div>
        <div style="font-size:15px;font-weight:700;color:#fff">Сделка</div>
        <div id="dealInfo" style="font-size:12px;color:#848e9c;margin-top:2px"></div>
      </div>
      <button onclick="closeDeal()" style="background:rgba(255,255,255,.08);border:none;color:#848e9c;width:32px;height:32px;border-radius:8px;cursor:pointer;font-size:18px">×</button>
    </div>

    <!-- Deal status bar -->
    <div id="dealStatusBar" style="padding:12px 20px;background:#0f1923;border-bottom:1px solid #1e2329;flex-shrink:0">
      <div style="display:flex;align-items:center;gap:8px">
        <div id="dealStatusDot" style="width:8px;height:8px;border-radius:50%;background:#f0b90b"></div>
        <div id="dealStatusText" style="font-size:13px;color:#f0b90b;font-weight:600">Ожидает оплаты</div>
      </div>
    </div>

    <!-- Chat messages -->
    <div id="dealMessages" style="flex:1;overflow-y:auto;padding:16px 20px;display:flex;flex-direction:column;gap:10px"></div>

    <!-- Action buttons -->
    <div id="dealActions" style="padding:12px 20px;border-top:1px solid #1e2329;flex-shrink:0"></div>

    <!-- Chat input -->
    <div style="padding:12px 20px;border-top:1px solid #1e2329;display:flex;gap:8px;flex-shrink:0">
      <input id="dealMsgInp" type="text" placeholder="Написать..." style="flex:1;background:#0b0e11;border:1px solid #2b3139;border-radius:8px;padding:10px 14px;color:#fff;font-size:13px;font-family:'Inter',sans-serif;outline:none" onfocus="this.style.borderColor='#f0b90b'" onblur="this.style.borderColor='#2b3139'" onkeydown="if(event.key==='Enter')sendDealMsg()">
      <button onclick="sendDealMsg()" style="background:#f0b90b;border:none;border-radius:8px;padding:10px 16px;color:#000;font-weight:700;cursor:pointer;font-size:13px">→</button>
    </div>
  </div>
</div>

</body>
</html>'''
results.append(('exchange page HTML', old2 in c))
if old2 in c: c = c.replace(old2, new2)

# ── 3. Добавить JS для обменника ─────────────────────────────────────────────
old3 = "function openWallet(){"
new3 = """// ── P2P Exchange ──────────────────────────────────
let exchangeOrders = {}; // id -> order
let activeDealId = null;
let currentExTab = 'buy';

function toggleWalletMenu(){
  const m=document.getElementById('walletMenuPop');
  m.style.display=m.style.display==='block'?'none':'block';
  if(m.style.display==='block'){
    setTimeout(()=>document.addEventListener('click',()=>m.style.display='none',{once:true}),50);
  }
}
function hideWalletMenu(){document.getElementById('walletMenuPop').style.display='none';}

function openExchange(){
  document.getElementById('exchangePage').style.display='flex';
  renderOrders();
}
function closeExchange(){document.getElementById('exchangePage').style.display='none';}

function switchExTab(tab){
  currentExTab=tab;
  ['buy','sell','my'].forEach(t=>{
    const btn=document.getElementById('tab'+t.charAt(0).toUpperCase()+t.slice(1));
    btn.style.borderBottomColor=t===tab?'#f0b90b':'transparent';
    btn.style.color=t===tab?'#f0b90b':'#848e9c';
  });
  renderOrders();
}

function renderOrders(){
  const list=document.getElementById('exchangeOrdersList');
  const empty=document.getElementById('exchangeEmpty');
  const orders=Object.values(exchangeOrders).filter(o=>{
    if(currentExTab==='my') return o.sellerId===myId;
    if(currentExTab==='buy') return o.sellerId!==myId && o.status==='open';
    if(currentExTab==='sell') return o.sellerId===myId && o.status==='open';
    return false;
  });
  // Remove old rows
  list.querySelectorAll('.ex-row').forEach(el=>el.remove());
  if(orders.length===0){empty.style.display='block';return;}
  empty.style.display='none';
  orders.forEach(o=>{
    const row=document.createElement('div');
    row.className='ex-row';
    row.style.cssText='display:grid;grid-template-columns:2fr 1.5fr 1.5fr 2fr 1fr;gap:12px;padding:14px 0;border-bottom:1px solid #1e2329;align-items:center';
    const isMine=o.sellerId===myId;
    const statusColor=o.status==='open'?'#0ecb81':o.status==='pending'?'#f0b90b':'#848e9c';
    const statusText=o.status==='open'?'Открыт':o.status==='pending'?'В процессе':'Закрыт';
    row.innerHTML=`
      <div style="display:flex;align-items:center;gap:10px">
        <div style="width:32px;height:32px;border-radius:50%;background:linear-gradient(135deg,#1ABC9C,#0e9b82);display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;color:#fff;flex-shrink:0">${(o.sellerName||'?')[0].toUpperCase()}</div>
        <div>
          <div style="font-size:13px;font-weight:600;color:#fff">@${esc(o.sellerName||'anon')}</div>
          <div style="font-size:11px;color:${statusColor};font-weight:500">${statusText}</div>
        </div>
      </div>
      <div>
        <div style="font-size:14px;font-weight:700;color:#0ecb81">${o.price} ₽</div>
        <div style="font-size:11px;color:#848e9c">за ${o.amount} SUP</div>
      </div>
      <div style="font-size:13px;color:#fff;font-weight:600">${o.amount} <span style="color:#848e9c;font-size:11px">SUP</span></div>
      <div style="font-size:12px;color:#848e9c">${esc(o.bank)}</div>
      <div>${isMine
        ? `<button onclick="cancelOrder('${o.id}')" style="background:rgba(246,70,93,.15);border:1px solid rgba(246,70,93,.3);color:#f6465d;font-size:12px;font-weight:600;padding:6px 12px;border-radius:6px;cursor:pointer;font-family:'Inter',sans-serif">Отменить</button>`
        : `<button onclick="startDeal('${o.id}')" style="background:#0ecb81;border:none;color:#fff;font-size:12px;font-weight:700;padding:6px 14px;border-radius:6px;cursor:pointer;font-family:'Inter',sans-serif">Купить</button>`
      }</div>`;
    list.appendChild(row);
  });
}

function showCreateOrder(){
  document.getElementById('createOrderModal').style.display='flex';
}
function hideCreateOrder(){
  document.getElementById('createOrderModal').style.display='none';
  document.getElementById('orderAmount').value='';
  document.getElementById('orderPrice').value='';
  document.getElementById('orderBank').value='';
  document.getElementById('orderCard').value='';
  document.getElementById('cardInputWrap').style.display='none';
}

function onBankChange(){
  const b=document.getElementById('orderBank').value;
  document.getElementById('cardInputWrap').style.display=b?'block':'none';
  const inp=document.getElementById('orderCard');
  inp.placeholder=b==='СБП'?'+7 900 000 00 00':'0000 0000 0000 0000';
}

function fmtCard(inp){
  let v=inp.value.replace(/\D/g,'');
  if(document.getElementById('orderBank').value==='СБП'){
    inp.value=v;return;
  }
  v=v.substring(0,16);
  inp.value=v.replace(/(.{4})/g,'$1 ').trim();
}

function submitOrder(){
  const amount=parseInt(document.getElementById('orderAmount').value)||0;
  const price=parseInt(document.getElementById('orderPrice').value)||0;
  const bank=document.getElementById('orderBank').value;
  const card=document.getElementById('orderCard').value.trim();
  if(!amount||amount<=0){toast('⚠️','Укажи количество SUP','');return;}
  if(!price||price<=0){toast('⚠️','Укажи цену','');return;}
  if(!bank){toast('⚠️','Выбери способ оплаты','');return;}
  if(!card){toast('⚠️','Введи номер карты','');return;}
  const id='ord_'+Date.now()+'_'+myId.slice(0,6);
  const order={id,sellerId:myId,sellerName:myU||'anon',amount,price,bank,card,status:'open',deals:{},createdAt:Date.now()};
  exchangeOrders[id]=order;
  // Broadcast to all peers
  Object.keys(peers).forEach(pid=>{
    if(peers[pid].online) cmd({cmd:'send',peer_id:pid,text:'__EX_ORDER__'+JSON.stringify({type:'new_order',order:{...order,card:'****'}})});
  });
  hideCreateOrder();
  switchExTab('my');
  toast('✅','Ордер создан!',amount+' SUP за '+price+' ₽');
}

function cancelOrder(id){
  const o=exchangeOrders[id];if(!o)return;
  o.status='cancelled';
  Object.keys(peers).forEach(pid=>{
    if(peers[pid].online) cmd({cmd:'send',peer_id:pid,text:'__EX_ORDER__'+JSON.stringify({type:'cancel_order',orderId:id})});
  });
  renderOrders();
  toast('❌','Ордер отменён','');
}

function startDeal(orderId){
  const o=exchangeOrders[orderId];if(!o)return;
  activeDealId=orderId;
  o.status='pending';
  o.buyerId=myId;
  o.buyerName=myU||'anon';
  if(!o.deals)o.deals={};
  o.deals[myId]={msgs:[],status:'waiting_payment'};
  // Notify seller
  if(peers[o.sellerId]){
    cmd({cmd:'send',peer_id:o.sellerId,text:'__EX_DEAL__'+JSON.stringify({type:'deal_start',orderId,buyerId:myId,buyerName:myU||'anon'})});
  }
  openDeal(orderId,false);
}

function openDeal(orderId, isSeller){
  const o=exchangeOrders[orderId];if(!o)return;
  activeDealId=orderId;
  document.getElementById('dealModal').style.display='flex';
  document.getElementById('dealInfo').textContent=o.amount+' SUP · '+o.price+' ₽ · '+o.bank;
  renderDealActions(o, isSeller);
  renderDealMsgs(o);
}

function closeDeal(){
  document.getElementById('dealModal').style.display='none';
  activeDealId=null;
}

function renderDealActions(o, isSeller){
  const bar=document.getElementById('dealActions');
  const deal=o.deals?.[o.buyerId||myId];
  const status=deal?.status||'waiting_payment';
  if(isSeller){
    if(status==='paid'){
      bar.innerHTML=`
        <div style="font-size:12px;color:#848e9c;margin-bottom:8px">Покупатель сообщил об оплате ${o.price} ₽ на карту ${o.card}</div>
        <div style="display:flex;gap:8px">
          <button onclick="confirmDeal()" style="flex:1;background:#0ecb81;border:none;border-radius:8px;padding:11px;color:#fff;font-size:13px;font-weight:700;cursor:pointer">✓ Подтвердить оплату</button>
          <button onclick="openDispute()" style="flex:1;background:rgba(246,70,93,.15);border:1px solid rgba(246,70,93,.3);border-radius:8px;padding:11px;color:#f6465d;font-size:13px;font-weight:700;cursor:pointer">⚑ Открыть спор</button>
        </div>`;
    } else if(status==='waiting_payment'){
      bar.innerHTML=`<div style="font-size:13px;color:#848e9c;text-align:center;padding:8px">Ожидаем оплату от покупателя...</div>`;
    } else if(status==='confirmed'){
      bar.innerHTML=`<div style="font-size:13px;color:#0ecb81;text-align:center;padding:8px;font-weight:600">✓ Сделка завершена</div>`;
    }
  } else {
    if(status==='waiting_payment'){
      bar.innerHTML=`
        <div style="font-size:12px;color:#848e9c;margin-bottom:8px">Переведи ${o.price} ₽ на карту ${o.bank}: <span style="color:#fff;font-weight:600">${o.card}</span></div>
        <button onclick="markPaid()" style="width:100%;background:#f0b90b;border:none;border-radius:8px;padding:11px;color:#000;font-size:13px;font-weight:700;cursor:pointer">Я оплатил →</button>`;
    } else if(status==='paid'){
      bar.innerHTML=`<div style="font-size:13px;color:#f0b90b;text-align:center;padding:8px;font-weight:600">⏳ Ожидаем подтверждение продавца</div>`;
    } else if(status==='confirmed'){
      bar.innerHTML=`<div style="font-size:13px;color:#0ecb81;text-align:center;padding:8px;font-weight:600">✓ SUP зачислены на ваш кошелёк</div>`;
    } else if(status==='dispute'){
      bar.innerHTML=`<div style="font-size:13px;color:#f6465d;text-align:center;padding:8px;font-weight:600">⚑ Открыт спор — ожидайте решения модератора</div>`;
    }
  }
}

function renderDealMsgs(o){
  const box=document.getElementById('dealMessages');
  box.innerHTML='';
  const deal=o.deals?.[o.buyerId||myId];
  (deal?.msgs||[]).forEach(m=>{
    const isMe=m.from===myId;
    const div=document.createElement('div');
    div.style.cssText='display:flex;justify-content:'+(isMe?'flex-end':'flex-start');
    div.innerHTML=`<div style="max-width:70%;background:${isMe?'#1e3a2f':'#1e2329'};border-radius:12px;padding:9px 13px"><div style="font-size:13px;color:#fff">${esc(m.text)}</div><div style="font-size:10px;color:#848e9c;margin-top:4px;text-align:right">${m.time}</div></div>`;
    box.appendChild(div);
  });
  box.scrollTop=box.scrollHeight;
}

function sendDealMsg(){
  const inp=document.getElementById('dealMsgInp');
  const text=inp.value.trim();if(!text||!activeDealId)return;
  const o=exchangeOrders[activeDealId];if(!o)return;
  const buyerKey=o.buyerId||myId;
  if(!o.deals)o.deals={};
  if(!o.deals[buyerKey])o.deals[buyerKey]={msgs:[],status:'waiting_payment'};
  const now=new Date().toTimeString().slice(0,5);
  o.deals[buyerKey].msgs.push({from:myId,text,time:now});
  // Send to counterpart
  const otherId=myId===o.sellerId?o.buyerId:o.sellerId;
  if(otherId&&peers[otherId]){
    cmd({cmd:'send',peer_id:otherId,text:'__EX_DEAL__'+JSON.stringify({type:'deal_msg',orderId:activeDealId,from:myId,text,time:now})});
  }
  renderDealMsgs(o);
  inp.value='';
}

function markPaid(){
  if(!activeDealId)return;
  const o=exchangeOrders[activeDealId];if(!o)return;
  const buyerKey=o.buyerId||myId;
  if(!o.deals[buyerKey])o.deals[buyerKey]={msgs:[],status:'waiting_payment'};
  o.deals[buyerKey].status='paid';
  if(peers[o.sellerId]){
    cmd({cmd:'send',peer_id:o.sellerId,text:'__EX_DEAL__'+JSON.stringify({type:'deal_paid',orderId:activeDealId,buyerId:myId})});
  }
  document.getElementById('dealStatusText').textContent='Оплата отправлена';
  document.getElementById('dealStatusDot').style.background='#f0b90b';
  renderDealActions(o,false);
  toast('✅','Уведомление отправлено продавцу','');
}

function confirmDeal(){
  if(!activeDealId)return;
  const o=exchangeOrders[activeDealId];if(!o)return;
  const buyerKey=o.buyerId;
  o.deals[buyerKey].status='confirmed';
  o.status='closed';
  if(peers[buyerKey]){
    cmd({cmd:'send',peer_id:buyerKey,text:'__EX_DEAL__'+JSON.stringify({type:'deal_confirmed',orderId:activeDealId})});
  }
  document.getElementById('dealStatusText').textContent='Сделка завершена';
  document.getElementById('dealStatusDot').style.background='#0ecb81';
  renderDealActions(o,true);
  toast('✅','Сделка подтверждена!','SUP переведены покупателю');
}

function openDispute(){
  if(!activeDealId)return;
  const o=exchangeOrders[activeDealId];if(!o)return;
  o.deals[o.buyerId].status='dispute';
  if(peers[o.buyerId]){
    cmd({cmd:'send',peer_id:o.buyerId,text:'__EX_DEAL__'+JSON.stringify({type:'deal_dispute',orderId:activeDealId})});
  }
  renderDealActions(o,true);
  toast('⚑','Спор открыт','Модератор рассмотрит заявку');
}

function handleExchangeMsg(peerId, text){
  if(text.startsWith('__EX_ORDER__')){
    try{
      const d=JSON.parse(text.slice(12));
      if(d.type==='new_order'){
        exchangeOrders[d.order.id]={...d.order};
        if(document.getElementById('exchangePage').style.display==='flex') renderOrders();
        toast('💱','Новый ордер','@'+d.order.sellerName+' продаёт '+d.order.amount+' SUP');
      } else if(d.type==='cancel_order'){
        if(exchangeOrders[d.orderId]) exchangeOrders[d.orderId].status='cancelled';
        if(document.getElementById('exchangePage').style.display==='flex') renderOrders();
      }
    }catch(e){}
    return true;
  }
  if(text.startsWith('__EX_DEAL__')){
    try{
      const d=JSON.parse(text.slice(11));
      const o=exchangeOrders[d.orderId];
      if(!o)return true;
      if(d.type==='deal_start'){
        o.buyerId=d.buyerId;o.buyerName=d.buyerName;o.status='pending';
        if(!o.deals)o.deals={};
        o.deals[d.buyerId]={msgs:[],status:'waiting_payment'};
        toast('💱','Новая сделка!','@'+d.buyerName+' хочет купить '+o.amount+' SUP');
        if(activeDealId===d.orderId) renderDealActions(o,true);
        // Auto open deal for seller
        if(o.sellerId===myId) openDeal(d.orderId, true);
      } else if(d.type==='deal_msg'){
        if(!o.deals)o.deals={};
        if(!o.deals[o.buyerId||peerId])o.deals[o.buyerId||peerId]={msgs:[],status:'waiting_payment'};
        o.deals[o.buyerId||peerId].msgs.push({from:d.from,text:d.text,time:d.time});
        if(activeDealId===d.orderId) renderDealMsgs(o);
      } else if(d.type==='deal_paid'){
        if(o.deals&&o.deals[d.buyerId]) o.deals[d.buyerId].status='paid';
        if(activeDealId===d.orderId) renderDealActions(o, o.sellerId===myId);
        toast('💰','Покупатель оплатил!','Подтвердите получение денег');
      } else if(d.type==='deal_confirmed'){
        if(o.deals&&o.deals[myId]) o.deals[myId].status='confirmed';
        if(activeDealId===d.orderId){
          document.getElementById('dealStatusText').textContent='Сделка завершена';
          document.getElementById('dealStatusDot').style.background='#0ecb81';
          renderDealActions(o,false);
        }
        toast('✅','SUP получены!','Сделка успешно завершена');
      } else if(d.type==='deal_dispute'){
        if(o.deals&&o.deals[myId]) o.deals[myId].status='dispute';
        if(activeDealId===d.orderId) renderDealActions(o,false);
        toast('⚑','Открыт спор','Ожидайте решения модератора');
      }
    }catch(e){}
    return true;
  }
  return false;
}

// ── Wallet ────────────────────────────────────
function openWallet(){"""
results.append(('exchange JS', old3 in c))
if old3 in c: c = c.replace(old3, new3)

# ── 4. В handle() добавить обработку exchange сообщений ──────────────────────
old4 = "  else if(ev.type==='call_signal'){\n    const from=ev.from, data=ev.data;\n    if(data&&from) handleCallSignal(from, data);\n  }"
new4 = """  else if(ev.type==='call_signal'){
    const from=ev.from, data=ev.data;
    if(data&&from) handleCallSignal(from, data);
  }"""
# Find the message handler and add exchange check
old5 = "  if(txt.startsWith(GP)){"
new5 = """  if(handleExchangeMsg(id,txt)) return;
  if(txt.startsWith(GP)){"""
results.append(('exchange message handler', old5 in c))
if old5 in c: c = c.replace(old5, new5)

with open('ui/gui.py', 'w', encoding='utf-8') as f:
    f.write(c)

print()
for name, found in results:
    print(f"  {'✓' if found else '✗ НЕ НАЙДЕНО'}  {name}")
print('\nГотово!')

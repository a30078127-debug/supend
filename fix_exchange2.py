with open('ui/gui.py', encoding='utf-8') as f:
    c = f.read()

results = []

# ── 1. Добавить вкладку История в табы ───────────────────────────────────────
old1 = '    <button id="tabBuy" onclick="switchExTab(\'buy\')" style="padding:14px 20px;background:none;border:none;border-bottom:2px solid #f0b90b;color:#f0b90b;font-size:14px;font-weight:600;cursor:pointer;font-family:\'Inter\',sans-serif">Купить SUP</button>\n    <button id="tabSell" onclick="switchExTab(\'sell\')" style="padding:14px 20px;background:none;border:none;border-bottom:2px solid transparent;color:#848e9c;font-size:14px;font-weight:600;cursor:pointer;font-family:\'Inter\',sans-serif">Продать SUP</button>\n    <button id="tabMy" onclick="switchExTab(\'my\')" style="padding:14px 20px;background:none;border:none;border-bottom:2px solid transparent;color:#848e9c;font-size:14px;font-weight:600;cursor:pointer;font-family:\'Inter\',sans-serif">Мои ордера</button>'
new1 = '    <button id="tabBuy" onclick="switchExTab(\'buy\')" style="padding:14px 20px;background:none;border:none;border-bottom:2px solid #f0b90b;color:#f0b90b;font-size:14px;font-weight:600;cursor:pointer;font-family:\'Inter\',sans-serif">Купить SUP</button>\n    <button id="tabSell" onclick="switchExTab(\'sell\')" style="padding:14px 20px;background:none;border:none;border-bottom:2px solid transparent;color:#848e9c;font-size:14px;font-weight:600;cursor:pointer;font-family:\'Inter\',sans-serif">Продать SUP</button>\n    <button id="tabMy" onclick="switchExTab(\'my\')" style="padding:14px 20px;background:none;border:none;border-bottom:2px solid transparent;color:#848e9c;font-size:14px;font-weight:600;cursor:pointer;font-family:\'Inter\',sans-serif">Мои ордера</button>\n    <button id="tabHistory" onclick="switchExTab(\'history\')" style="padding:14px 20px;background:none;border:none;border-bottom:2px solid transparent;color:#848e9c;font-size:14px;font-weight:600;cursor:pointer;font-family:\'Inter\',sans-serif">История</button>'
results.append(('history tab button', old1 in c))
if old1 in c: c = c.replace(old1, new1)

# ── 2. switchExTab — добавить history ────────────────────────────────────────
old2 = "function switchExTab(tab){\n  currentExTab=tab;\n  ['buy','sell','my'].forEach(t=>{\n    const btn=document.getElementById('tab'+t.charAt(0).toUpperCase()+t.slice(1));\n    btn.style.borderBottomColor=t===tab?'#f0b90b':'transparent';\n    btn.style.color=t===tab?'#f0b90b':'#848e9c';\n  });\n  renderOrders();\n}"
new2 = "function switchExTab(tab){\n  currentExTab=tab;\n  ['buy','sell','my','history'].forEach(t=>{\n    const btn=document.getElementById('tab'+t.charAt(0).toUpperCase()+t.slice(1));\n    if(btn){btn.style.borderBottomColor=t===tab?'#f0b90b':'transparent';btn.style.color=t===tab?'#f0b90b':'#848e9c';}\n  });\n  if(tab==='history') renderHistory();\n  else renderOrders();\n}"
results.append(('switchExTab history', old2 in c))
if old2 in c: c = c.replace(old2, new2)

# ── 3. renderOrders — фильтр убирает cancelled из buy/sell ───────────────────
old3 = "  const orders=Object.values(exchangeOrders).filter(o=>{\n    if(currentExTab==='my') return o.sellerId===myId;\n    if(currentExTab==='buy') return o.sellerId!==myId && o.status==='open';\n    if(currentExTab==='sell') return o.sellerId===myId && o.status==='open';\n    return false;\n  });"
new3 = "  const orders=Object.values(exchangeOrders).filter(o=>{\n    if(currentExTab==='my') return o.sellerId===myId && o.status!=='cancelled';\n    if(currentExTab==='buy') return o.sellerId!==myId && o.status==='open';\n    if(currentExTab==='sell') return o.sellerId===myId && o.status==='open';\n    return false;\n  });"
results.append(('filter cancelled orders', old3 in c))
if old3 in c: c = c.replace(old3, new3)

# ── 4. cancelOrder — добавить в историю и убрать из списка ───────────────────
old4 = "function cancelOrder(id){\n  const o=exchangeOrders[id];if(!o)return;\n  o.status='cancelled';\n  Object.keys(peers).forEach(pid=>{\n    if(peers[pid].online) cmd({cmd:'send',peer_id:pid,text:'__EX_ORDER__'+JSON.stringify({type:'cancel_order',orderId:id})});\n  });\n  renderOrders();\n  toast('❌','Ордер отменён','');\n}"
new4 = """function cancelOrder(id){
  const o=exchangeOrders[id];if(!o)return;
  o.status='cancelled';
  const now=new Date().toLocaleTimeString('ru',{hour:'2-digit',minute:'2-digit'});
  exchangeHistory.push({type:'cancelled',orderId:id,amount:o.amount,price:o.price,bank:o.bank,time:now,date:new Date().toLocaleDateString('ru')});
  Object.keys(peers).forEach(pid=>{
    if(peers[pid].online) cmd({cmd:'send',peer_id:pid,text:'__EX_ORDER__'+JSON.stringify({type:'cancel_order',orderId:id})});
  });
  renderOrders();
  toast('❌','Ордер отменён','');
}"""
results.append(('cancelOrder with history', old4 in c))
if old4 in c: c = c.replace(old4, new4)

# ── 5. submitOrder — проверка баланса ────────────────────────────────────────
old5 = "  if(!amount||amount<=0){toast('⚠️','Укажи количество SUP','');return;}\n  if(!price||price<=0){toast('⚠️','Укажи цену','');return;}\n  if(!bank){toast('⚠️','Выбери способ оплаты','');return;}\n  if(!card){toast('⚠️','Введи номер карты','');return;}"
new5 = "  if(!amount||amount<=0){toast('⚠️','Укажи количество SUP','');return;}\n  if(amount>walletData.balance){toast('⚠️','Недостаточно SUP','У тебя '+walletData.balance+' SUP, а нужно '+amount);return;}\n  if(!price||price<=0){toast('⚠️','Укажи цену','');return;}\n  if(!bank){toast('⚠️','Выбери способ оплаты','');return;}\n  if(!card){toast('⚠️','Введи номер карты','');return;}"
results.append(('balance check in submitOrder', old5 in c))
if old5 in c: c = c.replace(old5, new5)

# ── 6. confirmDeal — реальный перевод SUP + история ──────────────────────────
old6 = "function confirmDeal(){\n  if(!activeDealId)return;\n  const o=exchangeOrders[activeDealId];if(!o)return;\n  const buyerKey=o.buyerId;\n  o.deals[buyerKey].status='confirmed';\n  o.status='closed';\n  if(peers[buyerKey]){\n    cmd({cmd:'send',peer_id:buyerKey,text:'__EX_DEAL__'+JSON.stringify({type:'deal_confirmed',orderId:activeDealId})});\n  }\n  document.getElementById('dealStatusText').textContent='Сделка завершена';\n  document.getElementById('dealStatusDot').style.background='#0ecb81';\n  renderDealActions(o,true);\n  toast('✅','Сделка подтверждена!','SUP переведены покупателю');\n}"
new6 = """function confirmDeal(){
  if(!activeDealId)return;
  const o=exchangeOrders[activeDealId];if(!o)return;
  const buyerKey=o.buyerId;
  o.deals[buyerKey].status='confirmed';
  o.status='closed';
  // Списываем SUP у продавца
  walletData.balance=Math.max(0,walletData.balance-o.amount);
  updateWalletUI();
  const now=new Date().toLocaleTimeString('ru',{hour:'2-digit',minute:'2-digit'});
  exchangeHistory.push({type:'sold',orderId:o.id,amount:o.amount,price:o.price,bank:o.bank,time:now,date:new Date().toLocaleDateString('ru'),counterpart:o.buyerName});
  if(peers[buyerKey]){
    cmd({cmd:'send',peer_id:buyerKey,text:'__EX_DEAL__'+JSON.stringify({type:'deal_confirmed',orderId:activeDealId,amount:o.amount})});
  }
  document.getElementById('dealStatusText').textContent='Сделка завершена';
  document.getElementById('dealStatusDot').style.background='#0ecb81';
  renderDealActions(o,true);
  toast('✅','Сделка подтверждена!','SUP переведены покупателю');
}"""
results.append(('confirmDeal with real SUP transfer', old6 in c))
if old6 in c: c = c.replace(old6, new6)

# ── 7. В handleExchangeMsg — deal_confirmed зачисляет SUP покупателю ─────────
old7 = "      } else if(d.type==='deal_confirmed'){\n        if(o.deals&&o.deals[myId]) o.deals[myId].status='confirmed';\n        if(activeDealId===d.orderId){\n          document.getElementById('dealStatusText').textContent='Сделка завершена';\n          document.getElementById('dealStatusDot').style.background='#0ecb81';\n          renderDealActions(o,false);\n        }\n        toast('✅','SUP получены!','Сделка успешно завершена');"
new7 = """      } else if(d.type==='deal_confirmed'){
        if(o.deals&&o.deals[myId]) o.deals[myId].status='confirmed';
        // Зачисляем SUP покупателю
        const earnedAmt=d.amount||o.amount||0;
        walletData.balance+=earnedAmt;
        updateWalletUI();
        const now2=new Date().toLocaleTimeString('ru',{hour:'2-digit',minute:'2-digit'});
        exchangeHistory.push({type:'bought',orderId:o.id,amount:earnedAmt,price:o.price,bank:o.bank,time:now2,date:new Date().toLocaleDateString('ru'),counterpart:o.sellerName});
        if(activeDealId===d.orderId){
          document.getElementById('dealStatusText').textContent='Сделка завершена';
          document.getElementById('dealStatusDot').style.background='#0ecb81';
          renderDealActions(o,false);
        }
        toast('✅','SUP получены! +'+earnedAmt,'Сделка успешно завершена');"""
results.append(('deal_confirmed credits SUP to buyer', old7 in c))
if old7 in c: c = c.replace(old7, new7)

# ── 8. Добавить переменную exchangeHistory и функцию renderHistory ────────────
old8 = "let exchangeOrders = {}; // id -> order"
new8 = """let exchangeOrders = {}; // id -> order
let exchangeHistory = []; // history of deals

function renderHistory(){
  const list=document.getElementById('exchangeOrdersList');
  const empty=document.getElementById('exchangeEmpty');
  list.querySelectorAll('.ex-row').forEach(el=>el.remove());
  if(exchangeHistory.length===0){
    empty.style.display='block';
    empty.querySelector('div:last-child').textContent='История сделок пуста';
    return;
  }
  empty.style.display='none';
  [...exchangeHistory].reverse().forEach(h=>{
    const row=document.createElement('div');
    row.className='ex-row';
    row.style.cssText='display:flex;align-items:center;justify-content:space-between;padding:14px 0;border-bottom:1px solid #1e2329';
    let badge,color;
    if(h.type==='bought'){badge='Куплено';color='#0ecb81';}
    else if(h.type==='sold'){badge='Продано';color='#0ecb81';}
    else{badge='Отменён';color='#f6465d';}
    row.innerHTML=`
      <div style="display:flex;align-items:center;gap:12px">
        <div style="width:36px;height:36px;border-radius:50%;background:${h.type==='cancelled'?'rgba(246,70,93,.15)':'rgba(14,203,129,.15)'};display:flex;align-items:center;justify-content:center">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="${color}" stroke-width="2">${h.type==='bought'?'<path d="M12 2v20M2 12l10 10 10-10"/>':'<path d="M12 22V2M22 12L12 2 2 12"/>'}</svg>
        </div>
        <div>
          <div style="font-size:13px;font-weight:700;color:${color}">${badge}</div>
          <div style="font-size:11px;color:#848e9c;margin-top:2px">${h.date} · ${h.time}${h.counterpart?' · @'+h.counterpart:''}</div>
        </div>
      </div>
      <div style="text-align:right">
        <div style="font-size:14px;font-weight:700;color:#fff">${h.type==='cancelled'?'—':((h.type==='bought'?'+':'-')+h.amount+' SUP')}</div>
        <div style="font-size:11px;color:#848e9c;margin-top:2px">${h.price?h.price+' ₽':''} · ${h.bank||''}</div>
      </div>`;
    list.appendChild(row);
  });
}"""
results.append(('exchangeHistory variable and renderHistory', old8 in c))
if old8 in c: c = c.replace(old8, new8)

# ── 9. В cancel_order из peer тоже добавляем в историю ───────────────────────
old9 = "        if(exchangeOrders[d.orderId]) exchangeOrders[d.orderId].status='cancelled';\n        if(document.getElementById('exchangePage').style.display==='flex') renderOrders();"
new9 = """        if(exchangeOrders[d.orderId]){
          const co=exchangeOrders[d.orderId];
          co.status='cancelled';
        }
        if(document.getElementById('exchangePage').style.display==='flex') renderOrders();"""
results.append(('cancel_order peer handler', old9 in c))
if old9 in c: c = c.replace(old9, new9)

with open('ui/gui.py', 'w', encoding='utf-8') as f:
    f.write(c)

print()
for name, found in results:
    print(f"  {'✓' if found else '✗ НЕ НАЙДЕНО'}  {name}")
print('\nГотово!')

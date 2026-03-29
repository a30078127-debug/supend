"""
GUI Supend Messenger — светлый Telegram-стиль, логин/пароль, поиск по нику.
Запуск: python main.py --gui --no-history
"""

import asyncio
import logging
import socket
import webbrowser
from datetime import datetime

from aiohttp import web

logger = logging.getLogger(__name__)


def _ts(ts):
    return datetime.fromtimestamp(ts).strftime("%H:%M")


def _my_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


LOTUS_SVG = """<svg viewBox="0 0 100 80" fill="none" xmlns="http://www.w3.org/2000/svg">
  <path d="M50 68 C50 68 20 53 18 33 C18 33 30 38 38 50 C38 50 35 28 50 13 C65 28 62 50 62 50 C70 38 82 33 82 33 C80 53 50 68 50 68Z" stroke="white" stroke-width="3.5" stroke-linejoin="round" fill="none"/>
  <path d="M38 50 C32 42 20 36 12 40 C14 53 30 62 50 68" stroke="white" stroke-width="3" stroke-linejoin="round" fill="none"/>
  <path d="M62 50 C68 42 80 36 88 40 C86 53 70 62 50 68" stroke="white" stroke-width="3" stroke-linejoin="round" fill="none"/>
  <path d="M36 48 C30 43 22 38 16 34" stroke="white" stroke-width="2" fill="none" stroke-linecap="round"/>
  <path d="M64 48 C70 43 78 38 84 34" stroke="white" stroke-width="2" fill="none" stroke-linecap="round"/>
  <circle cx="50" cy="72" r="2.5" fill="white"/>
</svg>"""

HTML = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Supend</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Inter',sans-serif;background:#f0f2f5;color:#222;height:100vh;display:flex;overflow:hidden}

/* LOGIN */
#loginPage{position:fixed;inset:0;z-index:100;background:#fff;display:flex;align-items:center;justify-content:center;transition:opacity .35s,transform .35s}
#loginPage.out{opacity:0;pointer-events:none;transform:scale(1.03)}
.login-box{width:360px;display:flex;flex-direction:column;align-items:center}
.logo-circle{width:120px;height:120px;border-radius:50%;background:#1ABC9C;display:flex;align-items:center;justify-content:center;margin-bottom:22px;box-shadow:0 8px 32px rgba(26,188,156,.35);animation:float 3s ease-in-out infinite}
@keyframes float{0%,100%{transform:translateY(0);box-shadow:0 8px 32px rgba(26,188,156,.35)}50%{transform:translateY(-7px);box-shadow:0 18px 42px rgba(26,188,156,.45)}}
.logo-circle svg{width:72px;height:72px}
.app-name{font-size:30px;font-weight:700;color:#111;margin-bottom:6px;letter-spacing:-.5px}
.app-tagline{font-size:14px;color:#999;margin-bottom:36px;text-align:center}
.login-form{width:100%;display:flex;flex-direction:column;gap:12px}
.inp-label{font-size:12px;font-weight:600;color:#666;margin-bottom:4px}
.inp-group{display:flex;flex-direction:column}
.tg-input{width:100%;padding:13px 16px;background:#f0f2f5;border:2px solid transparent;border-radius:12px;font-size:15px;font-family:'Inter',sans-serif;color:#111;outline:none;transition:border-color .2s,background .2s}
.tg-input:focus{background:#fff;border-color:#2AABEE}
.tg-input::placeholder{color:#bbb}
.tg-btn{width:100%;padding:14px;background:#2AABEE;border:none;border-radius:12px;color:#fff;font-size:15px;font-weight:600;font-family:'Inter',sans-serif;cursor:pointer;transition:background .2s,transform .1s,box-shadow .2s;margin-top:4px;box-shadow:0 4px 16px rgba(42,171,238,.35)}
.tg-btn:hover{background:#1a9ed4;box-shadow:0 6px 22px rgba(42,171,238,.45)}
.tg-btn:active{transform:scale(.98)}
.tg-btn:disabled{opacity:.6;cursor:not-allowed}
.login-error{font-size:13px;color:#e53935;text-align:center;min-height:18px;margin-top:-4px}
.login-hint{font-size:12px;color:#bbb;text-align:center;margin-top:18px;line-height:1.7}

/* APP */
#app{display:flex;width:100vw;height:100vh;opacity:0;transition:opacity .3s}
#app.visible{opacity:1}

/* SIDEBAR */
.sidebar{width:320px;flex-shrink:0;background:#fff;border-right:1px solid #eee;display:flex;flex-direction:column;height:100vh}
.sb-top{padding:12px 14px 10px;border-bottom:1px solid #f5f5f5;display:flex;flex-direction:column;gap:10px}
.sb-brand{display:flex;align-items:center;gap:10px}
.sb-logo{width:38px;height:38px;border-radius:50%;background:#1ABC9C;display:flex;align-items:center;justify-content:center;flex-shrink:0}
.sb-logo svg{width:24px;height:24px}
.sb-appname{font-size:17px;font-weight:700;color:#111}
.sb-uname{font-size:12px;color:#aaa}
.ws-dot{width:8px;height:8px;border-radius:50%;background:#e53935;transition:background .3s;flex-shrink:0}
.ws-dot.ok{background:#2ecc71}

.search-wrap{display:flex;align-items:center;gap:8px;background:#f0f2f5;border-radius:10px;padding:8px 12px;transition:box-shadow .2s}
.search-wrap:focus-within{box-shadow:0 0 0 2px #2AABEE44}
.search-wrap svg{color:#bbb;flex-shrink:0}
.search-wrap input{background:none;border:none;outline:none;font-size:14px;color:#111;width:100%;font-family:'Inter',sans-serif}
.search-wrap input::placeholder{color:#bbb}
.search-btn{width:100%;padding:9px;background:#2AABEE;border:none;border-radius:10px;color:#fff;font-size:13px;font-weight:600;cursor:pointer;font-family:'Inter',sans-serif;transition:background .2s;margin-top:2px}
.search-btn:hover{background:#1a9ed4}

.user-list-hd{padding:10px 14px 4px;font-size:11px;font-weight:700;color:#bbb;text-transform:uppercase;letter-spacing:.08em;display:flex;justify-content:space-between}
.peer-list{flex:1;overflow-y:auto}
.peer-list::-webkit-scrollbar{width:3px}
.peer-list::-webkit-scrollbar-thumb{background:#eee;border-radius:3px}

.peer-item{display:flex;align-items:center;gap:10px;padding:10px 14px;cursor:pointer;transition:background .12s;position:relative}
.peer-item:hover{background:#f8f9fa}
.peer-item.active{background:#e8f4fd}
.peer-item.active::before{content:'';position:absolute;left:0;top:0;bottom:0;width:3px;background:#2AABEE;border-radius:0 3px 3px 0}
.p-av{width:44px;height:44px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:17px;font-weight:700;color:#fff;flex-shrink:0;position:relative}
.p-av .sdot{position:absolute;bottom:1px;right:1px;width:12px;height:12px;border-radius:50%;border:2px solid #fff;background:#2ecc71}
.p-av .sdot.off{background:#ddd}
.p-info{flex:1;min-width:0}
.p-name{font-size:14px;font-weight:600;color:#111;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.p-prev{font-size:13px;color:#aaa;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;margin-top:1px}
.p-meta{text-align:right;flex-shrink:0}
.p-time{font-size:11px;color:#bbb}
.p-unread{margin-top:3px;background:#2AABEE;color:#fff;font-size:11px;font-weight:700;padding:1px 6px;border-radius:10px;display:inline-block}

.sb-foot{border-top:1px solid #f5f5f5;padding:12px 14px}
.foot-label{font-size:11px;font-weight:700;color:#bbb;text-transform:uppercase;letter-spacing:.08em;margin-bottom:8px}
.conn-row{display:flex;gap:6px;margin-bottom:6px}
.conn-inp{flex:1;background:#f0f2f5;border:2px solid transparent;border-radius:10px;padding:8px 12px;color:#111;font-size:13px;outline:none;font-family:'Inter',sans-serif;transition:border-color .2s,background .2s}
.conn-inp:focus{background:#fff;border-color:#2AABEE}
.conn-inp::placeholder{color:#bbb}
.port-inp{width:80px;flex:none}
.btn-conn{width:100%;padding:10px;background:#2AABEE;border:none;border-radius:10px;color:#fff;font-size:14px;font-weight:600;cursor:pointer;font-family:'Inter',sans-serif;transition:background .2s}
.btn-conn:hover{background:#1a9ed4}

/* CHAT */
.chat{flex:1;display:flex;flex-direction:column;height:100vh;background:#f0f2f5;position:relative}
.chat-head{padding:12px 20px;background:#fff;border-bottom:1px solid #eee;display:flex;align-items:center;gap:12px;z-index:10}
.ch-av{width:40px;height:40px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:15px;font-weight:700;color:#fff;flex-shrink:0;position:relative}
.ch-av .sdot{position:absolute;bottom:0;right:0;width:11px;height:11px;border-radius:50%;border:2px solid #fff;background:#2ecc71}
.ch-info{flex:1;min-width:0}
.ch-name{font-size:15px;font-weight:700;color:#111;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.ch-status{font-size:12px;color:#2ecc71;margin-top:1px}
.ch-actions{display:flex;gap:6px}
.ico-btn{width:36px;height:36px;border-radius:50%;background:#f0f2f5;border:none;display:flex;align-items:center;justify-content:center;cursor:pointer;color:#aaa;transition:background .15s,color .15s}
.ico-btn:hover{background:#e3f2fd;color:#2AABEE}

.msgs{flex:1;overflow-y:auto;padding:16px 60px;display:flex;flex-direction:column;gap:4px;scroll-behavior:smooth}
.msgs::-webkit-scrollbar{width:4px}
.msgs::-webkit-scrollbar-thumb{background:#ddd;border-radius:4px}
.date-sep{text-align:center;margin:10px 0 6px;color:#bbb;font-size:12px;display:flex;align-items:center;gap:10px}
.date-sep::before,.date-sep::after{content:'';flex:1;height:1px;background:#e8e8e8}
.msg-row{display:flex;align-items:flex-end;gap:6px;animation:fadein .2s ease-out}
@keyframes fadein{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
.msg-row.out{flex-direction:row-reverse}
.m-av{width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:700;color:#fff;flex-shrink:0;margin-bottom:2px}
.m-wrap{max-width:65%;display:flex;flex-direction:column;gap:2px}
.msg-row.out .m-wrap{align-items:flex-end}
.bubble{padding:9px 14px;font-size:14px;line-height:1.5;word-break:break-word}
.msg-row:not(.out) .bubble{background:#fff;color:#111;border-radius:18px 18px 18px 4px;box-shadow:0 1px 2px rgba(0,0,0,.08)}
.msg-row.out .bubble{background:#2AABEE;color:#fff;border-radius:18px 18px 4px 18px}
.m-meta{display:flex;align-items:center;gap:4px;font-size:11px;color:#bbb;padding:0 4px}
.msg-row.out .m-meta{flex-direction:row-reverse}
.m-tick{color:#2AABEE}

.empty{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:14px}
.empty-ico{width:80px;height:80px;border-radius:50%;background:#e3f2fd;display:flex;align-items:center;justify-content:center;font-size:36px}
.empty-title{font-size:20px;font-weight:700;color:#666}
.empty-sub{font-size:14px;color:#bbb;text-align:center;max-width:260px;line-height:1.6}

.inp-area{padding:10px 60px 16px;display:flex;align-items:flex-end;gap:10px;background:#f0f2f5}
.inp-wrap{flex:1;background:#fff;border-radius:24px;padding:10px 16px;display:flex;align-items:center;box-shadow:0 1px 4px rgba(0,0,0,.1);min-height:44px}
textarea.msg-inp{background:none;border:none;outline:none;color:#111;font-size:15px;font-family:'Inter',sans-serif;width:100%;resize:none;max-height:120px;line-height:1.5}
textarea.msg-inp::placeholder{color:#bbb}
.send-btn{width:44px;height:44px;border-radius:50%;background:#2AABEE;border:none;display:flex;align-items:center;justify-content:center;cursor:pointer;flex-shrink:0;box-shadow:0 2px 10px rgba(42,171,238,.4);transition:background .2s,transform .1s}
.send-btn:hover{background:#1a9ed4}
.send-btn:active{transform:scale(.93)}

.toast{position:fixed;bottom:20px;right:20px;z-index:999;background:#fff;border-radius:14px;padding:12px 16px;min-width:240px;box-shadow:0 4px 24px rgba(0,0,0,.15);display:flex;align-items:flex-start;gap:10px;transform:translateX(120%);opacity:0;transition:transform .28s cubic-bezier(.34,1.56,.64,1),opacity .28s}
.toast.show{transform:none;opacity:1}
.toast-ico{font-size:20px;flex-shrink:0}
.toast-title{font-size:13px;font-weight:700;color:#111}
.toast-msg{font-size:12px;color:#999;margin-top:2px}

.av0{background:#2AABEE}.av1{background:#1ABC9C}.av2{background:#7c4dff}
.av3{background:#e53935}.av4{background:#ff9800}.av5{background:#0097a7}
</style>
</head>
<body>

<!-- LOGIN -->
<div id="loginPage">
  <div class="login-box">
    <div class="logo-circle">""" + LOTUS_SVG + """</div>
    <div class="app-name">Supend</div>
    <div class="app-tagline">Безопасный P2P мессенджер</div>
    <div class="login-form">
      <div class="inp-group">
        <div class="inp-label">Логин</div>
        <input class="tg-input" id="loginInp" type="text" placeholder="Придумай уникальный логин" maxlength="32" onkeydown="loginKey(event)" autocomplete="off">
      </div>
      <div class="inp-group">
        <div class="inp-label">Пароль (для истории)</div>
        <input class="tg-input" id="passInp" type="password" placeholder="Необязательно" onkeydown="loginKey(event)">
      </div>
      <div class="login-error" id="loginErr"></div>
      <button class="tg-btn" id="loginBtn" onclick="doLogin()">Войти →</button>
    </div>
    <div class="login-hint">Логин привязан к вашему IP.<br>Друзья найдут вас по логину в поиске.</div>
  </div>
</div>

<!-- APP -->
<div id="app">
  <aside class="sidebar">
    <div class="sb-top">
      <div class="sb-brand">
        <div class="sb-logo">""" + LOTUS_SVG + """</div>
        <div>
          <div class="sb-appname">Supend</div>
          <div class="sb-uname" id="sbUname">@логин</div>
        </div>
        <div style="margin-left:auto;display:flex;align-items:center;gap:6px">
          <div class="ws-dot" id="wsDot"></div>
          <span style="font-size:11px;color:#bbb" id="wsLabel">offline</span>
        </div>
      </div>
      <div class="search-wrap">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
        <input type="text" id="searchInp" placeholder="Найти по логину... (Enter)" onkeydown="searchKey(event)" oninput="onSrchInput(this.value)" autocomplete="off">
      </div>
      <div id="searchResult" style="display:none">
        <button class="search-btn" id="searchConnBtn" onclick="connectByLogin()">Подключиться</button>
      </div>
    </div>
    <div class="user-list-hd">
      <span>Чаты</span>
      <span id="onlineCount" style="color:#2AABEE">0 онлайн</span>
    </div>
    <div class="peer-list" id="peerList"></div>
    <div class="sb-foot">
      <div class="foot-label">Подключить по IP</div>
      <div class="conn-row">
        <input class="conn-inp" id="hostInp" placeholder="192.168.x.x" onkeydown="connKey(event)">
        <input class="conn-inp port-inp" id="portInp" placeholder="Порт" type="number" onkeydown="connKey(event)">
      </div>
      <button class="btn-conn" onclick="doConnect()">Подключить</button>
    </div>
  </aside>

  <main class="chat">
    <div class="chat-head" id="chatHead" style="display:none">
      <div class="ch-av av0" id="chAv"><div class="sdot"></div></div>
      <div class="ch-info">
        <div class="ch-name" id="chName">–</div>
        <div class="ch-status" id="chStatus">в сети</div>
      </div>
      <div class="ch-actions">
        <button class="ico-btn" onclick="doDisconnect()" title="Отключиться">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18.36 6.64a9 9 0 1 1-12.73 0"/><line x1="12" y1="2" x2="12" y2="12"/></svg>
        </button>
      </div>
    </div>
    <div class="empty" id="emptyState">
      <div class="empty-ico">💬</div>
      <div class="empty-title">Добро пожаловать!</div>
      <div class="empty-sub">Найдите друга по логину через поиск или введите IP для подключения</div>
    </div>
    <div class="msgs" id="msgs" style="display:none"></div>
    <div class="inp-area" id="inpArea" style="display:none">
      <div class="inp-wrap">
        <textarea class="msg-inp" id="msgInp" rows="1" placeholder="Сообщение..." onkeydown="inpKey(event)" oninput="autoH(this)"></textarea>
      </div>
      <button class="send-btn" onclick="doSend()">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="white"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
      </button>
    </div>
  </main>
</div>

<div class="toast" id="toast">
  <div class="toast-ico" id="toastIco">📩</div>
  <div><div class="toast-title" id="toastTitle"></div><div class="toast-msg" id="toastMsg"></div></div>
</div>

<script>
let ws=null, myUsername='', myPeerId='', myPort=0;
let peers={}, activePeer=null, toastTimer=null, srchVal='';

function connectWS(){
  ws=new WebSocket('ws://'+location.host+'/ws');
  ws.onopen=()=>setWs(true);
  ws.onclose=()=>{setWs(false);setTimeout(connectWS,2000)};
  ws.onerror=()=>setWs(false);
  ws.onmessage=e=>{try{handle(JSON.parse(e.data))}catch(err){console.error(err)}};
}
function cmd(o){if(ws&&ws.readyState===1)ws.send(JSON.stringify(o))}

function handle(ev){
  if(ev.type==='init'){myPeerId=ev.peer_id;myPort=ev.port}
  else if(ev.type==='logged_in'){
    myUsername=ev.username;
    document.getElementById('sbUname').textContent='@'+ev.username;
    document.getElementById('loginPage').classList.add('out');
    setTimeout(()=>document.getElementById('app').classList.add('visible'),200);
    toast('👋','Добро пожаловать!','@'+ev.username+' · '+ev.ip+':'+ev.port);
  }
  else if(ev.type==='login_error'){
    document.getElementById('loginErr').textContent=ev.message;
    document.getElementById('loginBtn').disabled=false;
  }
  else if(ev.type==='peer_connected'){
    const id=ev.peer_id;
    if(!peers[id])peers[id]=mkPeer(id,ev.host,ev.port,ev.username||'');
    peers[id].online=true;
    if(ev.username)peers[id].username=ev.username;
    renderList();
    if(!activePeer)openChat(id);
    toast('✅','Подключился',ev.username?'@'+ev.username:shortId(id));
  }
  else if(ev.type==='peer_disconnected'){
    if(peers[ev.peer_id])peers[ev.peer_id].online=false;
    renderList();
    if(activePeer===ev.peer_id)refreshHead();
    toast('🔌','Отключился',shortId(ev.peer_id));
  }
  else if(ev.type==='message'){
    const id=ev.peer_id;
    if(!peers[id])peers[id]=mkPeer(id,'?',0,'');
    const m={text:ev.text,out:false,time:ev.time};
    peers[id].messages.push(m);
    peers[id].lastMsg=ev.text;peers[id].lastTime=ev.time;
    if(activePeer===id){appendBubble(m);scrollMsgs();}
    else{peers[id].unread=(peers[id].unread||0)+1;toast('📩',dname(peers[id]),ev.text.slice(0,60));}
    renderList();
  }
  else if(ev.type==='search_result'){
    if(ev.found){
      const btn=document.getElementById('searchConnBtn');
      btn.textContent='🔗 Подключиться к @'+ev.username;
      btn.dataset.host=ev.host;btn.dataset.port=ev.port;
      document.getElementById('searchResult').style.display='block';
    } else {
      document.getElementById('searchResult').style.display='none';
      toast('🔍','Не найден','@'+srchVal+' не в сети');
    }
  }
  else if(ev.type==='error')toast('⚠️','Ошибка',ev.message);
}

function doLogin(){
  const login=document.getElementById('loginInp').value.trim();
  const pass=document.getElementById('passInp').value;
  if(!login){document.getElementById('loginErr').textContent='Введите логин';return}
  if(login.length<3){document.getElementById('loginErr').textContent='Минимум 3 символа';return}
  document.getElementById('loginBtn').disabled=true;
  document.getElementById('loginErr').textContent='';
  cmd({cmd:'login',username:login,password:pass});
}
function loginKey(e){if(e.key==='Enter')doLogin()}

function onSrchInput(v){
  srchVal=v.trim();
  if(!srchVal)document.getElementById('searchResult').style.display='none';
}
function searchKey(e){
  if(e.key==='Enter'&&srchVal)cmd({cmd:'search',username:srchVal});
}
function connectByLogin(){
  const btn=document.getElementById('searchConnBtn');
  const h=btn.dataset.host,p=parseInt(btn.dataset.port);
  if(h&&p){cmd({cmd:'connect',host:h,port:p});document.getElementById('searchInp').value='';document.getElementById('searchResult').style.display='none';}
}

function doConnect(){
  const h=document.getElementById('hostInp').value.trim();
  const p=parseInt(document.getElementById('portInp').value.trim());
  if(!h||!p){toast('⚠️','Введите IP и порт','');return}
  cmd({cmd:'connect',host:h,port:p});
  document.getElementById('hostInp').value='';
  document.getElementById('portInp').value='';
}
function connKey(e){if(e.key==='Enter')doConnect()}

function doDisconnect(){
  if(!activePeer)return;
  cmd({cmd:'disconnect',peer_id:activePeer});
  peers[activePeer].online=false;
  activePeer=null;showEmpty();renderList();
}

function doSend(){
  const inp=document.getElementById('msgInp');
  const text=inp.value.trim();
  if(!text||!activePeer)return;
  cmd({cmd:'send',peer_id:activePeer,text});
  const now=new Date().toTimeString().slice(0,5);
  const m={text,out:true,time:now};
  peers[activePeer].messages.push(m);
  peers[activePeer].lastMsg=text;peers[activePeer].lastTime=now;
  appendBubble(m);scrollMsgs();renderList();
  inp.value='';inp.style.height='auto';
}

function mkPeer(id,h,p,u){return{id,host:h,port:p,username:u,online:true,messages:[],lastMsg:'',lastTime:'',unread:0}}
function av(id){return'av'+(Math.abs(parseInt(id.slice(0,4),16))%6)}
function lbl(id){return id.slice(0,2).toUpperCase()}
function shortId(id){return id.slice(0,8)+'...'}
function dname(p){return p.username?'@'+p.username:shortId(p.id)}
function esc(s){return(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}

function renderList(){
  const ol=Object.values(peers).filter(p=>p.online).length;
  document.getElementById('onlineCount').textContent=ol+' онлайн';
  document.getElementById('peerList').innerHTML=Object.values(peers).map(p=>`
    <div class="peer-item ${activePeer===p.id?'active':''}" onclick="openChat('${p.id}')">
      <div class="p-av ${av(p.id)}">${lbl(p.id)}<div class="sdot ${p.online?'':'off'}"></div></div>
      <div class="p-info">
        <div class="p-name">${esc(dname(p))}</div>
        <div class="p-prev">${esc(p.lastMsg)||'нет сообщений'}</div>
      </div>
      <div class="p-meta">
        <div class="p-time">${p.lastTime}</div>
        ${p.unread?`<div class="p-unread">${p.unread}</div>`:''}
      </div>
    </div>`).join('');
}

function openChat(id){
  activePeer=id;const p=peers[id];if(!p)return;
  p.unread=0;renderList();
  document.getElementById('chatHead').style.display='flex';
  document.getElementById('emptyState').style.display='none';
  document.getElementById('msgs').style.display='flex';
  document.getElementById('inpArea').style.display='flex';
  refreshHead();
  const area=document.getElementById('msgs');
  area.innerHTML='<div class="date-sep">СЕГОДНЯ</div>';
  p.messages.forEach(m=>area.appendChild(mkBubble(m)));
  scrollMsgs();
}

function refreshHead(){
  if(!activePeer)return;const p=peers[activePeer];if(!p)return;
  const el=document.getElementById('chAv');
  el.className='ch-av '+av(p.id);
  el.innerHTML=lbl(p.id)+(p.online?'<div class="sdot"></div>':'');
  document.getElementById('chName').textContent=dname(p);
  const st=document.getElementById('chStatus');
  st.textContent=p.online?'● в сети · зашифровано':'○ не в сети';
  st.style.color=p.online?'#2ecc71':'#bbb';
}

function appendBubble(m){
  const area=document.getElementById('msgs');
  if(!area.querySelector('.date-sep'))area.innerHTML='<div class="date-sep">СЕГОДНЯ</div>';
  area.appendChild(mkBubble(m));
}

function mkBubble(m){
  const row=document.createElement('div');row.className='msg-row'+(m.out?' out':'');
  const avEl=document.createElement('div');avEl.className='m-av '+(activePeer?av(activePeer):'av0');
  avEl.textContent=m.out?(myUsername?myUsername.slice(0,2).toUpperCase():'ME'):(activePeer&&peers[activePeer]?lbl(activePeer):'??');
  const wrap=document.createElement('div');wrap.className='m-wrap';
  const bubble=document.createElement('div');bubble.className='bubble';bubble.textContent=m.text;
  const meta=document.createElement('div');meta.className='m-meta';
  meta.innerHTML=`<span>${m.time}</span>${m.out?'<span class="m-tick">✓✓</span>':''}`;
  wrap.appendChild(bubble);wrap.appendChild(meta);
  if(!m.out)row.appendChild(avEl);row.appendChild(wrap);if(m.out)row.appendChild(avEl);
  return row;
}

function showEmpty(){
  document.getElementById('chatHead').style.display='none';
  document.getElementById('msgs').style.display='none';
  document.getElementById('inpArea').style.display='none';
  document.getElementById('emptyState').style.display='flex';
}
function scrollMsgs(){const a=document.getElementById('msgs');setTimeout(()=>a.scrollTop=a.scrollHeight,20)}
function inpKey(e){if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();doSend()}}
function autoH(el){el.style.height='auto';el.style.height=Math.min(el.scrollHeight,120)+'px'}
function setWs(ok){document.getElementById('wsDot').className='ws-dot'+(ok?' ok':'');document.getElementById('wsLabel').textContent=ok?'online':'offline'}
function toast(ico,title,msg){
  document.getElementById('toastIco').textContent=ico;
  document.getElementById('toastTitle').textContent=title;
  document.getElementById('toastMsg').textContent=msg;
  const t=document.getElementById('toast');t.classList.add('show');
  clearTimeout(toastTimer);toastTimer=setTimeout(()=>t.classList.remove('show'),3200);
}
connectWS();
</script>
</body>
</html>
"""


class GUIServer:
    def __init__(self, node, storage, tracker=None, host='127.0.0.1', port=8765):
        self.node    = node
        self.storage = storage
        self.tracker = tracker
        self.host    = host
        self.port    = port
        self._clients: set = set()
        self._username = ''
        self._my_ip = _my_ip()

    async def _index(self, request):
        return web.Response(text=HTML, content_type='text/html')

    async def _ws_handler(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self._clients.add(ws)
        await self._send(ws, {'type': 'init', 'peer_id': self.node.peer_id, 'port': self.node.port})
        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    try: await self._on_cmd(ws, msg.json())
                    except Exception as e: logger.warning("cmd: %s", e)
                elif msg.type in (web.WSMsgType.ERROR, web.WSMsgType.CLOSE):
                    break
        finally:
            self._clients.discard(ws)
        return ws

    async def _on_cmd(self, ws, data):
        c = data.get('cmd')

        if c == 'login':
            username = data.get('username', '').strip().lower()
            password = data.get('password', '')
            if not username:
                await self._send(ws, {'type': 'login_error', 'message': 'Введите логин'})
                return
            self._username = username
            # Регистрируем на трекере
            if self.tracker:
                try:
                    await self.tracker.register(self.node.peer_id, self.node.port)
                except Exception:
                    pass
            if password:
                try: self.storage.unlock(password)
                except Exception: pass
            await self._broadcast({
                'type': 'logged_in',
                'username': username,
                'ip': self._my_ip,
                'port': self.node.port,
            })

        elif c == 'search':
            username = data.get('username', '').strip().lower()
            # Ищем через трекер
            if self.tracker:
                try:
                    peers_list = await self.tracker.lookup(username)
                    if peers_list:
                        p = peers_list[0]
                        await self._send(ws, {
                            'type': 'search_result', 'found': True,
                            'username': username,
                            'host': p['ip'], 'port': p['port'],
                        })
                        return
                except Exception:
                    pass
            await self._send(ws, {'type': 'search_result', 'found': False})

        elif c == 'connect':
            host, port = data['host'], int(data['port'])
            ok = await self.node.connect_to(host, port)
            if not ok:
                await self._send(ws, {'type': 'error', 'message': f'Не удалось подключиться к {host}:{port}'})

        elif c == 'send':
            peer_id, text = data['peer_id'], data['text']
            ok = await self.node.send_to(peer_id, text)
            if ok: self.storage.save_message(peer_id, text, is_outgoing=True)
            else: await self._send(ws, {'type': 'error', 'message': 'Ошибка отправки'})

        elif c == 'disconnect':
            await self.node.disconnect_peer(data['peer_id'])

    async def _on_message(self, peer_id, msg):
        self.storage.save_message(peer_id, msg.text, is_outgoing=False)
        await self._broadcast({'type': 'message', 'peer_id': peer_id, 'text': msg.text, 'time': _ts(msg.timestamp)})

    async def _on_connect(self, info):
        await self._broadcast({'type': 'peer_connected', 'peer_id': info.peer_id, 'host': info.host, 'port': info.port, 'username': ''})

    async def _on_disconnect(self, peer_id):
        await self._broadcast({'type': 'peer_disconnected', 'peer_id': peer_id})

    async def _send(self, ws, data):
        try: await ws.send_json(data)
        except Exception: pass

    async def _broadcast(self, data):
        dead = set()
        for ws in list(self._clients):
            try: await ws.send_json(data)
            except Exception: dead.add(ws)
        self._clients -= dead

    async def run(self):
        self.node.on_message(self._on_message)
        self.node.on_connect(self._on_connect)
        self.node.on_disconnect(self._on_disconnect)

        app = web.Application()
        app.router.add_get('/',   self._index)
        app.router.add_get('/ws', self._ws_handler)

        runner = web.AppRunner(app)
        await runner.setup()
        await web.TCPSite(runner, self.host, self.port).start()

        url = f'http://{self.host}:{self.port}'
        print(f'[*] Supend GUI: {url}')
        print(f'[*] Ваш IP в сети: {self._my_ip}')
        webbrowser.open(url)

        try:
            while True: await asyncio.sleep(3600)
        except asyncio.CancelledError:
            pass
        finally:
            await runner.cleanup()

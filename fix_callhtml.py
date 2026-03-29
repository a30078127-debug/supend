f = open('ui/gui.py', encoding='utf-8')
c = f.read()
f.close()

# Вставляем HTML оверлея звонка перед закрывающим </div> основного контейнера
old = '<div class="incoming-call" id="incomingCall">'
new = '''<div class="call-overlay" id="callOverlay">
  <div class="call-avatar" id="callAvatar">?</div>
  <div class="call-name" id="callName">–</div>
  <div class="call-status" id="callStatus">Звоним...</div>
  <div class="call-timer" id="callTimer" style="display:none">0:00</div>
  <div style="display:flex;gap:16px;margin-top:10px">
    <button class="call-btn call-btn-end" onclick="endCall()" title="Завершить" style="width:56px;height:56px;border-radius:50%;background:#e74c3c;border:none;cursor:pointer;display:flex;align-items:center;justify-content:center"><svg width="24" height="24" viewBox="0 0 24 24" fill="white"><path d="M10.68 13.31a16 16 0 0 0 3.41 2.6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 2 2 0 0 1-.45-2.11 12.84 12.84 0 0 0 .7-2.81 2 2 0 0 1-2-2v-3a2 2 0 0 1 1.72-2 12.84 12.84 0 0 0 .7-2.81 2 2 0 0 1 .45-2.11L3.07 2.07A19.79 19.79 0 0 0 0 10.7 2 2 0 0 0 2 12.88h3a2 2 0 0 0 1.72-2z"/></svg></button>
  </div>
  <audio id="remoteAudio" autoplay></audio>
</div>
<div class="incoming-call" id="incomingCall">'''

if old in c:
    c = c.replace(old, new)
    f = open('ui/gui.py', 'w', encoding='utf-8')
    f.write(c)
    f.close()
    print('Готово! HTML звонка добавлен.')
else:
    print('ОШИБКА: строка не найдена!')

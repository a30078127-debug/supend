f = open('ui/gui.py', encoding='utf-8')
c = f.read()
f.close()

old = '  <div style="display:flex;gap:16px;margin-top:10px">\n    <button class="call-btn call-btn-end" onclick="endCall()"'
new = '  <div style="display:flex;gap:16px;margin-top:10px">\n    <button id="callMicBtn" onclick="toggleCallMic()" title="Микрофон" style="width:56px;height:56px;border-radius:50%;background:#1ABC9C;border:none;cursor:pointer;display:flex;align-items:center;justify-content:center"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><rect x="9" y="2" width="6" height="12" rx="3"/><path d="M5 10a7 7 0 0 0 14 0"/><line x1="12" y1="19" x2="12" y2="22"/><line x1="8" y1="22" x2="16" y2="22"/></svg></button>\n    <button class="call-btn call-btn-end" onclick="endCall()"'

if old in c:
    c = c.replace(old, new)
    f = open('ui/gui.py', 'w', encoding='utf-8')
    f.write(c)
    f.close()
    print('Готово!')
else:
    print('ОШИБКА: строка не найдена!')

import shutil

path = 'ui/gui.py'
with open(path, encoding='utf-8') as f:
    c = f.read()

results = []

# ── 1. Кнопки входящего звонка (принять/отклонить) ──────────────────────────
old1 = '    <button class="inc-btn inc-accept" onclick="acceptCall()" title="Принять">📞</button>\n    <button class="inc-btn inc-decline" onclick="declineCall()" title="Отклонить">📵</button>'
new1 = (
    '    <button onclick="acceptCall()" title="Принять" style="'
    'width:44px;height:44px;border-radius:50%;background:#fff;'
    'border:2px solid #1ABC9C;cursor:pointer;display:flex;align-items:center;'
    'justify-content:center;transition:all .2s;box-shadow:0 2px 8px rgba(26,188,156,.2)">'
    '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#1ABC9C" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.69 12 19.79 19.79 0 0 1 1.6 3.38 2 2 0 0 1 3.6 1.18h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L7.91 8.96a16 16 0 0 0 6.08 6.08l1.14-.95a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>'
    '</svg></button>\n'
    '    <button onclick="declineCall()" title="Отклонить" style="'
    'width:44px;height:44px;border-radius:50%;background:#e53935;'
    'border:none;cursor:pointer;display:flex;align-items:center;'
    'justify-content:center;transition:all .2s;box-shadow:0 2px 8px rgba(229,57,53,.3)">'
    '<svg width="20" height="20" viewBox="0 0 24 24" fill="white">'
    '<path d="M10.68 13.31a16 16 0 0 0 3.41 2.6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 2 2 0 0 1-.45-2.11 12.84 12.84 0 0 0 .7-2.81 2 2 0 0 1-2-2v-3a2 2 0 0 1 1.72-2 12.84 12.84 0 0 0 .7-2.81 2 2 0 0 1 .45-2.11L3.07 2.07A19.79 19.79 0 0 0 0 10.7 2 2 0 0 0 2 12.88h3a2 2 0 0 0 1.72-2z"/>'
    '</svg></button>'
)
results.append(('кнопки входящего звонка', old1 in c))
if old1 in c: c = c.replace(old1, new1)

# ── 2. Кнопки в оверлее звонка (микрофон + завершить) ───────────────────────
old2 = (
    '    <button id="callMicBtn" onclick="toggleCallMic()" title="Микрофон" style="width:56px;height:56px;border-radius:50%;background:#1ABC9C;border:none;cursor:pointer;display:flex;align-items:center;justify-content:center">'
    '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2">'
    '<rect x="9" y="2" width="6" height="12" rx="3"/>'
    '<path d="M5 10a7 7 0 0 0 14 0"/>'
    '<line x1="12" y1="19" x2="12" y2="22"/>'
    '<line x1="8" y1="22" x2="16" y2="22"/>'
    '</svg></button>\n'
    '    <button class="call-btn call-btn-end" onclick="endCall()" title="Завершить" style="width:56px;height:56px;border-radius:50%;background:#e74c3c;border:none;cursor:pointer;display:flex;align-items:center;justify-content:center">'
    '<svg width="24" height="24" viewBox="0 0 24 24" fill="white">'
    '<path d="M10.68 13.31a16 16 0 0 0 3.41 2.6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 2 2 0 0 1-.45-2.11 12.84 12.84 0 0 0 .7-2.81 2 2 0 0 1-2-2v-3a2 2 0 0 1 1.72-2 12.84 12.84 0 0 0 .7-2.81 2 2 0 0 1 .45-2.11L3.07 2.07A19.79 19.79 0 0 0 0 10.7 2 2 0 0 0 2 12.88h3a2 2 0 0 0 1.72-2z"/>'
    '</svg></button>'
)
new2 = (
    '    <button id="callMicBtn" onclick="toggleCallMic()" title="Микрофон" style="'
    'width:56px;height:56px;border-radius:50%;background:#1ABC9C;border:none;cursor:pointer;'
    'display:flex;align-items:center;justify-content:center;transition:all .2s;'
    'box-shadow:0 4px 16px rgba(26,188,156,.4)">'
    '<svg id="micIcon" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<rect x="9" y="2" width="6" height="12" rx="3"/>'
    '<path d="M5 10a7 7 0 0 0 14 0"/>'
    '<line x1="12" y1="19" x2="12" y2="22"/>'
    '<line x1="8" y1="22" x2="16" y2="22"/>'
    '</svg></button>\n'
    '    <button onclick="endCall()" title="Завершить" style="'
    'width:56px;height:56px;border-radius:50%;background:#e53935;border:none;cursor:pointer;'
    'display:flex;align-items:center;justify-content:center;transition:all .2s;'
    'box-shadow:0 4px 16px rgba(229,57,53,.4)">'
    '<svg width="22" height="22" viewBox="0 0 24 24" fill="white">'
    '<path d="M10.68 13.31a16 16 0 0 0 3.41 2.6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 2 2 0 0 1-.45-2.11 12.84 12.84 0 0 0 .7-2.81 2 2 0 0 1-2-2v-3a2 2 0 0 1 1.72-2 12.84 12.84 0 0 0 .7-2.81 2 2 0 0 1 .45-2.11L3.07 2.07A19.79 19.79 0 0 0 0 10.7 2 2 0 0 0 2 12.88h3a2 2 0 0 0 1.72-2z"/>'
    '</svg></button>'
)
results.append(('кнопки в оверлее звонка', old2 in c))
if old2 in c: c = c.replace(old2, new2)

# ── 3. toggleCallMic — обновить стиль кнопки и иконку ───────────────────────
old3 = (
    'function toggleCallMic(){\n'
    '  if(!localStream)return;\n'
    '  isMicMuted=!isMicMuted;\n'
    '  localStream.getAudioTracks().forEach(t=>t.enabled=!isMicMuted);\n'
    '  document.getElementById(\'callMicBtn\').classList.toggle(\'muted\',isMicMuted);\n'
    '}'
)
new3 = (
    'function toggleCallMic(){\n'
    '  if(!localStream)return;\n'
    '  isMicMuted=!isMicMuted;\n'
    '  localStream.getAudioTracks().forEach(t=>t.enabled=!isMicMuted);\n'
    '  const btn=document.getElementById(\'callMicBtn\');\n'
    '  if(isMicMuted){\n'
    '    btn.style.background=\'#fff\';\n'
    '    btn.style.boxShadow=\'0 4px 16px rgba(0,0,0,.15)\';\n'
    '    btn.innerHTML=\'<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#9e9e9e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="2" width="6" height="12" rx="3"/><path d="M5 10a7 7 0 0 0 14 0"/><line x1="12" y1="19" x2="12" y2="22"/><line x1="8" y1="22" x2="16" y2="22"/><line x1="2" y1="2" x2="22" y2="22" stroke="#e53935" stroke-width="2.5"/></svg>\';\n'
    '  } else {\n'
    '    btn.style.background=\'#1ABC9C\';\n'
    '    btn.style.boxShadow=\'0 4px 16px rgba(26,188,156,.4)\';\n'
    '    btn.innerHTML=\'<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="2" width="6" height="12" rx="3"/><path d="M5 10a7 7 0 0 0 14 0"/><line x1="12" y1="19" x2="12" y2="22"/><line x1="8" y1="22" x2="16" y2="22"/></svg>\';\n'
    '  }\n'
    '}'
)
results.append(('toggleCallMic стиль', old3 in c))
if old3 in c: c = c.replace(old3, new3)

# ── 4. Убрать кнопку палитры из сайдбара ────────────────────────────────────
old4 = (
    '    <!-- Custom button -->\n'
    '    <div style="position:absolute;right:16px;bottom:140px;z-index:51">\n'
    '      <button onclick="toggleCustom()" title="Кастомизация" style="width:52px;height:52px;border-radius:50%;background:#fff;border:none;display:flex;align-items:center;justify-content:center;cursor:pointer;box-shadow:0 4px 16px rgba(0,0,0,.15);font-size:22px;transition:transform .2s,box-shadow .2s" onmouseover="this.style.transform=\'scale(1.08)\';this.style.boxShadow=\'0 6px 20px rgba(0,0,0,.2)\'" onmouseout="this.style.transform=\'scale(1)\';this.style.boxShadow=\'0 4px 16px rgba(0,0,0,.15)\'">🎨</button>\n'
    '    </div>'
)
new4 = '    <!-- Custom button moved to input area -->'
results.append(('убрать палитру из сайдбара', old4 in c))
if old4 in c: c = c.replace(old4, new4)

# ── 5. Добавить кнопку палитры над микрофоном в input area ──────────────────
old5 = '      <button class="voice-btn" id="voiceBtn"'
new5 = (
    '      <button onclick="toggleCustom()" title="Кастомизация" style="'
    'width:46px;height:46px;border-radius:50%;background:#fff;border:2px solid #e0e0e0;'
    'display:flex;align-items:center;justify-content:center;cursor:pointer;'
    'flex-shrink:0;font-size:20px;transition:all .2s;box-shadow:0 2px 8px rgba(0,0,0,.1)" '
    'onmouseover="this.style.borderColor=\'#1ABC9C\'" '
    'onmouseout="this.style.borderColor=\'#e0e0e0\'">🎨</button>\n'
    '      <button class="voice-btn" id="voiceBtn"'
)
results.append(('кнопка палитры в input area', old5 in c))
if old5 in c: c = c.replace(old5, new5)

# ── Итог ────────────────────────────────────────────────────────────────────
print()
all_ok = True
for name, found in results:
    print(f"  {'v' if found else 'X НЕ НАЙДЕНО'}  {name}")
    if not found: all_ok = False

if all_ok:
    shutil.copy(path, path + '.backup')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(c)
    print('\nГотово! ui/gui.py обновлён.')
else:
    print('\nФайл НЕ сохранён — есть незамененные блоки.')

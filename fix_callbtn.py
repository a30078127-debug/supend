f = open('ui/gui.py', encoding='utf-8')
c = f.read()
f.close()

old = '      <button class="ico-btn" onclick="doDisconn()">'
new = '      <button class="call-ico-btn" id="callBtn" onclick="startCall()" title="Позвонить"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.69 12 19.79 19.79 0 0 1 1.6 3.38 2 2 0 0 1 3.6 1.18h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L7.91 8.96a16 16 0 0 0 6.08 6.08l1.14-.95a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg></button>\n      <button class="ico-btn" onclick="doDisconn()">'

if old in c:
    c = c.replace(old, new)
    f = open('ui/gui.py', 'w', encoding='utf-8')
    f.write(c)
    f.close()
    print('Готово! Кнопка звонка добавлена.')
else:
    print('ОШИБКА: строка не найдена!')

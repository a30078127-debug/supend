f = open('ui/gui.py', encoding='utf-8')
c = f.read()
f.close()

# Заменяем сломанный префикс на правильный
old = "txt.startsWith('\x00SC\x00')"
new = "txt.startsWith('\\x00SC\\x00')"

if old in c:
    c = c.replace(old, new)
    f = open('ui/gui.py', 'w', encoding='utf-8')
    f.write(c)
    f.close()
    print('Готово!')
else:
    print('Ищем другой вариант...')
    idx = c.find('SC')
    print(repr(c[idx-20:idx+20]))

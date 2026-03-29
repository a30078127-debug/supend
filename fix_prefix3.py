f = open('ui/gui.py', encoding='utf-8')
c = f.read()
f.close()

old = "txt.startsWith('\\x00SC\\x00')"
new = "txt.startsWith('\x00SC\x00')"

c = c.replace(old, new)
f = open('ui/gui.py', 'w', encoding='utf-8')
f.write(c)
f.close()

# Проверим
f = open('ui/gui.py', encoding='utf-8')
c2 = f.read()
f.close()
idx = c2.find('txt.startsWith')
print(repr(c2[idx:idx+40]))

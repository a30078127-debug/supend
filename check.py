f = open('ui/gui.py', encoding='utf-8')
c = f.read()
f.close()

idx = c.find("txt.startsWith")
print(repr(c[idx:idx+50]))

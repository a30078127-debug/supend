f = open('ui/gui.py', encoding='utf-8')
c = f.read()
f.close()

# Заменяем нулевые байты на безопасную строку
c = c.replace("CALL_PREFIX    = \"\x00SC\x00\"", "CALL_PREFIX    = \"__SC__\"")
c = c.replace("txt.startsWith('\x00SC\x00')", "txt.startsWith('__SC__')")
c = c.replace("const CALL_PREFIX = '\\x00SC\\x00'", "const CALL_PREFIX = '__SC__'")

f = open('ui/gui.py', 'w', encoding='utf-8')
f.write(c)
f.close()
print('Готово!')

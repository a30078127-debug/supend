f = open('ui/gui.py', encoding='utf-8')
c = f.read()
f.close()

old = 'GROUP_PREFIX   = "__SG__"'
new = 'GROUP_PREFIX   = "__SG__"\nCALL_PREFIX    = "\\x00SC\\x00"'

if 'CALL_PREFIX' in c:
    print('CALL_PREFIX уже есть — файл уже исправлен!')
elif old in c:
    c = c.replace(old, new)
    f = open('ui/gui.py', 'w', encoding='utf-8')
    f.write(c)
    f.close()
    print('Готово! CALL_PREFIX добавлен.')
else:
    print('ОШИБКА: строка GROUP_PREFIX не найдена, проверь файл!')

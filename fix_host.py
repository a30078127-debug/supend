f=open('main.py',encoding='utf-8')
c=f.read()
f.close()
old="host='127.0.0.1', port=args.gui_port"
new="host='0.0.0.0', port=args.gui_port"
print('found:', old in c)
if old in c:
    c=c.replace(old,new)
    open('main.py','w',encoding='utf-8').write(c)
    print('Done!')

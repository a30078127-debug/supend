f=open('ui/gui.py',encoding='utf-8')
c=f.read()
f.close()
idx=c.find('reply-preview')
while idx>=0:
    print(repr(c[idx:idx+120]))
    print('---')
    idx=c.find('reply-preview',idx+1)

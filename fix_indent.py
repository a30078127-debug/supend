f=open('ui/gui.py',encoding='utf-8')
c=f.read()
f.close()
old="            inv_code = data.get('invCode', '')\n                    await self._broadcast({'type': 'register_ok', 'username': username, 'bio': bio, 'avatar': avatar, 'invCode': inv_code})"
new="            inv_code = data.get('invCode', '')\n            await self._broadcast({'type': 'register_ok', 'username': username, 'bio': bio, 'avatar': avatar, 'invCode': inv_code})"
print('found:', old in c)
if old in c:
    c=c.replace(old,new)
    open('ui/gui.py','w',encoding='utf-8').write(c)
    print('Done!')
else:
    print('not found')

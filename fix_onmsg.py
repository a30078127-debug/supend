f=open('ui/gui.py',encoding='utf-8')
c=f.read()
f.close()
old="            self.storage.save_message(peer_id, text, is_outgoing=False)\n        await self._broadcast({'type': 'message', 'peer_id': peer_id, 'text': text, 'time': _ts(msg.timestamp)})"
new="            real_t=text\n            if text.startswith('__MSG__'):\n                try:\n                    import json as _mj2;_md2=_mj2.loads(text[7:]);real_t=_md2.get('text',text)\n                except:pass\n            self.storage.save_message(peer_id, real_t, is_outgoing=False)\n        await self._broadcast({'type': 'message', 'peer_id': peer_id, 'text': text, 'time': _ts(msg.timestamp)})"
print('found:', old in c)
if old in c:
    c=c.replace(old,new)
    open('ui/gui.py','w',encoding='utf-8').write(c)
    print('Done!')
else:
    print('not found')

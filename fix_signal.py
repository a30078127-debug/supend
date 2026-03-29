f=open('ui/gui.py',encoding='utf-8')
c=f.read()
f.close()

old='            try:\n                await self.tracker.start_signal_listener(self.node.peer_id, self._on_call_signal)\n            except Exception as e:\n                logger.warning("Signal start error: %s", e)\n            try:\n                await self.tracker.start_signal_listener(self.node.peer_id, self._on_call_signal)\n            except Exception as e:\n                logger.warning("Signal start error: %s", e)\n'
new='            try:\n                await self.tracker.start_signal_listener(self.node.peer_id, self._on_call_signal)\n            except Exception as e:\n                logger.warning("Signal start error: %s", e)\n'

print('found:', old in c)
if old in c:
    c=c.replace(old,new)
    f=open('ui/gui.py','w',encoding='utf-8')
    f.write(c)
    f.close()
    print('Done!')
else:
    print('не найдено')

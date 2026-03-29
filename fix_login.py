import asyncio as _a
f=open('ui/gui.py',encoding='utf-8')
c=f.read()
f.close()

# Исправление 1 - убрать дублированный except
old1='            try:\n                await self.tracker.start_signal_listener(self.node.peer_id, self._on_call_signal)\n            except Exception as e:\n                logger.warning("Signal start error: %s", e)\n            except Exception as e:\n                logger.warning("Relay start error: %s", e)\n'
new1='            try:\n                await self.tracker.start_signal_listener(self.node.peer_id, self._on_call_signal)\n            except Exception as e:\n                logger.warning("Signal start error: %s", e)\n'
print('fix1:', old1 in c)
if old1 in c: c=c.replace(old1,new1)

# Исправление 2 - таймаут на register в _do_enter
old2='await self.tracker.register(self.node.peer_id, self.node.port, username)'
new2='await asyncio.wait_for(self.tracker.register(self.node.peer_id, self.node.port, username), timeout=5.0)'
print('fix2:', old2 in c)
if old2 in c: c=c.replace(old2,new2)

f=open('ui/gui.py','w',encoding='utf-8')
f.write(c)
f.close()
print('Done!')

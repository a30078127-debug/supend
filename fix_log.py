f=open('ui/gui.py',encoding='utf-8')
c=f.read()
f.close()
old='try: await asyncio.wait_for(self.tracker.register(self.node.peer_id, self.node.port, username), timeout=5.0)\n            except: pass'
new='try:\n                res=await asyncio.wait_for(self.tracker.register(self.node.peer_id, self.node.port, username), timeout=5.0)\n                print("[*] Tracker login reg: "+str(username)+" port="+str(self.node.port)+" ok="+str(res))\n            except Exception as e:\n                print("[!] Tracker error: "+str(e))'
print('found:', old in c)
if old in c:
    c=c.replace(old,new)
    open('ui/gui.py','w',encoding='utf-8').write(c)
    print('Done!')
else:
    print('not found')

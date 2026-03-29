f=open('ui/gui.py',encoding='utf-8')
c=f.read()
f.close()
old="                real_text2=text\n                    if text.startswith('__MSG__'):\n                        try:\n                            import json as _mj3;_md3=_mj3.loads(text[7:]);real_text2=_md3.get('text',text)\n                        except:pass\n                    if not real_text2.startswith(PROFILE_PREFIX) and not real_text2.startswith(FILE_PREFIX) and not real_text2.startswith(GROUP_PREFIX):\n                        self.storage.save_message(peer_id, real_text2, is_outgoing=True)"
new="                real_text2=text\n                if text.startswith('__MSG__'):\n                    try:\n                        import json as _mj3;_md3=_mj3.loads(text[7:]);real_text2=_md3.get('text',text)\n                    except:pass\n                if not real_text2.startswith(PROFILE_PREFIX) and not real_text2.startswith(FILE_PREFIX) and not real_text2.startswith(GROUP_PREFIX):\n                    self.storage.save_message(peer_id, real_text2, is_outgoing=True)"
print('found:', old in c)
if old in c:
    c=c.replace(old,new)
    open('ui/gui.py','w',encoding='utf-8').write(c)
    print('Done!')
else:
    print('not found')

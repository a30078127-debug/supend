with open('ui/gui.py', encoding='utf-8') as f:
    c = f.read()

results = []

# ── 1. peer send with __MSG__ envelope ──────────────────────────────────────
old1 = "    cmd({cmd:'send',peer_id:active,text});\n    playSendSound();\n    earnCoins(text, undefined, 'За сообщение ('+text.length+' симв.)');\n    const m={id:Date.now()+'_out',text,out:true,time:now,type:'text'};\n    if(replyToId){m.replyTo=replyToId;m.replyToText=replyToText;m.replyToName=replyToName;cancelReply();}\n    peers[active].messages.push(m);peers[active].lastMsg=text;peers[active].lastTime=now;\n    appendBubble(m,'peer');"
new1 = "    const msgId=Date.now()+'_p'+myId.slice(0,4);\n    const replyData=replyToId?{replyTo:replyToId,replyToText,replyToName}:{};\n    const envelope='__MSG__'+JSON.stringify({id:msgId,text,...replyData});\n    cmd({cmd:'send',peer_id:active,text:envelope});\n    playSendSound();\n    earnCoins(text, undefined, 'За сообщение ('+text.length+' симв.)');\n    const m={id:msgId,text,out:true,time:now,type:'text',...replyData};\n    if(replyToId)cancelReply();\n    peers[active].messages.push(m);peers[active].lastMsg=text;peers[active].lastTime=now;\n    appendBubble(m,'peer');"
results.append(('peer send with __MSG__ envelope', old1 in c))
if old1 in c: c = c.replace(old1, new1)

# ── 2. receive __MSG__ envelope ──────────────────────────────────────────────
old2 = "    if(blacklist.has(id))return; // blocked\n    const m={id:Date.now()+'_r',text:txt,out:false,time:ev.time,type:'text',from:id};"
new2 = "    if(blacklist.has(id))return; // blocked\n    let msgTxt=txt,msgId=Date.now()+'_r',msgReply={};\n    if(txt.startsWith('__MSG__')){try{const env=JSON.parse(txt.slice(7));msgTxt=env.text||txt;msgId=env.id||msgId;if(env.replyTo)msgReply={replyTo:env.replyTo,replyToText:env.replyToText||'',replyToName:env.replyToName||''};}catch(e){}}\n    const m={id:msgId,text:msgTxt,out:false,time:ev.time,type:'text',from:id,...msgReply};"
results.append(('receive __MSG__ envelope', old2 in c))
if old2 in c: c = c.replace(old2, new2)

# ── 3. Python _on_message — pass through __MSG__ ─────────────────────────────
old3 = "        if not text.startswith(PROFILE_PREFIX) and not text.startswith(FILE_PREFIX) and not text.startswith(GROUP_PREFIX) and not text.startswith(CALL_PREFIX):\n                self.storage.save_message(peer_id, text, is_outgoing=False)\n            await self._broadcast({'type': 'message', 'peer_id': peer_id, 'text': text, 'time': _ts(msg.timestamp)})"
new3 = "        real_text=text\n            if text.startswith('__MSG__'):\n                try:\n                    import json as _mj2;_md2=_mj2.loads(text[7:]);real_text=_md2.get('text',text)\n                except:pass\n            if not real_text.startswith(PROFILE_PREFIX) and not real_text.startswith(FILE_PREFIX) and not real_text.startswith(GROUP_PREFIX) and not real_text.startswith(CALL_PREFIX):\n                self.storage.save_message(peer_id, real_text, is_outgoing=False)\n            await self._broadcast({'type': 'message', 'peer_id': peer_id, 'text': text, 'time': _ts(msg.timestamp)})"
results.append(('Python _on_message __MSG__', old3 in c))
if old3 in c: c = c.replace(old3, new3)

# ── 4. Python send handler — save real text not envelope ─────────────────────
old4 = "            if not text.startswith(PROFILE_PREFIX) and not text.startswith(FILE_PREFIX) and not text.startswith(GROUP_PREFIX):\n                    self.storage.save_message(peer_id, text, is_outgoing=True)"
new4 = "            real_text2=text\n                    if text.startswith('__MSG__'):\n                        try:\n                            import json as _mj3;_md3=_mj3.loads(text[7:]);real_text2=_md3.get('text',text)\n                        except:pass\n                    if not real_text2.startswith(PROFILE_PREFIX) and not real_text2.startswith(FILE_PREFIX) and not real_text2.startswith(GROUP_PREFIX):\n                        self.storage.save_message(peer_id, real_text2, is_outgoing=True)"
results.append(('Python send handler __MSG__', old4 in c))
if old4 in c: c = c.replace(old4, new4)

with open('ui/gui.py', 'w', encoding='utf-8') as f:
    f.write(c)

print()
for name, found in results:
    print(f"  {'v' if found else 'X НЕ НАЙДЕНО'}  {name}")
print('\nГотово!')

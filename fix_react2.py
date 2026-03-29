f=open('ui/gui.py',encoding='utf-8')
c=f.read()
f.close()

old="""          if(!msg.reactions)msg.reactions={};
          if(!msg.reactions[d.emoji])msg.reactions[d.emoji]=[];
          const idx=msg.reactions[d.emoji].indexOf(d.userId);
          if(idx>=0)msg.reactions[d.emoji].splice(idx,1);else msg.reactions[d.emoji].push(d.userId);
          const row=document.getElementById('react_'+d.msgId);
          if(row)renderReactRow(msg,row);"""

new="""          if(!msg.reactions)msg.reactions={};
          // Remove old reaction from this user
          Object.keys(msg.reactions).forEach(e=>{
            const i=msg.reactions[e].indexOf(d.userId);
            if(i>=0)msg.reactions[e].splice(i,1);
          });
          // Add new if not toggling same
          if(!d.oldEmoji||d.oldEmoji!==d.emoji){
            if(!msg.reactions[d.emoji])msg.reactions[d.emoji]=[];
            msg.reactions[d.emoji].push(d.userId);
          }
          const row=document.getElementById('react_'+d.msgId);
          if(row)renderReactRow(msg,row);"""

print('found:', old in c)
if old in c:
    c=c.replace(old,new)
    f=open('ui/gui.py','w',encoding='utf-8')
    f.write(c)
    f.close()
    print('Готово!')

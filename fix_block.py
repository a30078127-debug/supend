f=open('ui/gui.py',encoding='utf-8')
c=f.read()
f.close()
old="""function ctxToggleBlock(){
  hidePeerCtx();
  if(!ctxTgt)return;"""
new="""function ctxToggleBlock(){
  const _tgt=ctxTgt;
  hidePeerCtx();
  if(!_tgt)return;
  ctxTgt=_tgt;"""
print('found:', old in c)
if old in c:
    c=c.replace(old,new)
    open('ui/gui.py','w',encoding='utf-8').write(c)
    print('Done!')
else:
    print('not found')

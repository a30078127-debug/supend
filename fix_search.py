f=open('ui/gui.py',encoding='utf-8')
c=f.read()
f.close()

# 1. Переименовать первую doSearch в doUserSearch
c=c.replace('onclick="doSearch()"','onclick="doUserSearch()"')
c=c.replace('function srchKey(e){if(e.key===\'Enter\')doSearch()}','function srchKey(e){if(e.key===\'Enter\')doUserSearch()}')
c=c.replace('function doSearch(){const v=document.getElementById(\'srchInp\')','function doUserSearch(){const v=document.getElementById(\'srchInp\')')

print('Done!')
open('ui/gui.py','w',encoding='utf-8').write(c)

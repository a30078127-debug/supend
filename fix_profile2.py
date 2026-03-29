f=open('ui/gui.py',encoding='utf-8')
c=f.read()
f.close()

old="if(saved)walletData = saved;"
new="""if(saved)walletData = saved;
  try{const sp=JSON.parse(localStorage.getItem('sup_profile'));if(sp)profileData=sp;}catch(e){}
  if(!profileData.registeredAt){
    profileData.registeredAt=new Date().toLocaleDateString('ru',{day:'numeric',month:'long',year:'numeric'});
    try{localStorage.setItem('sup_profile',JSON.stringify(profileData))}catch(e){}
  }"""

if old in c:
    c=c.replace(old,new,1)
    f=open('ui/gui.py','w',encoding='utf-8')
    f.write(c)
    f.close()
    print('Готово!')
else:
    print('не найдено')

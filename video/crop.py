from PIL import Image
im=Image.open('assets/menu.png').convert('RGB')
s=1284/924
items={'chicken':(132,925,46),'lamb':(352,925,46),'fish':(571,925,46),'mutabaq':(790,925,46),
'mix':(352,1280,46),'broasted':(571,1328,46),'massoub':(790,1288,23),'molokhia':(539,1192,23),
'lamb_edam':(602,1192,23),'mazbi':(320,1131,23),'double_mandi':(382,1131,23),'full_mandi':(101,1252,23),'half_mandi':(163,1252,23)}
sheet=Image.new('RGB',(13*150,150))
for i,(k,(x,y,r)) in enumerate(items.items()):
    c=im.crop((int((x-r)*s),int((y-r)*s),int((x+r)*s),int((y+r)*s)))
    c.save(f'assets/{k}.png'); print(k,c.size)
    sheet.paste(c.resize((150,150)),(i*150,0))
sheet.save('/tmp/claude-0/-home-user-oncoal/fb0ac52a-6330-5bc9-a2c9-5c62305f79fc/scratchpad/sheet.png')

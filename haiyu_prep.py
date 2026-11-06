# 灰羽計畫 第二步：比對＋取詳細資料＋照片＋縮圖拼圖。
# 用法：python3 -I haiyu_prep.py diff [--full]   → need.json、gone.txt、changed.txt
#       python3 -I haiyu_prep.py sheets          → photos/<n>_1.jpg、sheets/sheet_XX.png、sheet_index.json
#       python3 -I haiyu_prep.py full 3 7 12 ... → 下載這些編號的全部照片與說明到 photos/<n>/，寫 detail.json
import json,re,sys,os,time,urllib.request,http.client,io
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"
def raw(url,cookie=None):
    h={"User-Agent":UA,"Accept-Language":"ja-JP"}
    if cookie: h["Cookie"]=cookie
    r=urllib.request.urlopen(urllib.request.Request(url,headers=h),timeout=25)
    try: return r.read()
    except http.client.IncompleteRead as e: return e.partial
def get(url,cookie=None): return raw(url,cookie).decode("utf-8","ignore")
mode=sys.argv[1]

if mode=="diff":
    FULL="--full" in sys.argv
    cand=json.load(open("cand.json"))
    known={}
    if os.path.exists("known.txt"):
        for ln in open("known.txt",encoding="utf-8"):
            p=ln.rstrip("\n").split("\t")
            if len(p)>=2 and p[0]: known[p[0]]=p[1:]
    now=time.time(); need=[]; changed=[]
    keys=set()
    for c in cand:
        k=c["site"]+":"+c["id"]; keys.add(k)
        if k in known:
            old=known[k][0]
            if old and str(c["price"])!=old and c["site"] not in("Amazon",):
                changed.append(f"{k}\t{old}→{c['price']}"); c["why"]="價格變動"; need.append(c)
            continue
        recent=c.get("ts",0)>=now-30*3600
        if FULL or recent or not c.get("ts"):
            c["why"]="新" if (FULL or recent) else "無時間戳且未判斷"; need.append(c)
    gone=[k for k in known if k not in keys]
    for i,c in enumerate(need,1): c["n"]=i
    json.dump(need,open("need.json","w"),ensure_ascii=False,indent=0)
    open("gone.txt","w").write("\n".join(gone)); open("changed.txt","w").write("\n".join(changed))
    print(f"候選 {len(cand)}／需判斷 {len(need)}（價格變動 {len(changed)}）／已不見 {len(gone)}")

def photo_urls(c):
    s,i=c["site"],c["id"]
    try:
        if s=="メルカリ":
            return [f"https://static.mercdn.net/item/detail/orig/photos/{i}_{n}.jpg" for n in range(1,11)]
        if s=="メルカリShops": return [c["thumb"].replace("/small/","/large/")] if c.get("thumb") else []
        if s in("ヤフオク","PayPayフリマ"):
            h=get(c["url"]); u=[]
            for m in re.findall(r'https://auctions\.c\.yimg\.jp/images\.auctions\.yahoo\.co\.jp/image/[^"\\\s?]+?\.jpg',h):
                if m not in u: u.append(m)
            if not u: u=[m for m in dict.fromkeys(re.findall(r'https://(?:paypayfleamarket|auctions)[^"\\\s]*?/(?:item|image)[^"\\\s]+?\.jpg',h))]
            return u
        if s=="ラクマ":
            h=get(c["url"]); return list(dict.fromkeys(re.findall(r'https://img\.fril\.jp/img/[^"\\\s?]+\.(?:jpg|jpeg|png)',h)))
        if s=="まんだらけ":
            h=get(c["url"],cookie="tr_mndrk_user=1"); return list(dict.fromkeys(re.findall(r'https://img\.mandarake\.co\.jp/webshopimg/[^"\\\s]+?\.jpg',h)))
    except Exception as e: print("照片網址錯誤",s,i,e)
    return []

def save_img(url,path):
    from PIL import Image
    b=raw(url)
    im=Image.open(io.BytesIO(b)).convert("RGB"); im.save(path,"JPEG",quality=88); return im

if mode=="sheets":
    from PIL import Image,ImageDraw,ImageFont
    need=json.load(open("need.json")); os.makedirs("photos",exist_ok=True); os.makedirs("sheets",exist_ok=True)
    ok=[];fail=[]
    for c in need:
        if c["site"] in("Amazon","Book Off","NetOff"): continue   # 示意圖：不需照片
        urls=[c["thumb"]] if c["site"]=="メルカリShops" and c.get("thumb") else photo_urls(c)[:1]
        if c["site"]=="メルカリ": urls=[f"https://static.mercdn.net/item/detail/orig/photos/{c['id']}_1.jpg"]
        if c["site"] in("ヤフオク","PayPayフリマ") and not urls and c.get("thumb"): urls=[c["thumb"]]
        p=f"photos/{c['n']}_1.jpg"
        try: save_img(urls[0],p); ok.append(c["n"])
        except Exception as e: fail.append(c["n"])
        time.sleep(0.15)
    try: font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",34)
    except Exception: font=ImageFont.load_default()
    W,H,COLS,ROWS=420,420,3,3; idx={}
    for si in range(0,len(ok),COLS*ROWS):
        grp=ok[si:si+COLS*ROWS]; sheet=Image.new("RGB",(W*COLS,H*ROWS),"white"); d=ImageDraw.Draw(sheet)
        for j,n in enumerate(grp):
            im=Image.open(f"photos/{n}_1.jpg"); im.thumbnail((W-8,H-8))
            x,y=(j%COLS)*W+4,(j//COLS)*H+4; sheet.paste(im,(x,y))
            d.rectangle([x,y,x+78,y+44],fill="black"); d.text((x+6,y+3),str(n),fill="yellow",font=font)
        name=f"sheets/sheet_{si//(COLS*ROWS)+1:02d}.png"; sheet.save(name); idx[name]=grp
    json.dump({"sheets":idx,"photo_fail":fail},open("sheet_index.json","w"),ensure_ascii=False,indent=0)
    print(f"拼圖 {len(idx)} 張（每張 9 件）；照片下載失敗 {len(fail)} 件：{fail}")

if mode=="full":
    need={c["n"]:c for c in json.load(open("need.json"))}
    out={}
    for n in map(int,sys.argv[2:]):
        c=need[n]; d=f"photos/{n}"; os.makedirs(d,exist_ok=True); desc=""; extra={}
        try:
            if c["site"]=="メルカリ":
                if "mcall" not in globals(): exec(open("haiyu_lib.py",encoding="utf-8").read(),globals())
                it=mcall("https://api.mercari.jp/items/get?id="+c["id"])["data"]
                desc=it.get("description",""); extra={"photos":len(it.get("photos",[])),"shipping":it.get("shipping_payer",{}).get("name","")}
                urls=it.get("photos") or photo_urls(c)
            elif c["site"] in("ヤフオク","PayPayフリマ"):
                h=get(c["url"]); m=re.search(r'"description":"((?:[^"\\]|\\.)*)"',h)
                desc=json.loads('"'+m.group(1)+'"') if m else ""; urls=photo_urls(c)
            elif c["site"]=="ラクマ":
                h=get(c["url"]); m=re.search(r'<div class="item__description[^>]*>(.*?)</div>',h,re.S)
                desc=re.sub(r"<[^>]+>","",m.group(1)).strip() if m else ""
                st=re.search(r'商品の状態</th>\s*<td[^>]*>\s*([^<]+)',h); extra={"cond":st.group(1).strip() if st else ""}
                urls=photo_urls(c)
            elif c["site"]=="まんだらけ":
                h=get(c["url"],cookie="tr_mndrk_user=1"); m=re.search(r'<div class="(?:caption|explanation)[^"]*">(.*?)</div>',h,re.S)
                desc=re.sub(r"<[^>]+>"," ",m.group(1)).strip() if m else ""; urls=photo_urls(c)
            else: urls=photo_urls(c)
        except Exception as e: desc=f"（說明取得失敗：{e}）"; urls=photo_urls(c)
        got=0
        for k,u in enumerate(urls[:12],1):
            try: save_img(u,f"{d}/{k}.jpg"); got+=1
            except Exception: pass
            time.sleep(0.15)
        out[n]={"site":c["site"],"title":c["title"],"url":c["url"],"desc":desc[:3000],"photos":got,**extra}
    old=json.load(open("detail.json")) if os.path.exists("detail.json") else {}
    old.update({str(k):v for k,v in out.items()}); json.dump(old,open("detail.json","w"),ensure_ascii=False,indent=0)
    print({k:(v["photos"],len(v["desc"])) for k,v in out.items()})

# 灰羽計畫 第三步・第二階段準備：用法 python3 -I huiyu_s2.py <編號…>（或讀 stage2_ids.json）。取說明＋照片，每件做一張合成圖（最多 6 張照片，3x2，每格 520px）
import json,sys,os,re,io,time,concurrent.futures as cf
exec(open("huiyu_lib.py",encoding="utf-8").read())
src=open("huiyu_prep.py",encoding="utf-8").read()
exec(src.split("mode=sys.argv[1]")[0])                 # raw/get
exec("def photo_urls"+src.split("def photo_urls")[1].split("def save_img")[0])
from PIL import Image,ImageDraw,ImageFont
need={c["n"]:c for c in json.load(open("need.json"))}
ids=[int(x) for x in sys.argv[1:]] if len(sys.argv)>1 else json.load(open("stage2_ids.json"))
os.makedirs("s2",exist_ok=True)
font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",30)
def work(n):
    c=need[n]; out={"n":n,"site":c["site"],"title":c["title"],"url":c["url"],"price":c["price"],"cond":c.get("cond",""),"end":c.get("end",""),"created":c.get("created",""),"shop":c.get("shop",""),"desc":"","photos":0}
    urls=[]
    try:
        if c["site"]=="メルカリ":
            it=mcall("https://api.mercari.jp/items/get?id="+c["id"])["data"]
            out["desc"]=it.get("description",""); urls=it.get("photos") or []
            out["shipping"]=(it.get("shipping_payer") or {}).get("name","")
            out["status"]=it.get("status","")
        elif c["site"] in("ヤフオク","PayPayフリマ"):
            h=get(c["url"]); m=re.search(r'"description":"((?:[^"\\]|\\.)*)"',h)
            if m:
                try: out["desc"]=re.sub(r"<[^>]+>"," ",json.loads('"'+m.group(1)+'"'))
                except Exception: out["desc"]=m.group(1)
            urls=list(dict.fromkeys(re.findall(r'https://auctions\.c\.yimg\.jp/images\.auctions\.yahoo\.co\.jp/image/[^"\\\s?]+?\.jpg',h)))
            if not urls and c.get("thumb"): urls=[re.sub(r"^https://auc-pctr\.c\.yimg\.jp/i/","https://",c["thumb"]).split("?")[0]]
        elif c["site"]=="ラクマ":
            h=get(c["url"]); m=re.search(r'<div class="item__description[^>]*>(.*?)</div>',h,re.S)
            out["desc"]=re.sub(r"<[^>]+>","",m.group(1)).strip() if m else ""
            st=re.search(r'商品の状態</th>\s*<td[^>]*>\s*([^<]+)',h); out["cond"]=st.group(1).strip() if st else out["cond"]
            urls=photo_urls(c)
        elif c["site"]=="メルカリShops":
            d=mcall(f"https://api.mercari.jp/v1/marketplaces/shops/products/{c['id']}?view=FULL"); p=d.get("productDetail",{})
            out["desc"]=p.get("description",""); urls=p.get("photos") or []
            out["cond"]=(p.get("condition") or {}).get("displayName",out["cond"])
        else: urls=photo_urls(c)
    except Exception as e: out["desc"]=f"（說明取得失敗：{e}）"
    out["desc"]=out["desc"][:2500]
    lim=6 if (c["tier"] in ("簽名","首刷本","一般") or "套組" in c["flags"] or "特装" in c["flags"]) else 3
    ims=[]
    for u in urls[:lim]:
        try:
            im=Image.open(io.BytesIO(raw(u))).convert("RGB"); ims.append(im)
        except Exception: pass
    out["photos"]=len(ims); out["photos_total"]=len(urls)
    if ims:
        C=3 if len(ims)>2 else len(ims); Rr=(len(ims)+C-1)//C; S=520
        sheet=Image.new("RGB",(S*C,S*Rr),"white"); d=ImageDraw.Draw(sheet)
        for j,im in enumerate(ims):
            im.thumbnail((S-6,S-6)); x,y=(j%C)*S+3,(j//C)*S+3; sheet.paste(im,(x,y))
            d.rectangle([x,y,x+44,y+38],fill="black"); d.text((x+8,y+2),str(j+1),fill="yellow",font=font)
        sheet.save(f"s2/{n}.jpg",quality=85)
    return out
res={}
with cf.ThreadPoolExecutor(6) as ex:
    for o in ex.map(work,ids): res[o["n"]]=o
old=json.load(open("s2_detail.json")) if os.path.exists("s2_detail.json") else {}
old.update({str(k):v for k,v in res.items()})
json.dump(old,open("s2_detail.json","w"),ensure_ascii=False,indent=0)
print(len(res),"件；有合成圖",sum(1 for v in res.values() if v["photos"]))

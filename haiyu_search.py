# 灰羽計畫 第一步：搜尋＋文字初篩。用法：python3 -I haiyu_search.py [--full]
import json,time,uuid,base64,re,sys,urllib.request,urllib.parse,unicodedata,datetime,http.cookiejar
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
FULL="--full" in sys.argv
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"
NOW=time.time(); TW=datetime.timezone(datetime.timedelta(hours=8))
LOG=[]
def log(*a): LOG.append(" ".join(map(str,a)))
import http.client
def get(url,cookie=None,timeout=25):
    h={"User-Agent":UA,"Accept-Language":"ja-JP,ja;q=0.9"}
    if cookie: h["Cookie"]=cookie
    r=urllib.request.urlopen(urllib.request.Request(url,headers=h),timeout=timeout)
    try: b=r.read()
    except http.client.IncompleteRead as e: b=e.partial
    return b.decode("utf-8","ignore")
def q(s): return urllib.parse.quote(s)
def twdate(ts): return datetime.datetime.fromtimestamp(ts,TW).strftime("%Y-%m-%d") if ts else "不明"

# ---------- 關鍵字 ----------
KW=["魔女の旅々","魔女の旅々 特典","魔女の旅々 特装版","魔女の旅々 限定","魔女の旅々 セット","魔女の旅々 まとめ売り",
    "魔女の旅々 初版","魔女の旅々 帯","魔女の旅々 サイン","白石定規 サイン","あずーる サイン",
    "魔女の旅々 アニメイト","魔女の旅々 メロンブックス","魔女の旅々 ゲーマーズ","魔女の旅々 とらのあな",
    "魔女の旅々 リーフレット","魔女の旅々 ブロマイド","魔女の旅々 イラストカード","魔女の旅々 色紙","魔女の旅々 タペストリー",
    "魔女の旅々 デジパック","魔女の旅々 収納BOX","魔女の旅々 ドラマCD","魔女の旅々 キャストトーク","魔女の旅々 ミニノート",
    "魔女の旅々 設定資料集","魔女の旅々 画集","あずーる 画集","あずーる 同人誌","あずーる イレイナ",
    "イレイナ 特典","魔女の旅々 フェア 特典","魔女の旅々 連動購入","魔女の旅々 レーベルポイント",
    "魔女の旅々 学園物語","祈りの国のリリエール",
    "魔女の旅々 4","魔女の旅々 4巻","魔女の旅々 21"]
KW_AMZ=["魔女の旅々 特装版","魔女の旅々 限定版","魔女の旅々 サイン","魔女の旅々 設定資料集","魔女の旅々 画集","あずーる 画集"]
KW_SHOP=["魔女の旅々 特装版","魔女の旅々 限定","魔女の旅々 特典","魔女の旅々 サイン","あずーる","イレイナ"]

# ---------- 文字分類 ----------
GOODS=re.compile(r"キーホルダー|キーリング|バッジ|ピンズ|アクリル|アクスタ|ラバー|スクラッチ|タイクレ|クレーンゲーム|景品|プライズ|コードホルダー|ステッカー|シール|マグカップ|Tシャツ|パーカー|タオル|うちわ|クッション|マウスパッド|ポーチ|トート|缶バッジ")
BONUSWORD=re.compile(r"特典|有償|同梱|限定セット|購入者|対象商品|フェア|連動|特装|特裝")
EXCL=re.compile(r"ブルーレイ|コミック|ガンガン|スクエニ|漫画|マンガ版|コミカライズ版|Blu-?ray|ＢＤ|\bBD\b|DVD|フィギュア|ぬいぐるみ|アクスタ|アクリルスタンド|"
    r"プライズ|一番くじ|くじ|台湾|台灣|中文|繁體|繁体|韓国|韓国語|英語版|英訳|電子書籍|文庫版|ヴァイス|ブシロード|カードゲーム|"
    r"抱き枕|コスプレ|ウィッグ|ねんどろ|figma|ガチャ|カプセル")
BADCOND=re.compile(r"やや傷|傷や汚れあり|全体的に状態が悪い|ジャンク|難あり|水濡れ|書き込み|書込み|日焼け強|カビ|破れ")
FLAGS={"特装":r"特装|特裝|限定版|豪華版|ドラマCD|音声|設定資料集|画集付",
       "店舗特典":r"特典|アニメイト|animate|メロン|ゲーマーズ|とらのあな|虎の穴|TSUTAYA|WonderGOO|リーフレット|SS|小冊子|ブロマイド|イラストカード|カード|色紙|タペストリー|タペ|デジパック|収納BOX|収納ボックス|BOXケース|キャストトーク|ミニノート|カバー|しおり|栞|フェア|連動|ポイント",
       "簽名":r"サイン|直筆|署名|宛名",
       "雙簽":r"[WＷ]サイン|ダブルサイン|両先生|お二人|白石.{0,12}あずーる.{0,12}サイン|あずーる.{0,12}白石.{0,12}サイン",
       "首刷":r"初版|初刷|第1刷|1刷|帯付|帯あり",
       "套組":r"セット|まとめ|全巻|\d+\s*[〜~～\-－]\s*\d+\s*巻|巻セット|冊",
       "畫集同人":r"画集|設定資料集|イラスト集|同人|C1\d\d|コミケ|コミックマーケット|スペシャルブック",
       "外傳":r"学園物語|リリエール",
       "無腰封":r"帯なし|帯無し|帯欠|カバーのみ"}
FL={k:re.compile(v,re.I) for k,v in FLAGS.items()}
def vols(t):
    s=set()
    for m in re.finditer(r"魔女の旅[々ゝ]\s*(?:第)?\s*(\d{1,2})(?!\d)",t): s.add(int(m.group(1)))
    for m in re.finditer(r"(?<!\d)(\d{1,2})\s*巻(?!セット)",t): s.add(int(m.group(1)))
    for m in re.finditer(r"(\d{1,2})\s*[〜~～\-－]\s*(\d{1,2})\s*巻",t):
        a,b=int(m.group(1)),int(m.group(2))
        if 1<=a<b<=30: s.update(range(a,b+1))
    return sorted(v for v in s if 1<=v<=30)
def classify(title,cond_ok=True):
    t=unicodedata.normalize("NFKC",title)
    if not (re.search(r"魔女の旅|イレイナ|リリエール",t) or re.search(r"(白石定規|あずーる).{0,20}(サイン|直筆)",t)): return None,"非魔女之旅"
    if EXCL.search(t) and not re.search(r"特装版|特裝版",t): return None,"排除類別"
    if GOODS.search(t) and not BONUSWORD.search(t): return None,"一般周邊"
    f=[k for k,r in FL.items() if r.search(t)]
    if re.search(r"[3３]冊セット\s*特装版",t) and "套組" in f: f.remove("套組")   # 第20卷特裝版本身，不是套組
    v=vols(t)
    # 第8、16卷單買不要：只有該卷、不是套組、也不是簽名
    if v and set(v)<= {8,16} and "套組" not in f and "簽名" not in f: return None,"8/16卷單品"
    # 第20、22卷：只要店鋪特典（特裝版本身不要）；套組、簽名照常
    if v and set(v)<= {20,22} and "套組" not in f and "簽名" not in f and "店舗特典" not in f: return None,"20/22卷只要店鋪特典"
    if "簽名" in f or "雙簽" in f: tier="簽名"
    elif any(k in f for k in ("特装","店舗特典","畫集同人","套組")): tier="特典"
    elif v==[4] or v==[1]: tier="首刷本"       # 第4卷首刷、第1卷要靠照片
    else: tier="一般"                          # 其他卷普通本：只做縮圖篩書衣
    if tier=="首刷本" and v==[1]: tier="一般"   # 第1卷沒有簽名字樣：不要（只收首刷親簽）
    if "無腰封" in f and v==[4]: return None,"第4卷無腰封"
    pri=9
    if 21 in v and (tier!="一般"): pri=1
    elif "雙簽" in f: pri=2
    elif 4 in v and tier in ("首刷本","簽名"): pri=3
    elif tier=="簽名" and (set(v)&{1,2,3,4,5} or any(x>=21 for x in v)): pri=4
    elif tier in ("特典","簽名"): pri=5
    elif tier=="一般": pri=8
    return {"tier":tier,"flags":f,"vols":v,"pri":pri},None

C={}
def add(site,iid,url,title,price,**kw):
    key=site+":"+iid
    if key in C: return
    cls,why=classify(title)
    if not cls: return
    if kw.get("cond_bad"): return
    C[key]=dict(site=site,id=iid,url=url,title=title,price=price,**cls,**{k:v for k,v in kw.items() if k!="cond_bad"})

# ---------- メルカリ ----------
exec(open("haiyu_lib.py",encoding="utf-8").read())
def msearch(kw,tok="",status="STATUS_ON_SALE"):
    return mcall("https://api.mercari.jp/v2/entities:search","POST",{"userId":"","pageSize":120,"pageToken":tok,"searchSessionId":uuid.uuid4().hex,
      "indexRouting":"INDEX_ROUTING_UNSPECIFIED","thumbnailTypes":[],"searchCondition":{"keyword":kw,"excludeKeyword":"","sort":"SORT_CREATED_TIME","order":"ORDER_DESC","status":[status]},
      "defaultDatasets":["DATASET_TYPE_MERCARI","DATASET_TYPE_BEYOND"],"serviceFrom":"suruga","withItemBrand":False,"withItemSize":False,"withItemPromotions":False,"withItemSizes":False,"withShopname":True})
CONDJ={"1":"新品、未使用","2":"未使用に近い","3":"目立った傷や汚れなし","4":"やや傷や汚れあり","5":"傷や汚れあり","6":"全体的に状態が悪い"}
def mercari():
    n=0
    for kw in KW:
        tok=""
        for page in range(6 if FULL else (2 if kw=="魔女の旅々" else 1)):
            try: r=msearch(kw,tok)
            except Exception as e: log("メルカリ錯誤",kw,e); break
            for it in r.get("items",[]):
                iid=it["id"]; shop=not iid.startswith("m")
                c=str(it.get("itemConditionId",""))
                url=("https://jp.mercari.com/shops/product/" if shop else "https://jp.mercari.com/item/")+iid
                thumb=(it.get("photos") or [{}])[0].get("uri") if shop else f"https://static.mercdn.net/item/detail/orig/photos/{iid}_1.jpg"
                add("メルカリShops" if shop else "メルカリ",iid,url,it.get("name",""),int(it.get("price") or 0),
                    cond=CONDJ.get(c,c),cond_bad=c in("4","5","6"),created=twdate(int(it.get("created") or 0)),
                    created_ts=int(it.get("created") or 0),updated_ts=int(it.get("updated") or 0),shop=it.get("shopName",""),thumb=thumb); n+=1
            tok=r.get("meta",{}).get("nextPageToken","")
            if not tok: break
            time.sleep(0.3)
    log("メルカリ 結果",n)

# ---------- ヤフオク／PayPayフリマ ----------
YCOND={"NEW":"未使用","USED10":"未使用に近い","USED20":"目立った傷や汚れなし","USED40":"やや傷や汚れあり","USED60":"傷や汚れあり","USED80":"全体的に状態が悪い"}
def yitems(h):
    m=re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>',h,re.S)
    if not m: return []
    d=json.loads(m.group(1))
    try: return d["props"]["pageProps"]["initialState"]["search"]["items"]["listing"]["items"]
    except Exception: return []
def yadd(it,tag=""):
    aid=it["auctionId"]; pp=aid.startswith("z")
    url=("https://paypayfleamarket.yahoo.co.jp/item/" if pp else "https://auctions.yahoo.co.jp/jp/auction/")+aid
    c=it.get("itemCondition","")
    st=it.get("startTime","")
    add("PayPayフリマ" if pp else "ヤフオク",aid,url,it.get("title",""),int(float(it.get("price") or 0)),
        cond=YCOND.get(c,c),cond_bad=c in("USED40","USED60","USED80"),end=it.get("endTime",""),
        created=st[:10] or "不明",created_ts=datetime.datetime.fromisoformat(st).timestamp() if st else 0,
        bids=it.get("bidCount"),thumb=it.get("imageUrl"),seller_tag=tag)
def yahoo():
    n=0
    for kw in KW:
        for b in ([1,101,201] if FULL else [1]):
            try: h=get(f"https://auctions.yahoo.co.jp/search/search?p={q(kw)}&n=100&b={b}&s1=new&o1=d")
            except Exception as e: log("ヤフオク錯誤",kw,e); break
            its=yitems(h)
            for it in its: yadd(it); n+=1
            if len(its)<100: break
            time.sleep(0.3)
    log("ヤフオク 結果",n)
def dunh():
    try:
        h=get("https://auctions.yahoo.co.jp/seller/5oGBGnZdgQwqV5rmZsD7ZNRnNbd5p?user_type=c&n=100")
        m=re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>',h,re.S)
        s=m.group(1) if m else h
        hits=0
        for mm in re.finditer(r'\{[^{}]*"auctionId":"([a-z]?\d+)"[^{}]*\}',s):
            try: it=json.loads(mm.group(0))
            except Exception: continue
            if re.search("魔女の旅|イレイナ",it.get("title","")): yadd(it,"dunh"); hits+=1
        log("dunh 魔女之旅出品",hits)
    except Exception as e: log("dunh 錯誤",e)

# ---------- ラクマ ----------
def rakuma():
    n=0
    for kw in KW_SHOP+["魔女の旅々 4","魔女の旅々 21","魔女の旅々 セット","魔女の旅々 アニメイト"]:
        try: h=get("https://fril.jp/s?query="+q(kw)+"&sort=created_at&order=desc")
        except Exception as e: log("ラクマ錯誤",kw,e); continue
        for mm in re.finditer(r'href="https://item\.fril\.jp/([0-9a-f]{32})"[^>]*title="([^"]+?)の商品詳細ページへのリンク"',h):
            iid,t=mm.group(1),re.sub(r"\s*エンタメ/ホビー.*$","",mm.group(2))
            seg=h[mm.end():mm.end()+3000]
            pm=re.search(r'¥\s*([\d,]+)|"price":\s*"?(\d+)',seg)
            price=int((pm.group(1) or pm.group(2)).replace(",","")) if pm else 0
            add("ラクマ",iid,"https://item.fril.jp/"+iid,t,price,cond="（要看商品頁）",created="不明",created_ts=0); n+=1
        time.sleep(0.3)
    log("ラクマ 結果",n)

# ---------- Amazon（只看搜尋結果裡「中古品と新品」的出品數與最低價；出品照片多為示意圖，一律待確認） ----------
def amazon():
    n=0; seen=set()
    for kw in KW_AMZ:
        try: h=get("https://www.amazon.co.jp/s?k="+q(kw)+"&i=stripbooks",cookie="i18n-prefs=JPY; lc-acbjp=ja_JP")
        except Exception as e: log("Amazon錯誤",kw,e); continue
        if re.search(r"captcha|ロボットではない",h,re.I): log("Amazon 驗證頁",kw); return
        for blk in re.split(r'data-component-type="s-search-result"',h)[1:]:
            a=re.search(r'/dp/([0-9A-Z]{10})',blk); t=re.search(r'<h2[^>]*>.*?<span[^>]*>([^<]+)</span>',blk,re.S)
            if not(a and t) or a.group(1) in seen: continue
            seen.add(a.group(1)); txt=re.sub(r"\s+"," ",re.sub(r"<[^>]+>"," ",blk))
            m=re.search(r"([￥¥]\s*[\d,]+|USD\s*[\d.]+)\s*\((\d+)点の中古品と新品\)",txt)
            if not m: continue
            title=re.sub(r"\s+"," ",t.group(1)).strip()
            add("Amazon",a.group(1),f"https://www.amazon.co.jp/gp/offer-listing/{a.group(1)}/?f_used=true",title,0,
                cond=f"中古品と新品 {m.group(2)} 點，最低 {m.group(1)}",created="不明",created_ts=0,note="Amazon 出品照片多為示意圖：待確認"); n+=1
        time.sleep(1)
    log("Amazon 有中古出品的 ASIN",n)

# ---------- まんだらけ ----------
def mandarake():
    n=0
    for kw in KW_SHOP:
        try: h=get("https://order.mandarake.co.jp/order/listPage/list?keyword="+q(kw)+"&lang=ja",cookie="tr_mndrk_user=1")
        except Exception as e: log("まんだらけ錯誤",kw,e); continue
        for blk in re.split(r'<div class="block',h)[1:]:
            ic=re.search(r'itemCode=(\d+)',blk); t=re.search(r'<div class="title">.*?<a[^>]*>\s*([^<]+?)\s*</a>',blk,re.S)
            pr=re.search(r'([\d,]+)円',blk); img=re.search(r'<img src="(https://img\.mandarake[^"]+)"',blk)
            if not(ic and t): continue
            if "在庫なし" in blk or "SOLD" in blk: continue
            add("まんだらけ",ic.group(1),"https://order.mandarake.co.jp/order/detailPage/item?itemCode="+ic.group(1)+"&lang=ja",
                t.group(1),int(pr.group(1).replace(",","")) if pr else 0,cond="（要看商品頁）",created="不明",created_ts=0,thumb=img.group(1) if img else ""); n+=1
        time.sleep(0.5)
    log("まんだらけ 結果",n)

# ---------- 店家目錄型（照片為示意圖）：Book Off、NetOff ----------
def catalog_shops():
    n=0
    for kw in ["魔女の旅々 特装版","魔女の旅々 限定版","魔女の旅々 設定資料集"]:
        try:
            h=get("https://shopping.bookoff.co.jp/search/keyword/"+q(kw))
            for mm in re.finditer(r'href="/(used|new)/(\d+)" class="productItem__image[^>]*>\s*<img[^>]*alt="([^"]+)"',h):
                seg=h[mm.end():mm.end()+4000]
                pr=re.search(r'productItem__price[^>]*>\s*([\d,]+)',seg)
                out=bool(re.search(r"在庫なし|品切",seg[:2500]))
                if out: continue
                add("Book Off",mm.group(2),f"https://shopping.bookoff.co.jp/{mm.group(1)}/{mm.group(2)}",mm.group(3),int(pr.group(1).replace(",","")) if pr else 0,
                    cond="中古" if mm.group(1)=="used" else "新品",created="不明",created_ts=0,note="照片為示意圖"); n+=1
        except Exception as e: log("Book Off錯誤",kw,e)
        try:
            h=get("https://www.netoff.co.jp/cmdtyallsearch/?word="+q(kw))
            for blk in re.split(r'class="c-cassette ',h)[1:]:
                d=re.search(r'href="/detail/(\d+)/" class="c-link--blue c-cassette__title">\s*<span>([^<]+)</span>',blk)
                if not d or "c-cassette--disabled" in blk[:60] or "在庫なし" in blk: continue
                pr=re.search(r'([\d,]+)\s*円',blk)
                add("NetOff",d.group(1),f"https://www.netoff.co.jp/detail/{d.group(1)}/",d.group(2),int(pr.group(1).replace(",","")) if pr else 0,
                    cond="中古",created="不明",created_ts=0,note="照片為示意圖"); n+=1
        except Exception as e: log("NetOff錯誤",kw,e)
        time.sleep(0.5)
    try:
        h=get("https://shopping.bookoff.co.jp/used/0020159349")
        log("Book Off 第21卷特裝版固定頁：",("在庫あり" if re.search(r"カートに入れる|在庫あり",h) and "在庫なし" not in h else "在庫なし"))
    except Exception as e: log("Book Off 固定頁錯誤",e)
    log("店家目錄型 結果",n)

for f in (mercari,yahoo,dunh,rakuma,amazon,mandarake,catalog_shops):
    try: f()
    except Exception as e: log(f.__name__,"整體失敗",e)

# 一般（普通本）只留最近 3 天上架的，做縮圖篩安利美特書衣；第一次（--full）全留
cut=NOW-3*86400
out=[c for c in C.values() if c["tier"]!="一般" or FULL or c.get("created_ts",0)>=cut]
for c in out:
    c["ts"]=max(c.pop("created_ts",0) or 0,c.pop("updated_ts",0) or 0)
out.sort(key=lambda c:(c["pri"],c["site"]))
json.dump(out,open("cand.json","w"),ensure_ascii=False,indent=0)
from collections import Counter
log("候選總數",len(out),dict(Counter(c["tier"] for c in out)),dict(Counter(c["site"] for c in out)))
open("search_log.txt","w").write("\n".join(LOG)); print("\n".join(LOG))

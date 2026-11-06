# 灰羽計畫 共用：メルカリ DPoP 簽章
import json,time,uuid,base64,urllib.request
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"
def b64(b): return base64.urlsafe_b64encode(b).rstrip(b'=').decode()
_k=ec.generate_private_key(ec.SECP256R1()); _pn=_k.public_key().public_numbers()
_jwk={"crv":"P-256","kty":"EC","x":b64(_pn.x.to_bytes(32,'big')),"y":b64(_pn.y.to_bytes(32,'big'))}
def dpop(url,m):
    h={"typ":"dpop+jwt","alg":"ES256","jwk":_jwk}
    p={"iat":int(time.time()),"jti":str(uuid.uuid4()),"htu":url,"htm":m,"uuid":str(uuid.uuid4())}
    si=b64(json.dumps(h,separators=(',',':')).encode())+'.'+b64(json.dumps(p,separators=(',',':')).encode())
    r,s=decode_dss_signature(_k.sign(si.encode(),ec.ECDSA(hashes.SHA256())))
    return si+'.'+b64(r.to_bytes(32,'big')+s.to_bytes(32,'big'))
def mcall(url,m="GET",body=None):
    req=urllib.request.Request(url,data=json.dumps(body).encode() if body else None,method=m,
      headers={"DPoP":dpop(url,m),"X-Platform":"web","Content-Type":"application/json","Accept":"application/json","User-Agent":UA})
    return json.load(urllib.request.urlopen(req,timeout=25))

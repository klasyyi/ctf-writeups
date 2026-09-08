import hashlib
import sympy
import urllib.request
import urllib.parse
import json
import hmac

P = 309967783371909964659037772809563145007
Q = 154983891685954982329518886404781572503
G = 4
PUBLIC_KEY = 82286113946526975456927497908098965104

SIGNATURES = [
    ("Krypton log 01: sunrise", 209607831069536493146646496592015330779, 107188195476006259878518191275322566927),
    ("Krypton log 02: north gate", 301590948974401278594089397456900077023, 60262677914419596302181248925584993152),
    ("Krypton log 03: crystal check", 39931719901423134481341268118860756823, 48229030403632374689242531069926288587),
    ("Krypton log 05: flare passed", 231724402756192760129147589112814414813, 69736293180258353103101118471990217198),
    ("Krypton log 06: phantom zone", 54698703492379275241259823313736974477, 86975940973076512377188748650577142280),
    ("Krypton log 07: night watch", 42862981153119833466241733260295802551, 74487978435051030017743853154003166178),
]

def challenge(message: str, commitment: int) -> int:
    material = message.encode() + b"|" + str(commitment).encode()
    return int.from_bytes(hashlib.sha256(material).digest(), "big") % Q

e = []
s = []
for msg, R, sig in SIGNATURES:
    e.append(challenge(msg, R))
    s.append(sig)

# Set up the linear equations
eqs = []
def add_eq(c0, c1, c2, c3):
    eqs.append([c0 % Q, c1 % Q, c2 % Q, c3 % Q])

add_eq(s[1] - s[2], -(e[1] - e[2]), -(s[0] - s[1]), e[0] - e[1])
add_eq(s[4] - s[5], -(e[4] - e[5]), -(s[3] - s[4]), e[3] - e[4])
add_eq(s[2] - s[4], -(e[2] - e[4]), -(s[1] - s[3]), e[1] - e[3])

M = sympy.Matrix([
    [eqs[0][1], eqs[0][2], eqs[0][3]],
    [eqs[1][1], eqs[1][2], eqs[1][3]],
    [eqs[2][1], eqs[2][2], eqs[2][3]]
])
C = sympy.Matrix([-eqs[0][0], -eqs[1][0], -eqs[2][0]])

res = M.inv_mod(Q) * C
X = int(res[0] % Q)
print(f"[+] Recovered Private Key: {X}")
assert pow(G, X, P) == PUBLIC_KEY, "Key verification failed!"

# Fetch the flag from the live server
print("[+] Claiming flag from live verifier...")
start_url = 'https://proof.chal.sunwaycybersecurityclub.org/v1/crypto/kryptonite/start'
req = urllib.request.Request(start_url)
with urllib.request.urlopen(req) as response:
    data = json.loads(response.read().decode())
    
token = data['token']
nonce = data['nonce']

decimal_solution = str(X).encode()
key = hashlib.sha256(decimal_solution).digest()
message = f'proof-v1|kryptonite|{token}|{nonce}'.encode('utf-8')
proof = hmac.new(key, message, hashlib.sha256).hexdigest()

claim_url = 'https://proof.chal.sunwaycybersecurityclub.org/v1/crypto/kryptonite/claim'
payload = {'token': token, 'response': proof}

post_data = json.dumps(payload).encode('utf-8')
headers = {'Content-Type': 'application/json'}
req = urllib.request.Request(claim_url, data=post_data, headers=headers, method='POST')

try:
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode())
        print(f"[+] Flag: {result['flag']}")
except urllib.error.HTTPError as err:
    print(f"[-] HTTP Error: {err.read().decode()}")

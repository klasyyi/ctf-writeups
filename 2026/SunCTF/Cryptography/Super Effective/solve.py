import urllib.request
import json

def xor(a, b): return bytes(x ^ y for x, y in zip(a, b))
def bytes_to_int(b): return int.from_bytes(b, 'big')
def int_to_bytes(i): return i.to_bytes(16, 'big')

# GF(2^128) arithmetic functions for GCM
def gf_mult(a, b):
    R = 0xe1000000000000000000000000000000
    res = 0
    for i in range(128):
        if (a & (1 << (127 - i))): res ^= b
        if (b & 1): b = (b >> 1) ^ R
        else: b >>= 1
    return res

def gf_pow(a, n):
    res = 1 << 127
    base = a
    while n > 0:
        if n % 2 == 1: res = gf_mult(res, base)
        base = gf_mult(base, base)
        n //= 2
    return res

def gf_inv(a): return gf_pow(a, (1 << 128) - 2)

# Provided Samples
c1 = bytes.fromhex("ea91188871d72ad63e65e5aeed16577b")
t1 = bytes.fromhex("685338eb4b38fed1e129ea65aa1ed610")
p1 = b"trainer=ash;0___"

c2 = bytes.fromhex("ea91188871d72ad6327ffee1a472387b")
t2 = bytes.fromhex("d5875fab35698771b1b322c619da0205")

target_p = b"trainer=red;1___"

# 1. Recover keystream and Encrypt target plaintext
ks = xor(p1, c1)
target_c = xor(target_p, ks)

# 2. Calculate H^2 in GF(2^128)
c1_int, c2_int = bytes_to_int(c1), bytes_to_int(c2)
t1_int, t2_int = bytes_to_int(t1), bytes_to_int(t2)
h_sq = gf_mult(t1_int ^ t2_int, gf_inv(c1_int ^ c2_int))

# 3. Calculate target tag
target_c_int = bytes_to_int(target_c)
target_t_int = t1_int ^ gf_mult(target_c_int ^ c1_int, h_sq)
target_t = int_to_bytes(target_t_int)

nonce = "d56dffae7867187e09243db3"
token = f"{nonce}.{target_c.hex()}.{target_t.hex()}"
print(f"Forged Token: {token}")

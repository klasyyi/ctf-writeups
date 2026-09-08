# Super Effective

- **Event:** Sunway Cybersecurity Club CTF (SunCTF 2026)
- **Category:** Crypto
- **Difficulty:** Medium
- **Points:** 100 *(adjust if needed)*

---

## 1. Challenge Description
> The Vermilion Gym upgraded to authenticated, League-approved badges. Two sample badges are on the terminal, and the scanner accepts only a Champion. The terminal only issues a one-time verification claim for a Champion badge.

---

## 1. Challenge Description
> The Vermilion Gym upgraded to authenticated, League-approved badges. Two sample badges are on the terminal, and the scanner accepts only a Champion. The terminal only issues a one-time verification claim for a Champion badge.

---

## 2. Initial Reconnaissance & Analysis
When visiting the provided terminal URL, we are greeted with the following JSON output that gives us the algorithm, a target payload we need to spoof, and two sample badges to work with:

```json
{
  "algorithm": "AES-256-GCM; no associated data; 16-byte records",
  "encoding": "nonce.ciphertext.tag (hex)",
  "samples": [
    {
      "plaintext": "trainer=ash;0___",
      "token": "d56dffae7867187e09243db3.ea91188871d72ad63e65e5aeed16577b.685338eb4b38fed1e129ea65aa1ed610"
    },
    {
      "plaintext": "trainer=misty;0_",
      "token": "d56dffae7867187e09243db3.ea91188871d72ad6327ffee1a472387b.d5875fab35698771b1b322c619da0205"
    }
  ],
  "target_plaintext": "trainer=red;1___"
}
```

Looking closely at the structure of the tokens (`nonce.ciphertext.tag`), we immediately spot a critical vulnerability: **The 12-byte nonce (`d56dffae7867187e09243db3`) is reused for both samples.** 

AES-GCM is incredibly fragile to nonce reuse, leading to two immediate breaks that allow us to forge the Champion token:
1. **Keystream Reuse:** AES-GCM uses CTR mode under the hood. Reusing the nonce results in the same keystream. XORing a sample ciphertext with its known plaintext gives us the keystream, which we can use to encrypt our `target_plaintext`.
2. **Authentication Tag Forgery:** The AES-GCM authentication tag is generated using the GHASH polynomial MAC evaluated over the Galois field $GF(2^{128})$. With two messages sharing the same encrypted nonce block $E_k(J_0)$, we can exploit the linear properties of GHASH to solve for the hash subkey and forge a valid tag for our new ciphertext.

---

## 3. Exploitation & Solution

### Forging the Ciphertext
Because the keystream is reused, we can recover it by simply XORing the first sample plaintext (`P1`) with its ciphertext (`C1`). 
`Keystream = P1 ^ C1`

We can then use this keystream to encrypt the target plaintext (`P_target` = `trainer=red;1___`):
`C_target = P_target ^ Keystream`

### Forging the Tag
The authentication tag ($T$) in AES-GCM without Associated Data (AAD) is computed as:
$T = GHASH(C) \oplus E_k(J_0)$

Since our sample messages are exactly 1 block (16 bytes) long, the GHASH function simplifies significantly:
$T_1 = (C_1 \cdot H^2) \oplus E_k(J_0)$
$T_2 = (C_2 \cdot H^2) \oplus E_k(J_0)$

*(Note: $H^2$ represents the hash subkey squared, due to the structure of the single block of ciphertext and the block indicating the message lengths).*

If we XOR the two tags together, the $E_k(J_0)$ term cancels out entirely:
$T_1 \oplus T_2 = (C_1 \oplus C_2) \cdot H^2$

Now we can isolate $H^2$ by multiplying both sides by the modular inverse of $(C_1 \oplus C_2)$ in $GF(2^{128})$:
$H^2 = (T_1 \oplus T_2) \cdot (C_1 \oplus C_2)^{-1}$

Once we calculate $H^2$, forging the tag for our target ciphertext ($C_{target}$) is trivial:
$T_{target} = T_1 \oplus ( (C_{target} \oplus C_1) \cdot H^2 )$

### Exploit Script Execution
Running the exploit script to perform the $GF(2^{128})$ arithmetic gives us our forged token:
```bash
$ python3 solve.py
Forged Token: d56dffae7867187e09243db3.ea91188871d72ad62d73e9aeec16577b.265826145cc8b872031bebd608570a27
```

We send this valid token to the `/verify` endpoint and receive a one-time claim ticket (`brn7-1dBTvmzLZjdtJmnZe8rOop5KrJj`). Redeeming this claim ticket at the `/v1/claim` endpoint verifies we are a champion and rewards us with the flag.

---

## 4. Flag
`sunctf26{vermilion_proof_fdf5816d0e0839f69ac2e469}`

---

## 5. Key Takeaways
**What concept did this challenge teach?**
AES-GCM is an Authenticated Encryption with Associated Data (AEAD) cipher that completely falls apart if a nonce is reused under the same key. A reused nonce not only destroys the confidentiality of the data (keystream reuse), but it completely breaks the integrity of the data, allowing an attacker to trivially forge valid authentication tags for arbitrary data without knowing the underlying encryption key

**How can the vulnerability be mitigated in production?**
Always ensure nonces are absolutely unique for every single encryption operation performed with the same key. Use cryptographically secure random number generators (CSPRNG) to generate random 96-bit nonces, or use a strict, persistent counter that never repeats. Alternatively, consider using AES-GCM-SIV, which is specifically designed to provide resistance against nonce misuse.

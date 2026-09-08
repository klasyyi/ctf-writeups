# Kryptonite

- **Event:** SunCTF 2026
- **Category:** Crypto
- **Difficulty:** Medium-Hard

---

## 1. Challenge Description
> Lois recovered six signed Fortress logs. The signatures are valid, but a solar flare skipped one log and the Kryptonian nonce core kept following its old rhythm. Recover the Fortress key, then complete a fresh verification slip before the phantom zone closes.

The challenge provides a Python script containing public parameters, the server's public key, and 6 valid signatures. The signatures use a custom Schnorr signature scheme where the nonces are generated using a Linear Congruential Generator (LCG).

---

## 2. Initial Reconnaissance & Analysis

When inspecting `fortress_logs.py`, we can observe that a standard Schnorr signature over a subgroup of order $Q$ is implemented:

- $R = G^k \pmod P$
- $e = \text{SHA256}(message \parallel | \parallel R) \pmod Q$
- $s = k + eX \pmod Q$

The script also contains an important comment about the damaged firmware:
```python
next_nonce = (A * current_nonce + B) % Q
```
This indicates the nonces $k$ are derived sequentially using a Linear Congruential Generator (LCG). The starting nonce, multiplier $A$, increment $B$, and private key $X$ are all unknown.

Additionally, the log notes:
> "The incident log records one extra nonce advance between log 03 and log 05 during a solar flare."

This means we have two unbroken sequences of logs: 
- Logs 1, 2, 3 (corresponding to nonces $k_1, k_2, k_3$)
- Logs 5, 6, 7 (corresponding to nonces $k_5, k_6, k_7$, skipping $k_4$)

---

## 3. Exploitation & Solution

Our goal is to eliminate the LCG variables to isolate and solve for the private key $X$.

From the Schnorr signature equation, we can express the nonce $k_i$ as:
$$k_i = s_i - e_i X \pmod Q$$

Because the nonces are sequentially generated, we know:
$$k_2 = A k_1 + B$$
$$k_3 = A k_2 + B$$

We can eliminate the unknown $B$ by subtracting the two equations:
$$k_2 - k_3 = A(k_1 - k_2)$$

Substituting our Schnorr nonce equation into this relation:
$$(s_2 - e_2 X) - (s_3 - e_3 X) = A((s_1 - e_1 X) - (s_2 - e_2 X))$$
$$(s_2 - s_3) - (e_2 - e_3)X = A(s_1 - s_2) - A(e_1 - e_2)X$$

By defining new variables $Y = A$ and $Z = A \times X$, we obtain a linear equation:
$$(s_2 - s_3) - (e_2 - e_3)X - (s_1 - s_2)Y + (e_1 - e_2)Z \equiv 0 \pmod Q$$

Applying this pattern to the second sequence of logs (Logs 5, 6, 7 or $k_5, k_6, k_7$), we get a second equation:
$$(s_6 - s_7) - (e_6 - e_7)X - (s_5 - s_6)Y + (e_5 - e_6)Z \equiv 0 \pmod Q$$

To get a third equation, we extract an expression for $B$ from both sequences and equate them:
$$B = k_3 - A k_2 = (s_3 - e_3 X) - Y(s_2 - e_2 X) = s_3 - e_3 X - s_2 Y + e_2 Z$$
$$B = k_6 - A k_5 = (s_6 - e_6 X) - Y(s_5 - e_5 X) = s_6 - e_6 X - s_5 Y + e_5 Z$$
$$s_3 - s_6 - (e_3 - e_6)X - (s_2 - s_5)Y + (e_2 - e_5)Z \equiv 0 \pmod Q$$

This yields a system of three linear equations with three unknowns ($X, Y, Z$) modulo $Q$. We can solve this with `sympy` matrix inversion to recover the private key $X$.

Once $X$ is recovered, the challenge requires interacting with a live web verifier. We request a token and nonce from `/start`, generate an HMAC-SHA256 signature using the decimal private key, and POST the response to `/claim` to obtain the flag.

To automate this, run `solve.py`.

---

## 4. Flag
`sunctf26{kryptons_secret_a4959a6765364a6288a82ccf}`

---

## 5. Key Takeaways

- **Predictable Nonces in Signatures:** Schnorr (and ECDSA) signatures require the nonce $k$ to be completely uniformly random and secret. Any relationship between nonces (such as an LCG) completely destroys the security of the scheme and allows for private key recovery.
- **Mitigation:** In production environments, always use a Cryptographically Secure Pseudorandom Number Generator (CSPRNG) to generate random nonces. Alternatively, implement deterministic nonces (like RFC 6979 for ECDSA) where the nonce is derived securely from a hash of the private key and the message, eliminating the risk of weak PRNGs.

# Grand Line Ledger

- **CTF:** SunCTF 2026
- **Category:** Crypto

---

### Description
> The Straw Hats' signing ledger needs two captains to approve a route. Nami's abort handling is keeping the wrong voyage counters. Recover the treasure key, then complete its fresh verification slip before the Marines audit the logbook.

---

### Solution
When first approaching this problem, the description heavily hinted at state desynchronization with the clue: "Nami's abort handling is keeping the wrong voyage counters."
+ URLs Provided: The initial prompt provided a REST API interface with /manifest, /proof, /reset, and /sign
+ First Actions: My immediate goal was to understand the cryptographic parameters and how the abort flag affected the backend. I used curl to grab the challenge manifest and test the signature endpoint
+ Key Vulnerability Spotted: The manifest revealed two critical pieces of information:
  1) The cryptosystem was a Schnorr Multi-Signature scheme over a prime field $q$, combined with Shamir's Secret Sharing (SSS)
  2) The abort behavior explicitly stated that an aborted request does not commit the targeted captain's voyage counter. Because the counter generates the cryptographic nonce ($k$), aborting and retrying guarantees Nonce Reuse

Bash
+ curl -s https://grand-line.chal.sunwaycybersecurityclub.org/manifest | jq
+ curl -s -X POST https://grand-line.chal.sunwaycybersecurityclub.org/sign \
    -H "Content-Type: application/json" \
    -d '{"message":"test","abort":0}' | jq

---

### Exploitation
To exploit this, I needed to manipulate the application state to force nonce reuse for both Captain 1 and Captain 2, extract their private shares, and combine them to find the Treasure Key.
Step 1: Forcing Nonce ReuseI injected faults by sending a POST /sign request with abort: 1 (saving Captain 1's nonce but discarding the counter increment) followed by a successful abort: 0 request. This gave me two signatures ($z_1, z_2$) with different hashes ($e_1, e_2$) but the exact same nonce commitment ($R$). I repeated this with abort: 2 for Captain 2.
Step 2: Key Extraction LogicWith a reused nonce in a Schnorr signature ($z = k + e \cdot x \pmod q$), the nonce $k$ cancels out when you subtract the two signatures. I scripted this algebraic extraction for both captains:$$x = (z_1 - z_2) \cdot (e_1 - e_2)^{-1} \pmod q$$
Step 3: Shamir's Secret Sharing RecoveryThe manifest defined the threshold as a line $f(t) = \text{secret} + \text{slope} \cdot t$. Knowing Captain 1 is $x_1$ and Captain 2 is $x_2$, the secret (y-intercept) is simply $(2 \cdot x_1 - x_2) \pmod q$.
Step 4: HMAC VerifierOnce I had the decimal secret, I passed it through the server's HMAC verifier loop to claim the flag.

---

### Flag
sunctf26{one_piece_treasure_39715b6e18b061d3b4961774}

---

### Key Takeaways
+ Concepts Taught: This challenge perfectly illustrates the catastrophic failure of nonce reuse in discrete-logarithm-based signatures (Schnorr/ECDSA). A single reused nonce completely exposes the private key. It also demonstrates how Shamir's Secret Sharing threshold polynomials can be reconstructed algebraically once enough shares are compromised.
+ Production Mitigation: Never rely on stateful counters or standard system randomness (Math.random()) for cryptographic nonces. To mitigate this in production, implement RFC 6979, which generates the nonce deterministically by hashing the private key together with the message being signed. This ensures the nonce is always unique for different messages, and completely eliminates reliance on application state or random number generators.

---

### Read
+ https://en.wikipedia.org/wiki/Schnorr_signature
+ https://notsosecure.com/ecdsa-nonce-reuse-attack
+ http://mixoftix.net/tutorials/cryptography_ecdsa_rfc_6979.asp
+ https://www.geeksforgeeks.org/computer-networks/shamirs-secret-sharing-algorithm-cryptography/
+ https://www.geeksforgeeks.org/computer-networks/what-is-hmachash-based-message-authentication-code/
+ https://www.geeksforgeeks.org/computer-networks/hmac-algorithm-in-computer-network/

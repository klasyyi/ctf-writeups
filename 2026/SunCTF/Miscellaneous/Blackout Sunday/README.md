# Blackout Sunday

- **Event:** SunCTF 2026
- **Category:** Forensics / Misc
- **Difficulty:** Easy

---

## 1. Challenge Description
> Northstar Dynamics experienced a network blackout on 17 May 2026. A confidential archive disappeared during the incident, and several employee identities appear throughout the evidence. Get the flag. The flag format is `sunctf26{}`.

---

## 2. Initial Reconnaissance & Analysis
When looking at the problem:
- **Files provided:** A directory containing various log files, chat exports, a mailbox file, and several multimedia/PDF files (e.g., `04_mailbox.mbox`, `07_chat_export.json`, `13_case_recovery.log`).
- **Initial review:** We started by reviewing the textual log files to understand the sequence of events during the network blackout. 

```bash
# Listing the files
ls -l

# Checking the recovery instructions
cat 13_case_recovery.log
```

We noticed in `13_case_recovery.log` that the incident was tracked under `CASE_SESSION C-2317`. The log explicitly stated:
> "To close the case, submit the recovery keyword associated with CASE_SESSION C-2317... Check the incident correspondence associated with this case reference to recover the keyword."

---

## 3. Exploitation & Solution
Knowing the target case ID is `C-2317`, we searched for this ID across all the provided files to find the incident correspondence.

```bash
# Searching for the case ID across all files
grep -rn "C-2317" .
```

The search hits pointed us to `04_mailbox.mbox`. Inspecting the surrounding lines of the email located in `04_mailbox.mbox`, we found an email from `incident-response@northstar.local` containing the recovery procedure:

```text
Subject: Case C-2317 - Recovery Procedure
...
The recovery procedure requires the following keyword:

RECOVERY KEYWORD: NIGHTFALL

Use this keyword to close CASE_SESSION C-2317.
```

The keyword `NIGHTFALL` is the secret value we need. We wrap it in the required flag format.

---

## 4. Flag
`sunctf26{NIGHTFALL}`

---

## 5. Key Takeaways
- **What concept did this challenge teach?** The importance of centralized log analysis and effectively using `grep` (or similar search tools) to trace specific indicators (like a case ID) across disparate systems and log types (email, chat, system logs).
- **Mitigation:** Ensure that incident response documentation and sensitive recovery passwords are not stored alongside potentially compromised routine communication channels in plain text.

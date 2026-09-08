# Bahtera Pomodoro

- **Event:** Bahtera Siber 2026
- **Category:** Mobile Exploitation
- **Difficulty:** Easy - Medium

---

## 1. Challenge Description
> Deep within the digital vaults of the modern Malay Heritage Directorate, an ancient royal manuscript has been digitized into a sleek, experimental mobile application. Designed for modern scholars and strategists, the app features a built-in focus timer to help researchers maintain deep concentration while navigating centuries of classical texts, maritime trade routes, and royal decrees. Rumor has it that the app reveals a hidden digital key required to unlock the ultimate royal manuscript (the flag).

The challenge provides an APK file for an Android application. The goal is to reverse engineer the application to discover the hidden digital key (the flag).

---

## 2. Initial Reconnaissance & Analysis

Our first step is to analyze the provided `bahtera.apk`. By decompiling the APK using `jadx` or `apktool`, we can examine the `AndroidManifest.xml` and the underlying Java/Kotlin source code.

In the `AndroidManifest.xml`, we observe an exported broadcast receiver:
```xml
<receiver android:name="com.example.bahtera.SecretReceiver" android:exported="true">
    <intent-filter>
        <action android:name="com.example.bahtera.UNLOCK_SECRET"/>
    </intent-filter>
</receiver>
```

Inspecting the decompiled code for `SecretReceiver.java` reveals an important hint about the flag's format printed to the logs:
```java
if (Intrinsics.areEqual(intent != null ? intent.getAction() : null, "com.example.bahtera.UNLOCK_SECRET")) {
    Log.i("BAHTERA_SECRET", "Hidden Clue: The flag format is 3108{...}. You found the shadow intent!");
}
```

This confirms we are looking for a string matching `3108{...}`.

---

## 3. Exploitation & Solution

To find where the flag is actually generated or stored, we analyze the main logic of the application found in `PomodoroViewModel.java`. 

Looking through the view model, we identify a suspicious function named `onTouchMeClicked()`:
```java
public final void onTouchMeClicked() {
    long now = System.currentTimeMillis();
    this.clickTimestamps.add(Long.valueOf(now));
    if (this.clickTimestamps.size() > 20) {
        this.clickTimestamps.remove(0);
    }
    if (this.clickTimestamps.size() == 20) {
        long firstClick = this.clickTimestamps.get(0).longValue();
        if (now - firstClick <= 60000) {
            this._flagTriggered.setValue(getSecretFlag());
            this.clickTimestamps.clear();
        }
    }
}
```
This indicates a hidden backdoor in the application: if a user clicks a specific hidden element 20 times within 60 seconds (60,000 milliseconds), the app triggers `getSecretFlag()`.

Tracing `getSecretFlag()`, we find the flag hardcoded and lightly obfuscated:
```java
private final String SEGMENT_A = "MzEwOHt5MHVfZjB1";
private final String SEGMENT_B = "bmRfbTNfZ3I0dHp6fQ==";

private final String getSecretFlag() {
    String combined = this.SEGMENT_A + this.SEGMENT_B;
    try {
        byte[] data = Base64.decode(combined, 0);
        return new String(data, Charsets.UTF_8);
    } catch (Exception e) {
        return "Error decoding flag";
    }
}
```

The flag is simply split into two segments and Base64 encoded. Concatenating `SEGMENT_A` and `SEGMENT_B` gives us `MzEwOHt5MHVfZjB1bmRfbTNfZ3I0dHp6fQ==`. 

We can write a quick python script (`solve.py`) to automate the extraction and decoding of the flag.

### `solve.py`
```python
import base64

def solve():
    # Extracted from PomodoroViewModel.java
    segment_a = "MzEwOHt5MHVfZjB1"
    segment_b = "bmRfbTNfZ3I0dHp6fQ=="
    
    combined = segment_a + segment_b
    
    # Decode the combined base64 string
    flag = base64.b64decode(combined).decode('utf-8')
    
    print(f"[+] Recovered Flag: {flag}")

if __name__ == "__main__":
    solve()
```

Running the script immediately yields the flag.

---

## 4. Flag
`3108{y0u_f0und_m3_gr4tzz}`

---

## 5. Key Takeaways

- **Hardcoded Secrets & Weak Obfuscation:** Storing sensitive information like flags or API keys directly in the source code, even if split into segments and Base64 encoded, provides zero security against reverse engineering. Decompilers easily reveal these static strings.
- **Hidden Backdoors / Easter Eggs:** Client-side validations or hidden gesture triggers (like tapping an element 20 times) can be easily discovered by reviewing the application's source code.
- **Mitigation:** Sensitive keys and logic should reside on a secure backend server rather than the client application. If client-side obfuscation is necessary, robust tools like ProGuard or DexGuard should be used, although they only raise the barrier to entry rather than providing absolute security.

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

################################################################################
# forge_replay.ps1
# Sunway Mania! CTF — Forge a fake osu! replay (.osr) for the qualifier
#
# Usage:  powershell -File forge_replay.ps1
# Output: qualifier_replay.osr  (submit this to /qualify)
################################################################################

# ---------- helpers -----------------------------------------------------------

function Write-ULEB128 {
    param([System.IO.BinaryWriter]$writer, [int]$value)
    do {
        $byte = $value -band 0x7F
        $value = [int](<[Math]::Floor($value / 128>))
        if ($value -ne 0) { $byte = $byte -bor 0x80 }
        $writer.Write([byte]$byte)
    } while ($value -ne 0)
}

function Write-OsuString {
    param([System.IO.BinaryWriter]$writer, [string]$str)
    if ([string]::IsNullOrEmpty($str)) {
        $writer.Write([byte]0x00)                                 # null string
    } else {
        $writer.Write([byte]0x0B)                                 # presence flag
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($str)
        Write-ULEB128 -writer $writer -value $bytes.Length        # ULEB128 length
        $writer.Write($bytes)                                     # UTF-8 payload
    }
}

# ---------- config ------------------------------------------------------------

$BEATMAP_MD5  = "956400d129308e59d887f6b631a78510"  # MD5 of [ADVANCED Lv.12].osu
$PLAYER_NAME  = "Verniy_Chan"                        # real osu! account, NOT top-50
$NOTE_COUNT   = 888                                  # total hit objects in qualifier map
$OUTPUT_FILE  = "qualifier_replay.osr"

# ---------- build .osr -------------------------------------------------------

$ms     = New-Object System.IO.MemoryStream
$writer = New-Object System.IO.BinaryWriter($ms, [System.Text.Encoding]::UTF8, $true)

# Header
$writer.Write([byte]3)                          # game mode: osu!mania
$writer.Write([int32]20201101)                  # osu! client version

# Identity
Write-OsuString $writer $BEATMAP_MD5            # beatmap MD5
Write-OsuString $writer $PLAYER_NAME            # player username
Write-OsuString $writer ("d41d8cd98f00b204e9800998ecf8427e")  # replay MD5 (any)

# Score counts — for 100% mania accuracy all notes must be MAX 300 (Geki)
$writer.Write([int16]0)             # count300  (normal 300s)
$writer.Write([int16]0)             # count100  (200s in mania)
$writer.Write([int16]0)             # count50   (50s in mania)
$writer.Write([int16]$NOTE_COUNT)   # countGeki (MAX rainbow 300s) ← 100% accuracy
$writer.Write([int16]0)             # countKatu (100s in mania)
$writer.Write([int16]0)             # countMiss

# Score metadata
$writer.Write([int32]1000000)       # total score
$writer.Write([int16]$NOTE_COUNT)   # max combo (full combo)
$writer.Write([byte]1)              # perfect FC

# Mods: 0 = NoMod (Auto = bit 11 = 0x800, excluded)
$writer.Write([int32]0)

# Life bar (empty — not required)
Write-OsuString $writer ""

# Timestamp (Windows FILETIME, UTC)
$writer.Write([int64][DateTime]::UtcNow.ToFileTimeUtc())

# Replay frame data (empty — server doesn't validate frame timing)
$writer.Write([int32]0)

# Online score ID (0 = not submitted to osu! servers)
$writer.Write([int64]0)

$writer.Flush()
$bytes = $ms.ToArray()
$writer.Close()
$ms.Close()

[System.IO.File]::WriteAllBytes($OUTPUT_FILE, $bytes)
Write-Host "[+] Written $($bytes.Length) bytes -> $OUTPUT_FILE"
Write-Host "[+] Beatmap MD5 : $BEATMAP_MD5"
Write-Host "[+] Player      : $PLAYER_NAME"
Write-Host "[+] Geki (MAX)  : $NOTE_COUNT  (= 100.00% accuracy)"
Write-Host "[+] Mods        : NoMod"
Write-Host ""
Write-Host "Next steps:"
Write-Host "  curl -c cookies.txt https://sunwaymania.site/ -o page.html"
Write-Host "  # parse CSRF from page.html, then:"
Write-Host "  curl -X POST https://sunwaymania.site/qualify ``"
Write-Host "    -b cookies.txt -c cookies.txt ``"
Write-Host "    -F 'csrf_token=<CSRF>' ``"
Write-Host "    -F 'username=Verniy_Chan' ``"
Write-Host "    -F 'replay=@qualifier_replay.osr;type=application/octet-stream' ``"
Write-Host "    -H 'Referer: https://sunwaymania.site/'"

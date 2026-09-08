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
        $writer.Write([byte]0x00)
    } else {
        $writer.Write([byte]0x0B)
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($str)
        Write-ULEB128 -writer $writer -value $bytes.Length
        $writer.Write($bytes)
    }
}

$ms     = New-Object System.IO.MemoryStream
$writer = New-Object System.IO.BinaryWriter($ms)

$writer.Write([byte]3)            # Game mode: osu!mania
$writer.Write([int32]20201101)    # osu! version

Write-OsuString $writer "956400d129308e59d887f6b631a78510"  # Beatmap MD5
Write-OsuString $writer "Verniy_Chan"                        # Player (real, non-top-50)
Write-OsuString $writer "d41d8cd98f00b204e9800998ecf8427e"  # Replay MD5 (any)

$writer.Write([int16]0)     # count300 (normal 300s)
$writer.Write([int16]0)     # count100 (200s in mania)
$writer.Write([int16]0)     # count50  (50s in mania)
$writer.Write([int16]888)   # countGeki (MAX 300s = 100% in mania)
$writer.Write([int16]0)     # countKatu (100s in mania)
$writer.Write([int16]0)     # countMiss

$writer.Write([int32]1000000)   # Total score
$writer.Write([int16]888)       # Max combo (full combo)
$writer.Write([byte]1)          # Perfect FC
$writer.Write([int32]0)         # Mods: NoMod (no Auto)

Write-OsuString $writer ""      # Life bar (empty)

$writer.Write([int64][DateTime]::UtcNow.ToFileTimeUtc())
$writer.Write([int32]0)         # No replay frame data
$writer.Write([int64]0)         # Score ID (not submitted online)

$writer.Flush()
[System.IO.File]::WriteAllBytes("qualifier_replay.osr", $ms.ToArray())
Write-Host "Replay written: qualifier_replay.osr"

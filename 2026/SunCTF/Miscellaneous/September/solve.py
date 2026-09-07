import mido

MORSE_CODE_DICT = {'.-':'A', '-...':'B', '-.-.':'C', '-..':'D', '.':'E',
                   '..-.':'F', '--.':'G', '....':'H', '..':'I', '.---':'J',
                   '-.-':'K', '.-..':'L', '--':'M', '-.':'N', '---':'O',
                   '.--.':'P', '--.-':'Q', '.-.':'R', '...':'S', '-':'T',
                   '..-':'U', '...-':'V', '.--':'W', '-..-':'X', '-.--':'Y',
                   '--..':'Z', '-----':'0', '.----':'1', '..---':'2',
                   '...--':'3', '....-':'4', '.....':'5', '-....':'6',
                   '--...':'7', '---..':'8', '----.':'9'}

def decode_tuba_morse(filename):
    mid = mido.MidiFile(filename)
    morse_words = []
    current_word = ""
    current_char = ""
    
    for track in mid.tracks:
        if track.name == 'TUBA':
            for msg in track:
                # Note On events dictate the silence gaps
                if msg.type == 'note_on' and msg.velocity > 0:
                    if msg.time > 1000:  # The 1536-tick word gap
                        morse_words.append(current_word)
                        current_word = ""
                    elif msg.time > 300: # The ~384-tick character gap
                        if current_char:
                            current_word += MORSE_CODE_DICT.get(current_char, '?')
                            current_char = ""
                            
                # Note Off events dictate the dot/dash lengths
                elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                    if msg.time > 300:   # The ~384-tick dash
                        current_char += "-"
                    elif msg.time > 100: # The ~192-tick dot
                        current_char += "."
            
            # Catch the very last character and word
            if current_char:
                current_word += MORSE_CODE_DICT.get(current_char, '?')
            if current_word:
                morse_words.append(current_word)
                
            return morse_words

words = decode_tuba_morse('September.mid')
if words and len(words) >= 2:
    wrapper = words[0].lower()
    inner_flag = words[1].lower()
    print(f"Flag: {wrapper}{{{inner_flag}}}")
else:
    print("Failed to decode.")

import glob
import json
from ...melolib.chord_parser import chord_parser


def line_has_chords(line, threshold=0.8):
    total_words = len(line.split())
    if total_words == 0:
        return False
    words_with_chords = 0
    for word in line.split():
        if len(word) < 10:  # Ignore long words
            try:
                chord_parser(word)
                words_with_chords += 1
            except Exception:
                ...
    return words_with_chords / total_words > threshold


def is_chord(word):
    try:
        chord_parser(word)
        return True
    except Exception:
        return False


songs = []
for semitones in range(12):
    for path in glob.glob("out/songs/*"):
        chords = []
        with open(path) as f:
            total_lines = 0
            lines_predicted_to_have_chords = 0
            for line in f:
                if line_has_chords(line):
                    chords.extend(
                        [
                            str(chord_parser(word.strip()).transpose(semitones))
                            for word in line.split()
                            if is_chord(word.strip())
                        ]
                    )
        songs.append(chords)

with open("out/all_chord_progressions.json", "w") as f:
    f.write(json.dumps(songs))

with open("out/chord_progressions.json", "w") as f:
    f.write(json.dumps(songs[: len(songs) // 3]))

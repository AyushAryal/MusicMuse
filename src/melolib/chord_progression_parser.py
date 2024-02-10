from .chord_parser import chord_parser


def chord_progression_parser(chord_notations):
    parsed_chords = []
    for chord_notation in chord_notations:
        try:
            parsed_chord = chord_parser(chord_notation)
            parsed_chords.append(parsed_chord)
        except Exception:
            return []
    return parsed_chords

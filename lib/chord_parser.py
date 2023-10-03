import re
from .music import Chord, Note


TOKENS = {
    "note_name": [n for n in Note.chromatic_sharps if "#" not in n],
    "note_accidentals": ["#", 'b'],
    "chord_type": [re.escape(t) for t in Chord.chord_types.values() if t != ""]
}

ALL_TOKENS = sum([t for t in TOKENS.values()], [])


class Token:
    def __init__(self, value):
        if value not in ALL_TOKENS:
            raise ValueError(f"Invalid token: {value}")

        for key, val in TOKENS.items():
            if value in val:
                self.type = key
        self.value = value

    def __repr__(self):
        return self.value


def lexer(input_string):
    # Define regular expressions for each token type
    patterns = {
        "note_name": '|'.join(TOKENS["note_name"]),
        "note_accidentals": '|'.join(TOKENS["note_accidentals"]),
        "chord_type": '|'.join(TOKENS["chord_type"]),
    }

    # Combined pattern for all token types
    combined_pattern = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in patterns.items())
    tokens = []
    for match in re.finditer(combined_pattern, input_string):
        for name, _ in patterns.items():
            if match.group(name):
                tokens.append(Token(match.group()))
                break
    return tokens


def chord_parser(chord_notation):
    tokens = lexer(chord_notation)
    root_note = None
    chord_type = ""

    for token in tokens:
        if token.type == "note_name":
            if root_note is None:
                root_note = token.value
            else:
                raise ValueError(f"Invalid chord notation: {chord_notation}")
        elif token.type == "note_accidentals":
            if root_note is not None:
                root_note += token.value
            else:
                raise ValueError(f"Invalid chord notation: {chord_notation}")
        elif token.type == "chord_type":
            chord_type += token.value
        else:
            raise ValueError("Invalid token")

    if root_note is None:
        raise ValueError("Chord must have a root note")

    return Chord.from_name(root_note, chord_type)
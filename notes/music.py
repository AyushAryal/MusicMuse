class Note:
    chromatic_sharps = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    chromatic_flats = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]

    def __init__(self, note: int):
        self.note = note

    @staticmethod
    def from_name(name: str, octave: int):
        if name not in Note.chromatic_sharps and name not in Note.chromatic_flats:
            raise RecursionError(f"Invalid note: {name} {octave}")
        section = (
            Note.chromatic_sharps
            if name in Note.chromatic_sharps
            else Note.chromatic_flats
        )
        return Note(section.index(name) + octave * len(Note.chromatic_sharps))

    def get_name(self, sharps=True):
        section = Note.chromatic_sharps if sharps else Note.chromatic_flats
        name = section[self.note % len(section)]
        octave = self.note // len(section)
        return name, octave

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        name, octave = self.get_name()
        return name + str(octave)

    def __hash__(self):
        return hash(self.note)

    def __eq__(self, o):
        return self.note == o.note

    def str_sharp(self):
        return self.__str__()

    def str_flat(self):
        name, octave = self.get_name(sharps=False)
        return name + str(octave)

    def transpose(self, semitones):
        return Note(self.note + semitones)

    def __sub__(self, n):
        return self.note - n.note


class Chord:
    chord_types = {
        (1, 5, 8): "",
        (1, 4, 8): "m",
        (1, 8): "5",
        (1, 4, 7): "dim",
        (1, 5, 9): "+",
        (1, 3, 8): "sus2",
        (1, 6, 8): "sus4",
        (1, 5, 8, 10): "6",
        (1, 5, 8, 12): "maj7",
        (1, 4, 8, 11): "m7",
        (1, 5, 8, 11): "7",
        (1, 5, 8, 15): "add9",
        (1, 5, 8, 11, 15): "9",
    }

    def __init__(self, notes):
        if len(notes) < 2:
            raise ValueError("A chord must have at least 2 notes")
        self.notes = notes

    @staticmethod
    def from_name(root_note_str, chord_type):
        root_note = Note.from_name(root_note_str, 4)
        chord_types_reverse = {v: k for k, v in Chord.chord_types.items()}
        if chord_type not in chord_types_reverse:
            raise ValueError(f"Chord type is not defined: {chord_type}")
        intervals = chord_types_reverse[chord_type]
        notes = [Note(interval - 1 + root_note.note) for interval in intervals]
        return Chord(notes)

    def __str__(self):
        chord_name = self.get_name()
        return chord_name if chord_name else "Unknown"

    def __repr__(self):
        return self.__str__()

    def __hash__(self):
        return sum(hash(note) for note in self.notes)

    def __eq__(self, o):
        return self.notes == o.notes

    def transpose(self, semitones):
        transposed_notes = [note.transpose(semitones) for note in self.notes]
        return Chord(transposed_notes)

    def get_name(self):
        root, *_ = self.notes
        intervals = tuple(sorted([(note - root) + 1 for note in self.notes]))
        if intervals in Chord.chord_types:
            chord_type = Chord.chord_types[intervals]
            name, _ = root.get_name()
            return name + chord_type
        return None

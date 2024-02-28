from dataclasses import dataclass
import enum
import abc
from typing_extensions import override
from collections import Counter
from .music import Note


class JsonSerializable(abc.ABC):
    @abc.abstractmethod
    def to_json():
        ...


class DurationClass(enum.Enum):
    (
        Whole,
        Half,
        Quarter,
        Eighth,
        Sixteenth,
        ThirtySecond,
        SixtyFourth,
    ) = range(7)


@dataclass
class Duration:
    duration_class: DurationClass
    dots: int

    def __str__(self):
        duration_class_to_repr = {
            DurationClass.Whole: "w",
            DurationClass.Half: "h",
            DurationClass.Quarter: "q",
            DurationClass.Eighth: "8",
            DurationClass.Sixteenth: "16",
            DurationClass.ThirtySecond: "32",
            DurationClass.SixtyFourth: "64",
        }
        return duration_class_to_repr[self.duration_class] + "." * self.dots

    def __repr__(self):
        return self.__str__()


@dataclass
class Rest(JsonSerializable):
    duration: Duration

    def __str__(self):
        repr = str(self.duration)
        idx = repr.find(".")
        repr = repr + "r" if idx == -1 else repr[0:idx] + "r" + repr[idx:]
        return repr

    def __repr__(self):
        return self.__str__()

    @override
    def to_json(self):
        return {"keys": ["B/4"], "duration": str(self)}


@dataclass
class StaffNote(JsonSerializable):
    note: str
    octave: int
    duration: Duration

    def __str__(self):
        return f"{self.note}{self.octave}/{self.duration}"

    def __repr__(self):
        return self.__str__()

    @override
    def to_json(self):
        return {"keys": [f"{self.note}/{self.octave}"], "duration": str(self.duration)}


@dataclass
class PolyStaffNote(JsonSerializable):
    notes: list[StaffNote]

    def __str__(self):
        duration = self.notes[0].duration
        chord = " ".join(f"{note.note}/{note.octave}" for note in self.notes)
        return f"({chord})/{duration}"

    def __repr__(self):
        return self.__str__()

    @override
    def to_json(self):
        return {
            "keys": [f"{note.note}/{note.octave}" for note in self.notes],
            "duration": str(self.notes[0].duration),
        }


def convert_ticks_to_duration(ticks_per_beat, delta_ticks):
    ticks_per_sixty_fourth = int(ticks_per_beat / 2 / 2 / 2 / 2)
    num_sixty_fourth = delta_ticks // ticks_per_sixty_fourth
    num_sixty_fourth = num_sixty_fourth & 0b111_1111  # Convert to 7 bits (0-127)
    durations = [(num_sixty_fourth >> (6 - d.value)) & 1 for d in DurationClass]
    duration_tuples = enumerate(
        zip(durations, durations[1:] + [0], durations[2:] + [0] * 2)
    )
    duration, context = next(
        ((i, (b, c)) for i, (a, b, c) in duration_tuples if a), (6, (1, 0, 0))
    )
    return Duration(DurationClass(duration), sum(context))


def generate_rests(rest, note, ticks_per_beat, last_end_tick):
    rests = []
    rest = note["start_tick"] - last_end_tick
    if rest > 0:
        num_full_rest = rest // (ticks_per_beat * 2 * 2)
        for i in range(0, num_full_rest - 1):
            rests.append(
                {
                    "start_tick": last_end_tick + i * ticks_per_beat * 2 * 2,
                    "end_tick": last_end_tick + (i + 1) * ticks_per_beat * 2 * 2,
                    "notation": Rest(
                        convert_ticks_to_duration(
                            ticks_per_beat, ticks_per_beat * 2 * 2
                        )
                    ),
                }
            )

        duration = convert_ticks_to_duration(
            ticks_per_beat, rest - max(num_full_rest - 1, 0) * ticks_per_beat * 2 * 2
        )
        if duration.duration_class.value < DurationClass.SixtyFourth.value:
            rests.append(
                {
                    "start_tick": last_end_tick
                    + max(num_full_rest - 1, 0) * ticks_per_beat * 2 * 2,
                    "end_tick": note["start_tick"],
                    "notation": Rest(duration),
                }
            )
    return rests


def get_error_values_for_all_keys(observed):
    key_signatures = {
        "G#": ["G#", "A#", "B", "C#", "D#", "E", "F"],
        "D#": ["D#", "E", "F", "G#", "A#", "B", "C"],
        "A#": ["A#", "B", "C", "D#", "E", "F", "G"],
        "F": ["F", "G", "A#", "B", "C", "D", "E"],
        "C": ["C", "D", "E", "F", "G", "A", "B"],
        "G": ["G", "A", "B", "C", "D", "E", "F#"],
        "D": ["D", "E", "F#", "G", "A", "B", "C#"],
        "A": ["A", "B", "C#", "D", "E", "F#", "G#"],
        "E": ["E", "F#", "G#", "A", "B", "C#", "D#"],
        "B": ["B", "C#", "D#", "E", "F#", "G#", "A#"],
        "F#": ["F#", "G#", "A#", "B", "C#", "D#", "F"],
        "C#": ["C#", "D#", "F", "F#", "G#", "A#", "C"],
    }
    key_signatures = {
        k: {note for note in Note.chromatic_sharps if note in v}
        for k, v in key_signatures.items()
    }

    error_values = {}
    for key, expected_notes in key_signatures.items():
        error_values[key] = sum(
            [v for k, v in observed.items() if k not in expected_notes]
        )

    return error_values


def estimate_key_signature(notes_count):
    error_values = get_error_values_for_all_keys(notes_count)
    return tuple(sorted(error_values.items(), key=lambda item: item[1])[:3])


def get_notes_count(score):
    counter = Counter(**{note: 0 for note in Note.chromatic_sharps})
    for note in score:
        notation = note["notation"]
        if isinstance(notation, StaffNote):
            counter.update({notation.note: 1})
        elif isinstance(notation, PolyStaffNote):
            for note in notation.notes:
                counter.update({note.note: 1})

    return counter


def generate_score_from_parsed_midi(parsed):
    scores = []
    ticks_per_beat = parsed["ticks_per_beat"]
    for track in parsed["tracks"]:
        score = []
        last_start_tick, last_end_tick = 0, 0
        for note in track["data"]:
            # Calculate rests
            rest = note["start_tick"] - last_end_tick
            score.extend(generate_rests(rest, note, ticks_per_beat, last_end_tick))

            # Calculate note
            delta_ticks = note["end_tick"] - note["start_tick"]
            duration = convert_ticks_to_duration(ticks_per_beat, delta_ticks)
            staff_note = StaffNote(note["note"], note["octave"], duration)

            # Check if note is played simultaneously
            if note["start_tick"] == last_start_tick and len(score) != 0:
                prev_staff_note = score[-1]
                if isinstance(prev_staff_note["notation"], PolyStaffNote):
                    prev_staff_note["notation"] = PolyStaffNote(
                        prev_staff_note["notation"].notes + [staff_note]
                    )
                elif isinstance(prev_staff_note["notation"], StaffNote):
                    prev_staff_note["notation"] = PolyStaffNote(
                        [prev_staff_note["notation"], staff_note]
                    )
                score[-1] = prev_staff_note
            else:
                score.append(
                    {
                        "start_tick": note["start_tick"],
                        "end_tick": note["end_tick"],
                        "notation": staff_note,
                    }
                )

            # Update last ticks
            last_start_tick = max(last_start_tick, note["start_tick"])
            last_end_tick = max(last_end_tick, note["end_tick"])

        notes_count = get_notes_count(score)
        key_signature = estimate_key_signature(notes_count)

        # serialize StaffNote, PolyStaffNote, Rest
        for i, note in enumerate(score):
            if isinstance(note["notation"], JsonSerializable):
                note["notation"] = note["notation"].to_json()
                score[i] = note

        scores.append(
            {"name": track["name"], "key_signature": key_signature, "data": score}
        )
    return scores

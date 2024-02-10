from dataclasses import dataclass
import enum


class DurationClass(enum.Enum):
    (
        DoubleWhole,
        Whole,
        Half,
        Quarter,
        Eighth,
        Sixteenth,
        ThirtySecond,
        SixtyFourth,
    ) = range(8)


@dataclass
class Duration:
    duration_class: DurationClass
    dots: int

    def __str__(self):
        duration_class_to_repr = {
            DurationClass.DoubleWhole: "1d",
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
class Rest:
    duration: Duration

    def __str__(self):
        repr = str(self.duration)
        idx = repr.find(".")
        repr = repr + "r" if idx == -1 else repr[0:idx] + "r" + repr[idx:]
        return repr

    def __repr__(self):
        return self.__str__()


@dataclass
class StaffNote:
    note: str
    octave: int
    duration: Duration

    def __str__(self):
        return f"{self.note}{self.octave}/{self.duration}"

    def __repr__(self):
        return self.__str__()


def convert_ticks_to_duration(ticks_per_beat, delta_ticks):
    ticks_per_thirty_second = int(ticks_per_beat / 2 / 2 / 2)
    num_thirty_second = delta_ticks // ticks_per_thirty_second
    num_thirty_second = num_thirty_second & 0b1111_1111  # Convert to 8 bits (0-127)
    durations = [(num_thirty_second >> (7 - d.value)) & 1 for d in DurationClass]
    duration_tuples = enumerate(
        zip(durations, durations[1:] + [0], durations[2:] + [0] * 2)
    )
    duration, context = next(
        ((i, (b, c)) for i, (a, b, c) in duration_tuples if a), (7, (1, 0, 0))
    )
    return Duration(DurationClass(duration), sum(context))


def generate_score_from_parsed_midi(parsed):
    scores = []
    ticks_per_beat = parsed["ticks_per_beat"]
    for track in parsed["tracks"]:
        score = []
        last_start_tick, last_end_tick = 0, 0
        for note in track["data"]:
            # Calculate rests
            rest = note["start_tick"] - last_end_tick
            if rest > 0:
                duration = convert_ticks_to_duration(ticks_per_beat, rest)
                if duration.duration_class.value < DurationClass.SixtyFourth.value:
                    score.append(Rest(duration))

            # Calculate note
            delta_ticks = note["end_tick"] - note["start_tick"]
            duration = convert_ticks_to_duration(ticks_per_beat, delta_ticks)
            staff_note = StaffNote(note["note"], note["octave"], duration)

            # Check if note is played simultaneously
            if note["start_tick"] == last_start_tick and len(score) != 0:
                if isinstance(score[-1], list):
                    score[-1].append(staff_note)
                elif isinstance(score[-1], StaffNote):
                    score[-1] = [score[-1], staff_note]
            else:
                score.append(staff_note)

            # Update last ticks
            last_start_tick = max(last_start_tick, note["start_tick"])
            last_end_tick = max(last_end_tick, note["end_tick"])

        scores.append({"name": track["name"], "data": score})
    return scores

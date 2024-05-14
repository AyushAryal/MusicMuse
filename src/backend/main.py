import sys
from flask import Flask, render_template, request
from pathlib import Path
import random

sys.path.append("..")
from melolib.chord_parser import chord_parser
from melolib.midi import parse_midi
from melolib.notation import generate_score_from_parsed_midi
from melolib.wav_to_midi import wav_to_midi
from trained_models.chord_progression import get_chord_progression_from_key

app = Flask(__name__)

PROJECT_NAME = "MELOWAVE"

AVAILABLE_SONGS = [
    Path("res/adl-piano-midi/World/Canadian Pop/Avril Lavigne/Complicated.mid"),
    Path("res/adl-piano-midi/Electronic/Disco/Cândido/Viajando Sem Rumo.mid"),
    Path("res/adl-piano-midi/Pop/Pop/Taylor Swift/Youre Not Sorry.mid"),
    Path("res/adl-piano-midi/Classical/Operatic Pop/Lara Fabian/Tout.mid"),
    Path("res/adl-piano-midi/Rock/Anadolu Rock/Hayko Cepkin/Melekler Intro.mid"),
    Path("res/adl-piano-midi/Folk/Lilith/Amanda Ghost/Youre Beautiful.mid"),
    Path("res/adl-piano-midi/Soul/R&B/Rihanna/Unfaithful.mid"),
    Path("res/adl-piano-midi/Rap/J-Rap/Fire Ball/I Love You.mid"),
    Path("res/adl-piano-midi/World/Canadian Pop/Justin Bieber/Down To Earth.mid"),
    Path("res/adl-piano-midi/World/Canadian Pop/Avril Lavigne/My Happy Ending.mid"),
    Path("res/adl-piano-midi/Rap/Rap/Eminem/Hailies Song.mid"),
    Path("res/adl-piano-midi/Pop/Dance Pop/Lady Gaga/Bad Romance.mid"),
    Path("res/midi/unravel.mid"),
    Path("res/midi/Nepali.mid"),
    Path("res/midi/ChhaideuTimi.mid"),
    Path("res/midi/ngnl.mid"),
    Path("res/midi/summertime_sadness.mid"),
]


@app.route("/")
def index():
    return render_template("index.html", project_name=PROJECT_NAME)


@app.get("/song_list")
def song_list():
    return list(
        map(lambda song_path: song_path.name.removesuffix(".mid"), AVAILABLE_SONGS)
    )


@app.get("/song/<int:song_num>")
def song(song_num):
    song_num = song_num % len(AVAILABLE_SONGS)
    song_path = AVAILABLE_SONGS[song_num]
    midi = parse_midi(song_path)
    scores = generate_score_from_parsed_midi(midi)
    return {
        "name": song_path.name.removesuffix(".mid"),
        "scores": scores,
        "midi": midi,
    }


def track_from_chord_progression_full(chord_progression, ticks_per_beat):
    midi_notes = []
    num_beats = 0
    beats_per_chord = 4
    for _ in range(3):
        for chord_repr in chord_progression:
            chord = chord_parser(chord_repr)
            random.shuffle(chord.notes)
            for i, note in enumerate(chord.notes):
                start_tick = int(num_beats * beats_per_chord * ticks_per_beat)
                end_tick = int(start_tick + ticks_per_beat * beats_per_chord)
                key, octave = note.get_name()
                octave = max(2, min(3, octave))
                midi_notes.append(
                    {
                        "note": key,
                        "octave": octave,
                        "velocity": 0.4,
                        "start_tick": start_tick,
                        "end_tick": end_tick,
                    }
                )
            num_beats += 1
    return {"name": "Chord progression", "data": midi_notes}


def track_from_chord_progression(chord_progression, ticks_per_beat, octaver):
    midi_notes = []
    num_beats = 0
    beats_per_chord = 4
    for _ in range(3):
        for chord_repr in chord_progression:
            chord = chord_parser(chord_repr)
            chord.notes = chord.notes + chord.notes[::-1]
            random.shuffle(chord.notes)
            for i, note in enumerate(chord.notes):
                if random.random() > 0.65:
                    continue
                start_tick = int(
                    (
                        num_beats * beats_per_chord
                        + i * beats_per_chord / len(chord.notes)
                    )
                    * ticks_per_beat
                )
                end_tick = int(
                    start_tick
                    + ticks_per_beat
                    * (beats_per_chord / len(chord.notes))
                    * random.randint(1, 4)
                )
                key, octave = note.get_name()
                octave = max(octaver, min(octaver, octave))
                midi_notes.append(
                    {
                        "note": key,
                        "octave": octave,
                        "velocity": 0.7,
                        "start_tick": start_tick,
                        "end_tick": end_tick,
                    }
                )
            num_beats += 1
    return {"name": "Melody Line", "data": midi_notes}


@app.post("/generate")
def generate():
    file = request.files["sample"]
    tempo = request.form["tempo"]
    chord_complexity = request.form["chord_complexity"]

    midi = wav_to_midi(file, int(tempo))
    scores = generate_score_from_parsed_midi(midi)

    key = scores[0]["key_signature"][0][0]
    chord_progression = get_chord_progression_from_key(key, chord_complexity)
    midi["tracks"] = []

    midi["tracks"].append(
        track_from_chord_progression(chord_progression, midi["ticks_per_beat"], 4)
    )
    midi["tracks"].append(
        track_from_chord_progression_full(chord_progression, midi["ticks_per_beat"])
    )
  

    scores = generate_score_from_parsed_midi(midi)  # Regenerate score for added track
    return {
        "name": "UserInput",
        "scores": scores,
        "midi": midi,
    }


@app.get("/test")
def test():
    return get_chord_progression_from_key("G", "complex")

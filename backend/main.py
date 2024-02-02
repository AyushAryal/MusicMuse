from flask import Flask, render_template, request
import mido
from pathlib import Path

app = Flask(__name__)

PROJECT_NAME = "MuseGen"

AVAILABLE_SONGS = [
    Path(
        "res/adl-piano-midi/Classical/Japanese Classical/Michiru Oshima/Beaming Sunlight.mid"
    ),
    Path("res/adl-piano-midi/Pop/Pop/Taylor Swift/Youre Not Sorry.mid"),
    Path(
        "res/adl-piano-midi/Pop/Piano Cover/Piano Tribute Players/Til Summer Comes Around.mid"
    ),
    Path(
        "res/adl-piano-midi/Rock/Album Rock/Fleetwood Mac/Silver Springs (Live Album Version).mid"
    ),
    Path("res/adl-piano-midi/Classical/Operatic Pop/Lara Fabian/Tout.mid"),
    Path("res/midi dataset/Allure/All_Cried_Out.mid"),
    Path("res/adl-piano-midi/Electronic/Disco/Cândido/Viajando Sem Rumo.mid"),
    Path("res/midi dataset/ABBA/Dancing_Queen.mid"),
    Path("res/midi dataset/Aqua/Barbie_Girl.mid"),
    Path("res/midi dataset/Linkin_Park/One_Step_Closer.mid"),
    Path("res/midi dataset/Alexia/Goodbye.mid"),
    Path("res/adl-piano-midi/Rock/Anadolu Rock/Hayko Cepkin/Melekler Intro.mid"),
    Path("res/adl-piano-midi/Folk/Lilith/Amanda Ghost/Youre Beautiful.mid"),
    Path("res/adl-piano-midi/Soul/R&B/Rihanna/Unfaithful.mid"),
    Path("res/adl-piano-midi/Rap/J-Rap/Fire Ball/I Love You.mid"),
    Path("res/adl-piano-midi/World/Canadian Pop/Justin Bieber/Down To Earth.mid"),
    Path("res/adl-piano-midi/World/Canadian Pop/Avril Lavigne/Complicated.mid"),
    Path("res/adl-piano-midi/World/Canadian Pop/Avril Lavigne/My Happy Ending.mid"),
    Path("res/adl-piano-midi/Rap/Rap/Eminem/Hailies Song.mid"),
    Path("res/adl-piano-midi/Pop/Dance Pop/Lady Gaga/Bad Romance.mid"),
]


@app.route("/")
def index():
    return render_template("index.html", project_name=PROJECT_NAME)


def convert_midi_to_structure(midi_file_path):
    midi = mido.MidiFile(midi_file_path)
    song_data = []

    ticks_per_beat = midi.ticks_per_beat

    channels = [{} for _ in range(17)]

    for track in midi.tracks:
        current_time = 0
        tempo = 600000  # Default tempo in microseconds per beat
        for msg in track:
            if msg.type == "set_tempo":
                tempo = msg.tempo

            current_time += mido.tick2second(msg.time, ticks_per_beat, tempo) * 1000

            if msg.type == "note_on" and msg.velocity != 0:
                note_number = msg.note
                channels[msg.channel][note_number] = {
                    "time": current_time,
                    "velocity": msg.velocity,
                }
            elif msg.type == "note_off" or (
                msg.type == "note_on" and msg.velocity == 0
            ):
                if msg.note in channels[msg.channel]:
                    info = channels[msg.channel][msg.note]
                    note, octave = convert_midi_to_note_octave(msg.note)
                    start_time = info["time"]
                    velocity = info["velocity"]
                    end_time = current_time
                    song_data.append(
                        {
                            "note": note,
                            "octave": octave,
                            "velocity": velocity,
                            "start_time": start_time,
                            "end_time": end_time,
                        }
                    )
    return song_data


def convert_midi_to_note_octave(note_number):
    notes_mapping = {
        0: "C",
        1: "C#",
        2: "D",
        3: "D#",
        4: "E",
        5: "F",
        6: "F#",
        7: "G",
        8: "G#",
        9: "A",
        10: "A#",
        11: "B",
    }
    note = notes_mapping[note_number % 12]
    octave = note_number // 12 - 1
    return note, octave


@app.get("/song_list")
def song_list():
    return list(
        map(lambda song_path: song_path.name.removesuffix(".mid"), AVAILABLE_SONGS)
    )


@app.get("/song/<int:song_num>")
def song(song_num):
    song_num = song_num % len(AVAILABLE_SONGS)
    return convert_midi_to_structure(AVAILABLE_SONGS[song_num])


@app.post("/generate")
def generate():
    file = request.files["sample"]
    return f"{len(file.read())} bytes uploaded"

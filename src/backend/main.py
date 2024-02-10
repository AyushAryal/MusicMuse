from flask import Flask, render_template, request
from pathlib import Path
import sys

sys.path.append("..")
from melolib.midi import parse_midi

app = Flask(__name__)

PROJECT_NAME = "Melowave"

AVAILABLE_SONGS = [
    Path("res/adl-piano-midi/Electronic/Disco/Cândido/Viajando Sem Rumo.mid"),
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
    Path("res/adl-piano-midi/Rock/Anadolu Rock/Hayko Cepkin/Melekler Intro.mid"),
    Path("res/adl-piano-midi/Folk/Lilith/Amanda Ghost/Youre Beautiful.mid"),
    Path("res/adl-piano-midi/Soul/R&B/Rihanna/Unfaithful.mid"),
    Path("res/adl-piano-midi/Rap/J-Rap/Fire Ball/I Love You.mid"),
    Path("res/adl-piano-midi/World/Canadian Pop/Justin Bieber/Down To Earth.mid"),
    Path("res/adl-piano-midi/World/Canadian Pop/Avril Lavigne/Complicated.mid"),
    Path("res/adl-piano-midi/World/Canadian Pop/Avril Lavigne/My Happy Ending.mid"),
    Path("res/adl-piano-midi/Rap/Rap/Eminem/Hailies Song.mid"),
    Path("res/adl-piano-midi/Pop/Dance Pop/Lady Gaga/Bad Romance.mid"),
    Path("res/midi/moonlight.mid"),
    Path("res/midi/unravel.mid"),
    Path("res/midi/ngnl.mid"),
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
    return parse_midi(AVAILABLE_SONGS[song_num])


@app.post("/generate")
def generate():
    file = request.files["sample"]
    return f"{len(file.read())} bytes uploaded"

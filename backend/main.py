from flask import Flask, render_template, request
import mido

app = Flask(__name__)

PROJECT_NAME = "Mello Wave"


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
        tempo = 1000000  # Default tempo in microseconds per beat
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
                    end_time = current_time
                    song_data.append(
                        {
                            "note": note,
                            "octave": octave,
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


@app.get("/song")
def song():
    # path = "/home/shark/Documents/dev/major/res/adl-piano-midi/Classical/Japanese Classical/Michiru Oshima/Beaming Sunlight.mid"
    path = "/home/shark/Documents/dev/major/res/adl-piano-midi/Pop/Pop/Taylor Swift/Youre Not Sorry.mid"
    # path = "/home/shark/Documents/dev/major/res/adl-piano-midi/Pop/Piano Cover/Piano Tribute Players/Til Summer Comes Around.mid"
    # path = "/home/shark/Documents/dev/major/res/adl-piano-midi/Rock/Album Rock/Fleetwood Mac/Silver Springs (Live Album Version).mid"
    # path = "/home/shark/Documents/dev/major/res/adl-piano-midi/Classical/Operatic Pop/Lara Fabian/Tout.mid"
    # path = "/home/shark/Documents/dev/major/res/midi dataset/Allure/All_Cried_Out.mid"
    return convert_midi_to_structure(path)


@app.post("/generate")
def generate():
    file = request.files["sample"]
    return f"{len(file.read())} bytes uploaded"

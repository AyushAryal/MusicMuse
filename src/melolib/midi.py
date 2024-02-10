import mido


def parse_midi(midi_file_path):
    midi = mido.MidiFile(midi_file_path)
    ticks_per_beat = midi.ticks_per_beat

    track_list = []
    for track in midi.tracks:
        current_delta_ticks = 0
        channels = [{} for _ in range(17)]
        track_data = []

        for msg in track:
            current_delta_ticks += msg.time

            if msg.type == "note_on" and msg.velocity != 0:
                note_number = msg.note
                channels[msg.channel][note_number] = {
                    "tick": current_delta_ticks,
                    "velocity": msg.velocity,
                }
            elif msg.type == "note_off" or (
                msg.type == "note_on" and msg.velocity == 0
            ):
                if msg.note in channels[msg.channel]:
                    info = channels[msg.channel][msg.note]
                    note, octave = convert_midi_to_note_octave(msg.note)
                    start_tick = info["tick"]
                    velocity = info["velocity"]
                    end_tick = current_delta_ticks
                    track_data.append(
                        {
                            "note": note,
                            "octave": octave,
                            "velocity": velocity,
                            "start_tick": start_tick,
                            "end_tick": end_tick,
                        }
                    )

        track_list.append({"name": track.name, "data": track_data})
    return {"ticks_per_beat": ticks_per_beat, "tracks": track_list}


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

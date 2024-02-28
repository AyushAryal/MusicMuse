import numpy as np
import librosa
import math

from .music import Note


def coalesce_notes_and_rests(notes):
    coalesced_notes = []
    current_note = None
    current_duration = 0.0

    for note, duration in notes:
        if note == current_note or (note is None and current_note is None):
            # If the current note is the same as the previous one, or both are rests
            current_duration += duration  # Accumulate the duration
        else:
            if (
                current_note is not None
            ):  # If there was a previous note, append it to coalesced_notes
                coalesced_notes.append((current_note, current_duration))
            current_note = note
            current_duration = duration

    # Append the last note or rest
    if current_note is not None or current_duration > 0:
        coalesced_notes.append((current_note, current_duration))

    return coalesced_notes


def wav_to_pyin_estimated_pitches(track_path):
    track_data, sample_rate = librosa.load(track_path)

    # Normalize the audio data
    track_data = track_data.astype(np.float32) / np.max(np.abs(track_data))

    f0, _, _ = librosa.pyin(
        track_data,
        fmin=float(librosa.note_to_hz("C2")),
        fmax=float(librosa.note_to_hz("C7")),
        sr=sample_rate,
    )

    times = librosa.times_like(f0)
    dt = times[1] - times[0]

    notes = []
    for f in f0:
        if f > 0:
            note = Note(int(librosa.hz_to_midi(f)) - 12)
            notes.append((note, dt))
        else:
            notes.append((None, dt))

    notes = coalesce_notes_and_rests(notes)
    notes = [
        (note, dt) for note, dt in notes if dt > 0.05
    ]  # Remove all rests/notes that are not too long
    return coalesce_notes_and_rests(notes)


def pyin_estimated_pitches_to_midi(notes, tempo, ticks_per_beat=480):
    time = 0
    midi_notes = []
    for note, dt in notes:
        if note is not None:
            key, octave = note.get_name()
            start_tick = math.floor(ticks_per_beat * (tempo / 60) * time)
            end_tick = math.ceil(ticks_per_beat * (tempo / 60) * (time + dt))
            midi_notes.append(
                {
                    "note": key,
                    "octave": octave,
                    "velocity": 1,
                    "start_tick": start_tick,
                    "end_tick": end_tick,
                }
            )
        time += dt

    return {
        "ticks_per_beat": ticks_per_beat,
        "tracks": [
            {
                "name": "Untitled Track 1",
                "data": midi_notes,
            }
        ],
    }


def wav_to_midi(wav, tempo):
    notes = wav_to_pyin_estimated_pitches(wav)
    return pyin_estimated_pitches_to_midi(notes, tempo)

"use strict";

class Note {
    constructor(note, octave) {
        this._note = note;
        this._octave = octave;
    }

    get octave() { return this._octave; }
    get note() { return this._note; }

    is_accidental = () => this._note.length > 1;
    toString = () => `${this._note}${this._octave}`;
    order = () => ['C', 'D', 'E', 'F', 'G', 'A', 'B'].indexOf(this._note[0]);
}

class PianoNotesRenderer {
    constructor(canvas) {
        canvas.width = parseInt(getComputedStyle(canvas).width);
        canvas.height = parseInt(getComputedStyle(canvas).height);
        this.note_width = getComputedStyle(document.body).getPropertyValue('--white-key-width');
        this.canvas = canvas;
        this.context = canvas.getContext("2d");
    }

    static sec_to_pixels = (msec) => msec * 60;

    static get_note_fill_color({ note, time, duration, velocity, current }) {
        let hue = (note.order() + (0.5 * note.is_accidental())) * 360 / 7;
        let saturation = current ? "100%" : "60%";
        let lightness = current ? "60%" : "40%";
        let alpha = velocity;
        return `hsl(${hue}, ${saturation}, ${lightness}, ${alpha})`;
    }

    render_name() {
        this.context.font = "16px Arial";
        this.context.fillStyle = `hsl(${180 + Math.sin(+new Date() / 3000) * 180}, 40%, 60%)`;
        this.context.fillText("MuseGen", this.canvas.width - 95, 65);
    }


    render_waveform() {
        const CIRCLE_INNER_RADIUS = 50;
        let scaleY = 10;
        let offsetY = 60;
        let offsetX = this.canvas.width - 60;

        const waveformValues = state.waveform.getValue();
        const pointsToAverage = 16;

        let averagePoints = []
        for (let i = 0; i < waveformValues.length; i += pointsToAverage) {
            averagePoints.push(
                waveformValues
                    .slice(i, i + pointsToAverage)
                    .reduce((acc, val) => acc + val, 0) * scaleY / pointsToAverage
            );
        }

        const to_polar = (x, y) => {
            let theta = (x / (averagePoints.length - 2)) * (2 * Math.PI);
            let radius = CIRCLE_INNER_RADIUS + y;
            return [theta, radius];
        }

        this.context.beginPath();
        let [initialTheta, initialR] = to_polar(0, 0);
        let [initialX, initialY] = [initialR * Math.cos(initialTheta), initialR * Math.sin(initialTheta)];
        this.context.moveTo(initialX + offsetX, initialY + offsetY);

        for (let i = 1; i < averagePoints.length - 1; i += 2) {
            let pointA = averagePoints[i - 1];
            let pointB = averagePoints[i];
            let pointC = averagePoints[i + 1];
            let [controlPointTheta, controlPointR] = to_polar(i, 2 * pointB - 0.5 * (pointA + pointC));
            if (i + 2 >= averagePoints.length - 1) { pointC = 0; }
            let [theta, r] = to_polar(i + 1, pointC);
            if (i + 2 >= averagePoints.length - 1) { theta = 0; }
            let [controlPointX, controlPointY] = [controlPointR * Math.cos(controlPointTheta), controlPointR * Math.sin(controlPointTheta)];
            let [x, y] = [r * Math.cos(theta), r * Math.sin(theta)];
            this.context.quadraticCurveTo(controlPointX + offsetX, controlPointY + offsetY, x + offsetX, y + offsetY);
        }

        this.context.strokeStyle = `hsl(${180 + Math.sin(+new Date() / 3000) * 180}, 40%, 60%)`;
        this.context.lineWidth = 3;
        this.context.fillStyle = `hsl(${180 + Math.sin(+new Date() / 3000) * 180}, 40%, 60%, 0.1)`;
        this.context.fill();
        this.context.stroke();
    }

    render_notes() {
        let track_elapsed = Tone.Transport.seconds;
        for (let track of state.song.midi.tracks) {
            for (let { note, time, duration, velocity } of track.data) {
                let width = this.note_width;
                let height = PianoNotesRenderer.sec_to_pixels(duration);
                let x = ((note.octave - 2) * 7 + note.order() + 0.5 * note.is_accidental()) * width;
                let y = this.canvas.height + PianoNotesRenderer.sec_to_pixels(track_elapsed - time);

                let current = y - height < this.canvas.height && y > this.canvas.height;
                let color = PianoNotesRenderer.get_note_fill_color({ note, time, duration, velocity, current });
                this.context.fillStyle = color
                this.context.fillRect(x, y - height, width, height);
            }
        }
    }

    render_progress_bar() {
        let track_elapsed = Tone.Transport.seconds;
        const track_total = state.song.midi.tracks.reduce((accumulator, track) => {
            let max_duration_in_track = track.data.reduce((acc, { time, duration }) => Math.max(acc, time + duration), 0);
            return Math.max(accumulator, max_duration_in_track);
        }, 0);
        let progress = (track_total - track_elapsed) / track_total;
        this.context.fillStyle = "#aaaaaa";
        this.context.fillRect(0, 0, this.canvas.width * (1 - progress), 5);
    }

    render() {
        this.context.clearRect(0, 0, this.canvas.width, this.canvas.height);
        if (state.song !== null) {
            this.render_notes();
            this.render_waveform();
            this.render_progress_bar();
        }
        this.render_name();
    }
}


class PianoScoreRenderer {
    constructor(div) {
        this.width = 900;
        this.height = 220;
        this.current_score_index = 1;
        this.scroll_index = 0;
        this.num_notes_in_line = 16;
        this.renderer = new Vex.Flow.Renderer(div, Vex.Flow.Renderer.Backends.SVG);
        this.renderer.resize(this.width, this.height);
        this.context = this.renderer.getContext();

        this.treble = new Vex.Flow.Stave(30, 20, this.width - 75);
        this.treble.addClef("treble");
        this.treble.setContext(this.context);

        this.bass = new Vex.Flow.Stave(30, 20 + 60, this.width - 75);
        this.bass.addClef("bass");
        this.bass.setContext(this.context);

        this.voices = [];
    }

    static create_stave_note(time, total_duration, { keys, duration }) {
        let track_elapsed = Tone.Transport.seconds;
        let stave_note = new Vex.Flow.StaveNote({ keys, duration: duration.replace(".", "").replace(".", "") });
        if (duration.endsWith("..")) {
            Vex.Flow.Dot.buildAndAttach([stave_note], { all: true });
        } else if (duration.endsWith(".")) {
            Vex.Flow.Dot.buildAndAttach([stave_note], { all: true });
            Vex.Flow.Dot.buildAndAttach([stave_note], { all: true });
        }

        let current = (track_elapsed > time && track_elapsed < time + total_duration);

        for (let [idx, key] of keys.entries()) {
            let [note_repr, octave] = key.split("/");
            let note = new Note(note_repr, parseInt(octave));
            let hue = (note.order() + (0.5 * note.is_accidental())) * 360 / 7;
            let color = current ? "black" : `hsl(${hue}, 90%, 40%, 1)`;
            stave_note.setKeyStyle(idx, { strokeStyle: color, fillStyle: color });
            stave_note.setFlagStyle({ strokeStyle: color, fillStyle: color });
            stave_note.setStemStyle({ strokeStyle: color, fillStyle: color });
        }

        return stave_note;
    }


    render_voice() {
        let track_elapsed = Tone.Transport.seconds;
        const voice = new Vex.Flow.Voice({});
        let score = state.song.scores[this.current_score_index];
        if (!score || score.data.length === 0) { return; }

        let current_note_index = score.data.slice(this.scroll_index, this.scroll_index + this.num_notes_in_line).findIndex(({ time, duration }) => {
            return track_elapsed > time && track_elapsed < time + duration
        });

        if (current_note_index > 2 * this.num_notes_in_line / 3) {
            this.scroll_index += this.num_notes_in_line / 2;
        }

        let notes_ = score.data.slice(this.scroll_index, this.scroll_index + this.num_notes_in_line).map(({ time, duration, notation }) => {
            return PianoScoreRenderer.create_stave_note(time, duration, notation);
        });

        voice.setMode(Vex.Flow.Voice.Mode.SOFT);
        voice.addTickables(notes_);
        Vex.Flow.Accidental.applyAccidentals([voice], "C");
        new Vex.Flow.Formatter().joinVoices([voice]).format([voice], 800);
        voice.draw(this.context, this.treble);
    }

    render() {
        this.context.clear();
        this.treble.draw();
        this.bass.draw();

        if (state.song !== null) {
            this.render_voice();
        }
    }
}

function setup_sample_songs_selector() {
    fetch("/song_list").then(async (response) => {
        let data = await response.json();
        let select = document.getElementById("sample-songs");
        let options = "";
        for (let i = 0; i < data.length; i++) {
            let name = data[i];
            options += `<option value="${i}"> ${name} </option>`;
        }
        select.innerHTML = options;
        load();
    });
}


function load() {
    let selected_song = document.getElementById("sample-songs").selectedOptions[0].value;
    fetch(`/song/${selected_song}`).then(async (response) => {
        // Setup tonejs and renderer
        if (state.song !== null) {
            for (let track of state.song.midi.tracks) track.player?.dispose();
        }

        let song = await response.json();
        let ticks_per_beat = song.midi.ticks_per_beat;
        let tempo = 120 / 60; // Measured in beats per second

        song.scores = song.scores.map(({ name, data }) => {
            let data_ = data.map((section) => {
                let start_time = (section.start_tick / ticks_per_beat) / tempo;
                let end_time = (section.end_tick / ticks_per_beat) / tempo;
                return {
                    notation: section.notation,
                    time: start_time,
                    duration: end_time - start_time,
                }
            });

            return {
                name: name,
                data: data_,
            };
        });

        song.midi.tracks = song.midi.tracks.map(({ name, data }) => {
            let data_ = data.map((section) => {
                let start_time = (section.start_tick / ticks_per_beat) / tempo;
                let end_time = (section.end_tick / ticks_per_beat) / tempo;
                return {
                    note: new Note(section.note, section.octave),
                    time: start_time,
                    duration: end_time - start_time,
                    velocity: section.velocity / 100,
                };
            });

            let player = new Tone.Part(((time, value) => {
                state.synth.triggerAttackRelease(value.note.toString(), value.duration, time, value.velocity);
            }), data_).start(0);

            return {
                name: name,
                data: data_,
                player: player,
            };
        });

        state.song = song;
        Tone.Transport.stop();
    });
}

function toggle() {
    if (Tone.Transport.state == "stopped" || Tone.Transport.state == "paused") {
        Tone.Transport.start();
    } else {
        Tone.Transport.pause();
    }
}

function stop() {
    Tone.Transport.stop();
    state.piano_score_renderer.scroll_index = 0;
}

function main() {
    state.synth.connect(state.waveform);
    setup_sample_songs_selector();
    setInterval(state.piano_notes_renderer.render.bind(state.piano_notes_renderer), 25);
    setInterval(state.piano_score_renderer.render.bind(state.piano_score_renderer), 50);
}

let state = (() => {
    return {
        synth: new Tone.PolySynth(Tone.Synth).toDestination(),
        waveform: new Tone.Waveform,
        tempo: 120 / 60,
        song: null,
        piano_notes_renderer: new PianoNotesRenderer(document.getElementById("piano-notes")),
        piano_score_renderer: new PianoScoreRenderer(document.getElementById("score")),
    };
})();


document.addEventListener('keydown', (event) => event.code === 'Space' ? toggle() : null);
document.addEventListener("DOMContentLoaded", main);

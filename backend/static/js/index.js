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

class Renderer {
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

    render_notes() {
        let track_elapsed = Tone.Transport.seconds;
        for (let note_event of state.notes) {
            let { note, time, duration, velocity } = note_event;

            let width = this.note_width;
            let height = Renderer.sec_to_pixels(duration);
            let x = ((note.octave - 2) * 7 + note.order() + 0.5 * note.is_accidental()) * width;
            let y = this.canvas.height + Renderer.sec_to_pixels(track_elapsed - time);

            let current = y - height < this.canvas.height && y > this.canvas.height;
            let color = Renderer.get_note_fill_color({ note, time, duration, velocity, current });
            this.context.fillStyle = color
            this.context.fillRect(x, y - height, width, height);
        }
    }

    render_progress_bar() {
        let track_elapsed = Tone.Transport.seconds;
        const track_total = state.notes.reduce((accumulator, { time, duration }) => Math.max(accumulator, time + duration), 0);
        let progress = (track_total - track_elapsed) / track_total;
        this.context.fillStyle = "#aaaaaa";
        this.context.fillRect(0, 0, this.canvas.width * (1 - progress), 5);
    }

    render() {
        this.context.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.render_notes();
        this.render_progress_bar();
    }
}

let state = {
    synth: new Tone.PolySynth(Tone.Synth).toDestination(),
    track: null,
    notes: [],
    renderer: new Renderer(document.getElementById("piano-notes")),
};


function setup_button_callbacks() {
    let notes = document.querySelectorAll('.piano-keys > div > button[data-note]');
    for (let note of notes) {
        note.addEventListener("click", () => {
            state.synth.triggerAttackRelease(note.dataset.note, "8n", Tone.now());
        });
    }
}

function setup_renderer() {
    setInterval(state.renderer.render.bind(state.renderer), 25);
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
        if (state.track !== null) {
            state.track.dispose();
        }

        let data = await response.json();
        state.notes = data.map((section) => {
            return {
                note: new Note(section.note, section.octave),
                time: section.start_time / 1000,
                duration: (section.end_time - section.start_time) / 1000,
                velocity: section.velocity / 100,
            };
        });

        state.track = new Tone.Part(((time, value) => {
            state.synth.triggerAttackRelease(value.note.toString(), value.duration, time, value.velocity);
        }), state.notes).start(0);

        Tone.Transport.stop();
    });
}

function main() {
    setup_button_callbacks();
    setup_renderer();
    setup_sample_songs_selector();
}


document.addEventListener("DOMContentLoaded", main);

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
        for (let track of state.track_list) {
            for (let { note, time, duration, velocity } of track.data) {
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
    }

    render_progress_bar() {
        let track_elapsed = Tone.Transport.seconds;
        const track_total = state.track_list.reduce((accumulator, track) => {
            let max_duration_in_track = track.data.reduce((acc, { time, duration }) => Math.max(acc, time + duration), 0);
            return Math.max(accumulator, max_duration_in_track);
        }, 0);
        let progress = (track_total - track_elapsed) / track_total;
        this.context.fillStyle = "#aaaaaa";
        this.context.fillRect(0, 0, this.canvas.width * (1 - progress), 5);
    }

    render() {
        this.context.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.render_notes();
        this.render_waveform();
        this.render_name();
        this.render_progress_bar();
    }
}

let state = {
    synth: new Tone.PolySynth(Tone.Synth).toDestination(),
    waveform: new Tone.Waveform,
    track_list: [],
    renderer: new Renderer(document.getElementById("piano-notes")),
};


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
        for (let track of state.track_list) track.player?.dispose();

        let track_list = await response.json();

        state.track_list = track_list.map(({ name, data }) => {
            let data_ = data.map((section) => {
                return {
                    note: new Note(section.note, section.octave),
                    time: section.start_time / 1000,
                    duration: (section.end_time - section.start_time) / 1000,
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

function main() {
    state.synth.connect(state.waveform);

    setup_sample_songs_selector();
    setInterval(state.renderer.render.bind(state.renderer), 25);
}

document.addEventListener('keydown', function(event) {
    if (event.code === 'Space') toggle();
});

document.addEventListener("DOMContentLoaded", main);

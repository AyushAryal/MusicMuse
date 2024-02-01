let synth;
let now;

let piano_action_history = [];
let piano_note_history = [];

let mouse_down = 0;
document.body.onpointerdown = function() { ++mouse_down; }
document.body.onpointerup = function() { --mouse_down; }


function render_canvas() {
    const milliseconds_to_pixels = (msec) => msec / 1000 * 60;
    const canvas = document.getElementById("piano-notes");
    canvas.width = parseInt(getComputedStyle(canvas).width);
    canvas.height = parseInt(getComputedStyle(canvas).height);
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    let render_time = +new Date();
    let natural_notes_order = ['C', 'D', 'E', 'F', 'G', 'A', 'B'];
    for (let { note, octave, start_time, end_time } of piano_note_history) {
        let y = canvas.height - milliseconds_to_pixels(render_time - start_time)
        const width = getComputedStyle(document.body).getPropertyValue('--white-key-width');
        if (end_time === Infinity) end_time = render_time;
        let height = milliseconds_to_pixels(end_time - start_time);
        let is_accidental = note[1] === "#";
        let order = natural_notes_order.indexOf(note[0])
        let x = ((octave - 2) * 7 + order + 0.5 * is_accidental) * width;
        ctx.fillStyle = `hsl(${(order + (0.5 * is_accidental)) * 360 / 7}, 50%, 50%)`;
        ctx.fillRect(x, y, width, height);
    }
}


function generate_piano_note_history_from_action_history() {
    const map = new Map();
    piano_note_history = [];
    for (let { type, note, octave, timestamp } of piano_action_history) {
        let key = `${note}${octave}`;
        if (map.has(key) && type !== "stop" || !map.has(key) && type === "stop") {
            continue; // ignore invalid states
        }
        if (type == "start") {
            map.set(key, { note, octave, timestamp });
        } else if (type == "stop") {
            let start_note = map.get(key);
            piano_note_history.push({ note, octave, start_time: start_note.timestamp, end_time: timestamp });
            map.delete(key);
        }
    }

    for (let [_, value] of map) {
        let { note, octave, timestamp } = value;
        piano_note_history.push({ note, octave, start_time: timestamp, end_time: Infinity });
    }
}

function piano_on_action({ type, note, octave }) {
    let timestamp = +new Date();
    if (piano_action_history.length > 200) {
        piano_action_history = piano_action_history.slice(100);
    }
    if (type === "start") {
        synth.triggerAttack(`${note}${octave}`, now);
    } else {
        synth.triggerRelease(`${note}${octave}`, now + 1);
    }
    piano_action_history.push({ type, note, octave, timestamp });
    generate_piano_note_history_from_action_history();
}

function piano_on_event(event) {
    let event_type = event.type;
    let node = event.target;

    if (event_type == "pointerdown") {
        mouse_down += 1;
        event.stopPropagation();
    } else if (event_type == "pointerup") {
        mouse_down -= 1;
        event.stopPropagation();
    }

    if (mouse_down) {
        if (event_type == "pointerdown" || event_type == "pointerover") {
            piano_on_action({ type: "start", note: node.dataset.note, octave: node.dataset.octave });
        } else if (event_type == "pointerout" || event_type == "pointerup") {
            piano_on_action({ type: "stop", note: node.dataset.note, octave: node.dataset.octave });
        }
    } else {
        if (event_type == "pointerup") {
            piano_on_action({ type: "stop", note: node.dataset.note, octave: node.dataset.octave });
        }
    }
}

function main() {
    synth = new Tone.PolySynth(Tone.Synth).toDestination();
    now = Tone.now();

    let notes = document.querySelectorAll('.piano-keys > div > div[data-note]');
    for (let note of notes) {
        note.addEventListener("pointerdown", piano_on_event);
        note.addEventListener("pointerup", piano_on_event);
        note.addEventListener("pointerover", piano_on_event);
        note.addEventListener("pointerout", piano_on_event);
    }

    setInterval(render_canvas, 25);
}

function download_and_play() {
    fetch("/song").then(async (response) => {
        let data = await response.json();
        let current_time = +new Date();
        now = Tone.now();
        for (let section of data) {
            synth.triggerAttackRelease(
                `${section.note}${section.octave}`,
                (section.end_time - section.start_time) / 1000,
                now + section.start_time / 1000,
            );
            section.start_time += current_time;
            section.end_time += current_time;
        }
        piano_note_history = data;
    });
}

document.addEventListener("DOMContentLoaded", main);

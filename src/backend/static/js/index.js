"use strict";

class Note {
  constructor(note, octave) {
    this._note = note;
    this._octave = octave;
  }

  get octave() {
    return this._octave;
  }
  get note() {
    return this._note;
  }

  is_accidental = () => this._note.length > 1;
  toString = () => `${this._note}${this._octave}`;
  order = () => ["C", "D", "E", "F", "G", "A", "B"].indexOf(this._note[0]);
}

class PianoNotesRenderer {
  constructor(canvas) {
    canvas.width = parseInt(getComputedStyle(canvas).width);
    canvas.height = parseInt(getComputedStyle(canvas).height);
    this.note_width = getComputedStyle(document.body).getPropertyValue(
      "--white-key-width",
    );
    this.canvas = canvas;
    this.context = canvas.getContext("2d");
  }

  static sec_to_pixels = (msec) => msec * 60;

  static get_note_fill_color({ note, time, duration, velocity, current }) {
    let hue = ((note.order() + 0.5 * note.is_accidental()) * 360) / 7;
    let saturation = current ? "100%" : "60%";
    let lightness = current ? "60%" : "40%";
    let alpha = velocity;
    return `hsl(${hue}, ${saturation}, ${lightness}, ${alpha})`;
  }

  render_name() {
    this.context.font = "16px Arial";
    this.context.fillStyle = `hsl(${180 + Math.sin(+new Date() / 3000) * 180}, 40%, 60%)`;
    this.context.fillText("MeloWave", this.canvas.width - 95, 65);
  }

  render_waveform() {
    const CIRCLE_INNER_RADIUS = 50;
    let scaleY = 10;
    let offsetY = 60;
    let offsetX = this.canvas.width - 60;

    const waveformValues = state.waveform.getValue();
    const pointsToAverage = 16;

    let averagePoints = [];
    for (let i = 0; i < waveformValues.length; i += pointsToAverage) {
      averagePoints.push(
        (waveformValues
          .slice(i, i + pointsToAverage)
          .reduce((acc, val) => acc + val, 0) *
          scaleY) /
          pointsToAverage,
      );
    }

    const to_polar = (x, y) => {
      let theta = (x / (averagePoints.length - 2)) * (2 * Math.PI);
      let radius = CIRCLE_INNER_RADIUS + y;
      return [theta, radius];
    };

    this.context.beginPath();
    let [initialTheta, initialR] = to_polar(0, 0);
    let [initialX, initialY] = [
      initialR * Math.cos(initialTheta),
      initialR * Math.sin(initialTheta),
    ];
    this.context.moveTo(initialX + offsetX, initialY + offsetY);

    for (let i = 1; i < averagePoints.length - 1; i += 2) {
      let pointA = averagePoints[i - 1];
      let pointB = averagePoints[i];
      let pointC = averagePoints[i + 1];
      let [controlPointTheta, controlPointR] = to_polar(
        i,
        2 * pointB - 0.5 * (pointA + pointC),
      );
      if (i + 2 >= averagePoints.length - 1) {
        pointC = 0;
      }
      let [theta, r] = to_polar(i + 1, pointC);
      if (i + 2 >= averagePoints.length - 1) {
        theta = 0;
      }
      let [controlPointX, controlPointY] = [
        controlPointR * Math.cos(controlPointTheta),
        controlPointR * Math.sin(controlPointTheta),
      ];
      let [x, y] = [r * Math.cos(theta), r * Math.sin(theta)];
      this.context.quadraticCurveTo(
        controlPointX + offsetX,
        controlPointY + offsetY,
        x + offsetX,
        y + offsetY,
      );
    }

    this.context.strokeStyle = `hsl(${180 + Math.sin(+new Date() / 3000) * 180}, 40%, 60%)`;
    this.context.lineWidth = 3;
    this.context.fillStyle = `hsl(${180 + Math.sin(+new Date() / 3000) * 180}, 40%, 60%, 0.1)`;
    this.context.fill();
    this.context.stroke();
  }

  render_notes() {
    let track_elapsed = Tone.Transport.seconds;
    const tracks = state.song.midi.tracks.filter((_, index) =>
      state.controls.selected_tracks_for_playback.includes(index),
    );
    for (let track of tracks) {
      for (let { note, octave, time, duration, velocity } of track.data) {
        let note_ = new Note(note, octave);
        let width = this.note_width;
        let height = PianoNotesRenderer.sec_to_pixels(duration);
        let x =
          ((note_.octave - 2) * 7 +
            note_.order() +
            0.5 * note_.is_accidental()) *
          width;
        let y =
          this.canvas.height +
          PianoNotesRenderer.sec_to_pixels(track_elapsed - time);

        let current = y - height < this.canvas.height && y > this.canvas.height;
        let color = PianoNotesRenderer.get_note_fill_color({
          note: note_,
          time,
          duration,
          velocity,
          current,
        });
        this.context.fillStyle = color;
        this.context.fillRect(x, y - height, width, height);
      }
    }
  }

  render_progress_bar() {
    let track_elapsed = Tone.Transport.seconds;
    const track_total = state.song.midi.tracks.reduce((accumulator, track) => {
      let max_duration_in_track = track.data.reduce(
        (acc, { time, duration }) => Math.max(acc, time + duration),
        0,
      );
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
    this.current_score_index = 0;
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
    let stave_note = new Vex.Flow.StaveNote({
      keys,
      duration: duration.replace(".", "").replace(".", ""),
    });
    if (duration.endsWith("..")) {
      Vex.Flow.Dot.buildAndAttach([stave_note], { all: true });
    } else if (duration.endsWith(".")) {
      Vex.Flow.Dot.buildAndAttach([stave_note], { all: true });
      Vex.Flow.Dot.buildAndAttach([stave_note], { all: true });
    }

    let current = track_elapsed > time && track_elapsed < time + total_duration;

    for (let [idx, key] of keys.entries()) {
      let [note_repr, octave] = key.split("/");
      let note = new Note(note_repr, parseInt(octave));
      let hue = ((note.order() + 0.5 * note.is_accidental()) * 360) / 7;
      let color = current ? "black" : `hsl(${hue}, 90%, 40%, 1)`;
      stave_note.setKeyStyle(idx, { strokeStyle: color, fillStyle: color });
    }

    return stave_note;
  }

  render_voice() {
    let track_elapsed = Tone.Transport.seconds;
    const voice = new Vex.Flow.Voice({});
    let score = state.song.scores[this.current_score_index];
    if (!score || score.data.length === 0) {
      return;
    }

    let current_note_index = score.data
      .slice(this.scroll_index, this.scroll_index + this.num_notes_in_line)
      .findIndex(({ time, duration }) => {
        return track_elapsed > time && track_elapsed < time + duration;
      });

    if (current_note_index > (2 * this.num_notes_in_line) / 3) {
      this.scroll_index += this.num_notes_in_line / 2;
    }

    let notes_ = score.data
      .slice(this.scroll_index, this.scroll_index + this.num_notes_in_line)
      .map(({ time, duration, notation }) => {
        return PianoScoreRenderer.create_stave_note(time, duration, notation);
      });

    var beams = Vex.Flow.Beam.generateBeams(notes_);
    voice.setMode(Vex.Flow.Voice.Mode.SOFT);
    voice.addTickables(notes_);

    Vex.Flow.Accidental.applyAccidentals([voice], "C");
    new Vex.Flow.Formatter().joinVoices([voice]).format([voice], 800);

    voice.draw(this.context, this.treble);

    for (let beam of beams) {
      beam.setContext(this.context).draw();
    }
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

function setup_controls() {
  // Song selector
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

  // Tempo input
  let dom_tempo = document.getElementById("tempo");
  dom_tempo.addEventListener("change", () => {
    state.controls.tempo = dom_tempo.value;
    stop();
    on_tempo_change();
  });
}

function update_song(song) {
  if (state.song !== null) {
    for (let track of state.song.midi.tracks) track.player?.dispose();
  }

  let ticks_per_beat = song.midi.ticks_per_beat;
  song.scores = song.scores.map(({ name, data }) => {
    let data_ = data.map((section) => {
      let start_time =
        (60 * section.start_tick) / ticks_per_beat / state.controls.tempo;
      let end_time =
        (60 * section.end_tick) / ticks_per_beat / state.controls.tempo;
      return {
        start_tick: section.start_tick,
        end_tick: section.end_tick,
        notation: section.notation,
        time: start_time,
        duration: end_time - start_time,
      };
    });

    return {
      name: name,
      data: data_,
    };
  });

  song.midi.tracks = song.midi.tracks.map(({ name, data }) => {
    let data_ = data.map((section) => {
      let start_time =
        (60 * section.start_tick) / ticks_per_beat / state.controls.tempo;
      let end_time =
        (60 * section.end_tick) / ticks_per_beat / state.controls.tempo;
      return {
        start_tick: section.start_tick,
        end_tick: section.end_tick,
        note: section.note,
        octave: section.octave,
        time: start_time,
        duration: end_time - start_time,
        velocity: section.velocity,
      };
    });

    let player = new Tone.Part((time, value) => {
      state.synth.triggerAttackRelease(
        `${value.note}${value.octave}`,
        value.duration,
        time,
        value.velocity,
      );
    }, data_).start(0);

    return {
      name: name,
      data: data_,
      player: player,
    };
  });
  state.song = song;
}

function on_update_song() {
  // Stop playback
  stop();

  // Setup new track controllers
  let template = document.getElementById("track-controls-template");
  let tracks = document.getElementById("tracks");
  tracks.innerHTML = "";

  for (let [i, track] of state.song.midi.tracks.entries()) {
    let dom_track = document.importNode(template.content, true);

    dom_track.querySelector("span").innerHTML =
      track.name !== "" ? track.name : `Untitled Track ${i}`;

    dom_track.getElementById("track-0-playback-toggle").id =
      `track-${i + 1}-playback-toggle`;
    dom_track.querySelector("label[for='track-0-playback-toggle']").htmlFor =
      `track-${i + 1}-playback-toggle`;
    dom_track.getElementById("track-0-score-toggle").id =
      `track-${i + 1}-score-toggle`;
    dom_track.querySelector("label[for='track-0-score-toggle']").htmlFor =
      `track-${i + 1}-score-toggle`;

    for (let elem of dom_track.querySelectorAll(
      ".track-control-playback, .track-control-score",
    )) {
      elem.addEventListener("change", () => {
        update_selected_track_list();
      });
    }
    tracks.appendChild(dom_track);
  }
  update_selected_track_list();
}

function on_tempo_change() {
  update_song(state.song);
  on_update_song();
}

function update_selected_track_list() {
  state.controls.selected_tracks_for_playback = [
    ...document.querySelectorAll(".track-control-playback").entries(),
  ]
    .filter(([_, dom]) => dom.checked)
    .map(([i, _]) => i);

  state.controls.selected_tracks_for_score = [
    ...document.querySelectorAll(".track-control-score").entries(),
  ]
    .filter(([_, dom]) => dom.checked)
    .map(([i, _]) => i);
}

function on_track_update() {}

function load() {
  let selected_song =
    document.getElementById("sample-songs").selectedOptions[0].value;
  fetch(`/song/${selected_song}`).then(async (response) => {
    update_song(await response.json());
    on_update_song();
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
  setup_controls();
  setInterval(
    state.piano_notes_renderer.render.bind(state.piano_notes_renderer),
    25,
  );
  setInterval(
    state.piano_score_renderer.render.bind(state.piano_score_renderer),
    50,
  );
}

let state = (() => {
  return {
    synth: new Tone.PolySynth(Tone.Synth).toDestination(),
    waveform: new Tone.Waveform(),
    song: null,
    piano_notes_renderer: new PianoNotesRenderer(
      document.getElementById("piano-notes"),
    ),
    piano_score_renderer: new PianoScoreRenderer(
      document.getElementById("score"),
    ),
    controls: {
      tempo: document.getElementById("tempo").value,
      selected_tracks_for_playback: [],
      selected_tracks_for_score: [],
    },
  };
})();

document.addEventListener("keydown", (event) =>
  event.code === "Space" ? toggle() : null,
);
document.addEventListener("DOMContentLoaded", main);

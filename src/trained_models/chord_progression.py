import functools
import json
import torch
import torch.nn
import random
from torch.utils.data import Dataset


class UltimateGuitarSongDataset(Dataset):
    def __init__(self, filename="out/chord_progressions_augmented.json"):
        with open(filename) as f:
            songs_info = json.load(f)
        songs_info = [
            (song_info[0], song_info[1][:8])
            for song_info in songs_info
            if len(song_info[1]) > 8
        ]
        self.songs_info = songs_info

        song_complexities, songs = zip(*songs_info)
        self.song_complexities = song_complexities
        self.songs = songs

        self.unique_chords = sorted(
            list(functools.reduce(lambda acc, x: acc | set(x), songs, set()))
        )

        self.unique_chords_to_tensors = {}
        for i, chord in enumerate(self.unique_chords):
            tensor = torch.zeros(len(self.unique_chords), dtype=torch.long)
            tensor[i] = 1
            self.unique_chords_to_tensors[chord] = tensor

        self.data = []
        for song_complexity, song in songs_info:
            x = (
                torch.cat(
                    (
                        torch.FloatTensor(song_complexity),
                        self.unique_chords_to_tensors[chord],
                    )
                )
                for chord in song[:-1]
            )
            y = (self.unique_chords_to_tensors[chord] for chord in song[1:])
            self.data.append((torch.stack(list(x)), torch.stack(list(y))))

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        return self.data[idx]


dataset = UltimateGuitarSongDataset()

OUTPUT_SIZE = len(dataset.unique_chords)
INPUT_SIZE = OUTPUT_SIZE + len(dataset.song_complexities[0])
HIDDEN_SIZE = 30
STATE_SIZE = 15


class RNNetwork(torch.nn.Module):
    def __init__(self, input_size, output_size, hidden_size, state_size):
        super().__init__()
        self.input_size = input_size
        self.output_size = output_size
        self.hidden_size = hidden_size
        self.state_size = state_size

        self.i2s = torch.nn.Linear(self.input_size + self.state_size, self.state_size)
        self.i2h = torch.nn.Linear(self.input_size + self.state_size, self.hidden_size)
        self.h2o = torch.nn.Linear(self.hidden_size, self.output_size)
        self.dropout = torch.nn.Dropout(0.10)
        self.softmax = torch.nn.LogSoftmax(dim=0)

    def forward(self, i: torch.Tensor, state: torch.Tensor):
        i_ = torch.cat((i, state))
        s = self.i2s(i_)
        h = self.i2h(i_)
        o = self.h2o(torch.relu(h))
        o = self.dropout(o)
        return self.softmax(o), s

    def init_hidden(self):
        return torch.zeros(self.state_size)


device = (
    "cuda"
    if torch.cuda.is_available()
    else "mps"
    if torch.backends.mps.is_available()
    else "cpu"
)

model = RNNetwork(INPUT_SIZE, OUTPUT_SIZE, HIDDEN_SIZE, STATE_SIZE).to(device)
model.load_state_dict(torch.load("out/rnn_chord_progressions_classification.pth"))
model.eval()


def get_chord_progression_from_key(key, preset_type):
    presets = {
        "simple": {"variance": 0.05, "mean": 0.45, "entropy": 2, "num_chords": 4},
        "advanced": {"variance": 1.0, "mean": 1.0, "entropy": 2.8, "num_chords": 6},
        "complex": {"variance": 2, "mean": 1, "entropy": 3, "num_chords": 8},
    }
    preset = presets[preset_type]

    complexity_tensor = torch.FloatTensor(
        [preset["variance"], preset["mean"], preset["entropy"]]
    )


    chord_progression = [key]
    with torch.no_grad():
        state = model.init_hidden()
        pred = dataset.unique_chords_to_tensors[key]
        for _ in range(preset["num_chords"] - 1):
            pred, state = model(torch.cat((complexity_tensor, pred)), state)
            prob = torch.exp(pred)
            prob = prob / torch.sum(prob)
            _, idxs = torch.topk(prob, k=3)
            pred_idx = random.choice(idxs).item()
            predicted_chord = dataset.unique_chords[pred_idx]
            chord_progression.append(predicted_chord)

            pred = torch.zeros(len(dataset.unique_chords))
            pred[pred_idx] = 1

    return chord_progression

import sys
import json
import torch
import torch.nn as nn
import numpy as np
from torch.utils.data import Dataset, DataLoader, random_split
from gensim.models import KeyedVectors


class UltimateGuitarSongDataset(Dataset):
    def __init__(self, chord_vectors, filename="out/chord_progressions.json"):
        with open(filename) as f:
            songs = json.load(f)
            assert isinstance(songs, list)

        songs = [song for song in songs if len(song) > 1 and len(song) < 200]
        len_ = max(len(song) for song in songs)

        songs = [lst * ((len_ + len(lst) - 1) // len(lst)) for lst in songs]
        songs = [lst[:len_] for lst in songs]

        songs = [
            [torch.from_numpy(chord_vectors[chord].copy()) for chord in song]
            for song in songs
        ]

        self.data = []
        for song in songs:
            x = torch.stack(song[:-1])
            y = torch.stack(song[1:])
            self.data.append((x, y))

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        return self.data[idx]


class LSTMNetwork(nn.Module):
    def __init__(self, dim, hidden=None):
        super().__init__()
        if not hidden:
            hidden = dim

        self.dim = dim
        self.hidden = hidden

        self.lstm = nn.LSTM(self.dim, self.hidden, batch_first=True)
        self.hidden2out = nn.Linear(self.hidden, self.dim)

    def forward(self, batch: torch.Tensor):
        out, _ = self.lstm(batch)
        pred = self.hidden2out(out)
        return pred


def train_loop(dataloader, model, loss, optimizer):
    model.train()
    for batch_num, (x, y) in enumerate(dataloader):
        pred = model(x)
        cost = loss(pred, y)
        cost.backward()
        optimizer.step()
        optimizer.zero_grad()
        if batch_num % 1000 == 0:
            print(f"Loss: {cost:>7f}")


def test_loop(dataloader, model, loss, wv):
    model.eval()
    test_loss, correct = 0, 0

    (64, 198, 8), (64, 198, 8)

    total_len = 0
    with torch.no_grad():
        for x, y in dataloader:
            pred = model(x)
            test_loss += loss(pred, y)
            total_len += y.size(1) * y.size(0)
            for pred_, y_ in zip(pred, y):
                similar = wv.similar_by_vector(pred_.numpy(), topn=5)
                if any(np.array_equal(wv[chord], y_) for chord, _ in similar):
                    correct += 1
    correct = correct / total_len * 100
    test_loss /= len(dataloader)
    print(f"Accuracy: {correct:>0.1f}, Average Loss: {test_loss:>8f}")


def main():
    chord_vectors = KeyedVectors.load("./out/vectors.bin")
    dim = chord_vectors["C"].size

    train_, test_ = random_split(UltimateGuitarSongDataset(chord_vectors), [0.8, 0.2])
    batch_size = 64
    train = DataLoader(train_, batch_size=batch_size)
    test = DataLoader(test_, batch_size=batch_size, shuffle=True)

    device = (
        "cuda"
        if torch.cuda.is_available()
        else "mps"
        if torch.backends.mps.is_available()
        else "cpu"
    )
    print(f"Using {device} device")

    model = LSTMNetwork(dim).to(device)
    loss = nn.MSELoss()
    optimizer = torch.optim.SGD(model.parameters(), lr=0.1)
    epochs = 2
    for epoch in range(epochs):
        print(f"Epoch: {epoch+1}")
        print("---------------")
        train_loop(train, model, loss, optimizer)
        test_loop(test, model, loss, chord_vectors)

    torch.save(model.state_dict(), "./out/model.pth")


def test():
    chord_vectors = KeyedVectors.load("./out/vectors.bin")
    dim = chord_vectors["C"].size

    device = (
        "cuda"
        if torch.cuda.is_available()
        else "mps"
        if torch.backends.mps.is_available()
        else "cpu"
    )
    print(f"Using {device} device")
    model = LSTMNetwork(dim).to(device)
    model.load_state_dict(torch.load("./out/model.pth"))
    model.eval()

    with torch.no_grad():
        while True:
            try:
                chord_sequence_str = input("Enter chord sequence: ").strip()
            except KeyboardInterrupt:
                break

            if chord_sequence_str == "":
                break

            chord_sequence = torch.stack(
                [
                    torch.from_numpy(np.copy(chord_vectors[c]))
                    for c in chord_sequence_str.split()
                ]
            )
            pred = model(chord_sequence)
            similar = chord_vectors.similar_by_vector(pred[-1].numpy(), topn=6)
            chords, _ = zip(*similar)
            print(chord_sequence)
            print(pred)
            print(chords)


if __name__ == "__main__":
    main()

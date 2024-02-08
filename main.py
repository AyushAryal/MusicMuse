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

        songs = [song for song in songs if len(song) > 10 and len(song) < 200]
        len_ = max(len(song) for song in songs)
        songs = [lst * ((len_ + len(lst) - 1) // len(lst)) for lst in songs]
        songs = [lst[:len_] for lst in songs]
        songs = [
            [torch.from_numpy(chord_vectors[chord].copy()) for chord in song]
            for song in songs
        ]

        self.data = []
        for song in songs:
            self.data.append((torch.stack(song[:-1]), torch.stack(song[1:])))

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        return self.data[idx]


class RNNetwork(nn.Module):
    def __init__(self, input_size, output_size, hidden_size, state_size):
        super().__init__()

        self.input_size = input_size
        self.output_size = output_size
        self.hidden_size = hidden_size
        self.state_size = state_size

        self.i2s = torch.nn.Linear(self.input_size + self.state_size, self.state_size)
        self.i2h = torch.nn.Linear(self.input_size + self.state_size, self.hidden_size)
        self.h2h = torch.nn.Linear(self.hidden_size, self.hidden_size)
        self.h2o = torch.nn.Linear(self.hidden_size, self.output_size)
        self.dropout = torch.nn.Dropout(0.1)
        self.softmax = torch.nn.LogSoftmax(dim=0)

    def forward(self, i: torch.Tensor, state: torch.Tensor):
        i_ = torch.cat((i, state))
        s = self.i2s(i_)
        h = self.i2h(i_)
        h2 = self.h2h(torch.relu(h))
        o = self.h2o(torch.relu(h2))
        o = self.dropout(o)
        return self.softmax(o), s

    def init_hidden(self):
        return torch.zeros(self.state_size)


def train_loop(dataloader, model, loss, optimizer, epoch):
    model.train()
    total_loss = 0
    for batch_idx, (batched_x, batched_y) in enumerate(dataloader):
        cost = 0
        for x, y in zip(batched_x, batched_y):
            state = model.init_hidden()
            for i, (x_, y_) in enumerate(zip(x, y)):
                pred, state = model(x_, state)
                cost += loss(pred, y_)

        cost.backward()

        if (batch_idx + 1) % 10 == 0:
            optimizer.step()
            optimizer.zero_grad()

        batch_loss = cost.item() / (batched_x.size(0) * batched_x.size(1) * batched_x.size(2))
        print(f"Batch {batch_idx} loss: {batch_loss}")

        total_loss += batch_loss

    return total_loss


def test_loop(dataloader, model, loss, wv, epoch):
    model.eval()
    test_loss, correct = 0, 0
    total_len = 0
    with torch.no_grad():
        for batch_idx, (batched_x, batched_y) in enumerate(dataloader):
            batch_loss = 0
            for x, y in zip(batched_x, batched_y):
                state = model.init_hidden()
                for x_, y_ in zip(x, y):
                    pred, state = model(x_, state)
                    batch_loss += loss(pred, y_)
                    similar = wv.similar_by_vector(pred.numpy(), topn=3)
                    if any(np.array_equal(wv[chord], y_) for chord, _ in similar):
                        correct += 1
            batch_loss /= batched_x.size(0) * batched_x.size(1)
            print(f"Test Batch {batch_idx} loss: {batch_loss}")
            test_loss += batch_loss
            total_len += batched_x.size(0) * batched_x.size(1) * batched_x.size(2)
    correct = correct / total_len * 100
    print(f"Accuracy: {correct:>0.1f}, Average Loss: {test_loss:>8f}")


HIDDEN_SIZE = 10
STATE_SIZE = 10


def main():
    chord_vectors = KeyedVectors.load("./out/vectors.bin")
    dim = chord_vectors["C"].size

    _, train_, test_ = random_split(
        UltimateGuitarSongDataset(chord_vectors), [0.00, 0.80, 0.20]
    )
    train = DataLoader(train_, batch_size=128, shuffle=True)
    test = DataLoader(test_, batch_size=128, shuffle=True)

    device = (
        "cuda"
        if torch.cuda.is_available()
        else "mps"
        if torch.backends.mps.is_available()
        else "cpu"
    )
    print(f"Using {device} device")

    model = RNNetwork(dim, dim, HIDDEN_SIZE, STATE_SIZE).to(device)
    loss = nn.MSELoss()
    optimizer = torch.optim.SGD(model.parameters(), lr=0.005)
    epochs = 15
    for epoch in range(epochs):
        print(f"Epoch: {epoch+1}")
        print("---------------")
        cost = train_loop(train, model, loss, optimizer, epoch)
        print("Loss in training: ", cost)
        test_loop(test, model, loss, chord_vectors, epoch)

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
    model = RNNetwork(dim, dim, HIDDEN_SIZE, STATE_SIZE).to(device)
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

            chord_sequence = [
                torch.from_numpy(np.copy(chord_vectors[c]))
                for c in chord_sequence_str.split()
            ]

            state = model.init_hidden()
            pred = None
            for chord in chord_sequence:
                pred, state = model(chord, state)
            similar = chord_vectors.similar_by_vector(pred.numpy(), topn=6)
            chords, _ = zip(*similar)
            print(chords)


if __name__ == "__main__":
    main()

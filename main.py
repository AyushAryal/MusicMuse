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

        songs = [
            [torch.from_numpy(chord_vectors[chord].copy()) for chord in song]
            for song in songs
        ]

        self.data = []
        for song in songs:
            self.data.extend(zip(song, song[1:]))

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        return self.data[idx]


class NeuralNetwork(nn.Module):
    def __init__(self, dim):
        super().__init__()
        self.linear_relu_stack = nn.Sequential(
            nn.Linear(dim, 32),
            nn.ReLU(),
            nn.Linear(32, 32),
            nn.ReLU(),
            nn.Linear(32, 32),
            nn.ReLU(),
            nn.Linear(32, dim),
        )

    def forward(self, x):
        return self.linear_relu_stack(x)


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

    with torch.no_grad():
        for x, y in dataloader:
            pred = model(x)
            test_loss += loss(pred, y)
            for pred_, y_ in torch.stack((pred, y), dim=1):
                similar = wv.similar_by_vector(pred_.numpy(), topn=5)
                if any(np.array_equal(wv[chord], y_) for chord, _ in similar):
                    correct += 1
    correct = correct / len(dataloader.dataset) * 100
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

    model = NeuralNetwork(dim).to(device)
    loss = nn.MSELoss()
    optimizer = torch.optim.SGD(model.parameters(), lr=1e-3)
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
    model = NeuralNetwork(dim).to(device)
    model.load_state_dict(torch.load("./out/model.pth"))
    model.eval()

    with torch.no_grad():
        while True:
            s = input("Enter chord: ").strip()
            pred = model(torch.from_numpy(chord_vectors[s]))
            similar = chord_vectors.similar_by_vector(pred.numpy(), topn=5)
            print(chord_vectors[s], pred, similar)
            if not s:
                break


if __name__ == "__main__":
    main()

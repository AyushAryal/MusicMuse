import argparse
import json
import functools
import operator
from typing import List

import matplotlib.pyplot as plt

from lib.chord2vec import chord2vec
from lib.chord_progression_parser import chord_progression_parser
from lib.music import Chord


def plot_chord_vectors_2d(chord_progressions: List[List[Chord]], model):
    vocab = functools.reduce(
        operator.or_, (set(progression) for progression in chord_progressions)
    )
    data = [(chord, list(model.wv[chord])) for chord in vocab]
    labels, vectors = zip(*data)
    x, y = zip(*vectors)
    plt.style.use("ggplot")
    plt.figure(figsize=(6, 6))
    plt.scatter(x, y, edgecolors="k", c="r")
    for i, label in enumerate(labels):
        plt.text(x[i], y[i], label, fontsize=12, ha="center", va="bottom")
    plt.show()


def plot_chord_vectors_3d(chord_progressions: List[List[Chord]], model):
    vocab = functools.reduce(
        operator.or_, (set(progression) for progression in chord_progressions)
    )
    data = [(chord, list(model.wv[chord])) for chord in vocab]
    labels, vectors = zip(*data)
    x, y, z = zip(*vectors)

    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")
    ax.scatter(x, y, z, c="b", marker="o", label="Data Points")
    for i, label in enumerate(labels):
        ax.text(x[i], y[i], z[i], label, fontsize=12, ha="center", va="bottom")
    plt.show()


def print_chord_vectors_nd(chord_progressions: List[List[Chord]], model):
    vocab = functools.reduce(
        operator.or_, (set(progression) for progression in chord_progressions)
    )
    data = [(chord, list(model.wv[chord])) for chord in vocab]
    print(data)


def generate_chord_vectors(chord_progressions, args):
    model = chord2vec(
        chord_progressions,
        vector_size=args.dimensions,
        epochs=args.epochs,
        context_window=args.context_window,
    )
    model.wv.save(args.output)
    return model


def main():
    parser = argparse.ArgumentParser(
        "generate_chord_vectors", "Generates chord2vec embeddings"
    )
    parser.add_argument(
        "-i",
        "--input",
        default="res/chord_progressions.json",
        help="The input json file path",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="out/vectors.bin",
        help="The output file path",
    )
    parser.add_argument(
        "-d",
        "--dimensions",
        type=int,
        default=8,
        help="The vector dimension",
    )
    parser.add_argument(
        "-e",
        "--epochs",
        type=int,
        default=10,
        help="The number of epochs",
    )
    parser.add_argument(
        "-c",
        "--context-window",
        type=int,
        default=3,
        help="The context window",
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Plot the vectors (if two dimensional)",
    )
    args = parser.parse_args()

    chord_progressions = []
    with open(args.input, encoding="utf8") as f:
        chord_progressions_ = json.load(f)
        for progression in chord_progressions_:
            chord_progression = chord_progression_parser(progression)
            chord_progressions.append(list(map(str, chord_progression)))

    model = generate_chord_vectors(chord_progressions, args)
    if args.plot:
        if args.dimensions == 2:
            plot_chord_vectors_2d(chord_progressions, model)
        if args.dimensions == 3:
            plot_chord_vectors_3d(chord_progressions, model)
        else:
            print(f"Cannot plot vector of size: {args.dimensions}")
            print("Showing list of vectors instead")
            print_chord_vectors_nd(chord_progressions, model)


if __name__ == "__main__":
    main()

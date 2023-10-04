import csv
from lib.chord_progression_parser import chord_progression_parser
from lib.chord2vec import chord2vec
import matplotlib.pyplot as plt
import operator
import functools
import argparse


def plot_chord_vectors(chord_progressions, model):
    vocab = list(
        functools.reduce(
            operator.or_, (set(progression) for progression in chord_progressions)
        )
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


def generate_chord_vectors(chord_progressions, args):
    model = chord2vec(
        chord_progressions,
        vector_size=args.dimensions,
        epochs=args.epochs,
    )
    model.save(args.output)
    return model


def main():
    parser = argparse.ArgumentParser(
        "generate_chord_vectors", "Generates chord2vec embeddings"
    )
    parser.add_argument(
        "-i",
        "--input",
        default="res/chord_progressions.csv",
        help="The input csv file path",
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
        "--plot",
        action="store_true",
        help="Plot the vectors (if two dimensional)",
    )
    args = parser.parse_args()

    chord_progressions = []
    with open(args.input, encoding="utf8") as f:
        reader = csv.reader(f)
        for _, _, chord_notations, *_ in reader:
            chord_progression = chord_progression_parser(chord_notations.split("-"))
            for semitones in range(0, 12):
                transposed = [chord.transpose(semitones) for chord in chord_progression]
                chord_progressions.append(list(map(str, transposed)))

    model = generate_chord_vectors(chord_progressions, args)
    if args.plot:
        if args.dimensions == 2:
            plot_chord_vectors(chord_progressions, model)
        else:
            print(f"Cannot plot vector of size: {args.dimensions}")


if __name__ == "__main__":
    main()

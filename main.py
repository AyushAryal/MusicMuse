import csv
from lib.chord2vec import chord_progression_parser, chord2vec, EpochLogger
import matplotlib.pyplot as plt
import operator
import functools

def main():
    chord_progressions = []
    with open("res/chord_progressions.csv", encoding="utf8") as f:
        reader = csv.reader(f)
        for _, _, chord_notations, *_ in reader:
            chord_progression = chord_progression_parser(chord_notations.split("-"))
            for semitones in range(0, 12):
                transposed = [chord.transpose(semitones) for chord in chord_progression]
                chord_progressions.append(list(map(str, transposed)))
    model = chord2vec(chord_progressions, vector_size=2, epochs=10, callbacks=[EpochLogger()])
    model.save("res/vectors.bin")

    vocab = list(functools.reduce(operator.or_, (set(progression) for progression in chord_progressions)))
    data = [(chord, list(model.wv[chord])) for chord in vocab]
    labels, vectors = zip(*data)
    x, y = zip(*vectors)
    plt.style.use("ggplot")
    plt.figure(figsize=(6, 6))
    plt.scatter(x, y, edgecolors='k', c='r')
    for i, label in enumerate(labels):
        plt.text(x[i], y[i], label, fontsize=12, ha='center', va='bottom')
    plt.show()

    print(model.wv.distance("C", "G"))

if __name__ == '__main__':
    main()
import librosa
import glob

class Audio:
    def __init__(self, path):
        self.path = path

    def beat_tempo_data(self):
        y, sr = librosa.load(self.path, offset=20, duration=20)
        temp, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        beat_times = librosa.frames_to_time(beat_frames, sr=sr)
        return (temp, beat_times)


def calculate_differences(array):
    differences = []
    for i in range(1, len(array)):
        difference = array[i] - array[i - 1]
        differences.append(difference)
    return differences


def estimate_tempo(audio_path):
    tempo, _ = Audio(audio_path).beat_tempo_data()
    return tempo


def main():
    for f in glob.glob("res/others/*.wav"):
        tempo = estimate_tempo(f)
        print(f"{tempo:06.2f} {f}")


if __name__ == "__main__":
    main()

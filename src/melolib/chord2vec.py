import datetime
import time

from gensim.models import Word2Vec
from gensim.models.callbacks import CallbackAny2Vec


class EpochLogger(CallbackAny2Vec):
    def __init__(self):
        self.epoch = 1
        self.st = 0
        self.et = 0

    def on_epoch_begin(self, model):
        self.st = time.time()
        timestamp_st = datetime.datetime.fromtimestamp(self.st).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        print("{}: Beginning Epoch #{}...".format(timestamp_st, self.epoch))

    def on_epoch_end(self, model):
        self.et = time.time()
        timestamp_et = datetime.datetime.fromtimestamp(self.et).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        dur = self.et - self.st

        print(
            "{}: Epoch #{} completed in {:.1f} seconds.".format(
                timestamp_et, self.epoch, dur
            )
        )
        self.epoch += 1


def chord2vec(
    sentences,
    min_count=1,
    context_window=3,
    vector_size=10,
    algorithm=0,
    epochs=5,
    workers=3,
    callbacks=[EpochLogger()],
):
    model = Word2Vec(
        sentences,
        min_count=min_count,
        window=context_window,
        vector_size=vector_size,
        sg=algorithm,
        epochs=epochs,
        workers=workers,
        callbacks=callbacks,
    )
    return model

import beepy
from datetime import datetime, timedelta
import random
from time import sleep


class SIReaderReadout():

    CARD_POLL = list(range(2095960, 2095970))
    PUNCHES = {
        2095961: [45, 31, 40, 41, 39],
        2095962: [44, 35],
        2095963: [33, 41, 42, 43],
        2095964: [33, 34, 35, 36, 43],
        2095965: [41, 42, 43],
        2095966: [41, 42, 46, 43],
    }

    def __init__(self):
        self.sicard = None
        self.cardtype = None

    def _beep(self):
        beepy.beep('error')

    def _random_punches(self, count=2):
        punches = list(range(31, 49))
        random.shuffle(punches)
        return punches[0:count]

    def poll_sicard(self):
        if len(self.CARD_POLL) == 0:
            raise KeyboardInterrupt
        random.shuffle(self.CARD_POLL)
        self.sicard = self.CARD_POLL.pop()
        return self.sicard

    def read_sicard(self, reftime=None):
        if self.sicard in self.PUNCHES.keys():
            punches = self.PUNCHES[self.sicard]
        else:
            punches = self._random_punches(random.randint(2, 8))

        times = [datetime.now() - timedelta(seconds=random.randint(120, 300))]
        for _ in range(len(punches)):
            times.append(
                times[-1] + timedelta(seconds=random.randint(15, 120)))

        return {
            "sicard": self.sicard,
            "punches": list(zip(punches, times))
        }

    def ack_sicard(self):
        #print(f"Card {self.sicard} read")
        #self._beep()
        # sleep(0.5)
        pass

    def disconnect(self):
        pass

import beepy
import random
from time import sleep


class SIReaderReadout():

    CARD_POLL = list(range(2095960, 2095970))
    sicard = None

    def __init__(self):
        self.sicard = None
        self.cardtype = None

    def _beep(self):
        beepy.beep('error')

    def poll_sicard(self):
        random.shuffle(self.CARD_POLL)
        self.sicard = self.CARD_POLL.pop()
        return self.sicard

    def ack_sicard(self):
        print(f"Card {self.sicard} read")
        #self._beep()
        #sleep(0.5)


#!/usr/bin/env python3
#
#    Copyright (C)    2019  Per Magnusson <per.magnusson@gmail.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
Script to read out the data from an SI card.

To select a specific serial port, provide it's name as the first command line
parameter to the program.
"""

from pymongo import MongoClient
import pymongo
from sireader_mock import SIReaderReadout as SIReaderReadoutMock
from sireader2 import SIReaderReadout
import argparse
import csv
import datetime
from typing import Any, Dict, List, Tuple

Punch = Tuple[int, datetime.datetime]
ConfigRecord = Tuple[str, str, int, int, Any]
Config = Dict[int, ConfigRecord]


class CardNotFound(Exception):
    pass


class PunchChecker:
    def __init__(self, sireader):
        self._sireader = sireader
        self._mongo = MongoClient().routing_game

    def check_max_hops(self, card_data, max_hops) -> bool:
        # TODO: Odstranit duplicity
        return len(card_data["punches"]) <= max_hops

    def _check_task(self, task, punches):
        basic = len(punches) > 0 and punches[-1][0] == task["to"]
        bonus = basic and {
            'via': lambda x: x in [p[0] for p in punches[0:-1]],
            'till': lambda x: punches[-1][1] < x,
            'hops': lambda x: (len(punches)-1 <= x if punches[0][0] == task["from"] else len(punches) <= x),
        }[task["bonus"]["type"]](task["bonus"]["arg"])

        return {
            "basic": basic,
            "bonus": bonus,
        }

    def read_loop(self):
        try:
            packets = self._mongo.packets
            print('Insert SI card to be read')
            while True:
                # wait for a card to be inserted into the reader
                while not self._sireader.poll_sicard():
                    pass

                # read out card data
                sicard = self._sireader.sicard
                sidata = self._sireader.read_sicard()
                self._sireader.ack_sicard()

                punches = sidata["punches"]
                packet = next(packets.find({
                    "sicard": sicard,
                    "results": {
                        "$exists": False,
                    },
                }).sort([('created', pymongo.DESCENDING)]), None)
                if packet:
                    results = self._check_task(packet["task"], punches)
                    # print(results)
                    packets.update_one({
                        u'_id': packet["_id"],
                    }, {
                        '$set': {
                            'punches': punches,
                            'results': results,
                        },
                    })
                    print(
                        f"SI card {sicard} read and updated in the database.")
                else:
                    print(f"SI card {sicard} NOT FOUND in the database!")

        except KeyboardInterrupt:
            self._sireader.disconnect()


def parse_options():
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--mock', action='store_true', default=False)

    return parser.parse_args()


def check_scorelauf(controls: List[int], punches: List[int]) -> bool:
    return set(controls).intersection(set(punches)) == set(controls)


if __name__ == '__main__':
    options = parse_options()
    sireader = SIReaderReadoutMock() if options.mock else SIReaderReadout()
    checker = PunchChecker(sireader)
    checker.read_loop()

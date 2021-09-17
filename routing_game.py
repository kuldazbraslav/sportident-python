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

from sireader2 import SIReaderReadout
import argparse
import csv
import datetime
from typing import List, Tuple

Punch = Tuple[int, datetime.datetime]
Result = Tuple[bool, datetime.timedelta]


def parse_options():
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output-file', dest='output_file', required=True)

    return parser.parse_args()


def check_fixed_order(controls: List[int], punches: List[int]) -> bool:
    for c in controls:
        try:
            idx = punches.index(c)
            punches = punches[idx+1:]
        except ValueError:
            return False
    return True


def check_via(punches: List[int], start: int, finish: int, bonus: int) -> Tuple[bool, bool]:
    return (
        check_fixed_order([start, finish], punches),
        check_fixed_order([start, bonus, finish], punches),
    )


def check_scorelauf(controls: List[int], punches: List[int]) -> bool:
    return set(controls).intersection(set(punches)) == set(controls)


def read_loop(output_file: str):
    try:
        si = SIReaderReadout()
        print('Connected to station on port ' + si.port)
    except:
        print('Failed to connect to an SI station on any of the available serial ports.')
        exit(1)
    
    print('Insert SI-card to be read')
    try:
        while True:
            # wait for a card to be inserted into the reader
            while not si.poll_sicard():
                pass

            # some properties are now set
            card_number = si.sicard

            # read out card data
            card_data = si.read_sicard()
            print(card_data)

            # beep
            si.ack_sicard()

            # punches: List(Tuple(int, datetime.datetime))
            #   control number ----^    ^
            #   punch time -------------^
            punches = card_data["punches"]
            punch_controls = [x[0] for x in punches]
            total_time = punches[-1][1] - punches[0][1]
            result = check_via(punch_controls, 40, 100, 49)

            with open(output_file, 'a') as outfile:
                outwriter = csv.writer(outfile)
                outwriter.writerow([card_number, result[0], result[1], total_time])

    except KeyboardInterrupt:
        si.disconnect()


if __name__ == '__main__':
    options = parse_options()
    read_loop(options.output_file)

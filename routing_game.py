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
from typing import Any, Dict, List, Tuple

Punch = Tuple[int, datetime.datetime]
ConfigRecord = Tuple[str, str, int, int, Any]
Config = Dict[int, ConfigRecord]


def parse_options():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', dest='config_path', required=True)
    parser.add_argument('-o', '--output', dest='output_path', required=True)

    return parser.parse_args()


def check_fixed_order(controls: List[int], punches: List[Punch]) -> bool:
    punches = [x[0] for x in punches]
    for c in controls:
        try:
            idx = punches.index(c)
            punches = punches[idx+1:]
        except ValueError:
            return False
    return True


def check_via(punches: List[Punch], start: int, finish: int, bonus: int) -> Tuple[bool, bool]:
    return (
        check_fixed_order([start, finish], punches),
        check_fixed_order([start, bonus, finish], punches),
    )


def check_scorelauf(controls: List[int], punches: List[int]) -> bool:
    return set(controls).intersection(set(punches)) == set(controls)


def load_config(config_path: str):
    config = dict()
    with open(config_path, 'r') as config_file:
        r = csv.reader(config_file)
        for row in r:
            if r.line_num == 1:
                continue
            config[int(row[0])] = row[1:3] + [int(x) for x in row[3:]]

    return config



def read_loop(config: Config, output_path: str):
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

            # beep
            si.ack_sicard()

            # punches: List(Tuple(int, datetime.datetime))
            #   control number ----^    ^
            #   punch time -------------^
            punches = card_data["punches"]
            total_time = punches[-1][1] - punches[0][1]
            try:
                card_config = config[card_number]
            except KeyError:
                print("SI card {} not found in config!".format(card_number))
                continue

            result = globals()[card_config[1]](punches, card_config[2], card_config[3], card_config[4])

            with open(output_path, 'a') as output_file:
                outwriter = csv.writer(output_file)
                outwriter.writerow([card_number, card_config[0], result[0], result[1], total_time])

            print("SI card {} read successfully".format(card_number))

    except KeyboardInterrupt:
        si.disconnect()


if __name__ == '__main__':
    options = parse_options()
    config = load_config(options.config_path)
    read_loop(config, options.output_path)

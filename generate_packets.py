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
from sireader_mock import SIReaderReadout as SIReaderReadoutMock
from sireader2 import SIReaderReadout
from time import sleep
import argparse
import datetime


def parse_options():
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--teams', type=str,
                        dest='teams_path', default='teams.txt')
    parser.add_argument('-r', '--round', type=int, required=True),
    parser.add_argument('-b', '--batch', type=int, required=True),
    parser.add_argument('-m', '--mock', action='store_true', default=False)

    return parser.parse_args()


def generate_packets(round: int, batch: int, teams_path: str, sireader):
    mongo = MongoClient()
    task = mongo.routing_game.tasks.find_one({"round": round, "batch": batch})
    with open(teams_path, 'r') as teams_file:
        for team in teams_file.read().splitlines():
            print(f"Insert SI card for {team.upper()} team")
            while not sireader.poll_sicard():
                sleep(0.5)
            sicard = sireader.sicard
            packet = {
                "created": datetime.datetime.now().isoformat(),
                "sicard": sicard,
                "team": team,
                "task": task,
            }
            mongo.routing_game.packets.insert_one(packet)
            sireader.ack_sicard()


if __name__ == '__main__':
    options = parse_options()
    sireader = SIReaderReadoutMock() if options.mock else SIReaderReadout()
    generate_packets(options.round, options.batch,
                     options.teams_path, sireader)

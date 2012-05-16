#!/usr/bin/env python

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.

SCRITTA = ["Above", "Below", "Midline"]
PRESET = ["Normal", "Isomorphism", "Equal", "Injection", "Surjection", "Segment", "Dashed", "Invisible", "Manual"]
CODA = ["Normal", "Injection above", "Injection below", "Element"]
TRATTO = ["Normal", "Dashed", "Double", "No"]
DECORAZIONE = ["No", "Isomorphism"]
TESTA = ["Arrow", "Double arrow", "No"]


# Installation directory or just source directory?
import os

if 'commu.py' in os.listdir(os.path.dirname(os.path.realpath(__file__))):
    # launch from a source directory
    INSTALLATION_DIRECTORY = os.path.realpath(os.path.dirname(os.path.realpath(__file__)))
else:
    INSTALLATION_DIRECTORY = os.path.join("/", "usr", "share", "commu")

try:
    import xdg.BaseDirectory
    USER_DIRECTORY = os.path.join(xdg.BaseDirectory.xdg_config_home,
                                  "commu")
except ImportError:
    USER_DIRECTORY = os.path.join(os.path.expanduser("~"),
                                  ".config", "commu")

try:
    os.makedirs(USER_DIRECTORY)
except OSError:
    pass

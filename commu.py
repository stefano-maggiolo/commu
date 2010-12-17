#!/usr/bin/env python

"""
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import gtk
import sys

if __name__ == "__main__":
    import os
    if not 'commu_main.py' in os.listdir(os.path.dirname(__file__)):
        # commu is not launched from a source folder
        sys.path.append('/usr/share/python-support/commu/commu')
    import commu_main
    commu_main.Commu()
    gtk.main()

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

Create commutative diagrams with PGF/TikZ.
Version: 20080916
Author: Stefano Maggiolo <s.maggiolo@gmail.com>
"""

import gtk

if __name__ == "__main__":
    import commu_main
    try:
        import poppler
        commu_main.Commu(preview = True)
    except ImportError:
        commu_main.Commu(preview = False)
    gtk.main()
                

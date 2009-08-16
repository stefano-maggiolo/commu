#!/usr/bin/env python
from py2deb import Py2deb

version="2009.07.10"
changelog=open("changelog.txt","r").read()

p = Py2deb("commu")
p.author = "Stefano Maggiolo"
p.mail = "s.maggiolo@gmail.com"
p.description = "Draw commutative diagrams for LaTeX with PGF/TikZ"
p.url = "http://poisson.phc.unipi.it/~maggiolo/index.php/tag/commu/"
p.depends = "python-gtk2, python-glade2"
p.recommends = "pgf"
p.license = "gpl"
p.section = "tex"

p["/usr/bin"] = ["commu.py|commu",]
p["/usr/share/commu"] = ["commu.svg", "commu.glade"]
p["/usr/share/applications"] = ["commu.desktop"]
p.generate(version, changelog, rpm = True, src = True)

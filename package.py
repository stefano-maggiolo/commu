#!/usr/bin/env python
from py2deb import Py2deb

changelog=open("changelog.txt","r").read()
version=changelog.split("\n")[0][8:]

p = Py2deb("commu")
p.author = "Stefano Maggiolo"
p.mail = "s.maggiolo@gmail.com"
p.description = "Draw commutative diagrams for LaTeX with PGF/TikZ"
p.url = "http://poisson.phc.unipi.it/~maggiolo/index.php/tag/commu/"
p.depends = "python-gtk2, python-glade2, pgf"
p.recommends = "ghostscript, python-poppler, python-configobj"
p.license = "gpl"
p.section = "tex"

p["/usr/bin"] = ["commu.py|commu"]
p["/usr/share/python-support/commu/commu"] = ["commu_main.py", "commu_conf.py", "commu_objects.py", "commu_preview.py", "commu_templates.py"]
p["/usr/share/commu"] = ["commu.svg", "commu.glade", "no_diagram.png", "commu_templates.db"]
p["/usr/share/applications"] = ["commu.desktop"]
p.generate(version, changelog, rpm = True, src = True)

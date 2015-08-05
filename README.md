COMMU
=====

Commu is a graphical interface designed to aid drawing commutative
diagrams in LaTeX.

Commutative diagrams are used in almost all areas of mathematics,
especially in category theory and related fields, like algebraic
geometry, algebraic topology, logic, etc. They are composed of
objects, disposed in a grid-like fashion, and arrows (of many
different shapes) connecting them.

The usual way of drawing a commutative diagram in LaTeX is to use a
library like XYpic and write complex strings full of mnemonic codes to
draw different arrow shapes, directions, and so on.

With Commu, you have a graphical interface that can export
ready-to-use LaTeX code. You can save your diagram and edit them
afterwards. You can use templates to fill only the relevant changes of
many almost-equal diagrams. And, it exports code using the PGF/TikZ
library, often giving a more pleasant output with respect to XYpic.

To see a small presentation of Commu, go to the address
http://poisson.phc.unipi.it/~maggiolo/Software/commu/.


Installation on Linux
---------------------

You can just grab the sources from here or from the website
http://poisson.phc.unipi.it/~maggiolo/Software/commu/ and run them
from the repository

```bash
python ./commu.py
```

If you are running a Debian-based distribution, you can try install
the deb file in the same website.

```bash
sudo dpkg -i ./commu*deb
```


Installation on Max OS X
------------------------

It is possible to use Commu on Mac OS X. You have to install pyGTK
from http://sourceforge.net/projects/macpkg/files/PyGTK/.


Installation on Windows
-----------------------

It is possible to use Commu on Windows. The easiest way is to install
some Linux distribution. The hardest is to install pyGTK. But you have
to figure it out by yourself. If you manage to do it, please tell us
so we can update this section.



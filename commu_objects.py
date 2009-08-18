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

import pygtk
pygtk.require("2.0")
import gtk
import gtk.glade
import gobject
import operator
from collections import defaultdict
import os

from commu_conf import *

class Object:
    def __init__(self, tooltip):
        self.tooltip = tooltip
        
        self.label = gtk.Entry()
        tooltip.set_tip(self.label, "Drop here to create an arrow to this object.")
        self.box = gtk.HBox()
        self.coll = gtk.Button("0")
        self.coll.set_property('focus-on-click', False)
        self.coll.set_property('can-focus', False)
        tooltip.set_tip(self.coll, "Drag from here to create an arrow from this object.")
        self.box.add(self.label)
        self.box.add(self.coll)

        self.incomingArrows = self.outgoingArrows = 0
        self.coll.set_label("%d / %d" % (self.outgoingArrows, self.incomingArrows))

    def __del__(self):
        del(self.label)
        del(self.coll)
        del(self.box)

    def IncrementIncomingArrows(self, n = 1):
        self.incomingArrows += n
        self.coll.set_label("%d / %d" % (self.outgoingArrows, self.incomingArrows))
        
    def DecrementIncomingArrows(self, n = 1):
        self.incomingArrows -= n
        self.coll.set_label("%d / %d" % (self.outgoingArrows, self.incomingArrows))

    def IncrementOutgoingArrows(self, n = 1):
        self.outgoingArrows += n
        self.coll.set_label("%d / %d" % (self.outgoingArrows, self.incomingArrows))

    def DecrementOutgoingArrows(self, n = 1):
        self.outgoingArrows -= n
        self.coll.set_label("%d / %d" % (self.outgoingArrows, self.incomingArrows))

    def Reset(self):
        self.outgoingArrows = self.incomingArrows = 0
        self.coll.set_label("%d / %d" % (self.outgoingArrows, self.incomingArrows))
        self.label.set_text("")

    def Name(self):
        return self.label.get_text()

    def SetName(self, name):
        self.label.set_text(name)

    def Arrows(self):
        return self.outgoingArrows, self.incomingArrows

    def SetArrows(self, outgoingArrows, incomingArrows):
        self.outgoingArrows = outgoingArrows
        self.incomingArrows = incomingArrows
        self.coll.set_label("%d / %d" % (self.outgoingArrows, self.incomingArrows))        
        
    def ToWrite(self):
        return self.Name() != "" or self.outgoingArrows != 0 or self.incomingArrows != 0
    
    def SetFrom(self):
        red = gtk.gdk.color_parse("red")        
        self.coll.modify_bg(gtk.STATE_NORMAL, red)
        
    def SetTo(self):
        green = gtk.gdk.color_parse("green")
        self.coll.modify_bg(gtk.STATE_NORMAL, green)       

    def SetNormal(self, color):
        self.coll.modify_bg(gtk.STATE_NORMAL, color)

    def isEmpty(self):
        return self.outgoingArrows == 0 and self.incomingArrows == 0 and self.Name() == ""
        
class Arrow:
    def __init__(self, tooltip):
        self.tooltip = tooltip
        self.box = gtk.HBox()
        self.funz = gtk.Entry()
        self.tooltip.set_tip(self.funz, "The function.")
        self.ab = gtk.combo_box_new_text()
        self.tooltip.set_tip(self.ab, "Where the funtion should be.")
        self.preset = gtk.combo_box_new_text()
        self.tooltip.set_tip(self.preset, "Arrow type.")
        self.inarc = gtk.SpinButton(digits = 0)
        self.tooltip.set_tip(self.inarc, "Arrow curve, in degree.")
        self.canc = gtk.Button("Delete")
        self.tooltip.set_tip(self.canc, "Delete the arrow.")
        
        self.inarc.set_increments(5, 30)
        self.inarc.set_range(-180, 180)
        for x in SCRITTA:
            self.ab.append_text(x)
        for x in PRESET:
            self.preset.append_text(x)

        self.ab.set_active(0)
        self.preset.set_active(0)

        self.box.pack_start(self.funz, False, False)
        self.box.pack_start(self.ab, False, False)
        self.box.pack_start(self.preset, False, False)
        self.box.pack_start(self.inarc, False, False)
        self.box.pack_start(self.canc, False, False)

        self.set()

    def __del__(self):
        del(self.funz)
        del(self.preset)
        del(self.ab)
        del(self.inarc)
        del(self.box)

    def focus(self):
        self.funz.grab_focus()
        
    def funzione(self):
        return self.funz.get_text()

    def altobasso(self):
        return self.ab.get_active()

    def inarcamento(self):
        return self.inarc.get_value_as_int()

    def set(self, coda=CODA.index("Normal"), tratto = TRATTO.index("Normal"), decorazione = DECORAZIONE.index("No"), testa = TESTA.index("Arrow")):
        tipo = self.preset.get_active()
        if tipo == PRESET.index("Manual"):
            self.coda = coda
            self.tratto = tratto
            self.decorazione = decorazione
            self.testa = testa
        elif tipo == PRESET.index("Normal"):
            self.coda = CODA.index("Normal")
            self.tratto = TRATTO.index("Normal")
            self.decorazione = DECORAZIONE.index("No")
            self.testa = TESTA.index("Arrow")
        elif tipo == PRESET.index("Isomorphism"):
            self.coda = CODA.index("Normal")
            self.tratto = TRATTO.index("Normal")
            self.decorazione = DECORAZIONE.index("Isomorphism")
            self.testa = TESTA.index("Arrow")
        elif tipo == PRESET.index("Equal"):
            self.coda = CODA.index("Normal")
            self.tratto = TRATTO.index("Double")
            self.decorazione = DECORAZIONE.index("No")
            self.testa = TESTA.index("No")
        elif tipo == PRESET.index("Injection"):
            self.coda = CODA.index("Injection above")
            self.tratto = TRATTO.index("Normal")
            self.decorazione = DECORAZIONE.index("No")
            self.testa = TESTA.index("Arrow")
        elif tipo == PRESET.index("Surjection"):
            self.coda = CODA.index("Normal")
            self.tratto = TRATTO.index("Normal")
            self.decorazione = DECORAZIONE.index("No")
            self.testa = TESTA.index("Double arrow")
        elif tipo == PRESET.index("Segment"):
            self.coda = CODA.index("Normal")
            self.tratto = TRATTO.index("Normal")
            self.decorazione = DECORAZIONE.index("No")
            self.testa = TESTA.index("No")
        elif tipo == PRESET.index("Dashed"):
            self.coda = CODA.index("Normal")
            self.tratto = TRATTO.index("Dashed")
            self.decorazione = DECORAZIONE.index("No")
            self.testa = TESTA.index("Arrow")

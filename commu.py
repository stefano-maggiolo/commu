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

#Create commutative diagrams with PGF/TikZ.
#Version: 20080420
#Author: Stefano Maggiolo <maggiolo@mail.dm.unipi.it>

#Potential TODO:
#- clean up code (to english, fix row-col misunderstanding);
#- import of a diagram copied from the program;
#- move all object and arrows left-right-up-down;
#- object decorations (border...);
#- template: commutative square, exact sequences ... (?);
#- template to the power: different shape (polygons, cubes...?).

import pygtk
pygtk.require("2.0")
import gtk
import gtk.glade
import gobject
import operator
from collections import defaultdict
import os

BGcolor = 0
Tooltip = None

SCRITTA = ["Above", "Below", "Midline"]
PRESET = ["Normal", "Isomorphism", "Equal", "Injection", "Surjection", "Segment", "Dashed", "Manual"]
CODA = ["Normal", "Injection above", "Injection below", "Element"]
TRATTO = ["Normal", "Dashed", "Double"]
DECORAZIONE = ["No", "Isomorphism"]
TESTA = ["Arrow", "Double arrow", "No"]

class Oggetto:
    def __init__(self):
        global Tooltip
        
        self.label = gtk.Entry()
        self.label.set_size_request(80,30)
        Tooltip.set_tip(self.label, "Drop here to create an arrow to this object.")
        self.box = gtk.HBox()
        self.coll = gtk.Button("0")
        self.coll.set_size_request(30,30)
        Tooltip.set_tip(self.coll, "Drag from here to create an arrow from this object.")
        self.box.add(self.label)
        self.box.add(self.coll)

        self.frecceInArrivo = self.frecceInPartenza = 0
        self.coll.set_label("%d / %d" % (self.frecceInPartenza, self.frecceInArrivo))

    def __del__(self):
        del(self.label)
        del(self.coll)
        del(self.box)

    def incrementaFrecceInArrivo(self):
        self.frecceInArrivo += 1
        self.coll.set_label("%d / %d" % (self.frecceInPartenza, self.frecceInArrivo))
        
    def decrementaFrecceInArrivo(self):
        self.frecceInArrivo -= 1
        self.coll.set_label("%d / %d" % (self.frecceInPartenza, self.frecceInArrivo))

    def incrementaFrecceInPartenza(self):
        self.frecceInPartenza += 1
        self.coll.set_label("%d / %d" % (self.frecceInPartenza, self.frecceInArrivo))

    def decrementaFrecceInPartenza(self):
        self.frecceInPartenza -= 1
        self.coll.set_label("%d / %d" % (self.frecceInPartenza, self.frecceInArrivo))

    def reset(self):
        self.coll.set_label("%d / %d" % (self.frecceInPartenza, self.frecceInArrivo))
        self.label.set_text("")

    def nome(self):
        return self.label.get_text()

    def set_da(self):
        red = gtk.gdk.color_parse("red")        
        self.coll.modify_bg(gtk.STATE_NORMAL, red)
        
    def set_a(self):
        green = gtk.gdk.color_parse("green")
        self.coll.modify_bg(gtk.STATE_NORMAL, green)       

    def set_normale(self):
        self.coll.modify_bg(gtk.STATE_NORMAL, BGcolor)       
        
class Freccia:
    def __init__(self):
        global Tooltip
        self.box = gtk.HBox()
        self.funz = gtk.Entry()
        Tooltip.set_tip(self.funz, "The function.")
        self.ab = gtk.combo_box_new_text()
        Tooltip.set_tip(self.ab, "Where the funtion should be.")
        self.preset = gtk.combo_box_new_text()
        Tooltip.set_tip(self.preset, "Arrow type.")
        self.inarc = gtk.SpinButton(digits = 0)
        Tooltip.set_tip(self.inarc, "Arrow curve, in degree.")
        self.canc = gtk.Button("Delete")
        Tooltip.set_tip(self.canc, "Delete the arrow.")
        
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
            
class Commu:
    def __init__(self):
        self.gladefile = os.path.join(os.path.dirname(__file__), "commu.glade")
        self.w = gtk.glade.XML(self.gladefile) 
        
        dic = {"on_window_destroy": gtk.main_quit,
               "on_spinRow_value_changed": self.on_spinRow_change_value,
               "on_spinCol_value_changed": self.on_spinCol_change_value,
               "on_btCopia_clicked": self.on_btCopia_clicked,
               "on_btReset_clicked": self.on_btReset_clicked,
               "on_btNuova_clicked": self.on_btNuova_clicked,
               "on_ok_clicked": self.on_ok_clicked
               }

        self.w.signal_autoconnect(dic)
        global Tooltip
        Tooltip = gtk.Tooltips()

        self.spinRow = self.w.get_widget("spinRow")
        self.spinCol = self.w.get_widget("spinCol")
        self.spinW = self.w.get_widget("spinW")
        self.spinH = self.w.get_widget("spinH")
        self.spinR = self.w.get_widget("spinR")
        self.btCopia = self.w.get_widget("btCopia")
        self.table = self.w.get_widget("table")
        self.boxFrecce = self.w.get_widget("boxFrecce")
        self.window = self.w.get_widget("window")        

        self.oggetto = {}
        self.freccia = defaultdict(list)

        self.chiedi = self.w.get_widget("chiedi")
        self.ok = self.w.get_widget("ok")
        self.coda = self.w.get_widget("coda")
        self.testa = self.w.get_widget("testa")
        self.tratto = self.w.get_widget("tratto")
        self.decorazione = self.w.get_widget("decorazione")
        for x in CODA:
            self.coda.append_text(x)
        for x in DECORAZIONE:
            self.decorazione.append_text(x)
        for x in TRATTO:
            self.tratto.append_text(x)
        for x in TESTA:
            self.testa.append_text(x)

        self.curR = 0
        self.curC = 0
        self.aggiustaTabella()

        self.a = self.da = None
        
        self.window.show()
        global BGcolor
        BGcolor = self.btCopia.get_style().copy().bg[gtk.STATE_NORMAL]
        
    def aggiustaTabella(self):
        R = int(self.Row())
        C = int(self.Col())
        oldR = self.curR
        oldC = self.curC
        for i in xrange(oldR, R):
            for j in xrange(0, C):
                self.creaEntry(i, j)
        for i in xrange(R, oldR):
            for j in xrange(0, oldC):
                self.delEntry(i,j)
        for j in xrange(oldC, C):
            for i in xrange(0, min(R, oldR)):
                self.creaEntry(i, j)
        for j in xrange(C, oldC):
            for i in xrange(0, min(R, oldR)):
                self.delEntry(i,j)
        self.table.resize(R, C)
        for i in xrange(oldR, R):
            for j in xrange(0, C):
                self.table.attach(self.oggetto[(i,j)].box, i, i+1, j, j+1, 0, 0, 0, 0)
                self.oggetto[(i,j)].box.show_all()
        for j in xrange(oldC, C):
            for i in xrange(0, min(R, oldR)):
                self.table.attach(self.oggetto[(i,j)].box, i, i+1, j, j+1, 0, 0, 0, 0)
                self.oggetto[(i,j)].box.show_all()
        self.curR = R
        self.curC = C

    def creaEntry(self, i, j):
        o = Oggetto()
        self.oggetto[(i,j)] = o
        o.coll.connect("drag_data_get", self.on_entry_drag_data_get, (i,j))
        o.coll.drag_source_set(gtk.gdk.BUTTON1_MASK, [("text/plain", gtk.TARGET_SAME_APP, 80)], gtk.gdk.ACTION_LINK)
        o.label.connect("drag_data_received", self.on_entry_drag_data_received, (i,j))
        
    def delEntry(self, i, j):
        if (i,j) == self.da or (i,j) == self.a:
            self.oggetto[self.da].set_normale()
            self.oggetto[self.a].set_normale()
            self.da = self.a = None
        for da, a in self.freccia:
            if da == (i,j) or a == (i,j):
                while self.freccia[(da, a)] != []:
                    f = self.freccia[(da, a)].pop()
                    del(f)
                    self.oggetto[da].decrementaFrecceInPartenza()
                    self.oggetto[a].decrementaFrecceInArrivo()        
        self.table.remove(self.oggetto[(i,j)].box)
        del(self.oggetto[(i,j)])
        self.mostraDaA(self.da, self.a)

    def creaFreccia(self, da, a):
        f = Freccia()
        self.freccia[(da, a)].append(f)
        f.canc.connect("clicked", self.on_canc_clicked, f)
        f.preset.connect("changed", self.on_preset_changed, f)
        self.oggetto[self.da].incrementaFrecceInPartenza()
        self.oggetto[self.a].incrementaFrecceInArrivo()
        self.mostraDaA(da, a)

    def mostraDaA(self, da, a):
        self.boxFrecce.foreach(lambda w: self.boxFrecce.remove(w))
        if da != None and a != None:
            for f in self.freccia[(da,a)]:
                self.boxFrecce.add(f.box)
        self.boxFrecce.show_all()
        
    def Row(self):
        return self.spinRow.get_value()

    def Col(self):
        return self.spinCol.get_value()

    def on_spinRow_change_value(self, widget):
        self.aggiustaTabella()
    
    def on_spinCol_change_value(self, widget):
        self.aggiustaTabella()

    def on_entry_drag_data_get(self, widget, context, sel, targetType, eventTime, data):
        if self.da != None: self.oggetto[self.da].set_normale()
        self.da = data
        self.oggetto[self.da].set_da()
        
    def on_entry_drag_data_received(self, widget, context, x, y, sel, type, time, data):
        if self.a != None and self.da != self.a: self.oggetto[self.a].set_normale()
        self.a = data
        self.oggetto[self.a].set_a()
        if self.freccia[(self.da, self.a)] == []:
            self.creaFreccia(self.da, self.a)
        self.mostraDaA(self.da, self.a)

    def on_btReset_clicked(self, widget):
        if self.a != None: self.oggetto[self.a].set_normale()
        if self.da != None: self.oggetto[self.da].set_normale()
        self.a = self.da = None
        self.freccia = defaultdict(list)
        self.oggetto[(0,0)].reset()
        self.spinCol.set_value(0.0)
        self.spinRow.set_value(0.0)
        self.aggiustaTabella()
        self.spinCol.set_value(2.0)
        self.spinRow.set_value(2.0)
        self.aggiustaTabella()
        self.mostraDaA(None, None)

    def on_btNuova_clicked(self, widget):
        if self.da != None and self.a != None:
            self.creaFreccia(self.da, self.a)

    def on_canc_clicked(self, widget, freccia):
        self.freccia[(self.da, self.a)].remove(freccia)
        del(freccia)
        self.oggetto[self.da].decrementaFrecceInPartenza()
        self.oggetto[self.a].decrementaFrecceInArrivo()        
        self.mostraDaA(self.da,self.a)
        
    def on_preset_changed(self, widget, freccia):
        if freccia.preset.get_active() == PRESET.index("Manual"):
            self.curFreccia = freccia
            self.coda.set_active(freccia.coda)
            self.tratto.set_active(freccia.tratto)
            self.decorazione.set_active(freccia.decorazione)
            self.testa.set_active(freccia.testa)
            self.chiedi.show_all()
        else:
            freccia.set()

    def on_btCopia_clicked(self, widget):
        s = ""
        R = self.curR
        C = self.curC
        rientro = int(self.spinR.get_value())
        w = self.spinW.get_value()
        h = self.spinH.get_value()
        s += " " * rientro + "\\begin{center}\n"
        s += " " * rientro + "\\begin{tikzpicture}\n"
        s += " " * (rientro+2) + "\\def\\x{%.1f}\n" % w
        s += " " * (rientro+2) + "\\def\\y{%.1f}\n" % (-h)
        
        for i in xrange(R):
            for j in xrange(C):
                if self.oggetto[(i,j)].nome() != "" or (i,j) in [operator.itemgetter(0)(x) for x in self.freccia.keys()] or (i,j) in [operator.itemgetter(1)(x) for x in self.freccia.keys()]:
                    if self.oggetto[(i,j)].nome() != "":
                        s += " " * (rientro+2) + "\\node (A%d_%d) at (%d*\\x, %d*\\y) {$%s$};\n" % (i, j, i, j, self.oggetto[(i,j)].nome())
                    else:
                        s += " " * (rientro+2) + "\\node (A%d_%d) at (%d*\\x, %d*\\y) {};\n" % (i, j, i, j)

        for direzione in self.freccia.keys():
            for f in self.freccia[direzione]:
                da, a = direzione
                s += " " * (rientro+2) + "\\path (A%d_%d) edge [" % (da[0], da[1])

                if f.coda == CODA.index("Injection above"): s += "right hook"
                elif f.coda == CODA.index("Injection below"): s += "left hook"
                elif f.coda == CODA.index("Element"): s += "serif cm" #alternativa: "|"

                if f.tratto == TRATTO.index("Normal") or f.tratto == TRATTO.index("Dashed") or f.tratto == TRATTO.index("Double"): s += "-"
                
                if f.testa == TESTA.index("Arrow"): s += ">"
                elif f.testa == TESTA.index("Double arrow"): s += ">>"

                if f.tratto == TRATTO.index("Dashed"): s += ",dashed"
                elif f.tratto == TRATTO.index("Double"): s += ",double"

                if f.inarcamento() > 0: s += ",bend left=%d" % (f.inarcamento())
                elif f.inarcamento() < 0: s += ",bend right=%d" % (abs(f.inarcamento()))

                s += "] node ["

                if f.altobasso() == SCRITTA.index("Above"): s += "auto"
                elif f.altobasso() == SCRITTA.index("Below"): s += "auto,swap"
                
                s += "] {$\scriptstyle{%s}$} " % f.funzione()

                if f.decorazione == DECORAZIONE.index("Isomorphism"):
                    s += "node ["
                    if f.altobasso() == SCRITTA.index("Above"): s += "rotate=180,"
                    s += "sloped] {$\scriptstyle{\widetilde{\ \ \ }}$} "
                
                s += "(A%d_%d);\n" % (a[0], a[1])
            
        s += " " * rientro + "\\end{tikzpicture}\n"
        s += " " * rientro + "\\end{center}\n"
        c = gtk.Clipboard()
        c.set_text(s)

    def on_ok_clicked(self, widget):
        self.curFreccia.set(coda = self.coda.get_active(), tratto = self.tratto.get_active(), decorazione = self.decorazione.get_active(), testa = self.testa.get_active())
        self.chiedi.hide()
        
if __name__ == "__main__":
   c = Commu()
   gtk.main()
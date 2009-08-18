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
#Version: 20080916
#Author: Stefano Maggiolo <s.maggiolo@gmail.com>

#Potential TODO:
#- clean up code (to english);
#- import of a diagram copied from the program;
#- object decorations (border...);
#- template: commutative square, exact sequences ... (?);
#- template to the power: different shape (polygons, cubes...?).
#- give focus to the drawing area in the preview instead of the adjustable
#- clean up UI

import pygtk
pygtk.require("2.0")
import gtk
import gtk.glade
import gobject
import operator
from collections import defaultdict
import os

from commu_conf import *
from commu_objects import *
    
class Commu:
    def __init__(self, preview = "False"):
        try:
            self.gladefile = os.path.join("/", "usr", "share", "commu", "commu.glade")
            self.w = gtk.glade.XML(self.gladefile)
        except:
            # Assume all files are in the source directory
            self.gladefile = os.path.join(os.path.dirname(__file__), "commu.glade")
            self.w = gtk.glade.XML(self.gladefile)
            self.w.get_widget("window").set_icon(gtk.gdk.pixbuf_new_from_file("commu.svg"))

        dic = {"on_window_destroy": self.on_close,
               "on_spinRow_value_changed": self.on_spinRow_change_value,
               "on_spinCol_value_changed": self.on_spinCol_change_value,
               "on_btCopia_clicked": self.on_btCopia_clicked,
               "on_btReset_clicked": self.on_btReset_clicked,
               "on_btNuova_clicked": self.on_btNuova_clicked,
               "on_btImport_clicked": self.on_btImport_clicked,
               "on_btNW_clicked": self.on_btNW_clicked,
               "on_btN_clicked": self.on_btN_clicked,
               "on_btNE_clicked": self.on_btNE_clicked,
               "on_btE_clicked": self.on_btE_clicked,
               "on_btSE_clicked": self.on_btSE_clicked,
               "on_btS_clicked": self.on_btS_clicked,
               "on_btSW_clicked": self.on_btSW_clicked,
               "on_btW_clicked": self.on_btW_clicked,
               "on_ok_clicked": self.on_ok_clicked,
               "on_btPreview_clicked": self.on_btPreview_clicked
               }

        self.w.signal_autoconnect(dic)

        self.Tooltip = gtk.Tooltips()

        self.spinRow = self.w.get_widget("spinRow")
        self.spinCol = self.w.get_widget("spinCol")
        self.spinW = self.w.get_widget("spinW")
        self.spinH = self.w.get_widget("spinH")
        self.spinR = self.w.get_widget("spinR")
        self.btCopia = self.w.get_widget("btCopia")
        self.table = self.w.get_widget("table")
        self.boxFrecce = self.w.get_widget("boxFrecce")
        self.window = self.w.get_widget("window")        

        self.objects = {}
        self.arrows = defaultdict(list)

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
        self.AdjustTable()

        self._to = self._from = None

        accelgroup = gtk.AccelGroup()
        accelgroup.connect_group(ord('Q'), gtk.gdk.CONTROL_MASK, 0,
                                 lambda *etc: self.window.destroy())
        accelgroup.connect_group(ord('R'), gtk.gdk.CONTROL_MASK, 0,
                                 lambda *etc: self.on_btReset_clicked(None))
        accelgroup.connect_group(ord('P'), gtk.gdk.CONTROL_MASK, 0,
                                 lambda *etc: self.on_btPreview_clicked(None))
        self.window.add_accel_group(accelgroup)

        # Manage preview
        self.enablePreview = preview
        if self.enablePreview:
            import commu_preview
            self.preview = commu_preview.Preview()
            self.lastBuild = ""
            self.timer = gobject.timeout_add(2000, self.TryPreview)
        else:
            self.w.get_widget("btPreview").hide()

        self.window.show()

        self.BGcolor = self.btCopia.get_style().copy().bg[gtk.STATE_NORMAL]

    def on_close(self, widget):
        if self.enablePreview: self.preview.RemoveTemporaryFiles()
        gtk.main_quit()

    def TryPreview(self):
        if self.preview.isPreviewWindowCreated:
            s = self.Build()
            if s != self.lastBuild:
                self.lastBuild = s
                self.preview.SilentPreview(s)
        return True
    
    def MoveRows(self, n):
        R = int(self.Row())
        lista = range(R)
        if n > 0: lista.reverse()
        for c in xrange(int(self.Col())):
            for r in lista:
                if r-n >= 0 and r-n < R:
                    self.objects[(r, c)].SetName(self.objects[(r-n, c)].Name())
                else:
                    self.objects[(r, c)].SetName("")
                self.objects[(r, c)].SetArrows(0, 0)

        self.newArrow = defaultdict(list)
        for f in self.arrows.keys():
            if f[0][0]+n >= 0 and f[0][0]+n < R and f[1][0]+n >= 0 and f[1][0]+n < R:
                self.newArrow[((f[0][0]+n, f[0][1]), (f[1][0]+n, f[1][1]))] = self.arrows[f]
                self.objects[(f[0][0]+n, f[0][1])].IncrementOutgoingArrows(len(self.arrows[f]))
                self.objects[(f[1][0]+n, f[1][1])].IncrementIncomingArrows(len(self.arrows[f]))
        self.arrows = self.newArrow

        if self._from != None and self._to != None:
            self.objects[self._from].SetNormal(self.BGcolor)
            self.objects[self._to].SetNormal(self.BGcolor)
            if self._from[0]+n >= 0 and self._from[0]+n < R and self._to[0]+n >= 0 and self._to[0]+n < R:
                self._from = (self._from[0]+n, self._from[1])
                self._to = (self._to[0]+n, self._to[1])
                self.objects[self._from].SetFrom()
                self.objects[self._to].SetTo()
            else:
                self._from = self._to = None

    def MoveCols(self, n):
        C = int(self.Col())
        lista = range(C)
        if n > 0: lista.reverse()
        for r in xrange(int(self.Row())):
            for c in lista:
                if c-n >= 0 and c-n < C:
                    self.objects[(r, c)].SetName(self.objects[(r, c-n)].Name())
                else:
                    self.objects[(r, c)].SetName("")
                self.objects[(r, c)].SetArrows(0, 0)

        self.newArrow = defaultdict(list)
        for f in self.arrows.keys():
            if f[0][1]+n >= 0 and f[0][1]+n < C and f[1][1]+n >= 0 and f[1][1]+n < C:
                self.newArrow[((f[0][0], f[0][1]+n), (f[1][0], f[1][1]+n))] = self.arrows[f]
                self.objects[(f[0][0], f[0][1]+n)].IncrementOutgoingArrows(len(self.arrows[f]))
                self.objects[(f[1][0], f[1][1]+n)].IncrementIncomingArrows(len(self.arrows[f]))
        self.arrows = self.newArrow

        if self._from != None and self._to != None:
            self.objects[self._from].SetNormal(self.BGcolor)
            self.objects[self._to].SetNormal(self.BGcolor)
            if self._from[1]+n >= 0 and self._from[1]+n < C and self._to[1]+n >= 0 and self._to[1]+n < C:
                self._from = (self._from[0], self._from[1]+n)
                self._to = (self._to[0], self._to[1]+n)
                self.objects[self._from].SetFrom()
                self.objects[self._to].SetTo()
            else:
                self._from = self._to = None

    def AdjustTable(self):
        R = int(self.Row())
        C = int(self.Col())
        oldR = self.curR
        oldC = self.curC
        for r in xrange(oldR, R):
            for c in xrange(0, C):
                self.NewEntry(r, c)
        for r in xrange(R, oldR):
            for c in xrange(0, oldC):
                self.delEntry(r, c)
        for c in xrange(oldC, C):
            for r in xrange(0, min(R, oldR)):
                self.NewEntry(r, c)
        for c in xrange(C, oldC):
            for r in xrange(0, min(R, oldR)):
                self.delEntry(r, c)
        self.table.resize(R, C)
        for r in xrange(oldR, R):
            for c in xrange(0, C):
                self.table.attach(self.objects[(r,c)].box, c, c+1, r, r+1, 0, 0, 0, 0)
                self.objects[(r,c)].box.show_all()
        for c in xrange(oldC, C):
            for r in xrange(0, min(R, oldR)):
                self.table.attach(self.objects[(r,c)].box, c, c+1, r, r+1, 0, 0, 0, 0)
                self.objects[(r,c)].box.show_all()
        self.table.get_children()[-1].get_children()[0].grab_focus()
        self.curR = R
        self.curC = C

    def NewEntry(self, i, j):
        o = Object(self.Tooltip)
        self.objects[(i,j)] = o
        o.coll.connect("drag_data_get", self.on_entry_drag_data_get, (i,j))
        o.coll.drag_source_set(gtk.gdk.BUTTON1_MASK, [("text/plain", gtk.TARGET_SAME_APP, 80)], gtk.gdk.ACTION_LINK)
        o.label.connect("drag_data_received", self.on_entry_drag_data_received, (i,j))
        
    def delEntry(self, i, j):
        if (i,j) == self._from or (i,j) == self._to:
            self.objects[self._from].SetNormal(self.BGcolor)
            self.objects[self._to].SetNormal(self.BGcolor)
            self._from = self._to = None
        for _from, _to in self.arrows:
            if _from == (i,j) or _to == (i,j):
                while self.arrows[(_from, _to)] != []:
                    f = self.arrows[(_from, _to)].pop()
                    del(f)
                    self.objects[_from].DecrementOutgoingArrows()
                    self.objects[_to].DecrementIncomingArrows()        
        self.table.remove(self.objects[(i,j)].box)
        del(self.objects[(i,j)])
        self.ShowFromTo(self._from, self._to)

    def creaArrows(self, _from, _to):
        f = Arrow(self.Tooltip)
        self.arrows[(_from, _to)].append(f)
        f.canc.connect("clicked", self.on_canc_clicked, f)
        f.preset.connect("changed", self.on_preset_changed, f)
        self.objects[self._from].IncrementOutgoingArrows()
        self.objects[self._to].IncrementIncomingArrows()
        self.ShowFromTo(_from, _to)

    def ShowFromTo(self, _from, _to):
        self.boxFrecce.foreach(lambda w: self.boxFrecce.remove(w))
        if _from != None and _to != None:
            for f in self.arrows[(_from, _to)]:
                self.boxFrecce.add(f.box)
            self.boxFrecce.show_all()
            if self.arrows[(_from, _to)] != []:
                self.arrows[(_from, _to)][-1].focus()
        
    def Row(self):
        return self.spinRow.get_value()

    def Col(self):
        return self.spinCol.get_value()

    def ask_loss_information(self):
        msgbox = gtk.MessageDialog(parent = None,
                                   buttons = gtk.BUTTONS_YES_NO,
                                   flags = gtk.DIALOG_MODAL,
                                   message_format = "This will delete some data you have inserted. Continue?",
                                   type = gtk.MESSAGE_QUESTION)
        msgbox.set_title("Alert")
        result = msgbox.run()
        msgbox.destroy()
        return result == gtk.RESPONSE_YES

    def empty_N(self):
        for i in xrange(int(self.Col())):
            if not self.objects[(0, i)].isEmpty():
                return False
        return True
    
    def empty_S(self):
        R = int(self.Row())
        for i in xrange(int(self.Col())):
            if not self.objects[(R-1, i)].isEmpty():
                return False
        return True

    def empty_W(self):
        for i in xrange(int(self.Row())):
            if not self.objects[(i, 0)].isEmpty():
                return False
        return True
    
    def empty_E(self):
        C = int(self.Col())
        for i in xrange(int(self.Row())):
            if not self.objects[(i, C-1)].isEmpty():
                return False
        return True

    def on_btNW_clicked(self, widget):
        if (self.empty_N() and self.empty_W()) or self.ask_loss_information():
            self.MoveRows(-1)
            self.MoveCols(-1)
    
    def on_btN_clicked(self, widget):
        if self.empty_N() or self.ask_loss_information():
            self.MoveRows(-1)
    
    def on_btNE_clicked(self, widget):
        if (self.empty_N() and self.empty_E()) or self.ask_loss_information():
            self.MoveRows(-1)
            self.MoveCols(1)
    
    def on_btE_clicked(self, widget):
        if self.empty_E() or self.ask_loss_information():
            self.MoveCols(1)
    
    def on_btSE_clicked(self, widget):
        if (self.empty_S() and self.empty_E()) or self.ask_loss_information():
            self.MoveRows(1)
            self.MoveCols(1)
    
    def on_btS_clicked(self, widget):
        if self.empty_S() or self.ask_loss_information():
            self.MoveRows(1)
    
    def on_btSW_clicked(self, widget):
        if (self.empty_S() and self.empty_W()) or self.ask_loss_information():
            self.MoveRows(1)
            self.MoveCols(-1)
    
    def on_btW_clicked(self, widget):
        if self.empty_W() or self.ask_loss_information():
            self.MoveCols(-1)
    
    def on_spinRow_change_value(self, widget):
        self.AdjustTable()
    
    def on_spinCol_change_value(self, widget):
        self.AdjustTable()

    def on_entry_drag_data_get(self, widget, context, sel, targetType, eventTime, data):
        if self._from != None: self.objects[self._from].SetNormal(self.BGcolor)
        self._from = data
        self.objects[self._from].SetFrom()
        
    def on_entry_drag_data_received(self, widget, context, x, y, sel, type, time, data):
        if self._to != None and self._from != self._to: self.objects[self._to].SetNormal(self.BGcolor)
        self._to = data
        self.objects[self._to].SetTo()
        if self.arrows[(self._from, self._to)] == []:
            self.creaArrows(self._from, self._to)
        self.ShowFromTo(self._from, self._to)

    def on_btReset_clicked(self, widget):
        if self._to != None: self.objects[self._to].SetNormal(self.BGcolor)
        if self._from != None: self.objects[self._from].SetNormal(self.BGcolor)
        self._to = self._from = None
        self.arrows = defaultdict(list)
        self.objects[(0,0)].Reset()
        self.spinCol.set_value(0.0)
        self.spinRow.set_value(0.0)
        self.AdjustTable()
        self.spinCol.set_value(2.0)
        self.spinRow.set_value(2.0)
        self.AdjustTable()
        self.ShowFromTo(None, None)

    def on_btNuova_clicked(self, widget):
        if self._from != None and self._to != None:
            self.creaArrows(self._from, self._to)

    def on_canc_clicked(self, widget, arrows):
        self.arrows[(self._from, self._to)].remove(arrows)
        del(arrows)
        self.objects[self._from].DecrementOutgoingArrows()
        self.objects[self._to].DecrementIncomingArrows()        
        self.ShowFromTo(self._from,self._to)
        
    def on_preset_changed(self, widget, arrows):
        if arrows.preset.get_active() == PRESET.index("Manual"):
            self.curArrows = arrows
            self.coda.set_active(arrows.coda)
            self.tratto.set_active(arrows.tratto)
            self.decorazione.set_active(arrows.decorazione)
            self.testa.set_active(arrows.testa)
            self.chiedi.show_all()
        else:
            arrows.set()
    
    def on_btPreview_clicked(self, widget):
        if self.enablePreview:
            self.preview.Preview(self.Build())
            self.window.present()

    def Build(self):
        s = ""
        R = self.curR
        C = self.curC
        rientro = int(self.spinR.get_value())
        w = self.spinW.get_value()
        h = self.spinH.get_value()
        s += " " * rientro + "\\[\n"
        s += " " * rientro + "\\begin{tikzpicture}[xscale=%.1f,yscale=%.1f]\n" % (w, -h)

        for r in xrange(R):
            for c in xrange(C):
                if self.objects[(r,c)].ToWrite():
                    if self.objects[(r,c)].Name() != "":
                        s += " " * (rientro+2) + "\\node (A%d_%d) at (%d, %d) {$%s$};\n" % (r, c, c, r, self.objects[(r,c)].Name())
                    else:
                        s += " " * (rientro+2) + "\\node (A%d_%d) at (%d, %d) {};\n" % (r, c, c, r)

        for direzione in self.arrows.keys():
            for f in self.arrows[direzione]:
                _from, _to = direzione
                s += " " * (rientro+2) + "\\path (A%d_%d) edge [" % (_from[0], _from[1])

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
                
                s += "(A%d_%d);\n" % (_to[0], _to[1])
            
        s += " " * rientro + "\\end{tikzpicture}\n"
        s += " " * rientro + "\\]\n"
        return s

    def on_btCopia_clicked(self, widget):
        c = gtk.Clipboard()
        c.set_text(self.Build())

    def on_btImport_clicked(self, widget):
        c = gtk.Clipboard()
        s = c.wait_for_text().split('\n')
        rientro = len(s[0]) - 2
        #TODO

    def on_ok_clicked(self, widget):
        self.curArrows.set(coda = self.coda.get_active(), tratto = self.tratto.get_active(), decorazione = self.decorazione.get_active(), testa = self.testa.get_active())
        self.chiedi.hide()

if __name__ == "__main__":
    try:
        import poppler
        Commu(preview = True)
    except ImportError:
        Commu(preview = False)
    gtk.main()

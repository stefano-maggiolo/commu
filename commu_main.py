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

#Potential TODO:
#- clean up code (to english);
#- import of a diagram copied from the program;
#- object decorations (border...);
#- template: commutative square, exact sequences ... (?);
#- template to the power: different shape (polygons, cubes...?).
#- give focus to the drawing area in the preview instead of the adjustable
#- clean up UI

## TO CHECK
# svg icon in glade (when we start from source)

import pygtk
pygtk.require("2.0")
import gtk
import gtk.glade
import gobject
import operator
import os
import re

from commu_conf import *
from commu_objects import *

def display_warning(message):
    msgbox = gtk.MessageDialog(parent = None,
                               buttons = gtk.BUTTONS_CLOSE,
                               flags = gtk.DIALOG_MODAL,
                               message_format = message,
                               type = gtk.MESSAGE_WARNING)
    msgbox.set_title("Alert")
    result = msgbox.run()
    msgbox.destroy()

class Commu:
    message_warning_missing_package = 'If you want to use this feature you have to install the package %s'
    def __init__(self, templates = False):
        self.gladefile = os.path.join(INSTALLATION_DIRECTORY,'commu.glade')
        self.w = gtk.glade.XML(self.gladefile)
        svg_icon = os.path.join(INSTALLATION_DIRECTORY,'commu.svg')
        self.w.get_widget("window").set_icon(gtk.gdk.pixbuf_new_from_file(svg_icon))

        dic = {"on_window_destroy": self.on_close,
               "on_btExport_clicked": self.on_btExport_clicked,
               "on_btReset_clicked": self.on_btReset_clicked,
               "on_btSaveAs_clicked": self.on_btSaveAs_clicked,
               "on_btUserCommands_clicked": self.on_btUserCommands_clicked,
               "on_btSave_clicked": self.on_btSave_clicked,
               "on_btLoad_clicked": self.on_btLoad_clicked,
               "on_btNW_clicked": self.on_btNW_clicked,
               "on_btN_clicked": self.on_btN_clicked,
               "on_btN_P_clicked": self.on_btN_P_clicked,
               "on_btN_M_clicked": self.on_btN_M_clicked,
               "on_btNE_clicked": self.on_btNE_clicked,
               "on_btE_clicked": self.on_btE_clicked,
               "on_btE_P_clicked": self.on_btE_P_clicked,
               "on_btE_M_clicked": self.on_btE_M_clicked,
               "on_btSE_clicked": self.on_btSE_clicked,
               "on_btS_clicked": self.on_btS_clicked,
               "on_btS_P_clicked": self.on_btS_P_clicked,
               "on_btS_M_clicked": self.on_btS_M_clicked,
               "on_btSW_clicked": self.on_btSW_clicked,
               "on_btW_clicked": self.on_btW_clicked,
               "on_btW_P_clicked": self.on_btW_P_clicked,
               "on_btW_M_clicked": self.on_btW_M_clicked,
               "on_ok_clicked": self.on_ok_clicked,
               "on_btPreview_clicked": self.on_btPreview_clicked
               }

        self.w.signal_autoconnect(dic)

        self.spinW = self.w.get_widget("spinW")
        self.spinH = self.w.get_widget("spinH")
        self.spinR = self.w.get_widget("spinR")
        self.btExport = self.w.get_widget("btExport")
        self.table = self.w.get_widget("table")
        self.boxFrecce = self.w.get_widget("boxFrecce")
        self.window = self.w.get_widget("window")

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

        self.rows = 0
        self.cols = 0
        self.objects = {}
        self.arrows = {}
        self.previousFocus = (0,0)
        self._to = self._from = None
        self.NewEntry(0,0)
        self.AdjustTable(4,4)

        accelgroup = gtk.AccelGroup()
        accelgroup.connect_group(ord('Q'), gtk.gdk.CONTROL_MASK, 0,
                                 lambda *etc: self.window.destroy())
        accelgroup.connect_group(ord('R'), gtk.gdk.CONTROL_MASK, 0,
                                 lambda *etc: self.on_btReset_clicked(None))
        accelgroup.connect_group(ord('P'), gtk.gdk.CONTROL_MASK, 0,
                                 lambda *etc: self.on_btPreview_clicked(None))
        accelgroup.connect_group(ord('A'), gtk.gdk.CONTROL_MASK, 0,
                                 lambda *etc: self.arrow_left())
        accelgroup.connect_group(ord('S'), gtk.gdk.CONTROL_MASK, 0,
                                 lambda *etc: self.arrow_down())
        accelgroup.connect_group(ord('W'), gtk.gdk.CONTROL_MASK, 0,
                                 lambda *etc: self.arrow_up())
        accelgroup.connect_group(ord('D'), gtk.gdk.CONTROL_MASK, 0,
                                 lambda *etc: self.arrow_right())
        self.window.add_accel_group(accelgroup)

        # Manage preview
        import commu_preview
        self.preview = commu_preview.Preview(self)
        self.TemporaryBuild = None

        # Manage templates
        self.activate_templates()

        self.window.show()

        self.BGcolor = self.btExport.get_style().copy().bg[gtk.STATE_NORMAL]

    def on_close(self, widget):
        self.preview.RemoveTemporaryFiles()
        gtk.main_quit()

    def TryPreview(self):
        if self.preview.isPreviewWindowCreated:
            if self.TemporaryBuild == None:
                s = self.Build()
            else:
                s = self.TemporaryBuild
            if s != self.lastBuild:
                self.lastBuild = s
                self.preview.Preview(s)
        return True

    def MoveRows(self, n):
        lista = range(self.rows)
        if n > 0: lista.reverse()
        for c in xrange(self.cols):
            for r in lista:
                if r-n >= 0 and r-n < self.rows:
                    self.objects[(r, c)].SetName(self.objects[(r-n, c)].Name())
                else:
                    self.objects[(r, c)].SetName("")
                self.objects[(r, c)].SetArrows(0, 0)

        self.newArrow = {}
        for f in self.arrows.keys():
            if f[0][0]+n >= 0 and f[0][0]+n < self.rows and f[1][0]+n >= 0 and f[1][0]+n < self.rows:
                self.newArrow[((f[0][0]+n, f[0][1]), (f[1][0]+n, f[1][1]))] = self.arrows[f]
                self.objects[(f[0][0]+n, f[0][1])].IncrementOutgoingArrows(len(self.arrows[f]))
                self.objects[(f[1][0]+n, f[1][1])].IncrementIncomingArrows(len(self.arrows[f]))
        self.arrows = self.newArrow

        if self._from != None and self._to != None:
            self.objects[self._from].SetNormal(self.BGcolor)
            self.objects[self._to].SetNormal(self.BGcolor)
            if self._from[0]+n >= 0 and self._from[0]+n < self.rows and self._to[0]+n >= 0 and self._to[0]+n < self.rows:
                self._from = (self._from[0]+n, self._from[1])
                self._to = (self._to[0]+n, self._to[1])
                self.objects[self._from].SetFrom()
                self.objects[self._to].SetTo()
            else:
                self._from = self._to = None
        self.previousFocus = list(self.getFocused())
        self.previousFocus[0] += n
        if self.previousFocus[0] < 0: self.previousFocus[0] = 0
        elif self.previousFocus[0] >= self.rows: self.previousFocus[0] = self.rows-1
        self.previousFocus = tuple(self.previousFocus)
        self.objects[self.previousFocus].label.grab_focus()

    def MoveCols(self, n):
        lista = range(self.cols)
        if n > 0: lista.reverse()
        for r in xrange(self.rows):
            for c in lista:
                if c-n >= 0 and c-n < self.cols:
                    self.objects[(r, c)].SetName(self.objects[(r, c-n)].Name())
                else:
                    self.objects[(r, c)].SetName("")
                self.objects[(r, c)].SetArrows(0, 0)

        self.newArrow = {}
        for f in self.arrows.keys():
            if f[0][1]+n >= 0 and f[0][1]+n < self.cols and f[1][1]+n >= 0 and f[1][1]+n < self.cols:
                self.newArrow[((f[0][0], f[0][1]+n), (f[1][0], f[1][1]+n))] = self.arrows[f]
                self.objects[(f[0][0], f[0][1]+n)].IncrementOutgoingArrows(len(self.arrows[f]))
                self.objects[(f[1][0], f[1][1]+n)].IncrementIncomingArrows(len(self.arrows[f]))
        self.arrows = self.newArrow

        if self._from != None and self._to != None:
            self.objects[self._from].SetNormal(self.BGcolor)
            self.objects[self._to].SetNormal(self.BGcolor)
            if self._from[1]+n >= 0 and self._from[1]+n < self.cols and self._to[1]+n >= 0 and self._to[1]+n < self.cols:
                self._from = (self._from[0], self._from[1]+n)
                self._to = (self._to[0], self._to[1]+n)
                self.objects[self._from].SetFrom()
                self.objects[self._to].SetTo()
            else:
                self._from = self._to = None
        self.previousFocus = list(self.getFocused())
        self.previousFocus[1] += n
        if self.previousFocus[1] < 0: self.previousFocus[1] = 0
        elif self.previousFocus[1] >= self.cols: self.previousFocus[1] = self.cols-1
        self.previousFocus = tuple(self.previousFocus)
        self.objects[self.previousFocus].label.grab_focus()

    def getFocused(self):
        for o in self.objects.keys():
            if self.objects[o].label.is_focus():
                return o
        return (0,0)

    def AdjustTable(self, R, C):
        self.previousFocus = self.getFocused()
        oldR = self.rows
        oldC = self.cols
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
        self.rows = R
        self.cols = C
        if self.objects.has_key(self.previousFocus):
            self.objects[self.previousFocus].label.grab_focus()
        else:
            self.objects[(0,0)].label.grab_focus()


    def NewEntry(self, i, j):
        o = Object()
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
        f = Arrow()
        if (_from, _to) not in self.arrows.keys():
            self.arrows[(_from, _to)] = []
        self.arrows[(_from, _to)].append(f)
        f.canc.connect("clicked", self.on_canc_clicked, f)
        f.add.connect("clicked", self.on_add_clicked, f)
        f.preset.connect("changed", self.on_preset_changed, f)
        self.objects[_from].IncrementOutgoingArrows()
        self.objects[_to].IncrementIncomingArrows()
        self.ShowFromTo(_from, _to)
        return f

    def ShowFromTo(self, _from, _to):
        self.boxFrecce.foreach(lambda w: self.boxFrecce.remove(w))
        if _from != None and _to != None:
            if (_from, _to) in self.arrows.keys():
                for f in self.arrows[(_from, _to)]:
                    self.boxFrecce.add(f.box)
            self.boxFrecce.show_all()
            if (_from, _to) in self.arrows.keys() and \
                    self.arrows[(_from, _to)] != []:
                self.arrows[(_from, _to)][-1].focus()

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
        for i in xrange(self.cols):
            if not self.objects[(0, i)].isEmpty():
                return False
        return True

    def empty_S(self):
        for i in xrange(self.cols):
            if not self.objects[(self.rows-1, i)].isEmpty():
                return False
        return True

    def empty_W(self):
        for i in xrange(self.rows):
            if not self.objects[(i, 0)].isEmpty():
                return False
        return True

    def empty_E(self):
        for i in xrange(self.rows):
            if not self.objects[(i, self.cols-1)].isEmpty():
                return False
        return True

    def on_btNW_clicked(self, widget):
        if (self.empty_N() and self.empty_W()) or self.ask_loss_information():
            self.MoveRows(-1)
            self.MoveCols(-1)

    def on_btN_clicked(self, widget):
        if self.empty_N() or self.ask_loss_information():
            self.MoveRows(-1)

    def on_btN_P_clicked(self, widget):
        self.AdjustTable(self.rows + 1, self.cols)
        self.MoveRows(1)

    def on_btN_M_clicked(self, widget):
        if self.rows > 1 and (self.empty_N() or self.ask_loss_information()):
            self.MoveRows(-1)
            self.AdjustTable(self.rows - 1, self.cols)

    def on_btNE_clicked(self, widget):
        if (self.empty_N() and self.empty_E()) or self.ask_loss_information():
            self.MoveRows(-1)
            self.MoveCols(1)

    def on_btE_clicked(self, widget):
        if self.empty_E() or self.ask_loss_information():
            self.MoveCols(1)

    def on_btE_P_clicked(self, widget):
        self.AdjustTable(self.rows, self.cols + 1)

    def on_btE_M_clicked(self, widget):
        if self.cols > 1 and (self.empty_E() or self.ask_loss_information()):
            self.AdjustTable(self.rows, self.cols - 1)

    def on_btSE_clicked(self, widget):
        if (self.empty_S() and self.empty_E()) or self.ask_loss_information():
            self.MoveRows(1)
            self.MoveCols(1)

    def on_btS_clicked(self, widget):
        if self.empty_S() or self.ask_loss_information():
            self.MoveRows(1)

    def on_btS_P_clicked(self, widget):
        self.AdjustTable(self.rows + 1, self.cols)

    def on_btS_M_clicked(self, widget):
        if self.rows > 1 and (self.empty_S() or self.ask_loss_information()):
            self.AdjustTable(self.rows - 1, self.cols)

    def on_btSW_clicked(self, widget):
        if (self.empty_S() and self.empty_W()) or self.ask_loss_information():
            self.MoveRows(1)
            self.MoveCols(-1)

    def on_btW_clicked(self, widget):
        if self.empty_W() or self.ask_loss_information():
            self.MoveCols(-1)

    def on_btW_P_clicked(self, widget):
        self.AdjustTable(self.rows, self.cols + 1)
        self.MoveCols(1)

    def on_btW_M_clicked(self, widget):
        if self.cols > 1 and (self.empty_W() or self.ask_loss_information()):
            self.MoveCols(-1)
            self.AdjustTable(self.rows, self.cols - 1)

    def on_entry_drag_data_get(self, widget, context, sel, targetType, eventTime, data):
        if self._from != None: self.objects[self._from].SetNormal(self.BGcolor)
        self._from = data
        self.objects[self._from].SetFrom()

    def on_entry_drag_data_received(self, widget, context, x, y, sel, type, time, data):
        if self._to != None and self._from != self._to: self.objects[self._to].SetNormal(self.BGcolor)
        self._to = data
        self.objects[self._to].SetTo()
        if (self._from, self._to) not in self.arrows.keys() or \
                self.arrows[(self._from, self._to)] == []:
            self.creaArrows(self._from, self._to)
        self.ShowFromTo(self._from, self._to)

    def on_btReset_clicked(self, widget):
        if self.ask_loss_information():
            self.Reset()

    def on_add_clicked(self, widget, data):
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

    def activate_preview(self):
        if not hasattr(self,'lastBuild'):
            self.lastBuild = ""
            self.timer = gobject.timeout_add(2000, self.TryPreview)

    def on_btPreview_clicked(self, widget):
        try: import poppler
        except ImportError: display_warning(Commu.message_warning_missing_package % 'python-poppler')
        else:
            self.activate_preview()
            self.preview.Preview(self.Build())
            self.window.present()


    def arrow_left(self):
        for o in self.objects.keys():
            if self.objects[o].label.is_focus():
                if o[1] == 0:
                    self.AdjustTable(self.rows, self.cols + 1)
                    self.MoveCols(1)
                    o = (o[0], 1)
                newo = (o[0], o[1]-1)
                self.previousFocus = newo
                self.on_entry_drag_data_get(self, None, None,
                                            None, None, o)
                self.on_entry_drag_data_received(self, None, None,
                                                 None, None, None,
                                                 None, newo)
                return
        self.objects[self.previousFocus].label.grab_focus()

    def arrow_right(self):
        for o in self.objects.keys():
            if self.objects[o].label.is_focus():
                if o[1] == self.cols-1:
                    self.AdjustTable(self.rows, self.cols + 1)
                newo = (o[0], o[1]+1)
                self.previousFocus = newo
                self.on_entry_drag_data_get(self, None, None,
                                            None, None, o)
                self.on_entry_drag_data_received(self, None, None,
                                                 None, None, None,
                                                 None, newo)
                return
        self.objects[self.previousFocus].label.grab_focus()

    def arrow_up(self):
        for o in self.objects.keys():
            if self.objects[o].label.is_focus():
                if o[0] == 0:
                    self.AdjustTable(self.rows + 1, self.cols)
                    self.MoveRows(1)
                    o = (1, o[1])
                newo = (o[0]-1, o[1])
                self.previousFocus = newo
                self.on_entry_drag_data_get(self, None, None,
                                            None, None, o)
                self.on_entry_drag_data_received(self, None, None,
                                                 None, None, None,
                                                 None, newo)
                return
        self.objects[self.previousFocus].label.grab_focus()

    def arrow_down(self):
        for o in self.objects.keys():
            if self.objects[o].label.is_focus():
                if o[0] == self.rows-1:
                    self.AdjustTable(self.rows + 1, self.cols)
                newo = (o[0]+1, o[1])
                self.previousFocus = newo
                self.on_entry_drag_data_get(self, None, None,
                                            None, None, o)
                self.on_entry_drag_data_received(self, None, None,
                                                 None, None, None,
                                                 None, newo)
                return
        self.objects[self.previousFocus].label.grab_focus()

    def Reset(self):
        if self._to != None: self.objects[self._to].SetNormal(self.BGcolor)
        if self._from != None: self.objects[self._from].SetNormal(self.BGcolor)
        self._to = self._from = None
        self.arrows = {}
        self.objects[(0,0)].Reset()
        self.AdjustTable(1, 1)
        self.AdjustTable(4, 4)
        self.ShowFromTo(None, None)
        self.globalConfiguration.UnSetLastDiagramSaved()

    def GenerateNodeName(self,r,c):
        return 'A%d_%d' % (r,c)

    def Build(self):
        s = ""
        rientro = int(self.spinR.get_value())
        w = self.spinW.get_value()
        h = self.spinH.get_value()

        s += " " * rientro + "\\[\n"
        s += " " * rientro + "\\begin{tikzpicture}[xscale=%.1f,yscale=%.1f]\n" % (w, -h)

        for r in xrange(self.rows):
            for c in xrange(self.cols):
                if self.objects[(r,c)].ToWrite():
                    if self.objects[(r,c)].Name() != "":
                        s += " " * (rientro+2) + "\\node (%s) at (%d, %d) {$%s$};\n" % (self.GenerateNodeName(r ,c), c, r, self.objects[(r,c)].Name())
                    else:
                        s += " " * (rientro+2) + "\\node (%s) at (%d, %d) {};\n" % (self.GenerateNodeName(r,c), c, r)

        for direzione in self.arrows.keys():
            for f in self.arrows[direzione]:
                _from, _to = direzione
                s += " " * (rientro+2) + "\\path (%s)" % self.GenerateNodeName(_from[0], _from[1])
                if f.tratto == TRATTO.index("No"):
                    s += " --"
                else:
                    s += " edge ["

                    if f.coda == CODA.index("Injection above"): s += "right hook"
                    elif f.coda == CODA.index("Injection below"): s += "left hook"
                    elif f.coda == CODA.index("Element"): s += "serif cm" #alternativa: "|"

                    if f.tratto == TRATTO.index("Normal") or f.tratto == TRATTO.index("Dashed") or f.tratto == TRATTO.index("Double"): s += "-"

                    if f.testa == TESTA.index("Arrow"): s += ">"
                    elif f.testa == TESTA.index("Double arrow"): s += ">>"

                    if f.tratto == TRATTO.index("Dashed"): s += ",dashed"
                    elif f.tratto == TRATTO.index("Double"): s += ",double distance=1.5pt"

                    if f.inarcamento() > 0: s += ",bend left=%d" % (f.inarcamento())
                    elif f.inarcamento() < 0: s += ",bend right=%d" % (abs(f.inarcamento()))
                    s += "]"

                s += "node ["

                if f.altobasso() == SCRITTA.index("Above"): s += "auto"
                elif f.altobasso() == SCRITTA.index("Below"): s += "auto,swap"

                s += "] {$\scriptstyle{%s}$} " % f.funzione()

                if f.decorazione == DECORAZIONE.index("Isomorphism"):
                    s += "node ["
                    if f.altobasso() == SCRITTA.index("Above"): s += "rotate=180,"
                    s += "sloped] {$\scriptstyle{\widetilde{\ \ \ }}$} "

                s += "(%s)" % self.GenerateNodeName(_to[0], _to[1])
                s += ";\n"
        s += " " * rientro + "\\end{tikzpicture}\n"
        s += " " * rientro + "\\]\n"
        s = re.sub("%\(([^\)]*)\)", "\\\\fbox{\\1}", s)
        return s

    def on_btExport_clicked(self, widget):
        c = gtk.Clipboard()
        c.set_text(self.Build())

    def on_btUserCommands_clicked(self,widget):
        self.preview.CreateUserDefinedCommandsWindow()

    def activate_templates(self):
        # Manage templates
        try: import configobj
        except ImportError: self.has_configobj = False
        else:
            self.has_configobj = True
            import commu_templates
            try:
                if hasattr(self,'globalConfiguration'):
                    self.globalConfiguration.LoadConfiguration()
                else:
                    self.globalConfiguration = commu_templates.GlobalConfiguration(self)

            except Exception, Err:
                self.file_user_defined_commands_broken = True
                import sys
                sys.stderr.write(str(Err))
                return Err
            else: self.file_user_defined_commands_broken = False

    def HandleMissingConfigObjAndBrokenConfigurationFile(self, Err = None):
        if not self.has_configobj:
            display_warning(Commu.message_warning_missing_package % 'python-configobj')
            return
        #we must have self.file_user_defined_commands_broken == True
        import commu_templates
        message = 'The configuration file \'%s\' is broken.\n' % commu_templates.template_conf_file
        message += 'The following error occurs loading it:\n%s\n' % str(Err)
        message += 'Do you want to restore a backup?'
        msgbox = gtk.MessageDialog(parent = None,
                                 buttons = gtk.BUTTONS_YES_NO,
                                  flags = gtk.DIALOG_MODAL,
                                message_format = message,
                                   type = gtk.MESSAGE_QUESTION)
        msgbox.set_title("Configuration broken. Restore a Backup?")
        result = msgbox.run()
        msgbox.destroy()
        if result == gtk.RESPONSE_YES:
            commu_templates.RestoreBackupConfiguration()

    def on_btLoad_clicked(self,widget):
        Err = self.activate_templates()
        if self.has_configobj and not self.file_user_defined_commands_broken:
            self.globalConfiguration.CreateLoadTemplatesWindow()
        else:
            self.HandleMissingConfigObjAndBrokenConfigurationFile(Err)

    def on_btSave_clicked(self,widget):
        Err = self.activate_templates()
        if self.has_configobj and not self.file_user_defined_commands_broken:
            self.globalConfiguration.SaveDirectlyToTheLastDiagram()
        else:
            self.HandleMissingConfigObjAndBrokenConfigurationFile(Err)

    def on_btSaveAs_clicked(self, widget):
        Err = self.activate_templates()
        if self.has_configobj and not self.file_user_defined_commands_broken:
            self.globalConfiguration.CreateChooseNameWindow()
        else:
            self.HandleMissingConfigObjAndBrokenConfigurationFile(Err)

    def on_ok_clicked(self, widget):
        self.curArrows.set(coda = self.coda.get_active(), tratto = self.tratto.get_active(), decorazione = self.decorazione.get_active(), testa = self.testa.get_active())
        self.chiedi.hide()

if __name__ == "__main__":
    Commu()
    gtk.main()

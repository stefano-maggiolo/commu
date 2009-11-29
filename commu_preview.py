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
import os
import poppler
import commands
import tempfile

class Preview:
    def __init__(self):
        try:
            import xdg.BaseDirectory
            self.configDir = os.path.join(xdg.BaseDirectory.xdg_config_home, "commu")
        except ImportError:
            self.configDir = os.path.join(os.path.expanduser("~"), ".commu")

        try:
            os.mkdir(self.configDir)
        except:
            pass
            
        self.tempDir = tempfile.mkdtemp()
        self.tempTex = os.path.join(self.tempDir, "commu_preview.tex")
        self.tempPdf = os.path.join(self.tempDir, "commu_preview.pdf")
        self.includeTex = os.path.join(self.configDir, "to_include.tex")
        self.textBefore = "The following diagram (see EGAXXII) proves the \
existence and the uniqueness of the canonical duality between coherent sheaves \
on spectral sites of stacks of quotient moduli spaces of pointed curves with \
fixed ultragenus and the category of categories fibered in megaloid over an \
abelian smooth autoisotropic of general type category:"
        self.textAfter = "As a consequence, the isotrivial families of \
superconnected unimodular curves are self-dual with respect to the motivic \
theory of ultrafilters."

        self.isPreviewWindowCreated=False
        self.isErrorWindowCreated=False
        self.isHelpWindowCreated=False
        self.scale=22

        self.possible_packages = [
            os.path.join("/", "usr", "share", "commu", "commu_packages"),
            os.path.join(os.path.realpath(os.path.dirname(__file__)), "commu_packages"),
            os.path.join(self.configDir, "commu_packages") ]

        self.GetHelpPackages()
        self.GetPackages()
        self.GetOtherCommands()

    def RemoveTemporaryFiles(self):
        for i in os.listdir(self.tempDir):
            os.remove(os.path.join(self.tempDir, i))
        os.rmdir(self.tempDir)
        
    def CreatePreviewWindow(self):
        win = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.win = win
        win.set_default_size(800, 400)
        win.set_title("Commu preview")
        win.connect("delete-event", self.DeletePreviewWindow)
        win.set_keep_above(False)

        accelgroup = gtk.AccelGroup()
        accelgroup.connect_group(ord('W'), gtk.gdk.CONTROL_MASK, 0,
                                 lambda *etc: win.destroy())
        win.add_accel_group(accelgroup)

        hbox = gtk.HBox()
        
        adjust = gtk.Adjustment(self.scale, 1, 50, 1)
        scale_selector = gtk.SpinButton(adjust, 0, 0);
        scale_selector.connect("value-changed", self.on_scale_changed)
        
        lab = gtk.Label('Scale:')

        button = gtk.Button("Close")
        button.connect("clicked", self.DeletePreviewWindow)

        hbox.pack_start(lab, False, False, 4)
        hbox.pack_start(scale_selector, False, False, 0)
        hbox.pack_end(button, expand = False, fill = False)

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        
        self.dwg = gtk.DrawingArea()
        self.dwg.set_size_request(self.WIDTH,self.HEIGHT)
        
        self.dwg.connect("expose-event", self.on_expose)
        
        sw.add_with_viewport(self.dwg)
        
        vbox = gtk.VBox()
        vbox.set_spacing(6)
        vbox.set_border_width(6)
        vbox.pack_start(sw)
        vbox.pack_start(hbox, expand = False, fill = False)
        
        win.add(vbox)
        
        win.show_all()
        
        sw.get_hadjustment().set_value(self.WIDTH/5)
        sw.get_vadjustment().set_value(self.HEIGHT/5.5)
        
        self.isPreviewWindowCreated=True
    
    def CreateErrorWindow(self):
        win = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.errorWin = win
        win.set_default_size(500, 400)
        win.set_title ("Compilation errors")
        win.connect("delete-event", self.DeleteErrorWindow)

        accelgroup = gtk.AccelGroup()
        accelgroup.connect_group(ord('W'), gtk.gdk.CONTROL_MASK, 0,
                                 lambda *etc: win.destroy())
        win.add_accel_group(accelgroup)

        sw = gtk.ScrolledWindow()
        
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        
        self.tv = gtk.TextView()
        self.tv.set_editable(False)
        self.tv.set_cursor_visible(False)
        
        sw.add_with_viewport(self.tv)
        
        button = gtk.Button("Close")
        button.connect("clicked", self.DeleteErrorWindow)

        hbox = gtk.HBox()
        hbox.set_spacing(6)
        hbox.pack_end(button, expand = False, fill = False)

        vbox = gtk.VBox()
        vbox.set_spacing(6)
        vbox.set_border_width(6)
        vbox.pack_start(sw)
        vbox.pack_start(hbox, expand = False, fill = False)
        
        win.add(vbox)
        win.show_all()
        
        self.isErrorWindowCreated=True
        
    def DeletePreviewWindow(self, widget, data = None):
        self.DeleteErrorWindow(None, None)
        self.DeleteHelpWindow(None, None)
        self.win.destroy()
        self.scale = 22
        self.isPreviewWindowCreated = False
    
    def DeleteErrorWindow(self, widget, data = None):
        self.DeleteHelpWindow(None, None)
        if self.isErrorWindowCreated:
            self.errorWin.destroy()
            self.isErrorWindowCreated = False

    def DeleteHelpWindow(self, widget, data = None):
        if self.isHelpWindowCreated:
            self.helpWin.destroy()
            self.isHelpWindowCreated = False

    def FillErrorWindow(self,error):
        self.tv.get_buffer().set_text(error)
        self.tv.parent.get_vadjustment().set_value(len(error))
        
    def GetPackages(self):
        self.commuPackages = None
        for pack in self.possible_packages:
            if os.path.exists(pack + ".tex"):
                self.commuPackages = pack
                break

    def GetOtherCommands(self):
        try:
            tex_list = os.listdir(self.includeTex)
        except:
            tex_list = []
        
        accepted_match = [
            '\\newcommand',
            '\\renewcommand',
            '\\use',
            '\\Declare'
            ]
        
        commands_list=[]
        for tex_file in tex_list:
            if not tex_file.endswith('.tex'):
                continue
            tex_file = open(os.path.realpath(os.path.join(self.includeTex, tex_file)),"r")
            while True:
                l=tex_file.readline()
                if l == '': break
                
                l = l.strip()
                
                if l.startswith('\\begin{document}'): break
                for m in accepted_match:
                    if l.startswith(m):
                       if not l in commands_list:
                           commands_list.append(l)
                       break
            tex_file.close()
        
        self.other_commands = '\n'.join(commands_list)
        
    def Compile(self, diagramCode):
        tmp = open(self.tempTex, "w")
        tmp.write("\\documentclass[a4paper,10pt]{report}\n")
        if self.commuPackages:
            tmp.write("\input{%s}\n" % self.commuPackages)
        tmp.write("\\usepackage{tikz}\n")
        tmp.write("\\usetikzlibrary{arrows}\n")
        tmp.write(self.other_commands)
        tmp.write("\\begin{document}\n")
        tmp.write("%s\n" % (self.textBefore))
        tmp.write(diagramCode)
        tmp.write("%s\n" % (self.textAfter))
        tmp.write("\\end{document}\n")
        tmp.close()
        
        try:
            command = "TEXINPUTS=\"$TEXINPUTS:.::%s:%s\"  pdflatex -interaction nonstopmode -output-directory %s %s" % (
                self.tempDir,
                os.path.dirname(os.path.realpath(self.commuPackages + ".tex")),
                self.tempDir,
                tmp.name
                )
        except:
            command = "pdflatex -interaction nonstopmode -output-directory %s %s" % (
                self.tempDir,
                tmp.name
                )
        
        (exit_code, output) = commands.getstatusoutput(command)
        return exit_code, output
    
    def SetPercWH(self):
        self.SCALE = float(self.scale) / 10.0
        self.WIDTH = int(self.SCALE * self.width)
        self.HEIGHT = int(self.SCALE * self.height)
        
    def LoadPdf(self):
        self.document = poppler.document_new_from_file ("file://" + self.tempPdf, None)
        self.current_page = self.document.get_page(0)
        self.width, self.height = self.current_page.get_size()
        self.SetPercWH()
        
    def on_scale_changed(self, widget):
        self.scale = widget.get_value_as_int()
        self.SetPercWH()
        self.dwg.set_size_request(self.WIDTH,self.HEIGHT)
        self.dwg.queue_draw()
    
    def on_expose(self, widget, event):
        cr = widget.window.cairo_create()
        cr.set_source_rgb(1, 1, 1)
        if self.scale != 10:
            cr.scale(self.SCALE,self.SCALE)
        
        cr.rectangle(0, 0, self.WIDTH,self.HEIGHT)
        cr.fill()
        try:
            self.current_page.render(cr)
        except: pass
    
    def ThreadTarget(self, prgr, name):
        commands.getoutput('%s %s' % (prgr, name))
    
    def Preview(self, diagramCode):
        exitCode, output = self.Compile(diagramCode)
        if exitCode == 0:
            self.DeleteErrorWindow(None,None)
            self.LoadPdf()
            if self.isPreviewWindowCreated:
                self.on_expose(self.dwg, None)
                self.win.present()
            else:
                self.CreatePreviewWindow()
        else:
            if self.isErrorWindowCreated:
                self.FillErrorWindow(output)
            else:
                self.CreateErrorWindow()
                self.FillErrorWindow(output)
                while gtk.events_pending():
                    gtk.main_iteration()
                self.tv.parent.get_vadjustment().set_value(len(output))

            if self.commuPackages == None and self.showHelpPackages:
                self.CreateHelpWindow()

    def SilentPreview(self, diagramCode):
        exitCode, output = self.Compile(diagramCode)
        if exitCode == 0:
            self.DeleteErrorWindow(None,None)
            self.LoadPdf()
            if self.isPreviewWindowCreated:
                self.on_expose(self.dwg, None)
                self.win.present()
            else:
                self.CreatePreviewWindow()
                
    def ChangeHelpPackages(self, widget):
        show = not widget.get_active()
        self.SetHelpPackages(show)
                
    def GetHelpPackages(self):
        try:
            f = open(os.path.join(self.configDir, "display_help_packages.txt"), "r")
            c = int(f.read(1))
            f.close()
            if c == 0:
                self.showHelpPackages = False
            else:
                self.showHelpPackages = True
        except:
            self.showHelpPackages = True
                
    def SetHelpPackages(self, show):
        f = open(os.path.join(self.configDir, "display_help_packages.txt"), "w")
        if show:
            f.write("1")
        else:
            f.write("0")
        f.close()
        self.showHelpPackages = show

    def CreateHelpWindow(self):
        win = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.helpWin = win
        win.set_title ("Commu tips")
        win.connect("delete-event", self.DeleteHelpWindow)

        accelgroup = gtk.AccelGroup()
        accelgroup.connect_group(ord('W'), gtk.gdk.CONTROL_MASK, 0,
                                 lambda *etc: win.destroy())
        win.add_accel_group(accelgroup)
        
        s = "If you want to compile correctly your diagram, you can add the list of packages or commands you need.\n"
        s += "It's enough that you create a file in one of the following places:\n"
        for pack in self.possible_packages:
            s += "\t%s.tex\n" % pack
        s += "This file will be included before compilation.\n"
        s += "You can also use a symbolic link. In this case latex looks for packages also within the directory of the real location of commu_packages.tex."

        label = gtk.Label(s)

        check = gtk.CheckButton("Don't display this tip again.")
        check.connect("toggled", self.ChangeHelpPackages)

        button = gtk.Button("Close")
        button.connect("clicked", self.DeleteHelpWindow)

        hbox = gtk.HBox()
        hbox.set_spacing(6)
        hbox.pack_start(check, expand = False, fill = False)
        hbox.pack_end(button, expand = False, fill = False)
        
        vbox = gtk.VBox()
        vbox.set_spacing(6)
        vbox.set_border_width(6)
        vbox.pack_start(label)
        vbox.pack_start(hbox, expand = False, fill = False)
                
        win.add(vbox)
        win.show_all()
        
        self.isHelpWindowCreated=True
        

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
import tempfile
import subprocess
import re

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
        self.includeTex = os.path.join(self.configDir, "tex_to_include")
        self.textBefore = "The following diagram (see EGAXXII) proves the \
existence and the uniqueness of the canonical duality between coherent sheaves \
on spectral sites of stacks of quotient moduli spaces of pointed curves with \
fixed ultragenus and the category of categories fibered in megaloid over an \
abelian smooth autoisotropic of general type category:"
        self.textAfter = "As a consequence, the isotrivial families of \
superconnected unimodular curves are self-dual with respect to the motivic \
theory of ultrafilters."

        self.isPreviewWindowCreated = False
        self.isErrorWindowCreated = False
        self.isHelpWindowCreated = False
        self.scale = 22

        self.lastExitCode = 0
        self.lastOutput = ''

        self.possible_packages = [
            os.path.join("/", "usr", "share", "commu", "commu_packages"),
            os.path.join(os.path.realpath(os.path.dirname(__file__)), "commu_packages"),
            os.path.join(self.configDir, "commu_packages") ]

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

        ##################################################################
        #                                                                #
        #                                                                #
        #             Displayed PDF (ScrollWin + DrawingArea)            #
        #                                                                #
        #                                                                #
        #                                                                #
        ##################################################################
        # ScaleLab # ScaleSpin #                # Tex Log # Tips # Close #
        ##################################################################

        ### VBOX ###
        vbox = gtk.VBox()
        vbox.set_spacing(6)
        vbox.set_border_width(6)
        win.add(vbox)

        ## DrawingArea
        self.dwg = gtk.DrawingArea()
        self.dwg.set_size_request(self.WIDTH,self.HEIGHT)
        self.dwg.connect("expose-event", self.on_expose)

        ## ScrollWin
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.add_with_viewport(self.dwg)

        vbox.pack_start(sw)

        ### HBOX ###
        hbox = gtk.HBox()
        vbox.pack_start(hbox, expand = False, fill = False)

        ## Scale Lab
        lab = gtk.Label('Scale:')
        hbox.pack_start(lab, False, False, 4)

        ## Scale Spin
        adjust = gtk.Adjustment(self.scale, 1, 50, 1)
        scale_selector = gtk.SpinButton(adjust, 0, 0);
        scale_selector.connect("value-changed", self.on_scale_changed)

        hbox.pack_start(scale_selector, False, False, 0)

        ## close button
        button = gtk.Button(stock = gtk.STOCK_CLOSE)
        button.connect("clicked", self.DeletePreviewWindow)

        hbox.pack_end(button, expand = False, fill = False)

        ## tips button
        image = gtk.Image()
        image.set_from_stock (gtk.STOCK_HELP, gtk.ICON_SIZE_BUTTON)
        label = gtk.Label('Tips')
        THbox = gtk.HBox()
        THbox.pack_start(image)
        THbox.pack_start(label)
        buttonHelp = gtk.Button()
        buttonHelp.add(THbox)
        buttonHelp.connect("clicked", self.CreateHelpWindow)

        hbox.pack_end(buttonHelp, expand = False, fill = False)

        ## tex log
        self.LogImage = gtk.Image()
        self.LogImage.set_from_stock (gtk.STOCK_YES, gtk.ICON_SIZE_BUTTON)
        label = gtk.Label('Tex Log')
        THbox = gtk.HBox()
        THbox.pack_start(self.LogImage)
        THbox.pack_start(label)
        buttonLog = gtk.Button()
        buttonLog.add(THbox)
        buttonLog.connect("clicked", self.CreateErrorWindow)

        hbox.pack_end(buttonLog, expand = False, fill = False)

        ################################

        win.show_all()

        sw.get_hadjustment().set_value(self.WIDTH/5)
        sw.get_vadjustment().set_value(self.HEIGHT/5.5)

        self.isPreviewWindowCreated = True

    def CreateHelpWindow(self,bo = None):
        if self.isHelpWindowCreated: return

        win = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.helpWin = win
        win.set_default_size(400, 400)
        win.set_title ("Commu Tips")
        win.connect("delete-event", self.DeleteHelpWindow)

        accelgroup = gtk.AccelGroup()
        accelgroup.connect_group(ord('W'), gtk.gdk.CONTROL_MASK, 0,
                                 lambda *etc: win.destroy())
        win.add_accel_group(accelgroup)

        ###############################
        #--- Frame1 ------------------#
        #                             #
        #           Label1            #
        #                             #
        #                             #
        ###############################
        #--- Frame2 ------------------#
        #                             #
        #           Label2            #
        #                             #
        #                             #
        ###############################
        #                     # Close #
        ###############################

        ### VBOX ###
        vbox = gtk.VBox()
        vbox.set_spacing(6)
        vbox.set_border_width(6)
        win.add(vbox)

        ## FRAME 1

        TLabel = gtk.Label('<b>Add default commands or packages</b>')
        TLabel.set_use_markup(True)
        frame1 = gtk.Frame()
        frame1.set_label_widget(TLabel)

        vbox.pack_start(frame1)

        ## LABEL 1
        s = "If you want to compile correctly your diagram, you can add the list of packages or commands you need.\n"
        s += "It's enough that you create a file named 'commu_packages.tex' in one of the following places:\n\n"
        for pack in self.possible_packages:
            s += "\t%s/\n" % os.path.dirname( pack )
        s += "\nThis file will be included before compilation.\n"
        s += "You can also use a symbolic link. In this case latex looks for packages also within the directory of the real location of commu_packages.tex."

        label = gtk.Label(s)
        label.set_line_wrap(True)
        frame1.add(label)

        ## FRAME 2

        TLabel = gtk.Label('<b>Add commands or packages from your tex files</b>')
        TLabel.set_use_markup(True)
        frame2 = gtk.Frame()
        frame2.set_label_widget(TLabel)

        vbox.pack_start(frame2)

        ## LABEL 2

        s ='If you want that the commands or packages you are using in your tex file(s) will be included'
        s += ' before compilation, you can add them or links to them in:\n\n'
        s += '\t%s/\n' % self.includeTex
        s += '\nCommu will scan tex files in this directory extracting the commands or packages you have defined in them before the beginning'
        s += ' of the document.'

        label = gtk.Label(s)
        label.set_line_wrap(True)
        frame2.add(label)

        ## HBOX ##
        hbox = gtk.HBox()
        hbox.set_spacing(6)
        vbox.pack_end(hbox, expand = False, fill = False)

        ## Close Button
        button = gtk.Button(stock = gtk.STOCK_CLOSE)
        button.connect("clicked", self.DeleteHelpWindow)

        hbox.pack_end(button, expand = False, fill = False)

        ##################################################
        #check = gtk.CheckButton("Don't display this tip again.")
        #check.connect("toggled", self.ChangeHelpPackages)
        #hbox.pack_start(check, expand = False, fill = False)

        win.show_all()

        self.isHelpWindowCreated = True

    def CreateErrorWindow(self, bo = None):
        if self.isErrorWindowCreated: return

        win = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.errorWin = win
        win.set_default_size(500, 400)
        win.set_title ("Compilation errors")
        win.connect("delete-event", self.DeleteErrorWindow)

        accelgroup = gtk.AccelGroup()
        accelgroup.connect_group(ord('W'), gtk.gdk.CONTROL_MASK, 0,
                                 lambda *etc: win.destroy())
        win.add_accel_group(accelgroup)

        #######################################################
        #                                                     #
        #                                                     #
        #         Log Latex (ScrollWin + TextView)            #
        #                                                     #
        #                                                     #
        #                                                     #
        #######################################################
        #                                             # Close #
        #######################################################

        ### VBOX ###
        vbox = gtk.VBox()
        vbox.set_spacing(6)
        vbox.set_border_width(6)
        win.add(vbox)

        ## ScrollWind + TextView
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        self.tv = gtk.TextView()
        self.tv.set_editable(False)
        self.tv.set_cursor_visible(False)

        sw.add_with_viewport(self.tv)

        vbox.pack_start(sw)


        ### HBOX ###
        hbox = gtk.HBox()
        hbox.set_spacing(6)
        vbox.pack_end(hbox, expand = False, fill = False)

        ## Close Button
        button = gtk.Button(stock = gtk.STOCK_CLOSE)
        button.connect("clicked", self.DeleteErrorWindow)

        hbox.pack_end(button, expand = False, fill = False)

        ###########################

        win.show_all()

        self.isErrorWindowCreated = True
        self.FillErrorWindow()

    def DeletePreviewWindow(self, widget, data = None):
        self.DeleteErrorWindow(None, None)
        self.DeleteHelpWindow(None, None)
        self.lastExitCode = 0
        self.win.destroy()
        self.scale = 22
        self.isPreviewWindowCreated = False

    def DeleteHelpWindow(self, widget, data = None):
        if self.isHelpWindowCreated:
            self.helpWin.destroy()
            self.isHelpWindowCreated = False

    def DeleteErrorWindow(self, widget, data = None):
        self.lastOutput = ''

        if self.isErrorWindowCreated:
            self.errorWin.destroy()
            self.isErrorWindowCreated = False

    def FillErrorWindow(self):
        if self.isErrorWindowCreated and not self.lastOutput == self.Output:
            self.tv.get_buffer().set_text(self.Output)
            while gtk.events_pending():
                    gtk.main_iteration()
            self.tv.parent.get_vadjustment().set_value(len(self.Output))
            self.lastOutput = self.Output

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

        res = '[^{]*{([^}]*)}'
        reg = re.compile(res)

        already_defined_commands = []
        if self.commuPackages:
            try:
                commu_packages = open('%s.tex' % self.commuPackages,'r')
                for l in commu_packages:
                    try:
                        name = reg.findall(l)[0]
                    except:
                        continue
                    already_defined_commands.append(name)
                commu_packages.close()
            except: pass

        accepted_match = [
            '\\newcommand',
            '\\use',
            '\\Declare'
            ]

        commands_list = []
        for tex_file in tex_list:
            if not tex_file.endswith('.tex'):
                continue
            tex_file = open(os.path.realpath(os.path.join(self.includeTex, tex_file)),"r")
            while True:
                l = tex_file.readline()
                if l == '': break

                l = l.strip()

                if l.startswith('\\begin{document}'): break
                for m in accepted_match:
                    if l.startswith(m):
                       command_name = reg.findall(l)[0]
                       if not command_name in AlreadyDefinedCommands:
                           commands_list.append(l)
                           AlreadyDefinedCommands.append(command_name)
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

        args = [
                "pdflatex",
                "-interaction",
                "nonstopmode",
                "-output-directory",
                self.tempDir,
                tmp.name
            ]


        TEXINPUTS = os.environ.get('TEXINPUTS')
        try:
            if TEXINPUTS is None:
                TEXINPUTS = '.::%s:%s' % (self.tempDir, os.path.dirname(os.path.realpath(self.commuPackages + ".tex")) )
            else:
                TEXINPUTS = '%s:.::%s:%s' % (TEXINPUTS, self.tempDir, os.path.dirname(os.path.realpath(self.commuPackages + ".tex")) )
        except : pass
        else:
            os.environ['TEXINPUTS'] = TEXINPUTS

        LatexProc = subprocess.Popen(args = args, stdout = subprocess.PIPE)
        self.Output = LatexProc.communicate()[0]
        self.ExitCode = LatexProc.wait()

        if not self.ExitCode == 0:
            self.ExitCode = 1

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

    def Preview(self, diagramCode):
        self.GetPackages()
        self.GetOtherCommands()

        self.Compile(diagramCode)

        if not self.isPreviewWindowCreated:
            self.LoadPdf()
            self.CreatePreviewWindow()
        elif self.ExitCode == 0:
            self.LoadPdf()
            self.on_expose(self.dwg, None)

        if not self.ExitCode == self.lastExitCode:
            self.LogImage.set_from_stock ([ gtk.STOCK_YES, gtk.STOCK_NO][self.ExitCode], gtk.ICON_SIZE_BUTTON)
            self.lastExitCode = self.ExitCode

        self.FillErrorWindow()

    #def ChangeHelpPackages(self, widget):
        #show = not widget.get_active()
        #self.SetHelpPackages(show)

    #def GetHelpPackages(self):
        #try:
            #f = open(os.path.join(self.configDir, "display_help_packages.txt"), "r")
            #c = int(f.read(1))
            #f.close()
            #if c == 0:
                #self.showHelpPackages = False
            #else:
                #self.showHelpPackages = True
        #except:
            #self.showHelpPackages = True

    #def SetHelpPackages(self, show):
        #f = open(os.path.join(self.configDir, "display_help_packages.txt"), "w")
        #if show:
            #f.write("1")
        #else:
            #f.write("0")
        #f.close()
        #self.showHelpPackages = show

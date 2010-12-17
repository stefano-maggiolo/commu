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

# TO FIX: Make search in the textview case-insensitive. This seem impossible for now
import pygtk
pygtk.require("2.0")
import gtk
import gtk.glade
import gobject
import operator
import os
import tempfile
import subprocess
import re

from commu_conf import *

KEY_USER_DEFINED_COMMANDS = 'commu_user_defined_commands'
KEY_USER_DEFINED_DIRECTORIES = 'commu_user_defined_directories'
file_user_defined_directories = os.path.join(USER_DIRECTORY, KEY_USER_DEFINED_DIRECTORIES)
file_user_defined_commands_name = os.path.join(USER_DIRECTORY,KEY_USER_DEFINED_COMMANDS)
file_user_defined_commands = '%s.tex' % file_user_defined_commands_name

if not os.path.isfile(file_user_defined_commands):
    try:
        new = open(file_user_defined_commands,'w')
        new.write('% Here you can add the commands, symbols and packages you want to use in the diagrams\n%')
        new.write(' Alternatively you can directly modify the tex file %s\n' % file_user_defined_commands )
    except OSError: pass
    else:
        try: new.close()
        except: pass
if not os.path.isfile(file_user_defined_directories):
    try: new = open(file_user_defined_directories,'w')
    except OSError: pass
    else:
        try: new.close()
        except: pass

def GetButtonFromStock(gtkSTOCK,label,cb_function, data = None):
        ## load button
        image = gtk.Image()
        image.set_from_stock (gtkSTOCK, gtk.ICON_SIZE_BUTTON)
        label = gtk.Label(label)
        box = gtk.HBox()
        box.pack_start(image)
        box.pack_start(label)
        button = gtk.Button()
        button.add(box)
        button.connect("clicked", cb_function, data)
        return button

class Preview:
    def __init__(self, commu = None):
        self.commu = commu
        self.configDir = USER_DIRECTORY

        try:
            os.makedirs(self.configDir)
        except:
            pass

        self.tempDir = tempfile.mkdtemp()
        self.tempTex = os.path.join(self.tempDir, "commu_preview.tex")
        self.tempPdf = os.path.join(self.tempDir, "commu_preview.pdf")
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
        
        self.scale = 22

        self.lastExitCode = 0
        self.lastOutput = ''

    def RemoveTemporaryFiles(self):
        try: list_temp_dir = os.listdir(self.tempDir)
        except OSError: return
        for i in list_temp_dir:
            try: os.remove(os.path.join(self.tempDir, i))
            except OSError: pass
        try: os.rmdir(self.tempDir)
        except OSError: pass

    def CreatePreviewWindow(self):
        win = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.win = win
        win.set_default_size(800, 400)
        win.set_title("Commu preview")
        win.connect("delete-event", self.DeletePreviewWindow)
        win.set_keep_above(False)

        accelgroup = gtk.AccelGroup()
        accelgroup.connect_group(ord('W'), gtk.gdk.CONTROL_MASK, 0,
                                 lambda *etc: self.DeletePreviewWindow(None))
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
        button = GetButtonFromStock(gtk.STOCK_CLOSE,'Close',self.DeletePreviewWindow)
        hbox.pack_end(button, expand = False, fill = False)


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
        
        # User Defined Commands Button
        button = GetButtonFromStock(gtk.STOCK_HOME,'User Data',self.CreateUserDefinedCommandsWindow)
        hbox.pack_end(button, expand = False, fill = False)
        ################################

        win.show_all()

        sw.get_hadjustment().set_value(self.WIDTH/5)
        sw.get_vadjustment().set_value(self.HEIGHT/5.5)

        self.isPreviewWindowCreated = True

    def CreateErrorWindow(self, bo = None):
        if self.isErrorWindowCreated: return

        win = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.errorWin = win
        win.set_default_size(500, 400)
        win.set_title ("pdflatex output")
        win.connect("delete-event", self.DeleteErrorWindow)

        accelgroup = gtk.AccelGroup()
        accelgroup.connect_group(ord('W'), gtk.gdk.CONTROL_MASK, 0,
                                 lambda *etc: self.DeleteErrorWindow(None))
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
        self.lastExitCode = 0
        self.win.destroy()
        self.scale = 22
        self.isPreviewWindowCreated = False


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

    def Compile(self, diagramCode, text_before = True, text_after = True, other_commands = '',additional_args = []):
        
        tmp = open(self.tempTex, "w")
        tmp.write("\\documentclass[a4paper,10pt]{report}\n")
        if os.path.isfile(file_user_defined_commands):
            tmp.write("\input{%s}\n" % file_user_defined_commands)
        tmp.write("\\usepackage{tikz}\n")
        tmp.write("\\usetikzlibrary{arrows}\n")
        if other_commands:
            tmp.write('%s\n' % other_commands)
        tmp.write("\\begin{document}\n")
        if text_before: tmp.write("%s\n" % (self.textBefore))
        tmp.write(diagramCode)
        if text_after: tmp.write("%s\n" % (self.textAfter))
        tmp.write("\\end{document}\n")
        tmp.close()

        args = ['pdflatex'] + additional_args+[    
                "-interaction",
                "nonstopmode",
                "-output-directory",
                self.tempDir,
                tmp.name
            ]

        TEXINPUTS = os.environ.get('TEXINPUTS')
        if TEXINPUTS is None: TEXINPUTS = '.'
        try:
            dir_file = open(file_user_defined_directories,'r')
            dir_arr = [ d.strip() for d in dir_file.read().split('\n') if os.path.isdir(d.strip()) ]
            dir_file.close()
        except: dir_arr = []
        TEXINPUTS = ':'.join([TEXINPUTS,'.','',self.tempDir]+dir_arr)
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
        import poppler
        self.document = poppler.document_new_from_file ("file://" + self.tempPdf, None)
        self.current_page = self.document.get_page(0)
        self.width, self.height = self.current_page.get_size()
        self.SetPercWH()
    
    def SaveUserDefinedCommands(self,widget, data = None):
        commands = self.textbuffer_user_commands.get_text(
                                                    self.textbuffer_user_commands.get_start_iter(),
                                                    self.textbuffer_user_commands.get_end_iter()
                                                    )
        try:
            commands_file = open(file_user_defined_commands,'w')
            commands_file.write(commands)
            commands_file.close()
        except: pass
        try:
            dirs_file = open(file_user_defined_directories,'w')
            dirs_file.write('\n'.join([row[0] for row in self.store_directories]))
            dirs_file.close()
        except: pass
        self.DeleteUserDefinedCommandsWindow(None)
        if self.isPreviewWindowCreated:
            self.Preview(self.commu.Build())
    
    def MoveSelection(self, match_start, match_end):
        self.textbuffer_user_commands.move_mark(self.textbuffer_user_commands.get_insert(),match_start)
        self.textbuffer_user_commands.move_mark(self.textbuffer_user_commands.get_selection_bound(),match_end)
                
        self.tag_start = match_start
        self.tag_end = match_end
        self.textview.scroll_to_iter(match_start,0)
        
    def FindNext(self, widget, already_found = False):
        to_find = self.EntryUserDefinedCommands.get_text()
        if not to_find:
            self.RemoveAllTagCommandsWindow()
            return
        
        char_offset = self.textbuffer_user_commands.get_property('cursor-position')
        text_iter = self.textbuffer_user_commands.get_iter_at_offset(char_offset)

        try: match_start, match_end = text_iter.forward_search(to_find, gtk.TEXT_SEARCH_TEXT_ONLY)
        except:
            try: match_start, match_end = self.textbuffer_user_commands.get_start_iter().forward_search(to_find, gtk.TEXT_SEARCH_TEXT_ONLY)
            except:
                self.tag_start = self.tag_end = None
                self.RemoveAllTagCommandsWindow()
                return
        
        try:
            if match_start.get_offset() == self.tag_start.get_offset() and match_end.get_offset() == self.tag_end.get_offset():
                if already_found:
                    self.MoveSelection(match_start,match_end)
                    return
                match_start.forward_char()
                self.textbuffer_user_commands.place_cursor(match_start)
                self.FindNext(None, True)
                return
        except: pass
        
        self.MoveSelection(match_start,match_end)
    
    def FindPrevious(self, widget, data = None):
        to_find = self.EntryUserDefinedCommands.get_text()
        if not to_find:
            self.RemoveAllTagCommandsWindow()
            return
        
        char_offset = self.textbuffer_user_commands.get_property('cursor-position')
        text_iter = self.textbuffer_user_commands.get_iter_at_offset(char_offset)
        
        try: match_start, match_end = text_iter.backward_search(to_find, gtk.TEXT_SEARCH_TEXT_ONLY)
        except:
            try: match_start, match_end = self.textbuffer_user_commands.get_end_iter().backward_search(to_find, gtk.TEXT_SEARCH_TEXT_ONLY)
            except:
                self.tag_start = self.tag_end = None
                self.RemoveAllTagCommandsWindow()
                return
                
        self.MoveSelection(match_start,match_end)
    
    def TextViewGetFocus(self, widget = None, data = None):
        self.tag_start = self.tag_end = None
        
        
    def RemoveAllTagCommandsWindow(self, widget = None, data = None):
        char_offset = self.textbuffer_user_commands.get_property('cursor-position')
        text_iter = self.textbuffer_user_commands.get_iter_at_offset(char_offset)
        self.textbuffer_user_commands.place_cursor(text_iter)
        
    def EntryFindGrabFocus(self, widget = None, data = None):
        if self.EntryUserDefinedCommands.has_focus():
            return 
        sel_start = self.textbuffer_user_commands.get_iter_at_mark(self.textbuffer_user_commands.get_insert())
        sel_end   = self.textbuffer_user_commands.get_iter_at_mark(self.textbuffer_user_commands.get_selection_bound())
        if not sel_start.get_offset() == sel_end.get_offset():
            selected = self.textbuffer_user_commands.get_text(sel_start,sel_end)
            self.EntryUserDefinedCommands.set_text(selected)
        self.EntryUserDefinedCommands.grab_focus()
        self.FindNext(None)
        
    def DeleteUserDefinedCommandsWindow(self, widget, data = None):
        self.UserCommandsWin.destroy()
    
        
    def AddUserDirectory(self, widget, data = None):
        chooser = gtk.FileChooserDialog(title='Choose a directory',action= gtk.FILE_CHOOSER_ACTION_OPEN,
                                        buttons = (gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
        chooser.set_select_multiple(True)
        chooser.set_action(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
        response = chooser.run()
        dirnames = chooser.get_filenames()
        chooser.destroy()
        if response == gtk.RESPONSE_OK:
            for direc in dirnames:
                if os.path.isdir(direc):
                    self.store_directories.append((direc,))

    def RemoveUserDirectories(self, widget, data = None):
        treeselection = self.treeview_directories.get_selection()
        model, pathlist = treeselection.get_selected_rows()
        item_numbers = [ x[0] for x in pathlist ]
        if not item_numbers: return
        names = [model[number][0] for number in item_numbers]
        for row in model:
            if row[0] in names:
                model.remove(row.iter)
       
    def ShowHelpUserDeinedCommandsWindow(self, widget = None, data = None):
        message = 'This window lets you define the data pdflatex need to compile correctly your diagrams.\n'
        message+= 'In the part above you can add the commands or the packages you use in your diagrams.\n'
        message+= 'In the part below you can add the directories where pdflatex will look for, '
        message+= 'for example, your *.sty files.'
        msgbox = gtk.MessageDialog(parent = None,
                               buttons = gtk.BUTTONS_CLOSE,
                               flags = gtk.DIALOG_MODAL,
                               message_format = message,
                               type = gtk.MESSAGE_INFO)
        msgbox.set_title("What's this?")
        result = msgbox.run()
        msgbox.destroy()
        
    def CreateUserDefinedCommandsWindow(self, widget = None, data = None):
        win = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.UserCommandsWin = win
        win.set_modal(True)
        win.set_default_size(550, 600)
        win.set_title("User Data")
        win.connect("delete-event", self.DeleteUserDefinedCommandsWindow)

        accelgroup = gtk.AccelGroup()
        win.add_accel_group(accelgroup)
        accelgroup.connect_group(ord('W'), gtk.gdk.CONTROL_MASK, 0,
                                 lambda *etc: self.DeleteUserDefinedCommandsWindow(None))
        accelgroup.connect_group(ord('F'), gtk.gdk.CONTROL_MASK, 0,
                                 lambda *etc: self.EntryFindGrabFocus())
        accelgroup.connect_group(ord('G'), gtk.gdk.CONTROL_MASK, 0,
                                 lambda *etc: self.FindNext(None))
        accelgroup.connect_group(ord('S'), gtk.gdk.CONTROL_MASK, 0,
                                 lambda *etc: self.SaveUserDefinedCommands(None))
        accelgroup.connect_group(ord('G'), gtk.gdk.CONTROL_MASK | gtk.gdk.SHIFT_MASK, 0,
                                 lambda *etc: self.FindPrevious(None))
        
        
        ### MAIN VBOX ####             
        main_vbox = gtk.VBox()
        win.add(main_vbox)
        main_vbox.set_spacing(6)
        main_vbox.set_border_width(6)
        
        ### HBOX ###
        hbox = gtk.HBox()
        main_vbox.pack_end(hbox, expand = False, fill = False)
        
        ### BUTTONS ###
        ## Cancel button
        button = GetButtonFromStock(gtk.STOCK_CANCEL,'Cancel',self.DeleteUserDefinedCommandsWindow)
        hbox.pack_end(button, expand = False, fill = False)
        
        ## Save button
        button = GetButtonFromStock(gtk.STOCK_SAVE,'Save',self.SaveUserDefinedCommands)
        hbox.pack_end(button, expand = False, fill = False)
        
        ## Help button
        button = GetButtonFromStock(gtk.STOCK_HELP,'What\'s this?',self.ShowHelpUserDeinedCommandsWindow)
        hbox.pack_start(button, expand = False, fill = False)
        
        ### VPANE ###
        vpane = gtk.VPaned()
        main_vbox.pack_start(vpane, expand = True, fill = True)
        vpane.set_position(450)
        
        ### VBOX ###
        vbox = gtk.VBox()
        vpane.add1(vbox)
        #vbox.set_spacing(6)
        #vbox.set_border_width(6)
        
        ## label title commands ##
        label = gtk.Label('User commands and packages')
        vbox.pack_start(label, expand = False, fill = False)
        
        # TextView
        sw = gtk.ScrolledWindow()
        vbox.pack_start(sw, expand = True, fill = True)
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        
        textview = gtk.TextView()
        sw.add(textview)
        self.textview = textview
        textview.set_wrap_mode(gtk.WRAP_NONE)
        textview.set_editable(True)
        textview.set_cursor_visible(True)
        textview.connect('focus-in-event',self.TextViewGetFocus)
        textview.set_resize_mode(gtk.RESIZE_IMMEDIATE)
        self.editing = True
        self.tag_start = self.tag_end = None
        
        
        self.textbuffer_user_commands = textview.get_buffer()
        tag = self.textbuffer_user_commands.create_tag('MyTag')
        tag.set_property('background','yellow')
        
        try:
            commands_file = open(file_user_defined_commands,'r')
            self.textbuffer_user_commands.set_text(commands_file.read())
            commands_file.close()
        except:
            from commu_main import display_warning
            display_warning('Cannot open the file \'%s\'' % file_user_defined_commands)
            win.destroy()
            return 
        
        ## directories title and find
        hbox_find = gtk.HBox()
        vbox.pack_end(hbox_find, expand = False, fill = False)
        
        
        ## Find ####
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_FIND, gtk.ICON_SIZE_BUTTON)
        hbox_find.pack_end(image, expand = False, fill = False)
        
        entry = gtk.Entry()
        self.EntryUserDefinedCommands = entry
        hbox_find.pack_end(entry, expand = False, fill = False)
        entry.connect('changed',self.FindNext)
        
        ## GO forward button
        button = GetButtonFromStock(gtk.STOCK_GO_FORWARD,'',self.FindNext)
        hbox_find.pack_end(button, expand = False, fill = False)
        
        ## GO back button
        button = GetButtonFromStock(gtk.STOCK_GO_BACK,'',self.FindPrevious)
        hbox_find.pack_end(button, expand = False, fill = False)
        
        ### TREEVIEW ###
        vbox_dir = gtk.VBox()
        vpane.add2(vbox_dir)
        #vbox.set_spacing(6)
        #vbox.set_border_width(6)
        
        ## label title directories ##
        label = gtk.Label('User Directories')
        vbox_dir.pack_start(label, expand = False, fill = False)
        
        hbox_dir = gtk.HBox()
        vbox_dir.pack_end(hbox_dir, expand = True, fill = True)
        #vbox.pack_end(hbox_dir, expand = False, fill = False)
        
        add_remove_vbox = gtk.VBox()
        hbox_dir.pack_end(add_remove_vbox, expand = False, fill = False)
        
        # add button
        button = GetButtonFromStock(gtk.STOCK_ADD, 'Add', self.AddUserDirectory)
        add_remove_vbox.pack_start(button, expand = False, fill = False)
        
        # remove button
        button = GetButtonFromStock(gtk.STOCK_REMOVE, 'Remove', self.RemoveUserDirectories)
        add_remove_vbox.pack_start(button, expand = False, fill = False)
        
        sw = gtk.ScrolledWindow()
        hbox_dir.pack_start(sw, expand = True, fill = True)
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        
        store = gtk.ListStore(str)
        self.store_directories = store
        
        tv = gtk.TreeView(store)
        self.treeview_directories = tv
        sw.add(tv)
        tv.set_search_column(0)
        tv.set_property('rules-hint', True)
        tv.set_rubber_banding(True)
        tv.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        
        cell = gtk.CellRendererText()
        tvcolumn = gtk.TreeViewColumn('', cell, text=0)
        tv.append_column(tvcolumn)
        tvcolumn.set_sort_column_id(0)
        
        try:
            dir_file = open(file_user_defined_directories,'r')
            directories = [ d.strip() for d in dir_file.read().split('\n')]
            dir_file.close()
        except: directories = []
        for direc in directories:
            if os.path.isdir(direc):
                store.append((direc,))
        
        win.show_all()
        
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

        self.Compile(diagramCode)

        if not self.isPreviewWindowCreated:
            if self.ExitCode == 0:
                self.LoadPdf()
                self.CreatePreviewWindow()
            else:
                self.CreateErrorWindow()
                self.errorWin.set_modal(True)
                return
        elif self.ExitCode == 0:
            self.LoadPdf()
            self.on_expose(self.dwg, None)

        if not self.ExitCode == self.lastExitCode:
            self.LogImage.set_from_stock ([ gtk.STOCK_YES, gtk.STOCK_NO][self.ExitCode], gtk.ICON_SIZE_BUTTON)
            self.lastExitCode = self.ExitCode

        self.FillErrorWindow()


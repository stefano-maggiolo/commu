#!/usr/bin/python

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


# TO FIX: Make IconView searchable

import os, sys, shutil
import subprocess
import pygtk
pygtk.require("2.0")
import gtk

from commu_conf import *
from commu_preview import *

from commu_main import display_warning
from configobj import ConfigObj

KEY_TEMPLATE_DIRECTORY = 'Templates'
KEY_TEMPLATE_CONF_FILE = 'commu_templates.db'
KEY_TEMPLATE_NO_IMAGE = 'no_diagram.png'
template_conf_directory = os.path.join(USER_DIRECTORY,KEY_TEMPLATE_DIRECTORY)
template_conf_file = os.path.join(USER_DIRECTORY,KEY_TEMPLATE_CONF_FILE)
template_conf_file_backup = '%s.backup' % template_conf_file
template_conf_image_no_diagram = os.path.join(USER_DIRECTORY, KEY_TEMPLATE_NO_IMAGE)

try: os.makedirs(template_conf_directory)
except: pass
#copy the installation configuration
if not USER_DIRECTORY == INSTALLATION_DIRECTORY:
	if not os.path.isfile(template_conf_image_no_diagram):
		try: shutil.copy(os.path.join(INSTALLATION_DIRECTORY, KEY_TEMPLATE_NO_IMAGE),template_conf_image_no_diagram)
		except: pass
	if not os.path.isfile(template_conf_file):
		try: shutil.copy(os.path.join(INSTALLATION_DIRECTORY, KEY_TEMPLATE_CONF_FILE), template_conf_file)
		except: pass
		
############ GLOBAL CONFIGURATION KEYS ###########
key_diagrams = 'diagrams'
############ KEYS FOR NODES #############
key_nodes = 'nodes'
key_nodes_pos = 'pos'
default_key_nodes_pos = [0,0]
key_nodes_tex = 'tex'
default_key_nodes_tex = ''

############ KEYS FOR ARROWS #############
key_arrows = 'arrows'
key_arrows_source_label = 'source_label'
key_arrows_target_label = 'target_label'
key_arrows_inarcamento = 'inarcamento'
default_key_arrows_inarcamento = 0
key_arrows_altobasso = 'altobasso'
default_key_arrows_altobasso = SCRITTA.index("Above")
key_arrows_tex_label = 'tex_label'
default_key_arrows_tex_label = ''
key_arrows_tratto = 'TRATTO'
default_key_arrows_tratto = TRATTO.index('Normal')
key_arrows_coda = 'CODA'
default_key_arrows_coda = CODA.index('Normal')
key_arrows_decorazione = 'DECORAZIONE'
default_key_arrows_decorazione = DECORAZIONE.index('No')
key_arrows_testa = 'TESTA'
default_key_arrows_testa = TESTA.index('Arrow')
key_arrows_preset = 'PRESET'
default_key_arrows_preset = PRESET.index('Normal')

############ GLOBAL KEYS FOR DIAGRAMS ################
key_hor_distance = 'hdist'
default_key_hor_distance = 1.5
key_ver_distance = 'vdist'
default_key_ver_distance = 1.2
key_char_margin = 'cmar'
default_key_char_margin = 2

key_columns_number = 'cnum'
default_key_columns_number = 4
key_rows_number = 'rnum'
default_key_rows_number = 3

key_diagram_image = 'image'
default_key_diagram_image = template_conf_image_no_diagram

key_default_max_width_image = 200
key_default_max_height_image = 150

def DialogChooserBackup(mode):
	if mode == 'save':
		action = gtk.FILE_CHOOSER_ACTION_SAVE
		buttons = (gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_SAVE,gtk.RESPONSE_OK)
		title = 'Backup Diagrams'
	else:
		action = gtk.FILE_CHOOSER_ACTION_OPEN
		buttons = (gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK)
		title = 'Restore Diagrams'
		
	chooser = gtk.FileChooserDialog(title=title,action=action, buttons=buttons)
	if mode == 'save':
		chooser.set_current_folder(template_conf_directory)
		chooser.set_current_name(template_conf_file_backup)
	else:
		chooser.set_current_folder(os.path.join(INSTALLATION_DIRECTORY,KEY_TEMPLATE_DIRECTORY))
	chooser.set_select_multiple(False)
	
	response = chooser.run()
	filename = chooser.get_filename()
	chooser.destroy()
	return response == gtk.RESPONSE_OK, filename

def RestoreBackupConfiguration():
	response, filename = DialogChooserBackup('restore')
	
	if response and os.path.isfile(filename):
		
		try: ConfigObj(filename,raise_errors=True)
		except Exception, Err:
			display_warning('You cannot restore \'%s\'. The following error occurs:\n%s' % (filename, str(Err)))
			return
		
		message_format = 'Are you sure you want to use \'%s\' as your default configuration?\n' % filename
		message_format+= 'This action will delete the existing configuration.'
		msgbox = gtk.MessageDialog(parent = None,
							   buttons = gtk.BUTTONS_YES_NO,
							   flags = gtk.DIALOG_MODAL,
							   message_format = message_format,
							   type = gtk.MESSAGE_QUESTION)
		msgbox.set_title("Are You Sure?")
		response = msgbox.run()
		msgbox.destroy()
		if not response: return
		try:
			shutil.copy(filename,template_conf_file)
		except OSError, Err:
			display_warning('Restore action unsuccessful due to the following error:\n%s' % str(Err))
		else: return True
		
class GlobalConfiguration:
	def __init__(self,commu_class):
		self.LoadConfiguration()
		self.commu = commu_class
		
	def AddDiagram(self,name,diagram):
		# diagram here is not an instance of DiagramConfiguration, it's just a dict
		self.diagrams[name]=diagram
	
	def RemoveDiagramsByName(self, names):
		for name in names:
			try: del self.diagrams[name]
			except KeyError:
				# if this exception is raised, something is wrong
				pass
	
	def LoadDiagramFromGui(self):
		diagram = DiagramConfiguration()
		diagram.AddHorDist(self.commu.spinW.get_value())
		diagram.AddVerDist(self.commu.spinH.get_value())
		diagram.AddCharMargin(self.commu.spinR.get_value())
		diagram.AddColumnsRowsNumber(self.commu.cols,self.commu.rows)
		for r in xrange(self.commu.rows):
			for c in xrange(self.commu.cols):
				if self.commu.objects[(r,c)].ToWrite():
					node = self.commu.objects[(r,c)]
					diagram.AddNode(
									label = self.commu.GenerateNodeName(r,c),
									pos = [r,c],
									tex = node.Name()
									)
		
		for direzione in self.commu.arrows.keys():
			for f in self.commu.arrows[direzione]:
				_from, _to = direzione
				diagram.AddArrow(
								source_label = self.commu.GenerateNodeName(*_from),
								target_label = self.commu.GenerateNodeName(*_to),
								inarcamento = f.inarcamento(),
								tex_label = f.funzione(),
								tratto = f.tratto,
								coda = f.coda,
								testa = f.testa,
								altobasso = f.altobasso(),
								decorazione = f.decorazione,
								preset = f.preset.get_active()
								)
		return diagram
		
	def BuildFromDiagram(self,diag):
		if isinstance(diag,DiagramConfiguration):
			diag = diag.conf
		
		s = ""
		rientro = int(float(diag.get(key_char_margin,default_key_char_margin)))
		w = float(diag.get(key_hor_distance,default_key_hor_distance))
		h = float(diag.get(key_ver_distance,default_key_ver_distance))

		s += " " * rientro + "\\[\n"
		s += " " * rientro + "\\begin{tikzpicture}[xscale=%.1f,yscale=%.1f]\n" % (w, -h)
		
		Nodes = diag[key_nodes]
		for node_name in Nodes.sections:
			node = Nodes[node_name]
			r, c = node.get(key_nodes_pos, default_key_nodes_pos)
			r, c = int(r), int(c)
			tex_node = node.get(key_nodes_tex,default_key_nodes_tex)
			if tex_node == '':
				s += " " * (rientro+2) + "\\node (%s) at (%d, %d) {};\n" % (node_name, c, r)
			else:
				s += " " * (rientro+2) + "\\node (%s) at (%d, %d) {$%s$};\n" % (node_name, c, r, tex_node)
				
		Arrows = diag[key_arrows]
		for arr in Arrows.sections:
			arrow = Arrows[arr]
			_from = arrow[key_arrows_source_label]
			_to   = arrow[key_arrows_target_label]
			tratto = int(arrow.get(key_arrows_tratto, default_key_arrows_tratto))
			coda =   int(arrow.get(key_arrows_coda, default_key_arrows_coda))
			testa =  int(arrow.get(key_arrows_testa,default_key_arrows_testa))
			inarcamento = int(arrow.get(key_arrows_inarcamento,default_key_arrows_inarcamento))
			altobasso = int(arrow.get(key_arrows_altobasso,default_key_arrows_altobasso))
			decorazione = int(arrow.get(key_arrows_decorazione,default_key_arrows_decorazione))
			funzione = arrow.get(key_arrows_tex_label,default_key_arrows_tex_label)
			
			s += " " * (rientro+2) + "\\path (%s)" % _from
			if tratto == TRATTO.index("No"):
				s += " --"
			else:
				s += " edge ["

				if coda == CODA.index("Injection above"): s += "right hook"
				elif coda == CODA.index("Injection below"): s += "left hook"
				elif coda == CODA.index("Element"): s += "serif cm" #alternativa: "|"

				if tratto == TRATTO.index("Normal") or tratto == TRATTO.index("Dashed") or tratto == TRATTO.index("Double"): s += "-"

				if testa == TESTA.index("Arrow"): s += ">"
				elif testa == TESTA.index("Double arrow"): s += ">>"

				if tratto == TRATTO.index("Dashed"): s += ",dashed"
				elif tratto == TRATTO.index("Double"): s += ",double distance=1.5pt"

				if inarcamento > 0: s += ",bend left=%d" % (inarcamento)
				elif inarcamento < 0: s += ",bend right=%d" % (abs(inarcamento))
				s += "]"
				
			s += "node ["

			if altobasso == SCRITTA.index("Above"): s += "auto"
			elif altobasso == SCRITTA.index("Below"): s += "auto,swap"

			s += "] {$\scriptstyle{%s}$} " % funzione

			if decorazione == DECORAZIONE.index("Isomorphism"):
				s += "node ["
				if altobasso == SCRITTA.index("Above"): s += "rotate=180,"
				s += "sloped] {$\scriptstyle{\widetilde{\ \ \ }}$} "

			s += "(%s)" % _to
			s += ";\n"
		s += " " * rientro + "\\end{tikzpicture}\n"
		s += " " * rientro + "\\]\n"
		return s

	def CreateImageForDiagram(self,diagram, remove_temp = False, add_image = True, name = None):
		if isinstance(diagram,DiagramConfiguration):
			diagram = diagram.conf
		job_name = 'commu_export'
		preview = Preview()
		self.preview_for_template = preview
		diagram_code = self.BuildFromDiagram(diagram)
		
		diagram_code = diagram_code.replace('\[','$$',1)
		diagram_code = diagram_code[:-3]+'$$\n'
		diagram_code = '\n\\beginpgfgraphicnamed{%s}\n%s\\endpgfgraphicnamed' % (job_name,diagram_code)
		preview.Compile(diagram_code,False,False, other_commands = '\\pgfrealjobname{poppoppero}',additional_args=['-jobname=%s' % job_name])
		if preview.ExitCode == 1:
			if remove_temp: preview.RemoveTemporaryFiles()
			diagram[key_diagram_image] = template_conf_image_no_diagram
			return
		image_output = '%s/%s.png' % (preview.tempDir,job_name)
		
		try:
			args = ['gs',
					'-q',
					'-dBATCH',
					'-dNOPAUSE',
					'-sDEVICE=pngmono',
					 '-dMAxBitmap=500000000',
					 '-dGridFitTT=0',
					 '-r300x300',
					 '-sOutputFile=%s' % image_output,
					 os.path.join(preview.tempDir, '%s.pdf' % job_name)]
			ConvertProc = subprocess.Popen(args = args, stdout = subprocess.PIPE, stderr=sys.stderr)
			Output = ConvertProc.communicate()[0]
			ExitCode = ConvertProc.wait()
			if not ExitCode == 0: raise Exception
			if name:
				new_image_output = os.path.join(template_conf_directory,'%s.png' % name)
				try: shutil.move(image_output,new_image_output)
				except : raise Exception
				image_output = new_image_output
			diagram[key_diagram_image] = image_output
		except Exception,Err:
			diagram[key_diagram_image] = template_conf_image_no_diagram
		
		if remove_temp: preview.RemoveTemporaryFiles()
	
	def SetDiagramInGui(self,diag, diag_name):
		
		# self.commu e' l'istanza di commu, da cui puoi prendere quello che serve della gui
		
		rientro = int(float(diag.get(key_char_margin,default_key_char_margin)))
		w = float(diag.get(key_hor_distance,default_key_hor_distance))
		h = float(diag.get(key_ver_distance,default_key_ver_distance))
		
		Nodes = diag[key_nodes]
		for node_name in Nodes.sections:
			node = Nodes[node_name]
			r, c = node.get(key_nodes_pos, default_key_nodes_pos)
			r, c = int(r), int(c)
			tex_node = node.get(key_nodes_tex,default_key_nodes_tex)
		
		Arrows = diag[key_arrows]
		for arr in Arrows.sections:
			arrow = Arrows[arr]
			_from = arrow[key_arrows_source_label]
			_to   = arrow[key_arrows_target_label]
			tratto = int(arrow.get(key_arrows_tratto, default_key_arrows_tratto))
			coda =   int(arrow.get(key_arrows_coda, default_key_arrows_coda))
			testa =  int(arrow.get(key_arrows_testa,default_key_arrows_testa))
			inarcamento = int(arrow.get(key_arrows_inarcamento,default_key_arrows_inarcamento))
			altobasso = int(arrow.get(key_arrows_altobasso,default_key_arrows_altobasso))
			decorazione = int(arrow.get(key_arrows_decorazione,default_key_arrows_decorazione))
			tipo = int(arrow.get(key_arrows_preset, default_key_arrows_preset))
			funzione = arrow.get(key_arrows_tex_label,default_key_arrows_tex_label)
		
		
		## Lascia questo per ultimo
		self.SetLastDiagramSaved(diag_name)
		self.DeleteLoadWindow(None)
		
		
	def CreateBackupConfiguration(self, widget = None, data = None):
		response, filename = DialogChooserBackup('save')
		if response:
			try: shutil.copy(template_conf_file,filename)
			except OSError, Err:
				display_warning('Unsuccessful creation of a backup due to the following error:\n%s' % str(Err))

	def RestoreBackupConfigurationCallback(self, widget = None, data = None):
		if not RestoreBackupConfiguration(): return
		self.DeleteLoadWindow(None)
		
		try: self.LoadConfiguration()
		except Exception, Err:
			display_warning('Something bad happens loading the new configuration. The following error occurs:\n%s' % str(Err))
		else:
			self.CreateLoadTemplatesWindow()
	
	def SaveConfiguration(self):
		self.conf.write()
	
	def LoadConfiguration(self):
		##### Read Configuration ######
		self.conf = ConfigObj(template_conf_file, raise_errors=True, create_empty=True)

		try: 
			self.diagrams = self.conf[key_diagrams]
		except KeyError:
			self.conf[key_diagrams] = {}
			self.diagrams = self.conf[key_diagrams]
	
	def SaveDirectlyToTheLastDiagram(self):
		if not (hasattr(self,'last_diagram_saved') and self.last_diagram_saved in self.diagrams.sections):
			self.CreateChooseNameWindow()
			return
		
		new_diagram = self.LoadDiagramFromGui()
		self.CreateImageForDiagram(new_diagram, name = self.last_diagram_saved, remove_temp = True)
		old_image = self.diagrams[self.last_diagram_saved][key_diagram_image]
		if not old_image in [new_diagram.conf[key_diagram_image], template_conf_image_no_diagram]:
			try: os.remove(old_image)
			except OSError: pass
		
		self.AddDiagram(self.last_diagram_saved,new_diagram.conf.dict())
		self.SaveConfiguration()
		
	def DeleteChooseNameWindow(self, widget, data = None):
		if not self.renaming: self.preview_for_template.RemoveTemporaryFiles()
		self.ChooseNameWindow.destroy()
	
	def OverwriteChooseNameWindow(self, name):
		message_format = 'The diagram %s already exists. Do you want to overwrite it?' % name
		msgbox = gtk.MessageDialog(parent = None,
								   buttons = gtk.BUTTONS_YES_NO,
								   flags = gtk.DIALOG_MODAL,
								   message_format = message_format,
								   type = gtk.MESSAGE_QUESTION)
		msgbox.set_title("Overwrite??")
		
		return msgbox
	
	def SetLastDiagramSaved(self, name):
		self.last_diagram_saved = name
		self.commu.w.get_widget("window").set_title("commu - Diagram : %s" % name)
	def UnSetLastDiagramSaved(self):
		if hasattr(self,'last_diagram_saved'):
			delattr(self,'last_diagram_saved')
			self.commu.w.get_widget("window").set_title("commu")
		
	def SaveChooseNameWindow(self, widget, old_name = None):
		name = self.entry_for_ChooseName.get_text()
		if not name or name == old_name:
			return
		if name in self.diagrams.sections:
			msgbox = self.OverwriteChooseNameWindow(name)
			result = msgbox.run()
			if not result == gtk.RESPONSE_YES:
				msgbox.destroy()
				return
			msgbox.destroy()
			if self.renaming:
				self.RemoveDiagramsFromTheIconView([name])
				self.DeleteImageOfOldDiagrams([name])
			try:
				if name == self.last_diagram_saved:
					self.UnSetLastDiagramSaved()
					#delattr(self,'last_diagram_saved')
			except: pass
		
		if self.renaming:
			self.RemoveDiagramsByName([old_name])
			for row in self.store:
				if row[self.COL_NAMES] == old_name:
					row[self.COL_NAMES] = name
					break
			self.UnSetLastDiagramSaved()
		else:
			image_output = '%s/%s.png' % (template_conf_directory,name)
			image_name = self.new_diagram.conf[key_diagram_image]
			if not image_name == default_key_diagram_image:
				try:
					shutil.move(image_name,image_output)
					self.new_diagram.AddImage(image_output)
				except:
					self.new_diagram.AddImage()
			self.SetLastDiagramSaved(name)
			#self.last_diagram_saved = name
			self.new_diagram = self.new_diagram.conf.dict()
			
		self.AddDiagram(name,self.new_diagram)
		self.SaveConfiguration()

		self.DeleteChooseNameWindow(None)
		
	def CreateChooseNameWindow(self,
									title = 'Choose The Name',
									new_diagram = None,
									label = 'Choose a name for the diagram',
									old_name = ''):
		## in the rename mode new_diagram is not a DiagramConfiguration istance
		self.renaming = not new_diagram == None
		
		win = gtk.Window(gtk.WINDOW_TOPLEVEL)
		self.ChooseNameWindow = win
		win.set_modal(True)
		win.set_default_size(400, 300)
		win.set_title(title)
		win.connect("delete-event", self.DeleteChooseNameWindow)

		accelgroup = gtk.AccelGroup()
		accelgroup.connect_group(ord('W'), gtk.gdk.CONTROL_MASK, 0,
								 lambda *etc: self.DeleteChooseNameWindow(None))
		win.add_accel_group(accelgroup)
		
		### VBOX ###
		vbox = gtk.VBox()
		vbox.set_spacing(6)
		vbox.set_border_width(6)
		win.add(vbox)
		
		### IMAGE ###
		if self.renaming:
			self.new_diagram = new_diagram
			image_name = self.new_diagram[key_diagram_image]
		else:
			self.new_diagram = self.LoadDiagramFromGui()
			self.CreateImageForDiagram(self.new_diagram)
			image_name = self.new_diagram.conf[key_diagram_image]
		try: pixbuf = gtk.gdk.pixbuf_new_from_file(image_name)
		except: pixbuf = gtk.gdk.pixbuf_new_from_file(template_conf_image_no_diagram)
		pixbuf = self.ScaleImage(pixbuf)
		image = gtk.Image()
		image.set_from_pixbuf(pixbuf)
		vbox.pack_start(image, expand = True, fill = True)
		
		### HBOX ###
		hbox = gtk.HBox()
		vbox.pack_end(hbox, expand = False, fill = False)
		
		### BUTTONS ###
		## cancel button
		button = GetButtonFromStock(gtk.STOCK_CANCEL,'Cancel', self.DeleteChooseNameWindow)
		hbox.pack_end(button, expand = False, fill = False)
		
		## Save button
		button = GetButtonFromStock(gtk.STOCK_SAVE,'Save',self.SaveChooseNameWindow, old_name)
		hbox.pack_end(button, expand = False, fill = False)
		
		# Label and entry
		hbox = gtk.HBox()
		vbox.pack_end(hbox, expand = False, fill = False)
		
		
		label = gtk.Label(label)
		hbox.pack_start(label)
		
		self.entry_for_ChooseName = gtk.Entry()
		self.entry_for_ChooseName.connect("activate", self.SaveChooseNameWindow, old_name)
		self.entry_for_ChooseName.set_text(old_name)
		hbox.pack_end(self.entry_for_ChooseName)
		
		win.show_all()
		
	######## LOAD TEMPLATES WINDOW
	def DeleteLoadWindow(self, widget, data = None):
		self.loadWin.destroy()
	
	def AddLoadWindow(self, widget, data = None):
		selection = self.iconview.get_selected_items()
		try: item_number = selection[0][0]
		except: return
		row=self.store[item_number]
		diag_name = row[self.COL_NAMES]
		diagram = self.diagrams[diag_name]
		self.SetDiagramInGui(diagram, diag_name)
	
	def RenameLoadWindow(self, widget, data = None):
		selection = self.iconview.get_selected_items()
		try: item_number = selection[0][0]
		except: return
		row=self.store[item_number]
		old_name = row[self.COL_NAMES]
		new_diagram = self.diagrams[old_name]
		self.CreateChooseNameWindow(title = 'Choose a New Name',
									new_diagram = new_diagram,
									label = 'Choose a new name for the diagram',
									old_name = old_name)
	
	def ScaleImage(self, pixbuf, max_width = key_default_max_width_image, max_height = key_default_max_height_image):
		h=pixbuf.get_height()
		w=pixbuf.get_width()
		scale = min(float(max_width)/float(w),float(max_height)/float(h))
		return pixbuf.scale_simple(dest_width = int(w*scale),dest_height = int(h*scale),interp_type = gtk.gdk.INTERP_BILINEAR)
	
	def RemoveDiagramsFromTheIconView(self,names):
		for row in self.store:
			if row[self.COL_NAMES] in names:
				self.store.remove(row.iter)
	
	def DeleteImageOfOldDiagrams(self,names):
		for name in names:
			image_file = self.diagrams[name][key_diagram_image]
			if image_file == template_conf_image_no_diagram: continue
			try: os.remove(image_file)
			except OSError: pass
			
	def DeleteDiagramsFromLoadWindow(self, widget, data = None):
		selections = self.iconview.get_selected_items()
		item_numbers = [ x[0] for x in selections ]
		if not item_numbers: return
		if len(item_numbers) == 1:
			message_format = 'Are you sure you want to delete this diagram?'
		else:
			message_format = 'Are you sure you want to delete those diagrams?'
		msgbox = gtk.MessageDialog(parent = None,
								   buttons = gtk.BUTTONS_YES_NO,
								   flags = gtk.DIALOG_MODAL,
								   message_format = message_format,
								   type = gtk.MESSAGE_QUESTION)
		msgbox.set_title("Are You Sure??")
		result = msgbox.run()
		if not result == gtk.RESPONSE_YES:
			msgbox.destroy()
			return
		names = [self.store[number][self.COL_NAMES] for number in item_numbers]
		self.RemoveDiagramsFromTheIconView(names)
		self.DeleteImageOfOldDiagrams(names)
		self.RemoveDiagramsByName(names)
		
		self.SaveConfiguration()
		msgbox.destroy()
	
	def CreateLoadTemplatesWindow(self):
		win = gtk.Window(gtk.WINDOW_TOPLEVEL)
		self.loadWin = win
		win.set_modal(True)
		win.set_default_size(800, 700)
		win.set_title("Load a diagram")
		win.connect("delete-event", self.DeleteLoadWindow)

		accelgroup = gtk.AccelGroup()
		accelgroup.connect_group(ord('W'), gtk.gdk.CONTROL_MASK, 0,
								 lambda *etc: self.DeleteLoadWindow(None))
		win.add_accel_group(accelgroup)
		
		### VBOX ###
		vbox = gtk.VBox()
		vbox.set_spacing(6)
		vbox.set_border_width(6)
		win.add(vbox)
		
		### HBOX ###
		hbox = gtk.HBox()
		vbox.pack_end(hbox, expand = False, fill = False)
		
		### ICONS ###
		## close button
		button = GetButtonFromStock(gtk.STOCK_CLOSE,'Close',self.DeleteLoadWindow)
		hbox.pack_end(button, expand = False, fill = False)
		
		## load button
		button = GetButtonFromStock(gtk.STOCK_ADD,'Load',self.AddLoadWindow)
		hbox.pack_end(button, expand = False, fill = False)
		
		## rename button
		button = GetButtonFromStock(gtk.STOCK_EDIT,'Rename',self.RenameLoadWindow)
		hbox.pack_end(button, expand = False, fill = False)
		
		## remove button
		button = GetButtonFromStock(gtk.STOCK_DELETE,'Delete',self.DeleteDiagramsFromLoadWindow)
		hbox.pack_end(button, expand = False, fill = False)
		
		# backup label
		label = gtk.Label('Backup:')
		hbox.pack_start(label, expand = False, fill = False)
		
		## restore backup button
		button = GetButtonFromStock(gtk.STOCK_DIRECTORY,'Restore',self.RestoreBackupConfigurationCallback)
		hbox.pack_start(button, expand = False, fill = False)
		
		## create backup button
		button = GetButtonFromStock(gtk.STOCK_SAVE,'Create',self.CreateBackupConfiguration)
		hbox.pack_start(button, expand = False, fill = False)
		
		### ICONVIEW ###
		store = gtk.ListStore(str, gtk.gdk.Pixbuf)
		self.store = store
		store.set_sort_column_id(0, gtk.SORT_ASCENDING)
		
		self.COL_IMAGES = 1
		self.COL_NAMES = 0
		iv = gtk.IconView(store)
		self.iconview = iv
		iv.set_selection_mode(gtk.SELECTION_MULTIPLE)
		iv.set_text_column(self.COL_NAMES)
		iv.set_pixbuf_column(self.COL_IMAGES)
		iv.connect('item-activated', self.AddLoadWindow)
		iv.grab_focus()

		sw = gtk.ScrolledWindow()
		sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		vbox.pack_start(sw, expand = True, fill = True)
		sw.add(iv)
		win.show_all()
		while gtk.events_pending(): gtk.main_iteration()
		
		for name in self.diagrams.sections:
			diagram = self.diagrams[name]
			image_name = diagram[key_diagram_image]
			changed = False
			if image_name == template_conf_image_no_diagram or not os.path.isfile(image_name):
				changed = True
				self.CreateImageForDiagram(diagram, name = name, remove_temp = True)
				image_name = diagram[key_diagram_image]
					
			try: pixbuf = gtk.gdk.pixbuf_new_from_file(image_name)
			except:
				if changed == False:
					# this means that the initial image_name exists, but it's broken,
					# since we assume that the image for no diagram gives no error
					self.CreateImageForDiagram(diagram, name = name, remove_temp = True)
					image_name = diagram[key_diagram_image]
					try : pixbuf = gtk.gdk.pixbuf_new_from_file(image_name)
					except : changed = True
				if changed == True:
					pixbuf = gtk.gdk.pixbuf_new_from_file(template_conf_image_no_diagram)
			pixbuf = self.ScaleImage(pixbuf)
			store.append((name, pixbuf))
			while gtk.events_pending(): gtk.main_iteration()
		self.SaveConfiguration()

class DiagramConfiguration:
	def __init__(self,diag_configobj = None):
		if diag_configobj is None:
			self.conf = ConfigObj({})
			self.conf[key_nodes]={}
			self.conf[key_arrows]={}
		else:
			self.conf = diag_configobj
		
		self.Nodes = self.conf[key_nodes]
		self.Arrows = self.conf[key_arrows]
		self.arrows_count = len(self.Arrows.sections)
		
	def AddHorDist(self, value = default_key_hor_distance):
		self.conf[key_hor_distance] = str(value)
	def AddVerDist(self,value = default_key_ver_distance):
		self.conf[key_ver_distance] = str(value)
	def AddCharMargin(self,value = default_key_char_margin):
		self.conf[key_char_margin] = str(value)
	
	def AddColumnsRowsNumber(self,
							cnum = default_key_columns_number,
							rnum = default_key_rows_number):
		self.conf[key_columns_number] = int(cnum)
		self.conf[key_rows_number] = int(rnum)
	
	def AddImage(self,file_name = default_key_diagram_image):
		self.conf[key_diagram_image] = file_name
		
	def AddNode(self,
				label,
				pos = [0,0],
				tex = ''
				):
		
		NewNode = {}
		NewNode[key_nodes_pos] = pos
		NewNode[key_nodes_tex] = tex
		self.Nodes[label] = NewNode
		
	def AddArrow(self,
				source_label,
				target_label,
				inarcamento = default_key_arrows_inarcamento,
				altobasso = default_key_arrows_altobasso,
				tex_label = default_key_arrows_tex_label,
				tratto = default_key_arrows_tratto,
				coda = default_key_arrows_coda,
				decorazione = default_key_arrows_decorazione,
				testa = default_key_arrows_testa,
				preset = default_key_arrows_preset
				):
		NewArrow = {}
		
		for key, value in [
						[key_arrows_tratto, tratto],
						[key_arrows_altobasso, altobasso],
						[key_arrows_coda, coda],
						[key_arrows_tex_label,tex_label],
						[key_arrows_decorazione, decorazione],
						[key_arrows_testa, testa],
						[key_arrows_source_label, source_label],
						[key_arrows_target_label, target_label],
						[key_arrows_inarcamento, inarcamento],
						[key_arrows_preset, preset]
						]:
			NewArrow[key] = value 
		
		self.Arrows[str(self.arrows_count)] = NewArrow
		self.arrows_count+=1


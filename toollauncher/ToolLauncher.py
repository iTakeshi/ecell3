#!/bin/env python
#
# ToolLauncher.py  - to start up E-Cell3 Tool Launcher
#


from config import *
from CopyDirectory import *
from CompileCpp import *
from Eml import *
from ParentWindow import *

from ToolLauncherPreferences import *
from ToolLauncherErrorMessage import *
from ToolLauncherVersion import *
from ZipManager import *
from OutputMessage import *

from shutil import *
import MessageWindowToolLauncher
import re
import sys
import traceback
import string

try:
	import os
	import gtk
	import ConfigParser

except KeyboardInterrupt:
    	pass
	sys.exit(1)



class ToolLauncher(ParentWindow):
	"""MainWindow
	"""

	def __init__( self ):
		"""Constructor 
		- calls parent class's constructor
		- calls openWindow
		"""
		ParentWindow.__init__( self, 'ToolLauncher.glade' )
		self.initPref()
		self.theFileSelectorDlg = gtk.FileSelection( 'Select File' )
		self.theFileSelectorDlg.ok_button.connect('clicked', self.updateFileSelection)
		self.theFileSelectorDlg.cancel_button.connect('clicked', self.hideFileSelectorDlg)

		self.theFileSelectorDlg.connect('delete_event', self.__deleteFileSelection)

		self.conversionDirection = 'em2eml'
		self.theMessageBufferList=gtk.TextBuffer(None)

	def initPref( self ):
		self.thePref = {}
		self.thePrefFile = os.environ['ecell3_prefix']+'/lib' + os.sep+"toollauncher"+os.sep+'launcher.ini'
		if not os.path.isfile( self.thePrefFile ):
			aFile = open( self.thePrefFile, 'w' )
			aFile.write( '[DEFAULT]' )
			aFile.close()

		self.theConfig=ConfigParser.ConfigParser()
		self.theConfig.read( self.thePrefFile )
		self.thePref['ecell3_path'] = os.environ['ecell3_prefix']
		self.thePref['window_open'] = 0
		if self.theConfig.has_option( 'DEFAULT', 'auto_load_pref' ) and \
			self.theConfig.get( 'DEFAULT', 'auto_load_pref') == '1':
			self.assignPrefParameter('save_em')
			self.assignPrefParameter('save_eml')
			self.assignPrefParameter('translate_em')
			self.assignPrefParameter('auto_load_pref')
			self.assignPrefParameter('editor_path')
			self.assignPrefParameter('model_home')
			self.assignPrefParameter('model_path')
			self.assignPrefParameter('programs_path')
		else:
			self.thePref['save_em'] = '1'
			self.thePref['save_eml'] = '1'
			self.thePref['translate_em'] = '0'
			self.thePref['auto_load_pref'] = '1'
			self.thePref['editor_path'] = ""
			self.thePref['model_home'] = ""
			self.thePref['model_path'] = ""
			self.thePref['programs_path'] = ""

	def openWindow( self 
 ):
		"""override parent class' method
		Returns None
		"""
		ParentWindow.openWindow(self)
		self.theHandlerMap =  {
			'save_preferences_menu_activate'        : self.savePreferences ,
			'preferences_menu_activate'             : self.openPreferences ,
			'exit_menu_activate'                    : self.__deleted ,
			'refresh_menu_activate'                 : self.refreshMessage ,
			'output_menu_activate'                  : self.selectFile ,
			'version_menu_activate'                 : self.openVersion ,

			# buttons
			'on_execute_button_clicked'             : self.executeTab ,
			'on_em_file_select_button_clicked'      : self.selectFile ,
			'on_eml_file_select_button_clicked'     : self.selectFile ,
			'on_cpp_file_select_button_clicked'     : self.selectFile ,
			'on_model_path_button_clicked'          : self.selectFile ,
			'on_programs_path_button_clicked'       : self.selectFile ,
			'on_em_file_edit_button_clicked'        : self.editEM ,
			'on_eml_file_edit_button_clicked'       : self.editEML ,
			'on_cpp_file_edit_button_clicked'       : self.editCpp ,
			'on_conversion_direction_button_clicked': self.changeDirection ,
		}

		# -------------------------------------
		# creates MessageWindow 
		# -------------------------------------
		self.theMessageWindow = MessageWindowToolLauncher.MessageWindowToolLauncher( self['textview1'] ) 
		self.theMessageWindow.openWindow()
		self.MessageWindow_attached=True

		self.addHandlers( self.theHandlerMap )
		self.update()
		self.checkPref()


	def savePreferences( self, *arg ):
		"""save the Preferences
		arg[0]   ---  self['save_preferences_menu']
		Return None
		"""
		self.theConfig.read( self.thePrefFile )
		self.savePrefParameter( 'save_em', self.thePref['save_em'] )
		self.savePrefParameter( 'save_eml', self.thePref['save_eml'] )
		self.savePrefParameter( 'translate_em', self.thePref['translate_em'] )
		self.savePrefParameter( 'auto_load_pref', self.thePref['auto_load_pref'] )
		self.savePrefParameter( 'editor_path', self.thePref['editor_path'] )
		self.savePrefParameter( 'model_path', self.thePref['model_path'] )
		self.savePrefParameter( 'model_home', self.thePref['model_home'] )
		self.savePrefParameter( 'programs_path', self.thePref['programs_path'] )
		aFile = open( self.thePrefFile, 'w' )
		self.theConfig.write( aFile )
		aFile.close()

	def savePrefParameter( self, aParameter, aValue ):
		"""save a preference parameter in the launcher.ini file
		"""
		self.theConfig.set( 'DEFAULT', aParameter, aValue )

	def assignPrefParameter( self, aParameter ):
		"""save a preference parameter in the launcher.ini file
		"""
		self.thePref[aParameter] = self.theConfig.get( 'DEFAULT', aParameter )


	# ==========================================================================
	def openPreferences( self, *arg ):
		"""display the Preferences Window
		arg[0]   ---  self['preferences_menu']
		Return None
		"""
		if len( arg ) < 1:
			return None

		self.thePrefWindow = ToolLauncherPreferences( self )
		self.thePrefWindow.openWindow()
	# end of openPreferences


	# ==========================================================================
	def openMessageWindow( self, *arg ):
		"""display the Message Window
		arg[0]   ---  self['message_window_menu']
		Return None
		"""

		if len( arg ) < 1:
			return None
		self.theMsgWindow = ToolLauncherMessageWindow( self )
		self.theMsgWindow.openWindow()

	# end of openMessageWindow


	# ==========================================================================
	def openVersion( self, *arg ):
		"""display the Version Window
		arg[0]   ---  self['version_menu']
		Return None
		"""
		if +len( arg ) < 1:
			return None

		self.theVerWindow = ToolLauncherVersion( self )
		self.theVerWindow.openWindow()

	# end of openVersion


	# ==========================================================================
	def openErrorMessage( self, *arg ):
		"""display the ErrorMessage Window
		arg[0]   ---  self['version_menu']
		Return None
		"""
		self.viewErrorMessage( 'The inputted directory exists.' )

	# end of openErrorMessage


	# ==========================================================================
	def viewErrorMessage( self, msg ):

		gladePath = os.getcwd()
		os.chdir( self.thePref['ecell3_path']+'/lib'+os.sep+"toollauncher" )
		self.theErrorMessage = ToolLauncherErrorMessage( self )
		self.theErrorMessage.openWindow( msg )
		os.chdir( gladePath )

	# end of viewErrorMessage


	# ==========================================================================
	def editEM( self, *arg ):
		"""open EM file using a specified editor
		"""
		self.editFile( self['em_file'].get_text() )

	# end of editEM


	# ==========================================================================
	def editEML( self, *arg ):
		"""open EML file using a specified editor
		"""
		self.editFile( self['eml_file'].get_text() )

	# end of editEML


	# ==========================================================================
	def editEML( self, *arg ):
		"""open EML file using a specified editor
		"""
		self.editFile( self['eml_file'].get_text() )

	# end of editFile


	# ==========================================================================
	def editCpp( self, *arg ):
		"""open Cpp file using a specified editor
		"""
		self.editFile( self['cpp_file'].get_text() )

	# end of editFile


	# ==========================================================================
	def editFile( self, fileName ):

		if self.thePref['editor_path'] == "":
			self.viewErrorMessage( "Please specify the editor path on the preference window." )
		else:
			cmdstr = '\"'+self.thePref['editor_path']+'\" '+fileName
			msg = self.execute( cmdstr )
			if msg == 1:
				errorMsg = "Please specify the editor path on the preference window."
				self.printMessage( errorMsg )
				self.viewErrorMessage( errorMsg )

	# end of editFile


	# ==========================================================================
	def changeDirection( self, *arg ):
		"""
		"""
		if self.conversionDirection == 'em2eml':
			self['conversion_direction_image'].set_from_stock( gtk.STOCK_GO_UP, gtk.ICON_SIZE_BUTTON)
			self.conversionDirection = 'eml2em'
		else:
			self['conversion_direction_image'].set_from_stock( gtk.STOCK_GO_DOWN, gtk.ICON_SIZE_BUTTON)
			self.conversionDirection = 'em2eml'

	# end of changeDirection


	# ==========================================================================
	def execute( self, cmdstr ):

		return os.system( cmdstr )

	# end of execute


	# ==========================================================================
	def executeTab(self, *arg):
		"""
		"""
		if self['launcherNotebook'].get_current_page() == 0:
			self.copyNewModel()
		elif self['launcherNotebook'].get_current_page() == 1:
			if self.conversionDirection == 'em2eml':
				self.em2eml()
			elif self.conversionDirection == 'eml2em':
				self.eml2em()
		elif self['launcherNotebook'].get_current_page() == 2:
			self.compileCpp()
		elif self['launcherNotebook'].get_current_page() == 3:
			self.importModel()
		elif self['launcherNotebook'].get_current_page() == 4:
			self.exportModel()

	# end of executeTab


	# ==========================================================================
	def em2eml(self, *arg):

		eml = Eml( self )
		eml.compileEM( self['em_file'].get_text(), self['eml_file'].get_text() )
		del eml

	# end of em2eml


	# ==========================================================================
	def eml2em(self, *arg):

		eml = Eml( self )
		eml.compileEML( self['eml_file'].get_text(), self['em_file'].get_text() )
		del eml

	# end of eml2em


	def updateFileSelection( self, *arg ):
		"""update the selected path into the respective entry box
		when the OK button of Path Selector dialog is clicked
		"""

		if self.theFileSelectorDlg.get_title() == 'Select EM File':
			self['em_file'].set_text( self.theFileSelectorDlg.get_filename() )

		elif self.theFileSelectorDlg.get_title() == 'Select EML File':
			self['eml_file'].set_text( self.theFileSelectorDlg.get_filename() )

		elif self.theFileSelectorDlg.get_title() == 'Select Cpp File':
			self['cpp_file'].set_text( self.theFileSelectorDlg.get_filename() )

		elif self.theFileSelectorDlg.get_title() == 'Select Model Home Directory':
			self['model_path'].set_text( self.theFileSelectorDlg.get_filename() )

		elif self.theFileSelectorDlg.get_title() == 'Select Conversion Programs Directory':
			directoryName = os.path.dirname( self.theFileSelectorDlg.get_filename() )
			self['programs_path'].set_text( directoryName )

		elif self.theFileSelectorDlg.get_title() == 'Select Output Message File':
			self.outputMessage( self.theFileSelectorDlg.get_filename() )

		self.theFileSelectorDlg.hide( )


	def hideFileSelectorDlg( self, *arg):
		"""hide the Path Selector dialog when the Cancel button is clicked
		"""
		self.theFileSelectorDlg.hide()


	def selectFile( self, *arg ):
		"""when any of the path selection buttons is clicked
		"""
		if len( arg ) < 1:
			return None

		viewFlg = 0

		if self.theFileSelectorDlg == None:
			self.theFileSelectorDlg = gtk.FileSelection( 'Select File' )
			self.theFileSelectorDlg.ok_button.connect('clicked', self.updateFileSelection)
			self.theFileSelectorDlg.cancel_button.connect('clicked', self.hideFileSelectorDlg)

			self.theFileSelectorDlg.connect('delete_event', self.__deleteFileSelection)


		currentDir = os.getcwd()
		if self.thePref['model_path'] != '':
			if os.path.exists( self.thePref['model_path'] ) == False:
#				self.theFileSelectorDlg.set_filename( os.path.join( self.thePref['ecell3_path'], self.thePref['model_home'], +os.sep ) )
				self.theFileSelectorDlg.set_filename( self.thePref['ecell3_path']+self.thePref['model_home']+os.sep )
			else:
				self.theFileSelectorDlg.set_filename( self.thePref['model_path']+os.sep )
		else:
#			self.theFileSelectorDlg.set_filename( self.thePref['ecell3_path']+os.sep+ )
			self.theFileSelectorDlg.set_filename( self.thePref['ecell3_path']+self.thePref['model_home']+os.sep )
#			self.theFileSelectorDlg.set_filename( os.path.join( self.thePref['ecell3_path'], self.thePref['model_home'], +os.sep ) )




		if arg[0] == self['em_file_select_button']:
			self.theFileSelectorDlg.set_title('Select EM File')
		elif arg[0] == self['eml_file_select_button']:
			self.theFileSelectorDlg.set_title('Select EML File')
		elif arg[0] == self['cpp_file_select_button']:
			self.theFileSelectorDlg.set_title('Select Cpp File')
		elif arg[0] == self['model_path_button']:
			self.theFileSelectorDlg.set_title('Select Model Home Directory')
		elif arg[0] == self['programs_path_button']:
			self.theFileSelectorDlg.set_title('Select Conversion Programs Directory')
		elif arg[0] == self['output_menu']:
			if self.theMessageWindow.getMessage() == "":
				viewFlg = -1
				self.printMessage( 'Message window is empty.' )
				self.viewErrorMessage( 'Message window is empty.' )
			else:
				self.theFileSelectorDlg.set_filename( self.getDefaultLogName() )
				self.theFileSelectorDlg.set_title('Select Output Message File')

		if viewFlg == 0:
			self.theFileSelectorDlg.set_modal(True)
			self.theFileSelectorDlg.show_all()

	def deleted( self, *arg ):
		""" When 'delete_event' signal is caught,
		( for example, when [X] button is clicked ),
		delete this window.
		Returns TRUE
		"""
		return self.__deleted( *arg )


	# ==========================================================================
	def __deleted( self, *arg ):
		"""close the window, 
		arg[0] ---  self['exit_menu']
		Return True
		"""
		del self.theFileSelectorDlg
		self.close()
		gtk.mainquit()
		return gtk.TRUE


	# ==========================================================================
	def copyNewModel( self, symlinks=0):

		newDir = self.thePref['ecell3_path']+self.thePref['model_home']+os.sep+self['new_model_name'].get_text()
		copyClass = CopyDirectory( self, newDir )
		copyClass.copyDirectory( )
		self.thePref['model_path'] = newDir
		self.savePreferences()

	# end of copyNewModel



	# ==========================================================================
	def compileCpp(self, *arg):

		# tries to compileCpp
		try:
			if self.thePref['programs_path'] == "":
				self.viewErrorMessage( "Plase set the program path on the preference window." )
			else:
				compileCpp = CompileCpp( self )
				compileCpp.compile( self['cpp_file'].get_text() )

		# catch exceptions
		except:
			anErrorMessage = string.join( traceback.format_exception(sys.exc_type,sys.exc_value,sys.exc_traceback), '\n' )
			self.printMessage(anErrorMessage)
			self.viewErrorMessage( "Compile the \""+self['cpp_file'].get_text()+"\" was failed." )

	# end of compileCpp


	# ==========================================================================
	def importModel( self ):

		# tries to importModel
		try:

			uncompressClass = ZipManager( self )
			modelname = uncompressClass.uncompress( self['model_path'].get_text() )
			self.thePref['model_path'] = self.thePref['ecell3_path']+self.thePref['model_home']+os.sep+modelname
			self.savePreferences()

		# catch exceptions
		except:
			anErrorMessage = string.join( traceback.format_exception(sys.exc_type,sys.exc_value,sys.exc_traceback), '\n' )
			self.printMessage(anErrorMessage)
			msg = "The model \""+self['programs_path'].get_text()+"\" cannot be imported."
			self.viewErrorMessage( msg )
			self.printMessage( msg )

	# end of importModel


	# ==========================================================================
	def exportModel( self ):

		# tries to exportModel
		try:

			compressClass = ZipManager( self )
			compressClass.compress( self['programs_path'].get_text() )

		# catch exceptions
		except:
			anErrorMessage = string.join( traceback.format_exception(sys.exc_type,sys.exc_value,sys.exc_traceback), '\n' )
			self.printMessage(anErrorMessage)
			msg = "The model \""+self['programs_path'].get_text()+"\" cannot be exported."
			self.printMessage( msg )
			self.viewErrorMessage( msg )

	# end of exportModel


	# ==========================================================================
	def outputMessage( self, fileName ):
		# tries to outputMessage
		try:

			outputMsg = OutputMessage( self, fileName, self.theMessageWindow.getMessage() )
			outputMsg.putMessage()

		# catch exceptions
		except:
			anErrorMessage = string.join( traceback.format_exception(sys.exc_type,sys.exc_value,sys.exc_traceback), '\n' )
			self.printMessage(anErrorMessage)

	# end of outputMessage


	# ==========================================================================
	def checkExistFile( self, fileName ):

		returnMsg = -1
		if os.path.exists(fileName) != 0:
			returnMsg = 1
		elif os.path.exists( self.thePref['model_path']+os.sep+fileName ) != 0:
			returnMsg = 2

		return returnMsg

	# end of setFileName


	# ==========================================================================
	def checkExistDir( self, dirName ):

		returnMsg = -1
		if os.path.isdir(dirName) != 0:
			returnMsg = 1
		elif os.path.isdir( self.thePref['model_path']+os.sep+dirName ) != 0:
			returnMsg = 2

		return returnMsg

	# end of setFileName


	# ==========================================================================
	def checkPref ( self ):

		 checkPref = Preferences( self )
		 return checkPref.checkPreferencePash()

	# end of checkPref


	# ==========================================================================
	def setModelPath ( self, fileName ):

		return self.thePref['model_path']+os.sep+fileName

	# end of setFileName


	# ==========================================================================
	def refreshMessage( self, *arg ):
		# tries to refreshMessage
		try:

			self.theMessageWindow.deleteMessage()

		# catch exceptions
		except:
			anErrorMessage = string.join( traceback.format_exception(sys.exc_type,sys.exc_value,sys.exc_traceback), '\n' )
			self.printMessage(anErrorMessage)

	# end of refreshMessage


	# ==========================================================================
	def getDefaultLogName( self ):

		( modelPath, modelName ) = os.path.split( self.thePref['model_path'] )
		return self.thePref['model_path']+os.sep+modelName+".log"

	# end of getDefaultLogName


	# ==========================================================================
	def printMessage( self, aMessage ):

		# prints message on MessageWindow
		self.theMessageWindow.printMessage( aMessage )

	# end of printMessage


	# ==========================================================================
	def __deleteFileSelection( self, *arg ):
		"""deletes FileSelection
		Return None
		"""

		# deletes the reference to FileSelection
		if self.theFileSelectorDlg != None:
			self.theFileSelectorDlg.destroy()
			self.theFileSelectorDlg = None

	# end of __deleteFileSelection


def main():

	aLauncher = ToolLauncher()
	aMainWindow = aLauncher.openWindow()
	gtk.mainloop()

if __name__ == '__main__':
	try:
	    	main()
	except KeyboardInterrupt:
	    	sys.exit(1)
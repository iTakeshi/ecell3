#!/usr/bin/env python

#::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
#
#        This file is part of E-CELL Session Monitor package
#
#                Copyright (C) 1996-2002 Keio University
#
#::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
#
#
# E-CELL is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
# 
# E-CELL is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public
# License along with E-CELL -- see the file COPYING.
# If not, write to the Free Software Foundation, Inc.,
# 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
# 
#END_HEADER
#
# written by Masahiro Sugimoto <sugi@bioinformatics.org> at
# E-CELL Project, Lab. for Bioinformatics, Keio University.
#

import gtk 
from ModelEditor import *
from Constants import *
from Utils import *
from SystemTree import *
from EntityList import *


class FullIDBrowserWindow:

	# ==========================================================================
	def __init__(self, aParentWindow, anEntity ):
		"""Constructor
		aSystemPath string
		returns 
		"""
		# Sets the return number
		self.theModelEditor = aParentWindow.theModelEditor

		# Sets the return number
		self.__value = None

		# Create the Dialog
		self.win = gtk.Dialog( "VariableBrowser", None, gtk.DIALOG_MODAL)
		self.win.connect("destroy",self.destroy)

		# Sets size and position
		self.win.set_border_width(2)
		self.win.set_default_size(300,75)
		self.win.set_position(gtk.WIN_POS_MOUSE)

		# appends ok button
		ok_button = gtk.Button("  OK  ")
		self.win.action_area.pack_start(ok_button,gtk.FALSE,gtk.FALSE,)
		ok_button.set_flags(gtk.CAN_DEFAULT)
		ok_button.grab_default()
		ok_button.show()
		ok_button.connect("clicked",self.oKButtonClicked)


		# appends cancel button
		cancel_button = gtk.Button(" Cancel ")
		self.win.action_area.pack_start(cancel_button,gtk.FALSE,gtk.FALSE)
		cancel_button.show()
		cancel_button.connect("clicked",self.cancelButtonClicked)	

		# Sets title
		
		self.theComponent = ViewComponent( self.win.vbox, 'attachment_box', 'FullIDChooser.glade' )

		# create systree, processlist, propertylist
		self.theSystemTree = SystemTree( self, self.theComponent['SystemTreeFrame'] )
		self.theEntityList = EntityList( self, self.theComponent['EntityListFrame'], ME_VARIABLE_TYPE )

		if getFullIDType( anEntity) == ME_SYSTEM_TYPE:
			aSysID = anEntity
		else:
			aSysID = convertSysPathToSysID( anEntity.split(':')[1] )
		
		self.theSystemTree.changeSelection( [ aSysID ] )
		self.theSystemTree.selectByUser()
		self.theModelEditor.setFullIDBrowser( self )
		self.win.show_all()
		gtk.mainloop()


	# ==========================================================================
	def update( self, aType=None, aFullID=None ):
		if aType == ME_SYSTEM_TYPE:
			self.updateSystemTree( aFullID )
		elif aType == ME_VARIABLE_TYPE:
			self.updateEntityList( aFullID )
		else:
			self.updateEntityList()



	# ==========================================================================
	def updateSystemTree ( self, aSystemFullID = None ):
		"""
		in: string aSystemFullID where changes happened
		"""

		if aSystemFullID != None:
			self.theSystemTree.update ( aSystemFullID )
		self.updateEntityList( aSystemFullID )


	# ==========================================================================
	def updateEntityList ( self, aFullID = None ):
		"""
		in: string aFullID where changes happened
		"""

		displayedFullID = self.theEntityList.getDisplayedSysID() 
		systemTreeFullIDs = self.theSystemTree.getSelectedIDs() 
		if len(systemTreeFullIDs) != 1:
			systemTreeFullID = None
		else:
			systemTreeFullID = systemTreeFullIDs[0]

		# check if new system is selected
		if displayedFullID != systemTreeFullID:
			self.theEntityList.setDisplayedSysID( systemTreeFullID )

		elif displayedFullID == aFullID or aFullID == None:
			self.theEntityList.update( )




	# ==========================================================================
	def oKButtonClicked( self, *arg ):
		"""If OK button clicked or the return pressed, this method is called.
		"""

		# sets the return number
		selectedIDs = self.theLastActiveComponent.getSelectedIDs()
		if len(selectedIDs) == 1:
			selectedID = selectedIDs[0]
		else:
			selectedID = None

		self.__value = selectedID
		self.destroy()


	# ==========================================================================
	def cancelButtonClicked( self, *arg ):
		"""If Cancel button clicked or the return pressed, this method is called.
		"""

		# set the return number
		self.__value = None
		self.destroy()
	

	# ==========================================================================
	def return_result( self ):
		"""Returns result
		"""

		return self.__value


	# ==========================================================================
	def destroy( self, *arg ):
		"""destroy dialog
		"""
		self.theModelEditor.setFullIDBrowser( None )

		self.win.hide()
		gtk.mainquit()

	# ==========================================================================
	def setLastActiveComponent( self, aComponent ):
		self.theLastActiveComponent = aComponent




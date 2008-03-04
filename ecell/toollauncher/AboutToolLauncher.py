#::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
#
#       This file is part of the E-Cell System
#
#       Copyright (C) 1996-2008 Keio University
#       Copyright (C) 2005-2008 The Molecular Sciences Institute
#
#::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
#
#
# E-Cell System is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
# 
# E-Cell System is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public
# License along with E-Cell System -- see the file COPYING.
# If not, write to the Free Software Foundation, Inc.,
# 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
# 
#END_HEADER
#
# AboutToolLauncher.py  - About ToolLauncher Window
#


import gtk
import gtk.glade
import os
import gtk.gdk

from ToolLauncher import *


class  AboutToolLauncher:
	

	def __init__( self, aToolLauncher ):
		"""
		sets up a modal dialogwindow displaying 
		the AboutToolLauncher window
             
		""" 
		self.theToolLauncher = aToolLauncher	
		
		filename = os.environ["TLPATH"] + os.sep + "AboutToolLauncher.glade"
		widgets=gtk.glade.XML(filename,"attachment_box")
		att_box = widgets.get_widget("attachment_box")

		# Create the Dialog
		self.win = gtk.Dialog('AboutToolLauncher' , None)
		self.win.connect("destroy",self.destroy)

		# Sets size and position
		self.win.set_border_width(2)
		self.win.set_default_size(300,75)
		self.win.set_position(gtk.WIN_POS_MOUSE)

		# appends ok button
		ok_button = gtk.Button("  OK  ")
		self.win.action_area.pack_start(ok_button,False,False,)
		ok_button.set_flags(gtk.CAN_DEFAULT)
		ok_button.grab_default()
		ok_button.show()
		ok_button.connect("clicked",self.destroy)
		self.win.vbox.pack_start( att_box )
		# Sets title
		self.win.set_title('About ToolLauncher')
		aPixbuf16 = gtk.gdk.pixbuf_new_from_file(
                           os.environ['TLPATH'] + os.sep + "toollauncher.png")
		aPixbuf32 = gtk.gdk.pixbuf_new_from_file(
                           os.environ['TLPATH'] + os.sep + "toollauncher32.png")
		self.win.set_icon_list(aPixbuf16, aPixbuf32)

		widgets.get_widget("label1").set_markup("<b>E-Cell ToolLauncher Version 1.0 </b>")
		self.win.show_all()
		
		self.theToolLauncher.toggleAboutToolLauncher(True,self)
		

	def destroy( self, *arg ):
		"""destroy dialog
		"""
		
		self.win.destroy()

		self.theToolLauncher.toggleAboutToolLauncher(False,None)
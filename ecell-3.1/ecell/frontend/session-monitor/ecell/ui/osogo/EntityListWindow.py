#::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
#
#       This file is part of the E-Cell System
#
#       Copyright (C) 1996-2010 Keio University
#       Copyright (C) 2005-2009 The Molecular Sciences Institute
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

import operator
import re
import copy
import gtk
import gobject

from ecell.ecssupport import *

from ecell.ui.osogo.OsogoWindow import *
from ecell.ui.osogo.PluginInstanceSelection import *
from ecell.ui.osogo.FullPNQueue import *


class EntityListWindow(OsogoWindow):
    '''EntityListWindow
    '''

    DEFAULT_PLUGIN = 'TracerWindow'

    DEFAULT_VARIABLE_PROPERTY = 'Value'
    DEFAULT_PROCESS_PROPERTY = 'Activity'

    COMMON_COLUMN_INFO_MAP= {
        'ID':        gobject.TYPE_STRING,
        'Classname': gobject.TYPE_STRING,
        'Path':      gobject.TYPE_STRING
        }

    VARIABLE_COLUMN_INFO_MAP= {
        # Name:      Type
        'Value':     gobject.TYPE_STRING
        }

    PROCESS_COLUMN_INFO_MAP= {
        'Activity':  gobject.TYPE_STRING
        }

    VARIABLE_COLUMN_LIST = [ 'ID', 'Value', 'Classname', 'Path' ]
    PROCESS_COLUMN_LIST = [ 'ID', 'Activity', 'Classname', 'Path' ]


    def __init__( self, session, rootWidget, aStatusbar ):
        '''Constructor
        session   --   a reference to GtkSessionMonitor
        '''

        # call superclass's constructor 
        OsogoWindow.__init__( self, session, rootWidget=rootWidget )

        # initialize parameters
        self.theSelectedFullPNList = []
        self.theCheckedFullIDList = []

        self.searchString = ''

        # set status bar
        self.theStatusbar = aStatusbar

        # fix me
        self.thePluginManager = session.thePluginManager
        self.thePropertyWindow = None
        self.thePluginInstanceSelection = None

        

    def openWindow( self ):

        # call superclass's openWindow
        OsogoWindow.openWindow( self )

        self['search_method'].set_property('active', 0)
        self['search_scope'].set_property('active', 0)
        
        # add handers
        self.addHandlers( { 
            # system tree
            #			'on_system_tree_cursor_changed' :\
            #			self.updateSystemSelection,\
            'on_system_tree_button_press_event' : self.popupMenu,\
            # entity list
            #			'on_process_tree_cursor_changed': self.selectProcess,\
            #			'on_variable_tree_cursor_changed':self.selectVariable,\
            
            'on_view_button_clicked': self.createPluginWindow,\
            'on_log_all_button_clicked': self.logAllEntities,\
            'on_clear_checked_button_clicked': self.clearCheckboxes,
            'on_variable_tree_button_press_event': self.popupMenu,\
            'on_process_tree_button_press_event': self.popupMenu,\
            # search 
            'on_search_button_clicked': self.pushSearchButton,\
            'on_search_entry_key_press_event': self.keypressOnSearchEntry,\
            'on_clear_button_clicked': self.pushClearButton, 
            'on_search_scope_changed': self.searchScopeChanged
            } )

        self.entitySelected = False
        self.theLastSelectedWindow = None
        self.thePopupMenu = gtk.Menu()
        self.donotHandle = False
        self.systemTree   = self['system_tree']
        self.processTree  = self['process_tree']
        self.variableTree = self['variable_tree']

        # --------------------------------------------
        # initialize components
        # --------------------------------------------
        self.__initializeSystemTree()
        self.systemTreeConstructed = False
        if self.theSession.theModelWalker != None:
            self.reconstructSystemTree()
 
        self.__initializeProcessTree()
        self.__initializeVariableTree()
        self.__initializeSelection()
        self.__initializePluginWindowOptionMenu()

        aFullPN = convertFullIDToFullPN( createFullID ( 'System::/' ) )
        self.theQueue = FullPNQueue( self["navigator_area"] , [ aFullPN ] )

        self.theQueue.registerCallback( self.doSelection )        
        self.__initializePropertyWindow()
        self.__initializePopupMenu()

        # --------------------------------------------
        # initialize buffer
        # --------------------------------------------
        self.theSelectedEntityList = []
        self.theSelectedPluginInstanceList = []

        # --------------------------------------------
        # initialize Add to Board button
        # --------------------------------------------
        self.CloseOrder = False
        self.updateButtons()






    def updateButtons( self ):
        if ( self.theSession.theModelWalker != None ):
            self['search_button'].set_sensitive(True)
            self['view_button'].set_sensitive(True)
            self['log_all_button'].set_sensitive(True)
            self['search_entry'].set_sensitive(True)
            self['plugin_optionmenu'].set_sensitive(True)

            self['clear_checked_button'].set_sensitive( len( self.theCheckedFullIDList ) != 0 )

        else:
            self['search_button'].set_sensitive(0)
            self['view_button'].set_sensitive(0)
            self['log_all_button'].set_sensitive(0)
            self['search_entry'].set_sensitive(0)
            self['plugin_optionmenu'].set_sensitive(0)

    def getQueue( self ):
        return self.theQueue


    def deleted( self, *arg ):
        self.close()


    def close( self ):
        if self.CloseOrder:
            return
        self.CloseOrder = True

        if self.thePluginInstanceSelection != None:
            self.thePluginInstanceSelection.deleted()
            self.thePluginInstanceSelection = None

        if self.theSession != None:
            self.theSession.deleteEntityListWindow( self )
            OsogoWindow.close(self)


    def deletePluginInstanceSelection( self, *arg ):
        """sets 'delete_event' as 'hide_event'
        """

        # hide this window
        self['PluginInstanceSelection'].hide_all()

        # set 'delete_event' uneffective
        return True


    def __initializeSystemTree( self ):
        """initialize SystemTree
        """
        self.lastSelectedSystem = ""
        treeStore = gtk.TreeStore( gobject.TYPE_STRING )
        self.theSysTreeStore = treeStore
        column = gtk.TreeViewColumn( 'System Tree',
                                     gtk.CellRendererText(),
                                     text=0 )
        column.set_visible( True )
        self.systemTree.append_column(column)

        self.systemTree.set_model( treeStore )

        self.processTree.set_search_column( 0 )
        self.theSysSelection =  self.systemTree.get_selection()

    def __initializeSelection( self ):
        selection = self.systemTree.get_selection()
        selection.set_mode( gtk.SELECTION_MULTIPLE )
        selection.connect( 'changed', self.selectSystem )
        selection = self.processTree.get_selection()
        selection.set_mode( gtk.SELECTION_MULTIPLE )
        selection.connect( 'changed', self.selectProcess )
        selection = self.variableTree.get_selection()
        selection.set_mode( gtk.SELECTION_MULTIPLE )
        selection.connect( 'changed', self.selectVariable )

    def __initializeProcessTree( self ):
        """initialize ProcessTree
        """

        columnTypeList = [ gobject.TYPE_BOOLEAN ]
        renderer = gtk.CellRendererToggle()
        renderer.set_property( 'activatable', True )
        renderer.connect( 'toggled', self.__toggleCheckbox, self.processTree )
        checkboxColumn = gtk.TreeViewColumn( '', renderer, active=0 )
        checkboxColumn.set_reorderable( True )
        checkboxColumn.set_sort_column_id( 0 )
        self.processTree.append_column( checkboxColumn )

        for i in range( len( self.PROCESS_COLUMN_LIST ) ):
            title = self.PROCESS_COLUMN_LIST[ i ]

            try:
                type = self.PROCESS_COLUMN_INFO_MAP[ title ]
            except:
                type = self.COMMON_COLUMN_INFO_MAP[ title ]

            column = gtk.TreeViewColumn( title, 
                                         gtk.CellRendererText(), 
                                         text=i+1 )
            column.set_reorderable( True )
            column.set_sort_column_id( i+1 )

            self.processTree.append_column( column )
            columnTypeList.append( type )
            if type == gobject.TYPE_FLOAT:
                column.set_alignment( 1.0 )
                column.get_cell_renderers()[0].set_property( 'xalign', 1.0 )

        self.processTree.set_search_column( 1 )

        model = gtk.ListStore( *columnTypeList )
        self.processTree.set_model( model )


    def __initializeVariableTree( self ):
        """initializes VariableTree
        """

        columnTypeList = [ gobject.TYPE_BOOLEAN ]
        renderer = gtk.CellRendererToggle()
        renderer.set_property( 'activatable', True )
        renderer.connect( 'toggled', self.__toggleCheckbox, self.variableTree )
        checkboxColumn = gtk.TreeViewColumn( '', renderer, active=0 )
        checkboxColumn.set_reorderable( True )
        checkboxColumn.set_sort_column_id( 0 )
        self.variableTree.append_column( checkboxColumn )

        for i in range( len( self.VARIABLE_COLUMN_LIST ) ):
            title = self.VARIABLE_COLUMN_LIST[ i ]

            try:
                type = self.VARIABLE_COLUMN_INFO_MAP[ title ]
            except:
                type = self.COMMON_COLUMN_INFO_MAP[ title ]

            renderer = gtk.CellRendererText()
            if title == EntityListWindow.DEFAULT_VARIABLE_PROPERTY:
                renderer.connect( 'edited', self.editVariableColumn, i+1 )
                renderer.set_property( 'editable', True )

            column = gtk.TreeViewColumn( title, renderer, text=i+1 )
            column.set_reorderable( True )
            column.set_sort_column_id( i+1 )
            self.variableTree.append_column( column )
            columnTypeList.append( type )
            if type == gobject.TYPE_FLOAT:
                column.set_alignment( 1.0 )
                column.get_cell_renderers()[0].set_property( 'xalign', 1.0 )

        self.variableTree.set_search_column( 1 )

        model = gtk.ListStore( *columnTypeList )
        self.variableTree.set_model( model )

    def editVariableColumn( self, widget, path, new_text, col ):

        if self.theSession.theModelWalker == None:
            return

        model = self.variableTree.get_model()

        iter = model.get_iter( path )
        fullid = model.get_data( model.get_string_from_iter( iter ) )
        propertyName = EntityListWindow.VARIABLE_COLUMN_LIST[ col-1 ]
        # propertyName = self.variableTree.get_column( col-1 ).get_title()

        if propertyName != EntityListWindow.DEFAULT_VARIABLE_PROPERTY:
            return

        try:
            value = float( new_text )
        except:
            message = '[%s] is not a float number.' % new_text
            dialog = ConfirmWindow( OK_MODE, message, 'Error!' )
            return

        fullpn = createFullPN( '%s:%s' % ( fullid, propertyName ) )
        self.thePropertyWindow.setValue( fullpn, value )

    def __initializePluginWindowOptionMenu( self ):
        """initializes PluginWindowOptionMenu
        """

        aPluginWindowNameList = []
        aMenu = gtk.Menu()

        for aPluginWindowName in self.thePluginManager.thePluginMap.keys():

            aButton = gtk.Button()
            aMenuItem = gtk.MenuItem(aPluginWindowName)

            if aPluginWindowName == self.DEFAULT_PLUGIN:
                aMenu.prepend( aMenuItem )
            else:
                aMenu.append( aMenuItem )

        self['plugin_optionmenu'].set_menu(aMenu)
        self['plugin_optionmenu'].show_all()





    def __initializePropertyWindow( self ):
        if self.thePropertyWindow != None:
            return
        self.thePropertyWindow= self.thePluginManager.createInstance(
            'PropertyWindow',\
            [(SYSTEM, '', '/', '')],\
            rootWidget= 'top_frame',\
            parent= self ) 

        if ( self.theStatusbar != None ):
            self.thePropertyWindow.setStatusBar( self.theStatusbar )

        aPropertyWindowTopVBox = self.thePropertyWindow['top_frame']
        self['property_area'].add( aPropertyWindowTopVBox )
        self.thePropertyWindow.setParent( self )



    def __initializePopupMenu( self ):
        """Initialize popup menu
        Returns None
        [Note]:In this method, only 'PluginWindow type' menus, 'Create 
        Logger' menu and 'Add to Board' menu are created. 
        The menus of PluginWindow instances are appended
        dinamically in self.popupMenu() method.
        """

        # ------------------------------------------
        # menus for PluginWindow
        # ------------------------------------------

        # creaets menus of PluginWindow
        for aPluginWindowType in self.thePluginManager.thePluginMap.keys(): 
            aMenuItem = gtk.MenuItem( aPluginWindowType )
            aMenuItem.connect('activate', self.createPluginWindow )
            aMenuItem.set_name( aPluginWindowType )
            if aPluginWindowType == self.DEFAULT_PLUGIN:
                self.thePopupMenu.prepend( aMenuItem )
            else:
                self.thePopupMenu.append( aMenuItem )

        # appends separator
        self.thePopupMenu.append( gtk.MenuItem() )

        # ------------------------------------------
        # menus for Logger
        # ------------------------------------------
        # creates menu of Logger
        aLogMenuString = "Create Logger"
        aMenuItem = gtk.MenuItem( aLogMenuString )
        aMenuItem.connect('activate', self.createLogger )
        aMenuItem.set_name( aLogMenuString )
        self.thePopupMenu.append( aMenuItem )

        # appends separator
        self.thePopupMenu.append( gtk.MenuItem() )

        # ------------------------------------------
        # supporting selection
        # ------------------------------------------

        aMutatorString = "Select Mutators"
        aMenuItem = gtk.MenuItem( aMutatorString )
        aMenuItem.connect( 'activate', self.selectEffectors, 0 )
        aMenuItem.set_name( aMutatorString )
        self.thePopupMenu.append( aMenuItem )

        anAccessorString = "Select Accessors"
        aMenuItem = gtk.MenuItem( anAccessorString )
        aMenuItem.connect( 'activate', self.selectEffectors, 1 )
        aMenuItem.set_name( anAccessorString )
        self.thePopupMenu.append( aMenuItem )

#         firstid = aSelectedRawFullPNList[ 0 ]
#         entityType = convertFullPNToFullID( firstid )[ 0 ]
#         if entityType != VARIABLE and entityType != PROCESS:
#             pass

        # appends separator
        self.thePopupMenu.append( gtk.MenuItem() )

        # ------------------------------------------
        # menus for Bord
        # ------------------------------------------
        # creates menu of Board
        aSubMenu = gtk.Menu()

        for aPluginWindowType in self.thePluginManager.thePluginMap.keys(): 
            aMenuItem = gtk.MenuItem( aPluginWindowType )
            aMenuItem.connect('activate', self.addToBoard )
            aMenuItem.set_name( aPluginWindowType )
            if aPluginWindowType == self.DEFAULT_PLUGIN:
                aSubMenu.prepend( aMenuItem )
            else:
                aSubMenu.append( aMenuItem )

        aMenuString = "Add to Board"
        aMenuItem = gtk.MenuItem( aMenuString )
        aMenuItem.set_name( aLogMenuString )
        aMenuItem.set_submenu( aSubMenu )
        self.thePopupMenu.append( aMenuItem )
        self.theBoardMenu = aMenuItem

        # appends separator
        self.thePopupMenu.append( gtk.MenuItem() )

        # ------------------------------------------
        # menus for submenu
        # ------------------------------------------
        self.thePopupSubMenu = None  

    def __openPluginInstanceSelectionWindow( self, *arg ):
        """open PluginInstanceSelectionWindow
        Returns None
        """

        if self.thePluginInstanceSelection != None:
            self.thePluginInstanceSelection.present()

        else:

            self.thePluginInstanceSelection = \
            PluginInstanceSelection( self.theSession, self )
            self.thePluginInstanceSelection.openWindow()

            # updates list of PluginInstance
            self.thePluginInstanceSelection.update()




    def __updatePluginInstanceSelectionWindow2( self ):
        """updates list of PluginInstanceSelectionWindow
        Returns None
        """

        self.thePluginInstanceListStore.clear()
        aPluginInstanceList = self.thePluginManager.thePluginTitleDict.keys()

        for aPluginInstance in aPluginInstanceList:
            if aPluginInstance.theViewType == MULTIPLE:
                aPluginInstanceTitle = self.thePluginManager.thePluginTitleDict[aPluginInstance]
                iter = self.thePluginInstanceListStore.append()
                self.thePluginInstanceListStore.set_value( iter, 0, aPluginInstanceTitle )
                self.thePluginInstanceListStore.set_data( aPluginInstanceTitle, aPluginInstanceTitle )


    def closePluginInstanceSelectionWindow( self, *arg ):
        """closes PluginInstanceSelectionWindow
        Returns None
        """

        if self.thePluginInstanceSelection != None:
            #self.thePluginInstanceSelection['PluginInstanceSelection'].hide_all()
            self.thePluginInstanceSelection.deleted()
            self.thePluginInstanceSelection = None



    def popupMenu( self, aWidget, anEvent ):
        """displays popup menu only when right button is pressed.
        aWidget   --  EntityListWindow
        anEvent   --  an event
        Returns None
        [Note]:creates and adds submenu that includes menus of PluginWindow instances
        """

        # When right button is pressed
        if anEvent.type == gtk.gdk._2BUTTON_PRESS:

            aSelectedRawFullPNList = self.__getSelectedRawFullPNList()
            aPluginWindowType = self['plugin_optionmenu'].get_children()[0].get()

            # When no FullPN is selected, displays error message.
            if aSelectedRawFullPNList  != None:
                if len( aSelectedRawFullPNList ) == 0:

                    aMessage = 'No entity is selected.'
                    aDialog = ConfirmWindow(OK_MODE,aMessage,'Error!')
                    self.thePropertyWindow.showMessageOnStatusBar(aMessage)
                    return False

            # self.theQueue.pushFullPNList( aSelectedRawFullPNList )
            # self.thePluginManager.createInstance( aPluginWindowType, self.thePropertyWindow.theFullPNList() )

#             if self.thePropertyWindow.theFullPNList() \
#                     != aSelectedRawFullPNList:
#                 raise RuntimeError, 'Inconsistent internal lists: (%s == %s)' % ( self.thePropertyWindow.theFullPNList(), aSelectedRawFullPNList )

            self.thePluginManager.createInstance( aPluginWindowType, aSelectedRawFullPNList )


        # When right button is pressed
        if anEvent.type == gtk.gdk.BUTTON_PRESS and anEvent.button == 3:

            if self.theSession.getWindow('BoardWindow').exists():
                self.theBoardMenu.set_sensitive(True)
            else:
                self.theBoardMenu.set_sensitive(False)

            # removes previous sub menu
            # When PopupMenu was displayed last time without PluginWindows'
            # menus, the buffer (self.thePopupSubMenu) is None.
            if self.thePopupSubMenu != None:
                self.thePopupMenu.remove( self.thePopupSubMenu )

            if len(self.thePluginManager.theInstanceList)!=0:

                # creates submenu
                aSubMenu = gtk.Menu()

                # creaets menus of PluginWindow instances
                aMenuItemFlag = False
                for aPluginInstance in self.thePluginManager.theInstanceList: 

                    if aPluginInstance.theViewType == MULTIPLE:
                        aTitle = aPluginInstance.getTitle()
                        aMenuItem = gtk.MenuItem( aTitle )
                        aMenuItem.connect('activate', self.appendData )
                        aMenuItem.set_name( aTitle )
                        aSubMenu.append( aMenuItem )
                        aMenuItemFlag = True

                if aMenuItemFlag:
                    # creates parent MenuItem attached created submenu.
                    aMenuString = "Append data to"
                    aMenuItem = gtk.MenuItem( aMenuString )
                    aMenuItem.set_submenu( aSubMenu )

                    # appends parent MenuItem to PopupMenu
                    self.thePopupMenu.append( aMenuItem )

                    # saves this submenu set to buffer (self.thePopupSubMenu)
                    self.thePopupSubMenu = aMenuItem

            # displays all items on PopupMenu
            self.thePopupMenu.show_all() 

            # displays popup menu
            self.thePopupMenu.popup(None,None,None,anEvent.button,anEvent.time)


#    def reset( self ):
#
#        self.reconstructSystemTree()
#        self.reconstructLists()
#        self.update()


    def update( self ):
        """overwrite superclass's method
        updates this window and property window
        Returns None
        """
        if self.theSession.theModelWalker == None:
            return
        elif not self.systemTreeConstructed:
            self.reconstructSystemTree()
            
        # updates this window
        if not self.exists():
            return
        OsogoWindow.update(self)

        # updates property window
        self.thePropertyWindow.update()

        # update PluginInstanceSelectionWindow
        if self.thePluginInstanceSelection != None:
            self.thePluginInstanceSelection.update()

        self.updateLists()



    def constructSystemTree( self, parent, fullID ):

        # System tree

        newlabel = fullID[ID] 

        systemStore = self.systemTree.get_model()
        iter  = systemStore.append( parent )
        systemStore.set_value( iter, 0, newlabel )
        key = str( systemStore.get_path( iter ) )
        systemStore.set_data( key, fullID )

        systemPath = createSystemPathFromFullID( fullID )
        systemList = self.theSession.getEntityList( 'System', systemPath )
        systemListLength = len( systemList )

        if  systemListLength == 0:
            return

        for systemID in systemList:
            newSystemFullID = ( SYSTEM, systemPath, systemID )
            self.constructSystemTree( iter, newSystemFullID )

            path = systemStore.get_path( iter )
            if systemListLength < 6 and len( path ) < 6:
                self.systemTree.expand_row( path, True )


    def reconstructSystemTree( self ):

        rootSystemFullID = createFullID( 'System::/' )
        self.constructSystemTree( None, rootSystemFullID )
        self.systemTreeConstructed = True



    def reconstructLists( self ):
        selectedSystemList = self.getSelectedSystemList()

        if len( selectedSystemList ) == 0:
            return
        if self.entitySelected:
            return 
        # Variable list
        self.reconstructEntityList( 'Variable', self.variableTree,\
                                    selectedSystemList,\
                                    self.VARIABLE_COLUMN_LIST,\
                                    self.VARIABLE_COLUMN_INFO_MAP )

        # Process list
        self.reconstructEntityList( 'Process', self.processTree,\
                                    selectedSystemList,\
                                    self.PROCESS_COLUMN_LIST,\
                                    self.PROCESS_COLUMN_INFO_MAP )
        self.updateListLabels()

        

    def reconstructEntityList( self, type, view, systemList, columnList,\
                               columnInfoList ):
        # get the entity list in the selected system(s)
        typeID = ENTITYTYPE_DICT[ type ]

        fullIDList = []
        for systemFullID in systemList:

            systemPath = createSystemPathFromFullID( systemFullID )

            idList = self.theSession.getEntityList( type, systemPath )
            fullIDList += [ ( typeID, systemPath, id ) for id in idList ]


        entityStore = view.get_model()

        # clear the store
        donotHandle = self.donotHandle
        self.donotHandle = True
        entityStore.clear()
        self.donotHandle = donotHandle

        #		columnList = view.get_columns()
        # re-create the list
        for fullID in fullIDList:

            ID = fullID[2]
            # temporary hack for the entity searching.
            # this can be like this in python 2.3 or above:
            #    if not self.searchString in ID:
            if ID.find( self.searchString ) < 0:
                continue

            fullIDString = createFullIDString( fullID )

            stub = self.theSession.createEntityStub( fullIDString )

            if fullID in self.theCheckedFullIDList:
                valueList = [ True ]
            else:
                valueList = [ False ]

            for title in columnList:

                if title in self.COMMON_COLUMN_INFO_MAP.keys():
                    if title == 'ID':
                        value = ID
                    elif title == 'Classname':
                        value = stub.getClassname()
                    elif title == 'Path':
                        value =  fullID [SYSTEMPATH]
                    else:
                        raise "Unexpected error: invalid column title."
                else:
                    value = stub[ title ] # if not common, it's entity property

                valueList.append( value )

            iter = entityStore.append( valueList )
            iterString = entityStore.get_string_from_iter( iter )
            entityStore.set_data( iterString, fullIDString )


    def doSelection( self, aFullPNList ):
        if self.theSession.theModelWalker == None:
            return
        self.doSelectSystem( aFullPNList ) 
        self.doSelectProcess( aFullPNList )
        self.doSelectVariable( aFullPNList )


    def doSelectSystem( self, aFullPNList ):

        targetFullIDList = []
        if aFullPNList[0][TYPE] != SYSTEM:
            targetFullIDList += [ createFullIDFromSystemPath( aFullPN[SYSTEMPATH] )  for aFullPN in aFullPNList ]
        else:
            for aFullPN in aFullPNList:
                targetFullIDList.append( convertFullPNToFullID( aFullPN ) )

        # if to slow there should be a check whether this is needed in all cases
        donotHandle = self.donotHandle
        self.donotHandle = True
        self.theSysSelection.unselect_all()
        self.theSysSelection.set_mode( gtk.SELECTION_MULTIPLE )

        for  targetFullID in targetFullIDList:
            #doselection
            targetPath = createSystemPathFromFullID( targetFullID )
            anIter = self.getSysTreeIter( targetPath )

            aPath = self.theSysTreeStore.get_path( anIter )
            self.__expandRow( aPath )
            self.theSysSelection.select_iter( anIter )

        self.donotHandle = donotHandle

        self.reconstructLists()


    def getSysTreeIter( self, aSysPath, anIter = None ):
        """
        returns iter of string aSysPath or None if not available
        """
        systemStore = self.systemTree.get_model()
        if anIter == None:
            anIter = systemStore.get_iter_first()
            if aSysPath == '/':
                return anIter
            else:
                aSysPath = aSysPath.strip ('/')

        # get first path string
        anIndex = aSysPath.find( '/' )
        if anIndex == -1:
            anIndex = len( aSysPath )
        firstTag = aSysPath[ 0 : anIndex ]

        # create remaining path string
        aRemainder = aSysPath[ anIndex + 1 : len( aSysPath ) ]

        # find iter of first path string
        numChildren = systemStore.iter_n_children( anIter )
        isFound = False
        for i in range( 0, numChildren):
            childIter = systemStore.iter_nth_child( anIter, i )

            if systemStore.get_value( childIter, 0) == firstTag:
                isFound = True
                break

        # if not found return None
        if not isFound:
            return None

        # if remainder is '' return iter
        if aRemainder == '':
            return childIter

        # return recursive remainder with iter
        return self.getSysTreeIter( aRemainder, childIter )


    def __expandRow( self, aPath ):
        """
        in: gtktreePath aPath
        """
        if not self.systemTree.row_expanded( aPath ):

            # get iter
            anIter = self.theSysTreeStore.get_iter( aPath)

            # get parent iter
            parentIter = self.theSysTreeStore.iter_parent( anIter )

            # if iter is root expand
            if parentIter != None:

                # if not get parent path
                parentPath = self.theSysTreeStore.get_path( parentIter )
                
                # expand parentpath
                self.__expandRow( parentPath )
                
            # expand this path
            self.systemTree.expand_row( aPath, False )


    def selectListIter( self, aListStore, aSelection, anIDList ):

        anIter = aListStore.get_iter_first()
        while anIter != None:
            if aListStore.get_value( anIter, 1 ) in anIDList:
                donotHandle = self.donotHandle
                self.donotHandle = True
                aSelection.select_iter( anIter )
                self.donotHandle = donotHandle

            anIter = aListStore.iter_next( anIter )

    
    def doSelectProcess( self, aFullPNList ):
        #unselect all

        selection = self.processTree.get_selection()
        listStore = self.processTree.get_model()
        selection.unselect_all()
        selection.set_mode(gtk.SELECTION_MULTIPLE )

        if aFullPNList[0][TYPE] == PROCESS:
            # do select
            self.selectListIter( listStore, selection, self.__createIDList( aFullPNList ) )

    
    def __createIDList( self, aFullPNList ):
        anIDList = []
        for aFullPN in aFullPNList:
            anIDList.append( aFullPN[ID] )
        return anIDList
    
    
    def doSelectVariable( self, aFullPNList ):
        #unselect all
        selection = self.variableTree.get_selection()
        listStore = self.variableTree.get_model()
        selection.unselect_all()
        selection.set_mode(gtk.SELECTION_MULTIPLE )

        if aFullPNList[0][TYPE] == VARIABLE:
            # do select
            self.selectListIter( listStore, selection, self.__createIDList( aFullPNList ) )

    def selectSystem( self, obj ):
        if self.donotHandle:
            return

        # select the first selected System in the PropertyWindow
        systemFullIDList = self.getSelectedSystemList()
        fullPNList = []
        for systemFullID in systemFullIDList:
            fullPNList.append( convertFullIDToFullPN( systemFullID ) )
        self.donotHandle = True
        self.theQueue.pushFullPNList(  fullPNList  )
        self.donotHandle = False




    def getSelectedSystemList( self ):
        '''
        Return - a list of FullIDs of the currently selected Systems.
        '''

        # get system ID from selected items of system tree,
        # and get entity list from session

        systemList = []

        selection = self.systemTree.get_selection()
        selectedSystemTreePathList = selection.get_selected_rows()
        if selectedSystemTreePathList == None:
            return []
        selectedSystemTreePathList = selectedSystemTreePathList[1]
        
        systemStore = self.systemTree.get_model()


        for treePath in selectedSystemTreePathList:

            systemFullID = systemStore.get_data( str( treePath ) )
            systemList.append( systemFullID )

        return systemList


    def updateLists( self ):
        '''
        This method updates property values shown in the list of
        Variables and Processes.
        '''

        self.updateEntityList( 'Process', self.processTree.get_model(),\
                               self.PROCESS_COLUMN_LIST,\
                               self.PROCESS_COLUMN_INFO_MAP )

        self.updateEntityList( 'Variable', self.variableTree.get_model(),\
                               self.VARIABLE_COLUMN_LIST,\
                               self.VARIABLE_COLUMN_INFO_MAP )
                               

    def updateEntityList( self, type, model, columnList, columnInfoMap ): 

        propertyColumnList= [ ( columnList.index( i ), i )\
                              for i in columnInfoMap.keys() ]

        for row in model:

            iter = row.iter
            fullIDString = model.get_data( model.get_string_from_iter( iter ) )
            fullid = createFullID( fullIDString )
            stub = self.theSession.createEntityStub( fullIDString )

            columnList = []

            if fullid in self.theCheckedFullIDList:
                columnList += [ 0, True ]

            for propertyColumn in propertyColumnList:
                newValue = stub[ propertyColumn[ 1 ] ]
                columnList += [ propertyColumn[ 0 ] + 1, "%g" % ( newValue ) ] 

            model.set( iter, *columnList )


    def updateListLabels( self ):

        self.__updateViewLabel( 'Variable', self['variable_label'],\
                                self.variableTree )
        self.__updateViewLabel( 'Process', self['process_label'],\
                                self.processTree )
        self.__updateViewLabel( 'System', self['system_label'],\
                                self.systemTree )

    def __updateViewLabel( self, type, label, view ):

        shownCount    = len( view.get_model() )
        selectedCount = view.get_selection().count_selected_rows()
        labelText = type + ' (' + str( selectedCount ) + '/' + \
                    str( shownCount ) + ')' 
        label.set_text( labelText )



    def selectProcess( self, selection ):

        if self.donotHandle:
            return
        self.entitySelected = True
        self.theLastSelectedWindow = "Process"

        # clear fullPN list
        self.theSelectedFullPNList = []

        # get selected items
        selection.selected_foreach(self.process_select_func)

        if len(self.theSelectedFullPNList)>0:
            self.donotHandle = True
            self.theQueue.pushFullPNList( self.theSelectedFullPNList )
            self.donotHandle = False
        # clear selection of variable list
#        self.variableTree.get_selection().unselect_all()

        self.updateListLabels()
        self.entitySelected = False
        
    def selectVariable( self, selection ):
        if self.donotHandle:
            return
        self.entitySelected = True
        self.theLastSelectedWindow = "Variable"

        # clear fullPN list
        self.theSelectedFullPNList = []

        # get selected items
        selection.selected_foreach(self.variable_select_func)

        if len(self.theSelectedFullPNList)>0:
            self.donotHandle = True
            self.theQueue.pushFullPNList( self.theSelectedFullPNList )
            self.donotHandle = False

        # clear selection of process list
#        self.processTree.get_selection().unselect_all()

        self.updateListLabels()
        self.entitySelected = False

    def variable_select_func(self,tree,path,iter):
        '''function for variable list selection

        Return None
        '''

        model = self.variableTree.get_model()
        data = model.get_data( model.get_string_from_iter( iter ) )
        entityFullID = createFullID( data )
        entityFullPN = entityFullID + ( self.DEFAULT_VARIABLE_PROPERTY, )
        self.theSelectedFullPNList.append( entityFullPN )


    def process_select_func(self,tree,path,iter):
        '''function for process list selection

        Return None
        '''
        
        model = self.processTree.get_model()
        data = model.get_data( model.get_string_from_iter( iter ) )
        entityFullID = createFullID( data )
        entityFullPN = entityFullID + ( self.DEFAULT_PROCESS_PROPERTY, )
        self.theSelectedFullPNList.append( entityFullPN )



    def createPluginWindow( self, *obj ) :
        """creates new PluginWindow instance(s)
        *obj   --  gtk.MenuItem on popupMenu or gtk.Button
        Returns None
        """

        self.thePropertyWindow.clearStatusBar()

        if len(obj) == 0:
            return None

        aPluginWindowType = self.DEFAULT_PLUGIN
        aSetFlag = False

        # When this method is cadef doSeleclled by popup menu
        if type( obj[0] ) == gtk.MenuItem:
            aPluginWindowType = obj[0].get_name()

        # When this method is called by 'CreateWindow' button
        elif type( obj[0] ) == gtk.Button:
            aPluginWindowType = self['plugin_optionmenu'].get_children()[0].get()

        else:
            raise TypeErrir("%s must be gtk.MenuItem or gtk.Button" %str(type(obj[0])))

        aSelectedRawFullPNList = self.__getSelectedRawFullPNList()

        # When no FullPN is selected, displays error message.
        if aSelectedRawFullPNList  == None or len( aSelectedRawFullPNList ) == 0:

            aMessage = 'No entity is selected.'
            aDialog = ConfirmWindow(OK_MODE,aMessage,'Error!')
            self.thePropertyWindow.showMessageOnStatusBar(aMessage)
            return False

        # self.theQueue.pushFullPNList( aSelectedRawFullPNList )
        # self.thePluginManager.createInstance( aPluginWindowType, self.thePropertyWindow.theFullPNList() )

#         if self.thePropertyWindow.theFullPNList() \
#                 != aSelectedRawFullPNList:
#             raise RuntimeError, 'Inconsistent internal lists: (%s == %s)' % ( self.thePropertyWindow.theFullPNList(), aSelectedRawFullPNList )

        self.thePluginManager.createInstance( aPluginWindowType, aSelectedRawFullPNList )


    def appendData( self, *obj ):
        """appends RawFullPN to PluginWindow instance
        Returns TRUE(when appened) / FALSE(when not appened)
        """

        # clear status bar
        self.thePropertyWindow.clearStatusBar()

        if len(obj) == 0:
            return None

        # Only when at least one menu is selected.

        # ----------------------------------------------------
        # When this method is called by popup menu
        # ----------------------------------------------------
        if type( obj[0] ) == gtk.MenuItem:
            aSetFlag = True
            aPluginWindowTitle = obj[0].get_name()
            aSelectedRawFullPNList = self.__getSelectedRawFullPNList()

            for anInstance in self.thePluginManager.theInstanceList:
                if anInstance.getTitle() == aPluginWindowTitle:

                    try:
                        anInstance.appendRawFullPNList( aSelectedRawFullPNList )
                    except TypeError:
                        anErrorFlag = True
                        aMessage = "Can't append data to %s" %str(anInstance.getTitle())
                        self.thePropertyWindow.showMessageOnStatusBar(aMessage)
                    else:
                        aMessage = "Selected Data are added to %s" %aPluginWindowTitle
                        self.thePropertyWindow.showMessageOnStatusBar(aMessage)
                    break

            return True

        # ----------------------------------------------------
        # When this method is called by PluginInstanceWindow
        # ----------------------------------------------------
        elif type( obj[0] ) == gtk.Button:

            self.theSelectedPluginInstanceList = []
            selection=self.thePluginInstanceSelection['plugin_tree'].get_selection()
            selection.selected_foreach(self.thePluginInstanceSelection.plugin_select_func)
            aSelectedRawFullPNList = self.__getSelectedRawFullPNList()

            # When no FullPN is selected, displays error message.
            if aSelectedRawFullPNList == None or len( aSelectedRawFullPNList ) == 0:

                aMessage = 'No entity is selected.'
                aDialog = ConfirmWindow(OK_MODE,aMessage,'Error!')
                self.thePropertyWindow.showMessageOnStatusBar(aMessage)
                return False

            # When no plugin instance is selected, displays error message.
            if len(self.theSelectedPluginInstanceList) == 0:

                aMessage = 'No Plugin Instance is selected.'
                aDialog = ConfirmWindow(OK_MODE,aMessage,'Error!')
                self.thePropertyWindow.showMessageOnStatusBar(aMessage)
                return False

            # buffer of appended instance's title
            anAppendedTitle = []

            anErrorFlag = False

            # appneds data
            for aPluginWindowTitle in self.theSelectedPluginInstanceList:
                for anInstance in self.thePluginManager.theInstanceList:
                    if anInstance.getTitle() == aPluginWindowTitle:
                        try:
                            anInstance.appendRawFullPNList( aSelectedRawFullPNList )
                        except TypeError:
                            anErrorFlag = True
                            aMessage = "Can't append data to %s" %str(anInstance.getTitle())
                            self.thePropertyWindow.showMessageOnStatusBar(aMessage)
                        else:
                            anAppendedTitle.append( anInstance.getTitle() )
                        break

            # When at least one instance is appended
            if len(anAppendedTitle) > 0 and not anErrorFlag:
                # displays message
                aMessage = "Selected Data are added to %s" %str(anAppendedTitle)
                self.theSession.message(aMessage)
                self.thePropertyWindow.showMessageOnStatusBar(aMessage)

                # closes PluginInstanceSelectionWindow
                #self.__closePluginInstanceSelectionWindow()
                self.closePluginInstanceSelectionWindow()
                return True

            # When no instance is appended
            else:

                return NONE


    def __getCheckedFullPNList( self ):

        if len( self.theCheckedFullIDList ) == 0:
            return []

        if self.theCheckedFullIDList[ 0 ][ 0 ] == VARIABLE: 
            propertyName = self.DEFAULT_VARIABLE_PROPERTY
        else: # self.theCheckedFullIDList[ 0 ][ 0 ] == PROCESS
            propertyName = self.DEFAULT_PROCESS_PROPERTY
               
        fullpnList = []
        for fullid in self.theCheckedFullIDList:
            fullpnList.append( fullid + ( propertyName, ) )

        return map( self.thePropertyWindow.supplementFullPN, fullpnList )

    def __getSelectedRawFullPNList( self ):
        """
        Return a list of selected FullPNs
        """
        # return self.theQueue.getActualFullPNList()
        aCheckedFullPNList = self.__getCheckedFullPNList()
        if len( aCheckedFullPNList ) != 0:
            return aCheckedFullPNList
        else:
            return map( self.thePropertyWindow.supplementFullPN, 
                        self.theQueue.getActualFullPNList() )
 
#         # this is redundant
#         self.theSelectedFullPNList = []

#         if ( self.theLastSelectedWindow == "None" ):
#             return None

#         if ( self.theLastSelectedWindow == "Variable" ):

#             selection=self.variableTree.get_selection()
#             selection.selected_foreach(self.variable_select_func)

#         if ( self.theLastSelectedWindow == "Process" ):

#             selection=self.processTree.get_selection()
#             selection.selected_foreach(self.process_select_func)

#         if len(self.theSelectedFullPNList) == 0:
#             selectedSystemList = self.getSelectedSystemList()
#             for aSystemFullID in selectedSystemList:
#                 self.theSelectedFullPNList.append( convertFullIDToFullPN( aSystemFullID ) )


#         # If no property is selected on PropertyWindow, 
#         # create plugin Window with default property (aValue) 
#         if len( str(self.thePropertyWindow.getSelectedFullPN()) ) == 0:
#             return self.theSelectedFullPNList

#         # If a property is selected on PropertyWindow, 
#         # create plugin Window with selected property
#         else:
#             return [self.thePropertyWindow.getSelectedFullPN()]




    def addToBoard( self, *arg ):
        """add plugin window to board
        """

        self.thePropertyWindow.clearStatusBar()

        if len(arg) == 0:
            return None

        aPluginWindowType = self.DEFAULT_PLUGIN
        aSetFlag = False

        # When this method is called by popup menu
        if type( arg[0] ) == gtk.MenuItem:
            aPluginWindowType = arg[0].get_name()

        # When this method is called by 'CreateWindow' button
        elif type( arg[0] ) == gtk.Button:
            aPluginWindowType = self['plugin_optionmenu'].get_children()[0].get()

        else:
            raise TypeError("%s must be gtk.MenuItem or gtk.Button" %str(type(arg[0])))

        aSelectedRawFullPNList = self.__getSelectedRawFullPNList()

        # When no FullPN is selected, displays error message.
        if aSelectedRawFullPNList  == None or len( aSelectedRawFullPNList ) == 0:

            aMessage = 'No entity is selected.'
            aDialog = ConfirmWindow(OK_MODE,aMessage,'Error!')
            self.thePropertyWindow.showMessageOnStatusBar(aMessage)
            return False

        self.theSession.getWindow('BoardWindow').addPluginWindows( aPluginWindowType, aSelectedRawFullPNList )


    def searchEntity( self ):
        """search Entities
        Returns None
        """
        searchString = self['search_entry'].get_text()
        # set modelwalker to current selection
        aFullPNList = []

        modelWalker = self.theSession.theModelWalker

        modelWalker.reset()
        
        nextFullID = modelWalker.getCurrentFullID()

        while nextFullID != None:
            if nextFullID[TYPE] == SYSTEM:
                currentSystemID = nextFullID
                currentSystemSelected = False
                
            elif not currentSystemSelected and nextFullID[ID].find( searchString ) != -1:
                # select
                aFullPNList += [ convertFullIDToFullPN( currentSystemID ) ]
                currentSystemSelected = True
                
            nextFullID = modelWalker.getNextFullID()
            

        if len( aFullPNList ) == 0:
            aDialog = ConfirmWindow( OK_MODE, 
                                    "Search string %s not found."%searchString, 
                                    "Search failed" )
            return
        self.searchString = searchString
        self.theQueue.pushFullPNList( aFullPNList )
        self['search_button'].set_sensitive( False)
        if self.searchString != '':
            self['clear_button'].set_sensitive(True )


    def filterSelectedSystems( self ):
        
        self.searchString = self['search_entry'].get_text()
        self.reconstructLists()
        self['search_button'].set_sensitive( False)
        if self.searchString != '':
            self['clear_button'].set_sensitive(True )
        else:
            self['clear_button'].set_sensitive(False )


    def pushSearchButton( self, *arg ):
        searchScope = self['search_scope'].get_property( 'active' )
        if searchScope == 0:
            self.searchEntity()
        else:
            self.filterSelectedSystems()


    def keypressOnSearchEntry( self, *arg ):

        if( arg[1].keyval == 65293 ):

            self.pushSearchButton( None )
        else :
            self['search_button'].set_sensitive(True )

        
    def pushClearButton( self, *args ):
        self['search_entry'].set_text('')
        self.filterSelectedSystems()
        
    def searchScopeChanged( self, *args ):
        searchString = self['search_entry'].get_text()
        if self.searchString != '':
            self['search_button'].set_sensitive( True)
        else:
            self['search_button'].set_sensitive( False)
            
    def toggleDefaultProperties( self ):

        if EntityListWindow.DEFAULT_VARIABLE_PROPERTY == 'Value':

            EntityListWindow.DEFAULT_VARIABLE_PROPERTY = 'MolarConc'
            EntityListWindow.DEFAULT_PROCESS_PROPERTY = 'MolarActivity'

            EntityListWindow.VARIABLE_COLUMN_INFO_MAP= {
                'MolarConc': gobject.TYPE_STRING
                }

            EntityListWindow.PROCESS_COLUMN_INFO_MAP= {
                'MolarActivity': gobject.TYPE_STRING
                }

            EntityListWindow.VARIABLE_COLUMN_LIST \
                = [ 'ID', 'MolarConc', 'Classname', 'Path' ]
            EntityListWindow.PROCESS_COLUMN_LIST \
                = [ 'ID', 'MolarActivity', 'Classname', 'Path' ]

        elif EntityListWindow.DEFAULT_VARIABLE_PROPERTY == 'MolarConc':
            EntityListWindow.DEFAULT_VARIABLE_PROPERTY = 'Value'
            EntityListWindow.DEFAULT_PROCESS_PROPERTY = 'Activity'

            EntityListWindow.VARIABLE_COLUMN_INFO_MAP= {
                'Value': gobject.TYPE_STRING
                }

            EntityListWindow.PROCESS_COLUMN_INFO_MAP= {
                'Activity': gobject.TYPE_STRING
                }

            EntityListWindow.VARIABLE_COLUMN_LIST \
                = [ 'ID', 'Value', 'Classname', 'Path' ]
            EntityListWindow.PROCESS_COLUMN_LIST \
                = [ 'ID', 'Activity', 'Classname', 'Path' ]

        else:
            raise RuntimeError, 'Invalid DEFAULT_VARIABLE_PROPERTY [%s].' % EntityListWindow.DEFAULT_VARIABLE_PROPERTY

    def updateDefaultProperties( self ):

        for column in self.variableTree.get_columns():
            if column.get_title() == 'MolarConc':
                column.set_title( 'Value' )
            elif column.get_title() == 'Value':
                column.set_title( 'MolarConc' )

        for column in self.processTree.get_columns():
            if column.get_title() == 'MolarActivity':
                column.set_title( 'Activity' )
            elif column.get_title() == 'Activity':
                column.set_title( 'MolarActivity' )

        self.reconstructLists()

    def logAllEntities( self, *arg ):

        self.logAllVariables( *arg )
        self.logAllProcesses( *arg )

    def logAllVariables( self, *arg ):
        variableList = self.theSession.getVariableList()
        propertyList = [ '%s:%s' % ( fullid, self.DEFAULT_VARIABLE_PROPERTY ) 
                         for fullid in variableList ]

        self.__logAll( propertyList )

    def logAllProcesses( self, *arg ):
        processList = self.theSession.getProcessList()
        propertyList = [ '%s:%s' % ( fullid, self.DEFAULT_PROCESS_PROPERTY ) 
                         for fullid in processList ]

        self.__logAll( propertyList )

    def __logAll( self, propertyList ):
        if self.theSession.isRunning():
            return

        loggingPolicy = self.theSession.getLogPolicyParameters()
        loggerList = self.theSession.theSimulator.getLoggerList()

        for fullpn in propertyList:
            if not fullpn in loggerList:
                try:
                    self.theSession.theSimulator.createLogger( fullpn, 
                                                               loggingPolicy )
                except:
                    self.theSession.message( 'Error while creating logger\n logger for ' + fullpn + ' not created\n' )
                else:
                    self.theSession.message( 'Logger created for %s\n' % fullpn )

        self.thePluginManager.updateFundamentalWindows()

#         message = '%d properties were logged.' % len( propertyList )
#         dialog = ConfirmWindow( OK_MODE, message, 'Log All Properties' )

    def selectEffectors( self, *arg ):

        # 0: mutators, 1: accessors
        selectionType = arg[ 1 ]

        # gets selected RawFullPNList
        aSelectedRawFullPNList = self.__getSelectedRawFullPNList()

        # When no entity is selected, displays confirm window.
        if len( aSelectedRawFullPNList ) == 0:
            aMessage = 'No Entity is selected.'
            self.thePropertyWindow.showMessageOnStatusBar( aMessage )
            aDialog = ConfirmWindow( OK_MODE, aMessage, 'Error!' )
            return

        selectedIDList = []
        entityType = convertFullPNToFullID( aSelectedRawFullPNList[ 0 ] )[ 0 ]
        for fullpn in aSelectedRawFullPNList:
            fullid = convertFullPNToFullID( fullpn )
            if fullid[ 0 ] != entityType:
                aMessage = 'Multiple Entity type selection is not supported.'
                self.thePropertyWindow.showMessageOnStatusBar( aMessage )
                aDialog = ConfirmWindow( OK_MODE, aMessage, 'Error!' )
                return

            selectedIDList.append( ':%s:%s' % ( fullid[ 1 ], fullid[ 2 ] ) )

        self.clearCheckboxes()

        if entityType == VARIABLE:

            model = self.processTree.get_model()
            for row in model:
                iter = row.iter
                processid \
                    = model.get_data( model.get_string_from_iter( iter ) )
                stub = self.theSession.createEntityStub( processid )
                processid = createFullID( processid )
                references = stub.getProperty( 'VariableReferenceList' )

                references = [ ref[ 1 ] for ref in references 
                               if ref[ 2 ] != 0 or selectionType ]

                for fullid in selectedIDList:
                    if fullid in references:
                        self.toggleCheckbox( model, iter )

        elif entityType == PROCESS:

            tempList = []
            for processid in selectedIDList:
                stub = self.theSession.createEntityStub( 'Process%s' 
                                                         % processid )
                references = stub.getProperty( 'VariableReferenceList' )

                for ref in references:
                    fullid = 'Variable%s' % ref[ 1 ]
                    if ( ref[ 2 ] != 0 or selectionType ) \
                            and not fullid in tempList:
                        tempList.append( fullid )

            # sorted( set( tempList ), key=tempList.index) # uniq

            # the following would be redundant.
            fullidList = []
            model = self.variableTree.get_model()
            for row in model:
                iter = row.iter
                variableid \
                    = model.get_data( model.get_string_from_iter( iter ) )
                if variableid in tempList:
                    self.toggleCheckbox( model, iter )

    def createLogger( self, *arg ):
        """creates Logger about all FullPN selected on EntityTreeView
        Returns None
        """

        # clear status bar
        self.thePropertyWindow.clearStatusBar()

        # gets selected RawFullPNList
        aSelectedRawFullPNList = self.__getSelectedRawFullPNList()

        # When no entity is selected, displays confirm window.
        if len(aSelectedRawFullPNList) == 0:

            aMessage = 'No Entity is selected.'
            self.thePropertyWindow.showMessageOnStatusBar(aMessage)
            aDialog = ConfirmWindow(OK_MODE,aMessage,'Error!')
            return None

        # creates Logger using PropertyWindow
        # self.theQueue.pushFullPNList( aSelectedRawFullPNList )
        # self.thePropertyWindow.createLogger()
        self.__createLogger( aSelectedRawFullPNList )

        # display message on status bar
        if len(aSelectedRawFullPNList) == 1:
            aMessage = 'Logger was created.'
        else:
            aMessage = 'Loggers were created.'
        self.thePropertyWindow.showMessageOnStatusBar(aMessage)
        #self.checkCreateLoggerButton()

    def __createLogger( self, fullpnList ):

        loggingPolicy = self.theSession.getLogPolicyParameters()

        try:
            for fullpn in fullpnList:
                fullpnString = createFullPNString( fullpn )

                # creates loggerstub and call its create method.
                stub = self.theSession.createLoggerStub( fullpnString )
                if not stub.exists():
                    stub.create()
                    stub.setLoggerPolicy( loggingPolicy )

        except:
            # When to create log is failed, 
            # display error message on MessageWindow.
            message = traceback.format_exception( sys.exc_type,sys.exc_value, 
                                                  sys.exc_traceback )
            self.thePluginManager.printMessage( message )

            # updates fandamental windows.
            self.thePluginManager.updateFundamentalWindows()

    def clearCheckboxes( self, *arg ):

        if len( self.theCheckedFullIDList ) == 0:
            return

        if self.theCheckedFullIDList[ 0 ][ 0 ] == VARIABLE:
            model = self.variableTree.get_model()
        else: # self.theCheckedFullIDList[ 0 ][ 0 ] == PROCESS
            model = self.processTree.get_model()

        for row in model:
            model.set_value( row.iter, 0, False )

        self.theCheckedFullIDList = []
        self['clear_checked_button'].set_sensitive( 0 )

    def __toggleCheckbox( self, cell, path, tree ):

        model = tree.get_model()
        iter = model.get_iter( path )
        self.toggleCheckbox( model, iter )

    def toggleCheckbox( self, model, iter ):

        selected = model.get_value( iter, 0 )
        fullIDString = model.get_data( model.get_string_from_iter( iter ) )
        fullid = createFullID( fullIDString )

        if not selected:
            if len( self.theCheckedFullIDList ) > 0 \
                    and self.theCheckedFullIDList[ 0 ][ 0 ] != fullid[ 0 ]:
                if fullid[ 0 ] == VARIABLE:
                    another = self.processTree.get_model()
                else:
                    another = self.variableTree.get_model()

                for row in another:
                    if another.get_value( row.iter, 0 ):
                        another.set_value( row.iter, 0, False )

                self.theCheckedFullIDList = []

            self.theCheckedFullIDList.append( fullid )
            self['clear_checked_button'].set_sensitive( True )
        else:
            if fullid in self.theCheckedFullIDList:
                self.theCheckedFullIDList.remove( fullid )
            else:
                pass # never get here
            
            self['clear_checked_button'].set_sensitive( len( self.theCheckedFullIDList ) != 0 )

        model.set_value( iter, 0, not selected )
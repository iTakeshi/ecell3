import os

from config import *
from ViewWindow import *

class PluginWindow(ViewWindow):
    '''
    self.theRawFullPNList : [ FullPN1, FullID2, FullPN3, , , ]
    theFullPNList()       : [ FullPN1, FullPN2, FullPN3, , , ]
    theFullIDList()       : [ FullID1, FullID2, FullID3, , , ]
    theFullPN()           : FullPN1
    theFullID()           : FullID1
    '''

    def __init__( self, dirname, sim, data, pluginmanager ):
        aGladeFileName = os.path.join( dirname ,
                                       self.__class__.__name__ + ".glade" )
        ViewWindow.__init__( self, aGladeFileName, sim, data )

        self.thePluginManager = pluginmanager
        
        self.theRawFullPNList = data

    def theFullPNList( self ):
        return map( self.supplementFullPN, self.theRawFullPNList )

    def theFullIDList( self ):
        return map( convertFullPNToFullID, self.theRawFullPNList )

    def theFullPN( self ):
        return self.supplementFullPN( self.theRawFullPNList[0] )

    def theFullID( self ):
        return convertFullPNToFullID( self.theFullPN() )


    def supplementFullPN( self, aFullPN ):
        if aFullPN[PROPERTY] != '' :
            return aFullPN
        else :
            if aFullPN[TYPE] == SUBSTANCE :
                aPropertyName = 'Quantity'
            elif aFullPN[TYPE] == REACTOR :
                aPropertyName = 'Activity'
            elif aFullPN[TYPE] == SYSTEM :
                aPropertyName = 'Activity'
            aNewFullPN = convertFullIDToFullPN( convertFullPNToFullID(aFullPN),
                                                aPropertyName )
            return aNewFullPN

    def theAttributeMap( self ):
        aMap = {}
        for aFullPN in self.theRawFullPNList:
            aFullID = convertFullPNToFullID( aFullPN )
            aPropertyName = aFullPN[PROPERTY]
            aPropertyListFullPN = convertFullIDToFullPN( aFullID, 'PropertyList' )
            aPropertyList = self.theSimulator.getProperty( aPropertyListFullPN )
            aAttributeListFullPN = convertFullIDToFullPN( aFullID, 'PropertyAttributes')
            aAttributeList = self.theSimulator.getProperty( aAttributeListFullPN )
            num = 0
            for aProperty in aPropertyList:
                aPropertyFullPN = convertFullIDToFullPN( aFullID, aProperty )
                aMap[ aPropertyFullPN ] = aAttributeList[ num ]
                num += 1
        return aMap
        
    def getAttribute( self, aFullPN ):
        aMap = self.theAttributeMap()
        if aMap.has_key( aFullPN ):
            return aMap[ aFullPN ]
        else:
            return 99










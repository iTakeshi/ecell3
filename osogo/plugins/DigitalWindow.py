#!/usr/bin/env python


from PluginWindow import *
from ecell.ecssupport import *
import GTK
import operator

class DigitalWindow( PluginWindow ):

    def __init__( self, dirname, data, pluginmanager, root=None ):
	
        PluginWindow.__init__( self, dirname, data, pluginmanager, root )
        
        self.theSession = pluginmanager.theSession
        aFullPNString = createFullPNString( self.theFullPN() )
        aValue = self.theSession.theSimulator.getProperty( aFullPNString )
        if operator.isNumberType( aValue[0] ):

            self.openWindow()
            self.thePluginManager.appendInstance( self )
            PluginWindow.initialize( self, root )
            self.initialize()

        else:
            self.theSession.printMessage( "%s: not numerical data\n" % aFullPNString )

        if len( self.theFullPNList() ) > 1:
            aClassName = self.__class__.__name__
            self.thePluginManager.createInstance( aClassName, self.theFullPNList()[1:], root )


    def initialize( self ):

	self['toolbar5'].set_style( GTK.TOOLBAR_ICONS )
        self['toolbar5'].set_button_relief( GTK.RELIEF_HALF )

        self.addHandlers( { 'input_value'    :self.inputValue,
                            'increase_value' :self.increaseValue,
                            'decrease_value' :self.decreaseValue,
          		    'window_exit'    :self.exit,
                            'test'           :self.test } )

        aString = str( self.theFullPN()[ID] )
        aString += ':\n' + str( self.theFullPN()[PROPERTY] )
        self["id_label"].set_text( aString )
        self.update()
        

    def update( self ):
        self["value_frame"].set_text( str( self.getValue( self.theFullPN() ) ) )


    def inputValue( self, obj ):

        aValue =  string.atof(obj.get_text())
        self.setValue( self.theFullPN(), aValue )


    def increaseValue( self, obj ):

        if self.getValue( self.theFullPN() ):
            self.setValue( self.theFullPN(), self.getValue( self.theFullPN() ) * 2.0 )
        else:
            self.setValue( self.theFullPN(), 1.0 )
        

    def decreaseValue( self, obj ):

        self.setValue( self.theFullPN(), self.getValue( self.theFullPN() ) * 0.5 )

			
    def test( self, obj ):
        print 'you did it'

### test code

if __name__ == "__main__":

    class simulator:

        dic={('Substance', '/CELL/CYTOPLASM', 'ATP','Quantity') : (1950,),}

        def getProperty( self, fpn ):
            return simulator.dic[fpn]

        def setProperty( self, fpn, value ):
            simulator.dic[fpn] = value


    fpn = ('Substance','/CELL/CYTOPLASM','ATP','Quantity')

    def mainQuit( obj, data ):
        gtk.mainquit()
        
    def mainLoop():
        # FIXME: should be a custom function

        gtk.mainloop()

    def main():
        aDigitalWindow = DigitalWindow( 'plugins', simulator(), [fpn,] )
        aDigitalWindow.addHandler( 'gtk_main_quit', mainQuit )
        aDigitalWindow.update()

        mainLoop()

    main()










CLASSNAME = 'Cln3PProcess'
BASECLASS = 'FluxProcess'
PROPERTIES = [('Real','Max',0.0),('Real','D',0.0),('Real','J',0.0)]

PROTECTED_AUX = '''
  VariableReference C0;
  VariableReference P0;
'''

defineMethod( 'initialize', '''
  C0 = getVariableReference( "C0" );
  P0 = getVariableReference( "P0" );
''' )

defineMethod( 'process', '''
 const Real E1( C0.getVariable()->getConcentration() ); // const?
 Real V( Max * D * E1 );
 V /= J + D * E1;
 V *= getSuperSystem()->getVolume() * N_A;
 P0.getVariable()->setValue(V);
''' )

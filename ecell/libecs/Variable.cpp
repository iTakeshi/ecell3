//::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
//
//        This file is part of E-CELL Simulation Environment package
//
//                Copyright (C) 1996-2002 Keio University
//
//::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
//
//
// E-CELL is free software; you can redistribute it and/or
// modify it under the terms of the GNU General Public
// License as published by the Free Software Foundation; either
// version 2 of the License, or (at your option) any later version.
// 
// E-CELL is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
// See the GNU General Public License for more details.
// 
// You should have received a copy of the GNU General Public
// License along with E-CELL -- see the file COPYING.
// If not, write to the Free Software Foundation, Inc.,
// 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
// 
//END_HEADER
//
// written by Kouichi Takahashi <shafi@e-cell.org> at
// E-CELL Project, Lab. for Bioinformatics, Keio University.
//

#include "Util.hpp"
#include "System.hpp"
#include "FullID.hpp"
#include "Model.hpp"
#include "EntityType.hpp"
#include "PropertySlotMaker.hpp"

//#include "Accumulators.hpp"
//#include "AccumulatorMaker.hpp"


#include "Variable.hpp"


namespace libecs
{

  void Variable::makeSlots()
  {
    DEFINE_PROPERTYSLOT( "Value", Real,
			 &Variable::setValue,
			 &Variable::getValue );

    DEFINE_PROPERTYSLOT( "Velocity", Real,
			 &Variable::addVelocity,
			 &Variable::getVelocity );

    DEFINE_PROPERTYSLOT( "TotalVelocity", Real,
			 NULLPTR,
			 &Variable::getTotalVelocity );

    DEFINE_PROPERTYSLOT( "Fixed", Int,
			 &Variable::setFixed,
			 &Variable::getFixed );

    DEFINE_PROPERTYSLOT( "Concentration", Real,
			 NULLPTR,
			 &Variable::getConcentration );
  }


  Variable::Variable()
    : 
    theValue( 0.0 ),  
    theVelocity( 0.0 ),
    theTotalVelocity( 0.0 ),
    theFixed( false )
  {
    makeSlots();
  } 

  Variable::~Variable()
  {
    clearVariableProxyVector();
  }


  void Variable::initialize()
  {
    clearVariableProxyVector();
  }

  void Variable::clearVariableProxyVector()
  {
    for( VariableProxyVectorIterator i( theVariableProxyVector.begin() );
	 i != theVariableProxyVector.end(); ++i )
      {
	VariableProxyPtr anVariableProxyPtr( *i );
	delete anVariableProxyPtr;
      }

    theVariableProxyVector.clear();
  }


  void Variable::setFixed( IntCref aValue )
  { 
    theFixed = static_cast<bool>( aValue );
  }


  const Int Variable::getFixed() const                         
  { 
    return theFixed;
  }

  void Variable::registerStepper( VariableProxyPtr anVariableProxyPtr )
  {
    theVariableProxyVector.push_back( anVariableProxyPtr );
  }


  ///////////////////////// PositiveVariable

  void PositiveVariable::integrate( VariableProxyPtr anVariableProxy )
  {
    Variable::integrate( anVariableProxy );

    //    
    // Check if the value is in positive range.
    // | value | < epsilon is rounded to zero.
    //
    const Real anEpsilon( std::numeric_limits<Real>::epsilon() );
    const Real aValue( getValue() );
    if( aValue < anEpsilon )
      {
	if( aValue > - anEpsilon )
	  {
	    setValue( 0.0 );
	  }
	else
	  {
	    THROW_EXCEPTION( RangeError, "PositiveVariable [" + 
			     getFullID().getString() + 
			     "]: negative value occured in integrate()." );
	  }
      }
  }



#if 0

  const String SRMVariable::SYSTEM_DEFAULT_ACCUMULATOR_NAME = "ReserveAccumulator";

  //  const String SRMVariable::SYSTEM_DEFAULT_ACCUMULATOR_NAME = "SimpleAccumulator";


  SRMVariable::SRMVariable()
    : 
    theAccumulator( NULLPTR ),
    theFraction( 0 )
  {
    makeSlots();
    // FIXME: use AccumulatorMaker
    setAccumulator( new ReserveAccumulator );
  } 

  SRMVariable::~SRMVariable()
  {
    delete theAccumulator;
  }


  const String SRMVariable::getAccumulatorClass() const
  {
    return theAccumulator->getClassName();
  }

  void SRMVariable::setAccumulatorClass( StringCref anAccumulatorClassname )
  {
    AccumulatorPtr aAccumulatorPtr( getModel()->getAccumulatorMaker()
				    .make( anAccumulatorClassname ) );
    setAccumulator( aAccumulatorPtr );
  }

  void SRMVariable::setAccumulator( AccumulatorPtr anAccumulator )
  {
    if( theAccumulator != NULLPTR )
      {
	delete theAccumulator;
      }

    theAccumulator = anAccumulator;
    theAccumulator->setOwner( this );
    //    theAccumulator->update();
  }



  void SRMVariable::initialize()
  {
    // if the accumulator is not set, use user default
    if( theAccumulator == NULLPTR )
      {
	setAccumulatorClass( SYSTEM_DEFAULT_ACCUMULATOR_NAME );
      }

    theAccumulator->update();
  }


  const Real SRMVariable::saveValue()
  {
    return theAccumulator->save();
  }



  void SRMVariable::loadValue( RealCref aValue )
  {
    Variable::loadValue( aValue );
    theAccumulator->update();
  }


  void SRMVariable::integrate( RealCref aTime )
  { 
    if( isFixed() == false ) 
      {
	updateValue( aTime );

	theAccumulator->accumulate();
  
	if( theValue < 0.0 ) 
	  {
	    theValue = 0.0;
	    //FIXME:       throw LTZ();
	  }
      }
  }

  void SRMVariable::makeSlots()
  {
    registerSlot( getPropertySlotMaker()->
		  createPropertySlot( "AccumulatorClass", *this,
				      Type2Type<String>(),
				      &SRMVariable::setAccumulatorClass,
				      &SRMVariable::getAccumulatorClass ) );

  }

#endif // 0


} // namespace libecs


/*
  Do not modify
  $Author$
  $Revision$
  $Date$
  $Locker$
*/

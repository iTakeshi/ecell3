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

#ifndef __VARIABLE_HPP
#define __VARIABLE_HPP

#include <utility>
#include <iostream>

#include "libecs.hpp"
#include "EntityType.hpp"
#include "Entity.hpp"
#include "VariableProxy.hpp"
#include "System.hpp"
#include "Model.hpp"

namespace libecs
{

  /** @addtogroup entities
   *@{
   */

  /** @file */


  /**
     Variable class represents state variables in the simulation model, such as
     amounts of molecular species in a compartment.

  */

  LIBECS_DM_CLASS( Variable, Entity )
  {

  public:

    LIBECS_DM_BASECLASS( Variable );

    LIBECS_DM_OBJECT( Variable, Variable )
      {
	INHERIT_PROPERTIES( Entity );
	
	// Use addVelocity as the set method.  This won't be saved/loaded.
	PROPERTYSLOT_NO_LOAD_SAVE( Real, Velocity,
				   &Variable::addVelocity, 
				   &Variable::getVelocity );
	PROPERTYSLOT_SET_GET( Real, Value );
	PROPERTYSLOT_GET    ( Real, TotalVelocity );
	// Concentration can be saved, but cannot be loaded.
	PROPERTYSLOT_LOAD_SAVE( Real, Concentration,
				NULLPTR,
				&Variable::getConcentration,
				NULLPTR,
				&Variable::getConcentration );
	PROPERTYSLOT_SET_GET( Int,  Fixed );
      }

    Variable();
    virtual ~Variable();

    virtual const EntityType getEntityType() const
    {
      return EntityType( EntityType::VARIABLE );
    }


    /**
       Initializes this variable. 
    */

    virtual void initialize();


    /**
       Clear theVelocity by zero.
    */

    void clearVelocity()
    { 
      theVelocity = 0.0; 
    }

    /** 
	Integrate.
    */

    virtual void integrate( const Real aTime )
    {
      if( isFixed() == false )
	{
	  updateValue( aTime );
	}
    }

    const Real calculateVelocitySum( RealCref aCurrentTime, 
				     RealCref anInterval ) const
    {
      Real aVelocitySum( 0.0 );
      FOR_ALL( VariableProxyVector, theVariableProxyVector )
	{
	  VariableProxyPtr const anVariableProxyPtr( *i );
	  aVelocitySum += anVariableProxyPtr->getDifference( aCurrentTime,
							     anInterval );
	}

      return aVelocitySum;
    }


    void updateValue( RealCref aCurrentTime )
    {
      const Real anInterval( aCurrentTime - theLastTime );

      if( anInterval == 0.0 )
	{
	  return;
	}

      const Real aVelocitySum( calculateVelocitySum( aCurrentTime,
						     anInterval ) );

      // Give it in per second.
      theTotalVelocity = aVelocitySum / anInterval;

      loadValue( getValue() + aVelocitySum );

      theLastTime = aCurrentTime;
    }


    /**
       Check if the current total velocity doesn't exceed value range of 
       this object.


       @return true -> if estimated value at the next step is
       within the value range, false -> otherwise

       @note Variable class itself doesn't have the value range, thus
       this check always succeed.  Each subclass of Variable should override
       this method if it has the range.
    */

    virtual const bool checkRange( RealCref aStepInterval ) const
    {
      // this class has no range limit, thus this check always success
      return true;
    }

    /**
       This simply sets the value of this Variable if getFixed() is false.

       @see getFixed()
    */

    virtual SET_METHOD( Real, Value )
    { 
      if( ! isFixed() ) 
	{
	  loadValue( value ); 
	}
    }

    virtual GET_METHOD( Real, Value )
    { 
      return saveValue();
    }

    void addValue( RealCref aValue )
    {
      setValue( getValue() + aValue );
    }

    void loadValue( RealCref aValue )
    {
      theValue = aValue;
    }

    const Real saveValue() const
    {
      return theValue;
    }

    SET_METHOD( Real, theVelocity )
    {
      theVelocity = value;
    }


    // provide interface for value passing. (mainly for STL)
    void setVelocity( const Real value )
    {
      theVelocity = value;
    }


    /**
       @return current velocity value in (number of molecules)/(step)
    */

    GET_METHOD( Real, Velocity )
    { 
      return theVelocity; 
    }

    GET_METHOD( Real, TotalVelocity )
    {
      return theTotalVelocity;
    }

    /**
       @param aVelocity velocity in number of molecules to be added.
    */

    void addVelocity( RealCref aVelocity ) 
    {
      theVelocity += aVelocity; 
    }


    /**

    A wrapper to set Fixed property by a bool value.

    */

    void setFixed( const bool aValue )
    {
      theFixed = aValue;
    }

    /**
       @return true if the Variable is fixed or false if not.
    */

    const bool isFixed() const
    {
      return theFixed;
    }


    // wrappers to expose is/setFixed as PropertySlots 
    SET_METHOD( Int, Fixed )
    { 
      theFixed = static_cast<bool>( value );
    }

    GET_METHOD( Int, Fixed )
    { 
      return theFixed;
    }


    /**
       Returns the concentration of this Variable.

       @return Concentration in M (mol/L).
    */

    GET_METHOD( Real, Concentration )
    {
      return getValue() / ( getSuperSystem()->getSizeN_A() );
    }

    void registerProxy( VariableProxyPtr const anVariableProxy );
    //    void removeProxy( VariableProxyPtr const anVariableProxy );


  protected:

    void clearVariableProxyVector();

  protected:

    Real theValue;

    Real theVelocity;

    Real theTotalVelocity;

    Real theLastTime;

    VariableProxyVector theVariableProxyVector;

    //    StepperVector theStepperVector;
    // this is a list of indices of Steppers' VariableCache of this Variable.
    //    RealPtrVector theVelocityVector;

    bool theFixed;
  };



  LIBECS_DM_CLASS( PositiveVariable, Variable )
  {

  public:

    LIBECS_DM_OBJECT( PositiveVariable, Variable )
      {
	INHERIT_PROPERTIES( Variable );
      }


    PositiveVariable()
    {
      // do nothing
    }

    virtual ~PositiveVariable()
    {
      // do nothing
    }

    virtual SET_METHOD( Real, Value );


    /** 
	Integrate.

	In this class, the range (non-negative) is checked.
    */

    virtual void integrate( const Real aTime );

    virtual const bool checkRange( RealCref anInterval ) const
    {
      const Real aPutativeValue( getValue() + 
				 calculateVelocitySum( theLastTime 
						       + anInterval,
						       anInterval ) );

      if( aPutativeValue >= 0.0 )
	{
	  return true;
	}
      else
	{
	  return false;
	}
    }

  };


  /*@}*/

} // namespace libecs


#endif /* __VARIABLE_HPP */

/*
  Do not modify
  $Author$
  $Revision$
  $Date$
  $Locker$
*/




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
// modified by Masayuki Okayama <smash@e-cell.org> at
// E-CELL Project, Lab. for Bioinformatics, Keio University.
//

#include "PropertyInterface.hpp"
#include "Exceptions.hpp"

#include "PropertiedClass.hpp"

namespace libecs
{


  ///////////////////////////// PropertiedClass

  const Polymorph 
  PropertiedClass::getPropertyAttributes( StringCref aPropertyName ) const
  {
    PropertySlotBasePtr aPropertySlotPtr( getPropertySlot( aPropertyName ) );
    
    PolymorphVector aVector;
    
    // is setable?
    aVector.push_back( static_cast<Int>( aPropertySlotPtr->isSetable() ) );
    
    // is getable?
    aVector.push_back( static_cast<Int>( aPropertySlotPtr->isGetable() ) );
    
    return aVector;
  }


  void PropertiedClass::defaultSetProperty( StringCref aPropertyName, 
					     PolymorphCref aValue )
  {
    THROW_EXCEPTION( NoSlot,
		     getClassName() + 
		     String( ": No property slot found by name [" )
		     + aPropertyName + "].  Set property failed." );
  }

  const Polymorph 
  PropertiedClass::defaultGetProperty( StringCref aPropertyName ) const
  {
    THROW_EXCEPTION( NoSlot, 
		     getClassName() + 
		     String( ": No property slot found by name [" )
		     + aPropertyName + "].  Get property failed." );
  }


  void PropertiedClass::registerLogger( LoggerPtr aLoggerPtr )
  {
    if( std::find( theLoggerVector.begin(), theLoggerVector.end(), aLoggerPtr )
	== theLoggerVector.end() )
      {
   	theLoggerVector.push_back( aLoggerPtr );
      }
  }

  void PropertiedClass::removeLogger( LoggerPtr aLoggerPtr )
  {
    LoggerVectorIterator i( find( theLoggerVector.begin(), 
				  theLoggerVector.end(),
				  aLoggerPtr ) );
    
    if( i != theLoggerVector.end() )
      {
	theLoggerVector.erase( i );
      }

  }


  void PropertiedClass::throwNotSetable()
  {
    THROW_EXCEPTION( AttributeError, "Not setable." );
  }

  void PropertiedClass::throwNotGetable()
  {
    THROW_EXCEPTION( AttributeError, "Not getable." );
  }


#define NULLSET_SPECIALIZATION_DEF( TYPE )\
  template <> void PropertiedClass::nullSet<TYPE>( const TYPE& )\
  {\
    throwNotSetable();\
  } //

  NULLSET_SPECIALIZATION_DEF( Real );
  NULLSET_SPECIALIZATION_DEF( Int );
  NULLSET_SPECIALIZATION_DEF( String );
  NULLSET_SPECIALIZATION_DEF( Polymorph );

#define NULLGET_SPECIALIZATION_DEF( TYPE )\
  template <> const TYPE PropertiedClass::nullGet<TYPE>() const\
  {\
    throwNotGetable();\
  } //

  NULLGET_SPECIALIZATION_DEF( Real );
  NULLGET_SPECIALIZATION_DEF( Int );
  NULLGET_SPECIALIZATION_DEF( String );
  NULLGET_SPECIALIZATION_DEF( Polymorph );


} // namespace libecs


/*
  Do not modify
  $Author$
  $Revision$
  $Date$
  $Locker$
*/

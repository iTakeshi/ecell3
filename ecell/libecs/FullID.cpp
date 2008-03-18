//::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
//
//       This file is part of the E-Cell System
//
//       Copyright (C) 1996-2008 Keio University
//       Copyright (C) 2005-2008 The Molecular Sciences Institute
//
//::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
//
//
// E-Cell System is free software; you can redistribute it and/or
// modify it under the terms of the GNU General Public
// License as published by the Free Software Foundation; either
// version 2 of the License, or (at your option) any later version.
//
// E-Cell System is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
// See the GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public
// License along with E-Cell System -- see the file COPYING.
// If not, write to the Free Software Foundation, Inc.,
// 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
//
//END_HEADER
//
// written by Koichi Takahashi <shafi@e-cell.org>,
// E-Cell Project.
//
#ifdef HAVE_CONFIG_H
#include "ecell_config.h"
#endif /* HAVE_CONFIG_H */

#include "Exceptions.hpp"
#include "FullID.hpp"

namespace libecs {

FullID FullID::parse( const String& aString )
{
    // empty FullID string is invalid
    if ( aString.empty() )
    {
        THROW_EXCEPTION( BadFormat, "empty FullID string." );
    }

    // ignore leading white spaces
    String::size_type aFieldStart( 0 );
    String::size_type aFieldEnd( aString.find_first_of( DELIMITER,
                                 aFieldStart ) );
    if ( aFieldEnd == String::npos )
    {
        THROW_EXCEPTION( BadFormat,
                         "no ':' in the FullID string \"" + aString + "\"" );
    }

    const EntityType& entityType( EntityType::get(
                                      aString.substr( aFieldStart, aFieldEnd - aFieldStart ) ) );

    aFieldStart = aFieldEnd + 1;
    aFieldEnd = aString.find_first_of( DELIMITER, aFieldStart );
    if ( aFieldEnd == String::npos )
    {
        THROW_EXCEPTION( BadFormat,
                         "only one ':' in the FullID string \""
                         + aString + "\"" );
    }

    SystemPath systemPath( SystemPath::parse(
                               aString.substr( aFieldStart, aFieldEnd - aFieldStart ) ) );

    aFieldStart = aFieldEnd + 1;

    // drop trailing string after extra ':'(if this is  FullPN),
    // or go to the end
    aFieldEnd = aString.find_first_of( DELIMITER, aFieldStart );

    return FullID( entityType, systemPath,
                   aString.substr( aFieldStart, aFieldEnd - aFieldStart ) );
}

const String FullID::asString() const
{
    return localID_.getEntityType() + FullID::DELIMITER
           + systemPath_.asString() + FullID::DELIMITER
           + localID_.getID();
}

} // namespace libecs

/*
  Do not modify
  $Author$
  $Revision$
  $Date$
  $Locker$
*/

//::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
//
//       This file is part of the E-Cell System
//
//       Copyright (C) 1996-2012 Keio University
//       Copyright (C) 2005-2009 The Molecular Sciences Institute
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

#ifndef __ENTITYTYPE_HPP 
#define __ENTITYTYPE_HPP 

#include "libecs/Defs.hpp"


namespace libecs
{

class LIBECS_API EntityType
{

public:
    enum Type
    {
        NONE        = 0,
        ENTITY      = 1,
        VARIABLE    = 2,
        PROCESS     = 3,
        SYSTEM      = 4
    };


    EntityType( String const& typestring );


    EntityType( const int number );


    EntityType( const Type type )
        : theType( type )
    {
        ; // do nothing
    }


    EntityType( EntityType const& primitivetype )
        : theType( primitivetype.getType() )
    {
        ; // do nothing
    }


    EntityType()
        : theType( NONE )
    {
        ; // do nothing
    }

        
    String const& asString() const;

    /** @deprecated use asString() instead. */
    LIBECS_DEPRECATED String const& getString()
    {
        return asString();
    }

    operator String const&() const
    {
        return asString();
    }

    const Type& getType() const
    {
        return theType;
    }

    operator const Type&() const
    {
        return getType();
    }

    bool operator<( EntityType const& rhs ) const
    {
        return theType < rhs.getType();
    }

    bool operator<( const Type rhs ) const
    {
        return theType < rhs;
    }

    bool operator==( EntityType const& rhs ) const
    {
        return theType == rhs.getType();
    }

    bool operator==( const Type rhs ) const
    {
        return theType == rhs;
    }


    static const String entityTypeStringOfNone;

    static const String entityTypeStringOfEntity;

    static const String entityTypeStringOfProcess;
    
    static const String entityTypeStringOfVariable;
    
    static const String entityTypeStringOfSystem;

private:

    Type theType;
};

} // namespace libecs

#endif /* __ENTITYTYPE_HPP */

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

#ifndef __INTERPOLANT_HPP
#define __INTERPOLANT_HPP

#include "libecs/Defs.hpp"

namespace libecs
{
class Stepper;
class Variable;

class LIBECS_API Interpolant
{
    friend class libecs::Stepper;

public:
    class VariablePtrCompare
    {
    public:
        bool operator()( Interpolant const* aLhs, 
                         Interpolant const* aRhs ) const
        {
            return compare( aLhs->getVariable(), aRhs->getVariable() );
        }

        bool operator()( Interpolant const* aLhs,
                         Variable const* aRhs ) const
        {
            return compare( aLhs->getVariable(), aRhs );
        }

        bool operator()( Variable const* aLhs, 
                         Interpolant const* aRhs ) const
        {
            return compare( aLhs, aRhs->getVariable() );
        }

    private:
        // if statement can be faster than returning an expression directly
        static bool compare( Variable const* aLhs, 
                             Variable const* aRhs )
        {
            return aLhs < aRhs;
        }
    };


    Interpolant( Variable const* aVariable, Stepper const* aStepper )
        : theVariable( aVariable ), theStepper( aStepper )
    {
        // do nothing
    }


    virtual ~Interpolant();
    
    virtual const Real getVelocity( Real aTime ) const
    {
        return 0.0;
    }
    
    virtual const Real getDifference( Real aTime, Real anInterval ) const
    {
        return 0.0;
    }
     
    Variable const* getVariable() const
    {
        return theVariable;
    }

    Stepper const* getStepper() const
    {
        return theStepper;
    }

protected:
    Variable const* theVariable;
    Stepper const* theStepper;
};

} // namespace libecs

#endif /* __INTERPOLANT_HPP */

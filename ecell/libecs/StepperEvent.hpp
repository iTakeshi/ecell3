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

#ifndef __STEPPEREVENT_HPP
#define __STEPPEREVENT_HPP

#include "libecs.hpp"
#include "Stepper.hpp"
#include "EventBase.hpp"

/** @file */
namespace libecs {

class StepperEvent: public EventBase
{
public:
    StepperEvent( TimeParam aTime, Stepper* stepper )
        : EventBase( aTime ), stepper_( stepper )
    {
        ; // do nothing
    }

    void fire()
    {
        stepper_->integrate( getTime() );
        stepper_->step();
        stepper_->log();

        reschedule();
    }

    void update( TimeParam aTime )
    {
        stepper_->interrupt( aTime );

        reschedule();
    }

    void reschedule()
    {
        const Time aLocalTime( stepper_->getCurrentTime() );
        const Time aNewStepInterval( stepper_->getStepInterval() );
        setTime( aNewStepInterval + aLocalTime );
    }

    const bool isDependentOn( const StepperEvent& anEvent ) const
    {
        return stepper_->isDependentOn( anEvent.getStepper() );
    }

    const Stepper* getStepper() const
    {
        return stepper_;
    }

    // this method is basically used in initializing and rescheduling
    // in the Scheduler to determine if
    // goUp()/goDown (position change) is needed
    bool operator <( const StepperEvent& rhs ) const
    {
        if ( getTime() > rhs.getTime() )
        {
            return false;
        }
        if ( getTime() < rhs.getTime() )
        {
            return true;
        }
        if ( stepper_->getPriority() < rhs.getStepper()->getPriority() )
        {
            return true;
        }
        return false;
    }

    bool operator >( const StepperEvent& rhs ) const
    {
        if ( getTime() < rhs.getTime() )
        {
            return false;
        }
        if ( getTime() > rhs.getTime() )
        {
            return true;
        }
        if ( stepper_->getPriority() > rhs.getStepper()->getPriority() )
        {
            return true;
        }
        return false;
    }

    bool operator <=( const StepperEvent& rhs ) const
    {
        return !operator>( rhs );
    }

    bool operator >=( const StepperEvent& rhs ) const
    {
        return !operator<( rhs );
    }

    bool operator==( const StepperEvent& rhs ) const
    {
         return getStepper() == rhs.getStepper() &&
                getTime() == rhs.getTime();
    }

    bool operator!=( const StepperEvent& rhs ) const
    {
        return !operator==( rhs );
    }

private:
    Stepper* stepper_;
};

} // namespace libecs

#endif /* __STEPPEREVENT_HPP */


/*
  Do not modify
  $Author$
  $Revision$
  $Date$
  $Locker$
*/


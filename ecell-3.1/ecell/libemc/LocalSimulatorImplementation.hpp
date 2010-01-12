//::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
//
//       This file is part of the E-Cell System
//
//       Copyright (C) 1996-2010 Keio University
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

#ifndef __LOCALSIMULATORIMPLEMENTATION_HPP
#define __LOCALSIMULATORIMPLEMENTATION_HPP

#ifdef DLL_EXPORT
#undef DLL_EXPORT
#define _DLL_EXPORT
#endif /* DLL_EXPORT */

#include "libecs/libecs.hpp"
#include "libecs/Model.hpp"

#ifdef _DLL_EXPORT
#define DLL_EXPORT
#undef _DLL_EXPORT
#endif /* _DLL_EXPORT */

#include "libemc.hpp"
#include "SimulatorImplementation.hpp"


namespace libemc
{

  /** @defgroup libemc_module The Libemc Module 
   * This is the libemc module 
   * @{ 
   */ 
  
  class LIBEMC_API LocalSimulatorImplementation
    :
    public SimulatorImplementation
  {

  public:

    LocalSimulatorImplementation();
    virtual ~LocalSimulatorImplementation();

    virtual void createStepper( libecs::StringCref         aClassname,
				libecs::StringCref         anId );

    virtual void deleteStepper( libecs::StringCref anID );

    virtual const libecs::Polymorph getStepperList() const;

    virtual const libecs::Polymorph 
    getStepperPropertyList( libecs::StringCref aStepperID ) const;

    virtual const libecs::Polymorph 
    getStepperPropertyAttributes( libecs::StringCref aStepperID, 
				  libecs::StringCref aPropertyName ) const;

    virtual void setStepperProperty( libecs::StringCref    aStepperID,
				     libecs::StringCref    aPropertyName,
				     libecs::PolymorphCref aValue );

    virtual const libecs::Polymorph
    getStepperProperty( libecs::StringCref aStepperID,
			libecs::StringCref aPropertyName ) const;

    virtual void loadStepperProperty( libecs::StringCref    aStepperID,
				      libecs::StringCref    aPropertyName,
				      libecs::PolymorphCref aValue );

    virtual const libecs::Polymorph
    saveStepperProperty( libecs::StringCref aStepperID,
			 libecs::StringCref aPropertyName ) const;

    virtual const libecs::String
    getStepperClassName( libecs::StringCref aStepperID ) const;


    virtual const libecs::PolymorphMap
	   	 getClassInfo( libecs::StringCref aClasstype,
			       libecs::StringCref aClassname,
			       const libecs::Integer forceReload );

    
    virtual void createEntity( libecs::StringCref aClassname, 
			       libecs::StringCref aFullIDString );

    virtual void deleteEntity( libecs::StringCref aFullIDString );

    virtual const libecs::Polymorph 
    getEntityList( libecs::StringCref anEntityTypeString,
		   libecs::StringCref aSystemPathString ) const;

    virtual const libecs::Polymorph 
    getEntityPropertyList( libecs::StringCref aFullID ) const;

    virtual const bool isEntityExist( libecs::StringCref aFullIDString ) const;

    virtual void setEntityProperty( libecs::StringCref    aFullPNString,
				    libecs::PolymorphCref aValue );

    virtual const libecs::Polymorph
    getEntityProperty( libecs::StringCref aFullPNString ) const;

    virtual void loadEntityProperty( libecs::StringCref    aFullPNString,
				     libecs::PolymorphCref aValue );

    virtual const libecs::Polymorph
    saveEntityProperty( libecs::StringCref aFullPNString ) const;

    virtual const libecs::Polymorph
    getEntityPropertyAttributes( libecs::StringCref aFullPNString ) const;

    virtual const libecs::String
    getEntityClassName( libecs::StringCref aFullIDString ) const;

    virtual void createLogger( libecs::StringCref aFullPNString );

    virtual void createLogger( libecs::StringCref aFullPNString, libecs::Polymorph aParamList  );

    virtual const libecs::Polymorph getLoggerList() const;

    virtual const libecs::DataPointVectorSharedPtr 
    getLoggerData( libecs::StringCref aFullPNString ) const;

    virtual const libecs::DataPointVectorSharedPtr
    getLoggerData( libecs::StringCref aFullPNString, 
		   libecs::RealCref start, libecs::RealCref end ) const;

    virtual const libecs::DataPointVectorSharedPtr
    getLoggerData( libecs::StringCref aFullPNString,
		   libecs::RealCref start, libecs::RealCref end, 
		   libecs::RealCref interval ) const;

    virtual const libecs::Real 
    getLoggerStartTime( libecs::StringCref aFullPNString ) const;

    virtual const libecs::Real 
    getLoggerEndTime( libecs::StringCref aFullPNString ) const;

    virtual void setLoggerMinimumInterval( libecs::StringCref aFullPNString, 
					   libecs::RealCref anInterval );

    virtual const libecs::Real 
    getLoggerMinimumInterval( libecs::StringCref aFullPNString ) const;


    virtual void 
    setLoggerPolicy( libecs::StringCref aFullPNString, 
			      libecs::Polymorph aParamList ) ;

    virtual const libecs::Polymorph
    getLoggerPolicy( libecs::StringCref aFullPNString ) const;


    virtual const libecs::Logger::size_type 
    getLoggerSize( libecs::StringCref aFullPNString ) const;

    virtual const libecs::Polymorph getNextEvent() const;

    virtual void step( const libecs::Integer aNumSteps );

    virtual const libecs::Real getCurrentTime() const;

    virtual void run();

    virtual void run( const libecs::Real aDuration );

    virtual void stop();

    void clearEventChecker();

    virtual void setEventChecker( EventCheckerSharedPtrCref anEventChecker );

    virtual void setEventHandler( EventHandlerSharedPtrCref anEventHandler );

    virtual const libecs::Polymorph getDMInfo();

    virtual void initialize();

  protected:

    libecs::ModelRef getModel() 
    { 
      return theModel; 
    }

    libecs::ModelCref getModel() const 
    { 
      return theModel; 
    }

    libecs::LoggerPtr getLogger( libecs::StringCref aFullPNString ) const;


    void setDirty()
    {
      theDirtyFlag = true;
    }

    const bool isDirty() const
    {
      return theDirtyFlag;
    }

    inline void handleEvent()
    {
      while( (*theEventChecker)() )
	{
	  (*theEventHandler)();
	}

      clearDirty();
    }

    void clearDirty() const
    {
      if( isDirty() )
	{
	  const_cast< LocalSimulatorImplementation* >( this )->initialize();
	}
    }

    void start()
    {
      clearDirty();
      theRunningFlag = true;
    }

    void runWithEvent( libecs::Real const aStopTime );
    void runWithoutEvent( libecs::Real const aStopTime );

  private:

    bool                          theRunningFlag;

    mutable bool                  theDirtyFlag;

    libecs::Integer               theEventCheckInterval;

    libecs::PropertiedObjectMaker thePropertiedObjectMaker;
    libecs::Model                 theModel;

    EventCheckerSharedPtr         theEventChecker;
    EventHandlerSharedPtr         theEventHandler;

  };  

  /** @} */ //end of libemc_module 

} // namespace libemc


#endif   /* __LOCALSIMULATORIMPLEMENTATION_HPP */
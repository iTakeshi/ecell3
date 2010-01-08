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
// written by Koichi Takahashi <shafi@e-cell.org> for
// E-Cell Project.
//


#include <signal.h>
#include <string.h>

#include <boost/cast.hpp>
#include <boost/python.hpp>
#include <boost/python/suite/indexing/vector_indexing_suite.hpp>

#include <numpy/arrayobject.h>

#include "libecs/libecs.hpp"
#include "libecs/Process.hpp"
#include "libecs/Exceptions.hpp"
#include "libecs/Polymorph.hpp"
#include "libecs/DataPointVector.hpp"
#include "libecs/VariableReference.hpp"
#include "libemc/libemc.hpp"
#include "libemc/Simulator.hpp"

using namespace libecs;
using namespace libemc;
namespace python = boost::python;

class Polymorph_to_python
{
public:

  static PyObject* convert( libecs::PolymorphCref aPolymorph )
  {
    switch( aPolymorph.getType() )
      {
      case libecs::Polymorph::REAL :
	return PyFloat_FromDouble( aPolymorph.asReal() );
      case libecs::Polymorph::INTEGER :
	return PyInt_FromLong( aPolymorph.asInteger() );
      case libecs::Polymorph::POLYMORPH_VECTOR :
	return PolymorphVector_to_PyTuple( aPolymorph.asPolymorphVector() );
      case libecs::Polymorph::STRING :
      case libecs::Polymorph::NONE :
      default: // should this default be an error?
	return PyString_FromString( aPolymorph.asString().c_str() );
      }
  }

  static PyObject* 
  PolymorphVector_to_PyTuple( libecs::PolymorphVectorCref aVector )
  {
    libecs::PolymorphVector::size_type aSize( aVector.size() );
    
    PyObject* aPyTuple( PyTuple_New( aSize ) );
    
    for( size_t i( 0 ) ; i < aSize ; ++i )
      {
	PyTuple_SetItem( aPyTuple, i, 
			 Polymorph_to_python::convert( aVector[i] ) );
      }
    
    return aPyTuple;
  }


};


class DataPointVectorSharedPtr_to_python
{
public:

  static PyObject* 
  convert( const libecs::DataPointVectorSharedPtr& aVectorSharedPtr )
  {
    // here starts an ugly C hack :-/

    libecs::DataPointVectorCref aVector( *aVectorSharedPtr );

    npy_intp aDimensions[2] = { aVector.getSize(),
			   aVector.getElementSize() / sizeof( double ) };


    PyArrayObject* anArrayObject( reinterpret_cast<PyArrayObject*>
				  ( PyArray_New( &PyArray_Type, 2, aDimensions, 
						      PyArray_DOUBLE, NULL, NULL, 0, 0, NULL ) ) );

    memcpy( anArrayObject->data, aVector.getRawArray(),   
	    aVector.getSize() * aVector.getElementSize() );
    
    return PyArray_Return( anArrayObject );
  }

};


class register_Polymorph_from_python
{
public:

  register_Polymorph_from_python()
  {
    python::converter::
      registry::insert( &convertible, &construct,
			python::type_id<libecs::Polymorph>() );
  }

  static void* convertible( PyObject* aPyObject )
  {
    // always passes the test for efficiency.  overload won't work.
    return aPyObject;
  }

  static void construct( PyObject* aPyObjectPtr, 
			 python::converter::
			 rvalue_from_python_stage1_data* data )
  {
    void* storage( ( ( python::converter::
		       rvalue_from_python_storage<libecs::Polymorph>*) 
		     data )->storage.bytes );

    new (storage) libecs::Polymorph( Polymorph_from_python( aPyObjectPtr ) );
    data->convertible = storage;
  }


  static const libecs::Polymorph 
  Polymorph_from_python( PyObject* aPyObjectPtr )
  {
    if( PyFloat_Check( aPyObjectPtr ) )
      {
	return PyFloat_AS_DOUBLE( aPyObjectPtr );
      }
    else if( PyInt_Check( aPyObjectPtr ) )
      {
	return PyInt_AS_LONG( aPyObjectPtr );
      }
    else if ( PyTuple_Check( aPyObjectPtr ) )
      {
	return to_PolymorphVector( aPyObjectPtr );
      }
    else if( PyList_Check( aPyObjectPtr ) )
      {
	return to_PolymorphVector( PyList_AsTuple( aPyObjectPtr ) );
      }      
    else if( PyString_Check( aPyObjectPtr ) )
      {
	return libecs::Polymorph( PyString_AsString( aPyObjectPtr ) );
      }
	// conversion is failed. ( convert with repr() ? )
	PyErr_SetString( PyExc_TypeError, 
			 "Unacceptable type of an object in the tuple." );
	python::throw_error_already_set();
    // never get here: the following is for suppressing warnings
    return libecs::Polymorph();
  }


  static const libecs::PolymorphVector 
  to_PolymorphVector( PyObject* aPyObjectPtr )
  {
    std::size_t aSize( PyTuple_GET_SIZE( aPyObjectPtr ) );
      
    libecs::PolymorphVector aVector;
    aVector.reserve( aSize );
      
    for ( std::size_t i( 0 ); i < aSize; ++i )
      {
	aVector.
	  push_back( Polymorph_from_python( PyTuple_GET_ITEM( aPyObjectPtr, 
							      i ) ) );
      }
      
    return aVector;
  }
    
};

class PolymorphMap_to_python
{
public:
static PyObject* convert(const libecs::PolymorphMap& aPolymorphMapCref )
{
	//Polymorph_to_python aPolymorphConverter;
	PyObject * aPyDict(PyDict_New());
	libecs::PolymorphMap aPolymorphMap( aPolymorphMapCref );
	for (libecs::PolymorphMap::iterator i=aPolymorphMap.begin();
			i!=aPolymorphMap.end();++i)
	{
	PyDict_SetItem( aPyDict, PyString_FromString( i->first.c_str() ),
			Polymorph_to_python::convert( i->second ) );
			
	}
	return aPyDict;
}

};


// exception translators

//void translateException( libecs::ExceptionCref anException )
//{
//  PyErr_SetString( PyExc_RuntimeError, anException.what() );
//}

void translateException( const std::exception& anException )
{
  PyErr_SetString( PyExc_RuntimeError, anException.what() );
}


static PyObject* getLibECSVersionInfo()
{
  PyObject* aPyTuple( PyTuple_New( 3 ) );
    
  PyTuple_SetItem( aPyTuple, 0, PyInt_FromLong( libecs::getMajorVersion() ) );
  PyTuple_SetItem( aPyTuple, 1, PyInt_FromLong( libecs::getMinorVersion() ) );
  PyTuple_SetItem( aPyTuple, 2, PyInt_FromLong( libecs::getMicroVersion() ) );
  
  return aPyTuple;
}

// module initializer / finalizer
static struct _
{
  inline _()
  {
    if (!libecs::initialize())
      {
	throw std::runtime_error( "Failed to initialize libecs" );
      }
  }

  inline ~_()
  {
    libecs::finalize();
  }
} _;


class PythonWarningHandler
  : 
  public libecs::WarningHandler
{
public:

  PythonWarningHandler() {}

  PythonWarningHandler( boost::python::handle<> aCallable )
    : thePyObject( aCallable )
  {
    ; // do nothing
  }
    
  virtual ~PythonWarningHandler() {}

  virtual void operator()( String const& msg ) const
  {
    if ( thePyObject )
      PyObject_CallFunctionObjArgs( thePyObject.get(), python::object( msg ).ptr(), NULL );
  }

private:
  boost::python::handle<> thePyObject;
};


struct PySimulator: public libemc::Simulator
{
  struct WrappingEventChecker
    :
    public libemc::EventChecker
  {
    virtual ~WrappingEventChecker()
    {
      ; // do nothing
    }

    virtual bool operator()( void ) const
    {
      if ( PyErr_CheckSignals() )
	{
	  theSimulator.stop();
	  return false;
	}
      else if ( PyErr_Occurred() )
	{
	  theSimulator.stop();
	  python::throw_error_already_set();
	}
      return theEventCheckerImpl && PyObject_IsTrue( boost::python::handle<>( PyObject_CallFunction( theEventCheckerImpl.get(), NULL ) ).get() );
    }

    void setEventChecker( boost::python::handle<> aChecker )
    {
      theEventCheckerImpl = aChecker;
    }

    WrappingEventChecker( libemc::Simulator& aSimulator  )
      : theSimulator( aSimulator )
    {
      ; // do nothing
    }
  private:
    boost::python::handle<> theEventCheckerImpl;
    Simulator& theSimulator;
  };

  class WrappingEventHandler
    : 
    public libemc::EventHandler
  {
  public:
    virtual ~WrappingEventHandler() {}

    virtual void operator()( void ) const
    {
      if ( theEventHandlerImpl )
	{
	  PyObject_CallFunction( theEventHandlerImpl.get(), NULL );
	}
    }

    void setEventHandler( boost::python::handle<> aHandler )
    {
      theEventHandlerImpl = aHandler;
    }

  private:
    boost::python::handle<> theEventHandlerImpl;
  };

  DECLARE_SHAREDPTR( WrappingEventChecker )
  DECLARE_SHAREDPTR( WrappingEventHandler )

  void setEventChecker( boost::python::handle<> const& checker )
  {
    theWrappingEventChecker->setEventChecker( checker );
  }

  void setEventHandler( boost::python::handle<> const& handler )
  {
    theWrappingEventHandler->setEventHandler( handler );
  }

  PySimulator()
    :
    libemc::Simulator(),
    theWrappingEventHandler( new WrappingEventHandler() ),
    theWrappingEventChecker( new WrappingEventChecker( *this ) )
  {
    libemc::Simulator::setEventChecker( theWrappingEventChecker ); 
    libemc::Simulator::setEventHandler( theWrappingEventHandler );
  }

private:
  WrappingEventHandlerSharedPtr theWrappingEventHandler;
  WrappingEventCheckerSharedPtr theWrappingEventChecker;
};


static void setWarningHandler( boost::python::handle<> const& aHandler )
{
  static PythonWarningHandler theHandler;
  theHandler = aHandler;
  libecs::setWarningHandler( &theHandler );
}


BOOST_PYTHON_MODULE( _ecs )
{
  using namespace boost::python;

  if (!libecs::initialize())
    {
      throw std::runtime_error( "Failed to initialize libecs" );
    }

  // without this it crashes when Logger::getData() is called. why?
  import_array();

  // functions

  to_python_converter< Polymorph, Polymorph_to_python >();
  to_python_converter< DataPointVectorSharedPtr, 
    DataPointVectorSharedPtr_to_python >();
  to_python_converter< PolymorphMap, PolymorphMap_to_python>();
  
  register_Polymorph_from_python();

  register_exception_translator<Exception>     ( &translateException );
  register_exception_translator<std::exception>( &translateException );

  def( "getLibECSVersionInfo", &getLibECSVersionInfo );
  def( "getLibECSVersion",     &libecs::getVersion );

  def( "setDMSearchPath", &libecs::setDMSearchPath );
  def( "getDMSearchPath", &libecs::getDMSearchPath );
  def( "setWarningHandler", &::setWarningHandler );

  class_<VariableReference>( "VariableReference", no_init )

    // properties
    .add_property( "Coefficient",
		   &VariableReference::getCoefficient )   // read-only
    .add_property( "MolarConc", 
		   &VariableReference::getMolarConc ) // read-only
    .add_property( "Name", 
		   &VariableReference::getName ) // read-only
    .add_property( "NumberConc", 
		   &VariableReference::getNumberConc ) // read-only
    .add_property( "IsFixed",
    		   &VariableReference::isFixed )      // read-only
    .add_property( "IsAccessor",
    		   &VariableReference::isAccessor )       // read-only
    .add_property( "Value", 
		   &VariableReference::getValue, 
		   &VariableReference::setValue )
    .add_property( "Velocity",
		   &VariableReference::getVelocity )

    // methods
    .def( "addValue",    &VariableReference::addValue )
    .def( "getSuperSystem",  // this should be a property, but not supported
	  &VariableReference::getSuperSystem,
	  python::return_value_policy<python::reference_existing_object>() )
    ;

  class_<Process, bases<>, Process, boost::noncopyable>
    ( "Process", no_init )

    // properties
    .add_property( "Activity",
		   &Process::getActivity,
		   &Process::setActivity )
    .add_property( "Priority",
		   &Process::getPriority )
    .add_property( "StepperID",
		   &Process::getStepperID )

    // methods
    .def( "addValue",    &Process::addValue )
    .def( "getPositiveVariableReferenceOffset",     
	  &Process::getPositiveVariableReferenceOffset )
    .def( "getSuperSystem",   // this can be a property, but not supported
	  &Process::getSuperSystem,
	  python::return_value_policy<python::reference_existing_object>() )
    .def( "getVariableReference",       // this should be a property
	  &Process::getVariableReference,
	  python::return_internal_reference<>() )
    .def( "getVariableReferenceVector",       // this should be a property
	  &Process::getVariableReferenceVector,
	  python::return_value_policy<python::reference_existing_object>() )
    .def( "getZeroVariableReferenceOffset",     
	  &Process::getZeroVariableReferenceOffset )
    .def( "setFlux",     &Process::setFlux )
    ;


  class_<System, bases<>, System, boost::noncopyable>( "System", no_init )

    // properties
    .add_property( "Size",
		   &System::getSize )
    .add_property( "SizeN_A",
		   &System::getSizeN_A )
    .add_property( "StepperID",
		   &System::getStepperID )
    // methods
    .def( "getSuperSystem",   // this should be a property, but not supported
	  &System::getSuperSystem,
	  python::return_value_policy<python::reference_existing_object>() )
    ;



  class_<VariableReferenceVector>( "VariableReferenceVector" )
    //, bases<>, VariableReferenceVector>

    .def( vector_indexing_suite<VariableReferenceVector>() )
    ;


  // Simulator class
  class_<PySimulator>( "Simulator" )
    .def( init<>() )
    .def( "getClassInfo",
	  ( const libecs::PolymorphMap
	    ( PySimulator::* )( libecs::StringCref, libecs::StringCref ) )
	  &PySimulator::getClassInfo )
    .def( "getClassInfo",
	  ( const libecs::PolymorphMap
	    ( PySimulator::* )( libecs::StringCref, libecs::StringCref,
                                  const libecs::Integer ) )
	  &PySimulator::getClassInfo )
    // Stepper-related methods
    .def( "createStepper",
	  &PySimulator::createStepper )
    .def( "deleteStepper",
	  &PySimulator::deleteStepper )
    .def( "getStepperList",
	  &PySimulator::getStepperList )
    .def( "getStepperPropertyList",
	  &PySimulator::getStepperPropertyList )
    .def( "getStepperPropertyAttributes", 
	  &PySimulator::getStepperPropertyAttributes )
    .def( "setStepperProperty",
	  &PySimulator::setStepperProperty )
    .def( "getStepperProperty",
	  &PySimulator::getStepperProperty )
    .def( "loadStepperProperty",
	  &PySimulator::loadStepperProperty )
    .def( "saveStepperProperty",
	  &PySimulator::saveStepperProperty )
    .def( "getStepperClassName",
	  &PySimulator::getStepperClassName )

    // Entity-related methods
    .def( "createEntity",
	  &PySimulator::createEntity )
    .def( "deleteEntity",
	  &PySimulator::deleteEntity )
    .def( "getEntityList",
	  &PySimulator::getEntityList )
    .def( "isEntityExist",
	  &PySimulator::isEntityExist )
    .def( "getEntityPropertyList",
	  &PySimulator::getEntityPropertyList )
    .def( "setEntityProperty",
	  &PySimulator::setEntityProperty )
    .def( "getEntityProperty",
	  &PySimulator::getEntityProperty )
    .def( "loadEntityProperty",
	  &PySimulator::loadEntityProperty )
    .def( "saveEntityProperty",
	  &PySimulator::saveEntityProperty )
    .def( "getEntityPropertyAttributes", 
	  &PySimulator::getEntityPropertyAttributes )
    .def( "getEntityClassName",
	  &PySimulator::getEntityClassName )

    // Logger-related methods
    .def( "getLoggerList",
	  &PySimulator::getLoggerList )  
    .def( "createLogger",
	  ( void ( PySimulator::* )( libecs::StringCref ) )
	  &PySimulator::createLogger )  
    .def( "createLogger",		 
	  ( void ( PySimulator::* )( libecs::StringCref,
					   libecs::Polymorph ) )
	  &PySimulator::createLogger )  
    .def( "getLoggerData", 
	  ( const libecs::DataPointVectorSharedPtr
	    ( PySimulator::* )( libecs::StringCref ) const )
	  &PySimulator::getLoggerData )
    .def( "getLoggerData", 
	  ( const libecs::DataPointVectorSharedPtr 
	    ( PySimulator::* )( libecs::StringCref,
				      libecs::RealCref,
				      libecs::RealCref ) const )
	  &PySimulator::getLoggerData )
    .def( "getLoggerData",
	  ( const libecs::DataPointVectorSharedPtr
	    ( PySimulator::* )( libecs::StringCref,
				      libecs::RealCref, 
				      libecs::RealCref,
				      libecs::RealCref ) const )
	  &PySimulator::getLoggerData )
    .def( "getLoggerStartTime",
	  &PySimulator::getLoggerStartTime )  
    .def( "getLoggerEndTime",
	  &PySimulator::getLoggerEndTime )    
    .def( "getLoggerMinimumInterval",
          &PySimulator::getLoggerMinimumInterval )
    .def( "setLoggerMinimumInterval",
          &PySimulator::setLoggerMinimumInterval )
    .def( "getLoggerPolicy",
	  &PySimulator::getLoggerPolicy )
    .def( "setLoggerPolicy",
	  &PySimulator::setLoggerPolicy )
    .def( "getLoggerSize",
	  &PySimulator::getLoggerSize )

    // Simulation-related methods
    .def( "getCurrentTime",
	  &PySimulator::getCurrentTime )
    .def( "getNextEvent",
	  &PySimulator::getNextEvent )
    .def( "stop",
	  &PySimulator::stop )
    .def( "step",
	  ( void ( PySimulator::* )( void ) )
	  &PySimulator::step )
    .def( "step",
	  ( void ( PySimulator::* )( const libecs::Integer ) )
	  &PySimulator::step )
    .def( "run",
	  ( void ( PySimulator::* )() )
	  &PySimulator::run )
    .def( "run",
	  ( void ( PySimulator::* )( const libecs::Real ) ) 
	  &PySimulator::run )
    .def( "setEventChecker",
	  &PySimulator::setEventChecker )
    .def( "setEventHandler",
	  &PySimulator::setEventHandler )
    .def( "initialize",
      &PySimulator::initialize )
    ;  

}

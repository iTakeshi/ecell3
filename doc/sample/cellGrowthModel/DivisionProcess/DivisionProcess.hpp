//::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
//
//       This file is part of the E-Cell System
//
//       Copyright (C) 1996-2007 Keio University
//       Copyright (C) 2005-2007 The Molecular Sciences Institute
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
// Contact information:
//   Nathan Addy, Research Associate     Voice: 510-981-8748
//   The Molecular Sciences Institute    Email: addy@molsci.org  
//   2168 Shattuck Ave.                  
//   Berkeley, CA 94704
//
//END_HEADER

#ifndef __DIVISIONPROCESS_HPP
#define __DIVISIONPROCESS_HPP

#include <libecs/libecs.hpp>
#include <libecs/Model.hpp>
#include <libecs/Process.hpp>
#include <libecs/System.hpp>

#include <dm/PythonProcessBase.hpp>


USE_LIBECS;

LIBECS_DM_CLASS( DivisionProcess, PythonProcessBase )
{
  
 public:
  LIBECS_DM_OBJECT( DivisionProcess, Process )
    {
      INHERIT_PROPERTIES( PythonProcessBase );
      
      PROPERTYSLOT_SET_GET( String, Expression );
      PROPERTYSLOT_SET_GET( String, InitializeMethod );
    }

  DivisionProcess()
    :
    theInitializeMethod( "" ),
    theExpression( "False" )
    {
      ; // do nothing
    }

  ~DivisionProcess() 
    {
      ; // do nothing
    }

  virtual void initialize();
  virtual void fire();

  SET_METHOD( String, InitializeMethod )
    {
      theInitializeMethod = value;
      
      theCompiledInitializeMethod = compilePythonCode( theInitializeMethod,
                                                       getFullID().getString() +
                                                       ":InitializeMethod",
                                                       Py_file_input );
    }

  SET_METHOD( String, Expression )
    {
      theExpression = value;

      theCompiledExpressionMethod = compilePythonCode( theExpression,
                                                       getFullID().getString() +
                                                       ":FireMethod",
                                                       Py_file_input );      
    }


  GET_METHOD( String, InitializeMethod )
    {
      return theInitializeMethod;
    }


  GET_METHOD( String, Expression )
    {
      return theExpression;
    }
  

 private:
  void divideCell();

  SystemPtr createNewCellWithName( StringCref cellName );
  void halveSystemVariables( SystemPtr systemToHalf);
  void copySubsystemsToSystem( SystemPtr fromSystem, SystemPtr toSystem);
  void copyVariablesToSystem( SystemPtr fromSystem, SystemPtr toSystem);
  void copyProcessesToSystem( SystemPtr fromSystem, SystemPtr toSystem);

  void copyPropertiesBetweenEntities( const EntityPtr fromentity, EntityPtr toEntity, StringVectorCref propertiesNotToCopy);
  void copyVariableReferenceListPropertyBetweenProcesses(const ProcessPtr fromProcess, ProcessPtr toProcess);

  String getNextCellName();




 private:  
  String theInitializeMethod;  
  String theExpression;

  python::object theCompiledExpressionMethod;
  python::object theCompiledInitializeMethod;

 private:
  static Integer numberOfCells;



};

#endif

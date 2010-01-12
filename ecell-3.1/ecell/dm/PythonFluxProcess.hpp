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
// authors:
// Koichi Takahashi <shafi@e-cell.org>
// Nayuta Iwata
//
// E-Cell Project.
//

#ifndef __PYTHONFLUXPROCESS_HPP
#define __PYTHONFLUXPROCESS_HPP

#include "PythonProcessBase.hpp"

USE_LIBECS;

LIBECS_DM_CLASS( PythonFluxProcess, PythonProcessBase )
{

public:
  
  LIBECS_DM_OBJECT( PythonFluxProcess, Process )
    {
      INHERIT_PROPERTIES( Process );

      PROPERTYSLOT_SET_GET( String, Expression );
    }


  PythonFluxProcess()
  {
    //FIXME: additional properties:
    // Unidirectional   -> call declareUnidirectional() in initialize()
    //                     if this is set
  }

  virtual ~PythonFluxProcess()
  {
    ; // do nothing
  }

  virtual const bool isContinuous() const
    {
      return true;
    }

  SET_METHOD( String, Expression )
  {
    theExpression = value;

    theCompiledExpression = compilePythonCode( theExpression,
					       getFullID().getString() +
					       ":Expression",
					       Py_eval_input );
  }

  GET_METHOD( String, Expression )
  {
    return theExpression;
  }

  virtual void fire();

protected:

  String    theExpression;

  python::object theCompiledExpression;

};


#endif /* __PYTHONFLUXPROCESS_HPP */
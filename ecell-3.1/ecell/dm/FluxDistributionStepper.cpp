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
// written by Tomoya Kitayama <tomo@e-cell.org>,
// E-Cell Project.
//

#define GSL_RANGE_CHECK_OFF
#include <gsl/gsl_linalg.h>
#include <gsl/gsl_blas.h>

#include <map>

#include "libecs/DifferentialStepper.hpp"
#include "libecs/Model.hpp"
#include "libecs/Variable.hpp"

#include "QuasiDynamicFluxProcess.hpp"

USE_LIBECS;

LIBECS_DM_CLASS( FluxDistributionStepper, DifferentialStepper )
{  

  DECLARE_VECTOR( QuasiDynamicFluxProcessPtr, QuasiDynamicFluxProcessVector );
  
 public:
  
  LIBECS_DM_OBJECT( FluxDistributionStepper, DifferentialStepper )
    {
      INHERIT_PROPERTIES( Stepper );
      PROPERTYSLOT_SET_GET( Real, Epsilon );
    }
  
  FluxDistributionStepper();
  ~FluxDistributionStepper();

  SIMPLE_SET_GET_METHOD( Real, Epsilon );

  virtual void initialize();

  virtual void interrupt( StepperPtr const aCaller )
    {
      integrate( aCaller->getCurrentTime() );

      VariableVector::size_type aVariableVectorSize( theVariableVector.size() );  
      for( VariableVector::size_type i( 0 ); i < aVariableVectorSize; i++ )
	{
	  theTaylorSeries[ 0 ][ i ] = 0.0;
	}

      for( VariableVector::size_type i( 0 ); i < aVariableVectorSize; i++ )
	{
	  gsl_vector_set( theVariableVelocityVector, i, theVariableVector[i]->getVelocity() );
	}
      
      clearVariables();

      gsl_blas_dgemv( CblasNoTrans, -1.0, theInverseMatrix, 
		      theVariableVelocityVector, 0.0, theFluxVector );
      
      //
      // check Irreversible
      //

      if( theIrreversibleFlag )
	{
	  
	  QuasiDynamicFluxProcessVector aTmpQuasiDynamicFluxProcessVector = theQuasiDynamicFluxProcessVector;

	  gsl_matrix* aTmpUnknownMatrix;
	  aTmpUnknownMatrix = gsl_matrix_calloc( theMatrixSize, theMatrixSize );
	  gsl_matrix_memcpy( aTmpUnknownMatrix, theUnknownMatrix ); 

	  while( 1 )
	    {
	      bool aFlag( false );
	      
	      QuasiDynamicFluxProcessVector::size_type aProcessSize( theQuasiDynamicFluxProcessVector.size() );
	      for( QuasiDynamicFluxProcessVector::size_type i( 0 ); i < aProcessSize; ++i )
		{
		  QuasiDynamicFluxProcessVector::size_type anIrreversibleProcessVectorSize( theIrreversibleProcessVector.size() );
		  for( QuasiDynamicFluxProcessVector::size_type j( 0 ); j < anIrreversibleProcessVectorSize; ++j )
		    {
		      
		      if( theQuasiDynamicFluxProcessVector[i] == theIrreversibleProcessVector[j] )
			{

			  if( gsl_vector_get( theFluxVector, i ) < 0 )
			    {
			      aFlag = true;
			      VariableReferenceVector aVariableReferenceVector( theQuasiDynamicFluxProcessVector[i]->getFluxDistributionVector() );
			      VariableReferenceVector::size_type aVariableReferenceVectorSize( aVariableReferenceVector.size() );  
			      for( VariableReferenceVector::size_type k( 0 ); k < aVariableReferenceVectorSize; ++k )
				{
				  gsl_matrix_set( aTmpUnknownMatrix, theVariableMap.find( aVariableReferenceVector[k].getVariable() )->second, i, 0.0 );
				}
			    } 
			}
		    }	      
		}

	      if( aFlag )
		{	
		  gsl_matrix* aTmpInverseMatrix;
		  aTmpInverseMatrix = generateInverse( aTmpUnknownMatrix , theMatrixSize );
		  gsl_blas_dgemv( CblasNoTrans, -1.0, aTmpInverseMatrix, 
				  theVariableVelocityVector, 0.0, theFluxVector );
		  gsl_matrix_free( aTmpInverseMatrix );
		}
	      else
		{
		  break;
		}
	    }

	  gsl_matrix_free( aTmpUnknownMatrix );	  

	}

      QuasiDynamicFluxProcessVector::size_type aSize( theQuasiDynamicFluxProcessVector.size() );
      for( QuasiDynamicFluxProcessVector::size_type i( 0 ); i < aSize; ++i )
	{
	  theQuasiDynamicFluxProcessVector[i]->setActivity( gsl_vector_get( theFluxVector, i ) );  
	}

      setVariableVelocity( theTaylorSeries[ 0 ] );
      step();
      log();

    }
  
  virtual void updateInternalState( Real )
    {
      // do nothing.
    }
  
 protected:

  gsl_matrix* generateInverse( gsl_matrix *m_unknown, 
			       Integer matrix_size );

  QuasiDynamicFluxProcessVector theQuasiDynamicFluxProcessVector;
  QuasiDynamicFluxProcessVector theIrreversibleProcessVector;
  QuasiDynamicFluxProcessVector theVmaxProcessVector;

  gsl_matrix* theUnknownMatrix;
  gsl_matrix* theInverseMatrix;
  gsl_vector* theVariableVelocityVector;
  gsl_vector* theFluxVector;

  Real Epsilon;
  
  std::map< VariablePtr, Integer > theVariableMap;
  Integer theMatrixSize;
  bool theIrreversibleFlag;

};


LIBECS_DM_INIT( FluxDistributionStepper, Stepper );

FluxDistributionStepper::FluxDistributionStepper()
  :
  theUnknownMatrix( NULLPTR ),
  theInverseMatrix( NULLPTR ),
  theVariableVelocityVector( NULLPTR ),
  theFluxVector( NULLPTR ),
  theIrreversibleFlag( false ),
  Epsilon( 1e-6 )
{
  initializeStepInterval( INF );
}

FluxDistributionStepper::~FluxDistributionStepper()
{
  if ( theUnknownMatrix )
    {
      gsl_matrix_free( theUnknownMatrix );
    }
  if ( theInverseMatrix )
		{
			gsl_matrix_free( theInverseMatrix );
		}
	if ( theVariableVelocityVector )
		{
			gsl_vector_free( theVariableVelocityVector );
		}
	if ( theFluxVector )
		{
			gsl_vector_free( theFluxVector );
		}
}

void FluxDistributionStepper::initialize()
{

  DifferentialStepper::initialize();
  
  theVariableMap.clear();
  VariableVector::size_type aVariableVectorSize( theVariableVector.size() );  
  for( VariableVector::size_type i( 0 ); i < aVariableVectorSize; i++ )
    { 
      theVariableMap.insert( std::pair< VariablePtr, Integer >( theVariableVector[i], i ) );
    }
  
  //
  // gsl Matrix & Vector allocation
  //

  if( theProcessVector.size() > theVariableVector.size() )
    {
      theMatrixSize = theProcessVector.size();
    }
  else
    {
      theMatrixSize = theVariableVector.size(); 
    }

  if( theUnknownMatrix != NULLPTR )
    { 
      gsl_matrix_free( theUnknownMatrix );
      gsl_vector_free( theVariableVelocityVector );
      gsl_vector_free( theFluxVector );
    }
  
  theUnknownMatrix          = gsl_matrix_calloc( theMatrixSize, theMatrixSize );
  theVariableVelocityVector = gsl_vector_calloc( theMatrixSize );
  theFluxVector             = gsl_vector_calloc( theMatrixSize );

  //
  // generate theUnknownMatrix
  //

  theQuasiDynamicFluxProcessVector.clear();

  try
    {
      std::transform( theProcessVector.begin(), theProcessVector.end(),
		      std::back_inserter( theQuasiDynamicFluxProcessVector ),
		      DynamicCaster<QuasiDynamicFluxProcessPtr,ProcessPtr>() );
    }
  catch( const libecs::TypeError& )
    {
      THROW_EXCEPTION( InitializationFailed,
		       getClassNameString() +
		       ": Only QuasiDynamicFluxProcesses are allowed to exist "
		       "in this Stepper." );
    }

  QuasiDynamicFluxProcessVector::size_type aProcessVectorSize( theQuasiDynamicFluxProcessVector.size() );  

  for( QuasiDynamicFluxProcessVector::size_type i( 0 ); i < aProcessVectorSize; i++ )
    {    
      VariableReferenceVector aVariableReferenceVector( theQuasiDynamicFluxProcessVector[i]->getFluxDistributionVector() );    

      VariableReferenceVector::size_type aVariableReferenceVectorSize( aVariableReferenceVector.size() );  
      for( VariableReferenceVector::size_type j( 0 ); j < aVariableReferenceVectorSize; j++ )
	{
	  gsl_matrix_set( theUnknownMatrix, theVariableMap.find( aVariableReferenceVector[j].getVariable() )->second, i, aVariableReferenceVector[j].getCoefficient() );
	}
    }

  //
  // set Irreversible & Vmax
  //

  theIrreversibleProcessVector.clear();
  theVmaxProcessVector.clear();

  for( QuasiDynamicFluxProcessVector::size_type i( 0 ); i < aProcessVectorSize; i++ )
    {    
      if( theQuasiDynamicFluxProcessVector[i]->getIrreversible() )
	{
	  theIrreversibleFlag = true;
	  theIrreversibleProcessVector.push_back( theQuasiDynamicFluxProcessVector[i] );
	}

      if( theQuasiDynamicFluxProcessVector[i]->getVmax() != 0 )
	{
	  theVmaxProcessVector.push_back( theQuasiDynamicFluxProcessVector[i] );
	}
    }

  //
  // generate inverse matrix
  //

  if( theInverseMatrix != NULLPTR )
    { 
      gsl_matrix_free( theInverseMatrix );
    }

  theInverseMatrix = generateInverse( theUnknownMatrix , theMatrixSize );
  
}

gsl_matrix* FluxDistributionStepper::generateInverse(gsl_matrix *m_unknown, 
						     Integer matrix_size)
{      
  gsl_matrix *m_tmp1, *m_tmp2, *m_tmp3;
  gsl_matrix *inv;
  gsl_matrix *V; 
  gsl_vector *S, *work;
  
  m_tmp1 = gsl_matrix_calloc(matrix_size,matrix_size);
  m_tmp2 = gsl_matrix_calloc(matrix_size,matrix_size);
  m_tmp3 = gsl_matrix_calloc(matrix_size,matrix_size);
  inv = gsl_matrix_calloc(matrix_size,matrix_size);
  
  V = gsl_matrix_calloc (matrix_size,matrix_size); 
  S = gsl_vector_calloc (matrix_size);             
  work = gsl_vector_calloc (matrix_size);          
      
  gsl_matrix_memcpy(m_tmp1,m_unknown);
  gsl_linalg_SV_decomp(m_tmp1,V,S,work);
      
  //generate Singular Value Matrix
  
  for(int i=0;i<matrix_size;i++){
    Real singular_value = gsl_vector_get(S,i);
    if(singular_value > Epsilon){
      gsl_matrix_set(m_tmp2,i,i,1/singular_value);
    }
    else
      {
	gsl_matrix_set(m_tmp2,i,i,0.0);
      }
  }
  
  gsl_blas_dgemm(CblasNoTrans,CblasTrans,1.0,m_tmp2,m_tmp1,0.0,m_tmp3);
  gsl_blas_dgemm(CblasNoTrans,CblasNoTrans,1.0,V,m_tmp3,0.0,inv);
  
  gsl_matrix_free(m_tmp1);
  gsl_matrix_free(m_tmp2);
  gsl_matrix_free(m_tmp3);
  gsl_matrix_free(V);
  gsl_vector_free(S);

  gsl_vector_free(work);
  
  return inv;  
}
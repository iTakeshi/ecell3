//::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
//
//        This file is part of E-CELL Simulation Environment package
//
//                Copyright (C) 2002 Keio University
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

#include "Variable.hpp"
#include "Process.hpp"

#define GSL_RANGE_CHECK_OFF

#include <gsl/gsl_linalg.h>
#include <gsl/gsl_complex.h>

#include "DAEStepper.hpp"

LIBECS_DM_INIT( DAEStepper, Stepper );

namespace libecs
{

  DAEStepper::DAEStepper()
    :
    theSystemSize( 0 ),
    theJacobianMatrix1( NULLPTR ),
    thePermutation1( NULLPTR ),
    theVelocityVector1( NULLPTR ),
    theSolutionVector1( NULLPTR ),
    theJacobianMatrix2( NULLPTR ),
    thePermutation2( NULLPTR ),
    theVelocityVector2( NULLPTR ),
    theSolutionVector2( NULLPTR ),
    theMaxIterationNumber( 7 ),
    eta( 1.0 ),
    Uround( 1e-16 ),
    theAbsoluteTolerance( 1e-10 ),
    theRelativeTolerance( 1e-10 ),
    theStoppingCriterion( 0.0 ),
    theFirstStepFlag( true ),
    theRejectedStepFlag( false ),
    theJacobianCalculateFlag( true ),
    theAcceptedError( 0.0 ),
    theAcceptedStepInterval( 0.0 ),
    thePreviousStepInterval( 0.001 ),
    theJacobianRecalculateTheta( 0.001 )
  {
    const Real pow913( pow( 9.0, 1.0 / 3.0 ) );

    alpha = ( 12.0 - pow913*pow913 + pow913 ) / 60.0;
    beta = ( pow913*pow913 + pow913 ) * sqrt( 3.0 ) / 60.0;
    gamma = ( 6.0 + pow913*pow913 - pow913 ) / 30.0;

    const Real aNorm( alpha*alpha + beta*beta );
    const Real aStepInterval( getStepInterval() );

    alpha /= aNorm;
    beta /= aNorm;
    gamma = 1.0 / gamma;

    const Real aRatio( theAbsoluteTolerance / theRelativeTolerance );
    rtoler = 0.1 * pow( theRelativeTolerance, 2.0 / 3.0 );
    atoler = rtoler * aRatio;
  }
	    
  DAEStepper::~DAEStepper()
  {
    gsl_matrix_free( theJacobianMatrix1 );
    gsl_permutation_free( thePermutation1 );
    gsl_vector_free( theVelocityVector1 );
    gsl_vector_free( theSolutionVector1 );

    gsl_matrix_complex_free( theJacobianMatrix2 );
    gsl_permutation_free( thePermutation2 );
    gsl_vector_complex_free( theVelocityVector2 );
    gsl_vector_complex_free( theSolutionVector2 );
  }

  void DAEStepper::initialize()
  {
    DifferentialStepper::initialize();

    eta = 1.0;
    theStoppingCriterion
      = std::max( 10.0 * Uround / rtoler,
		  std::min( 0.03, sqrt( rtoler ) ) );

    theFirstStepFlag = true;
    theJacobianCalculateFlag = true;

    const VariableVector::size_type aSize( getReadOnlyVariableOffset() );
    if ( theSystemSize != aSize )
      {
	theSystemSize = aSize;

	theJacobian.resize( aSize );
	for ( VariableVector::size_type c( 0 ); c < aSize; c++ )
	  theJacobian[ c ].resize( aSize );

	if ( theJacobianMatrix1 )
	  gsl_matrix_free( theJacobianMatrix1 );
	theJacobianMatrix1 = gsl_matrix_calloc( aSize, aSize );

	if ( thePermutation1 )
	  gsl_permutation_free( thePermutation1 );
	thePermutation1 = gsl_permutation_alloc( aSize );

	if ( theVelocityVector1 )
	  gsl_vector_free( theVelocityVector1 );
	theVelocityVector1 = gsl_vector_calloc( aSize );

	if ( theSolutionVector1 )
	  gsl_vector_free( theSolutionVector1 );
	theSolutionVector1 = gsl_vector_calloc( aSize );

	theW.resize( aSize * 3 );

	if ( theJacobianMatrix2 )
	  gsl_matrix_complex_free( theJacobianMatrix2 );
	theJacobianMatrix2 = gsl_matrix_complex_calloc( aSize, aSize );

	if ( thePermutation2 )
	  gsl_permutation_free( thePermutation2 );
	thePermutation2 = gsl_permutation_alloc( aSize );

	if ( theVelocityVector2 )
	  gsl_vector_complex_free( theVelocityVector2 );
	theVelocityVector2 = gsl_vector_complex_calloc( aSize );

	if ( theSolutionVector2 )
	  gsl_vector_complex_free( theSolutionVector2 );
	theSolutionVector2 = gsl_vector_complex_calloc( aSize );
      }

    /**
    for ( VariableVector::size_type c( 0 ); c < 3*aSize; ++c )
      theW[ c ] = 0.0;

    thePreviousStepInterval( getStepInterval() );
    */
  }

  void DAEStepper::calculateJacobian()
  {
    UnsignedInt aSize( getReadOnlyVariableOffset() );
    Real aPerturbation;

    for ( VariableVector::size_type i( 0 ); i < aSize; ++i )
      {
	const VariablePtr aVariable( theVariableVector[ i ] );
	const Real aValue( aVariable->getValue() );

	//	aPerturbation = aValue * 1e-6 + 1e-13;
	//	aVariable->loadValue( aValue + aPerturbation );
	aPerturbation = theValueBuffer[ i ] * 1e-6 + 1e-13;
	aVariable->loadValue( theValueBuffer[ i ] + aPerturbation );

	fireProcesses();
	
	for ( VariableVector::size_type j( 0 ); j < aSize; ++j )
	  {
	    theJacobian[ j ][ i ]
	      = ( theVariableVector[ j ]->getVelocity()
		  - theVelocityBuffer[ j ] ) / aPerturbation;

	    //	    std::cout << "J(" << j << "," << i << ") = " 
	    //		      << aPartialDerivative << std::endl;

	    theVariableVector[ j ]->clearVelocity();
	  }

	aVariable->loadValue( aValue );
      }
  }

  void DAEStepper::setJacobianMatrix()
  {
    VariableVector::size_type aSize( getReadOnlyVariableOffset() );
    const Real aStepInterval( getStepInterval() );

    const Real alphah( alpha / aStepInterval );
    const Real betah( beta / aStepInterval );
    const Real gammah( gamma / aStepInterval );

    gsl_complex comp;

    for ( VariableVector::size_type i( 0 ); i < aSize; ++i )
      for ( VariableVector::size_type j( 0 ); j < aSize; ++j )
	{
	  const Real aPartialDerivative( theJacobian[ i ][ j ] );

	  if ( i == j ) {
	    gsl_matrix_set( theJacobianMatrix1, i, j,
			    gammah - aPartialDerivative );

	    GSL_SET_COMPLEX( &comp, alphah - aPartialDerivative, betah );
	    gsl_matrix_complex_set( theJacobianMatrix2, i, j, comp );
	  }
	  else {
	    gsl_matrix_set( theJacobianMatrix1, i, j,
			    -1.0 * aPartialDerivative );

	    GSL_SET_COMPLEX( &comp, -1.0 * aPartialDerivative, 0.0 );
	    gsl_matrix_complex_set( theJacobianMatrix2, i, j, comp );
	  }
	}

    /**
    std::cout << std::endl;
    for ( UnsignedInt i( 0 ); i < aSize; ++i )
      for ( UnsignedInt j( 0 ); j < aSize; ++j )
	std::cout << "m(" << i << "," << j << ") = " 
     << gsl_matrix_get( theJacobianMatrix1, i, j ) << std::endl;
    for ( UnsignedInt i( 0 ); i < aSize*2; ++i )
      for ( UnsignedInt j( 0 ); j < aSize*2; ++j )
	std::cout << "m(" << i+aSize << "," << j+aSize << ") = " 
		  << gsl_matrix_get( theJacobianMatrix2, i, j ) << std::endl;
    */

    decompJacobianMatrix();
  }

  void DAEStepper::decompJacobianMatrix()
  {
    int aSignNum;

    gsl_linalg_LU_decomp( theJacobianMatrix1, thePermutation1, &aSignNum );
    gsl_linalg_complex_LU_decomp( theJacobianMatrix2, thePermutation2, &aSignNum );
  }

  void DAEStepper::calculateVelocityVector()
  {
    const Real aCurrentTime( getCurrentTime() );
    const Real aStepInterval( getStepInterval() );
    const VariableVector::size_type aSize( getReadOnlyVariableOffset() );

    const Real alphah( alpha / aStepInterval );
    const Real betah( beta / aStepInterval );
    const Real gammah( gamma / aStepInterval );

    gsl_complex comp;

    RealVector aTIF;
    aTIF.resize( aSize * 3 );

    for ( VariableVector::size_type c( 0 ); c < aSize; ++c )
      {
	const Real z( theW[ c ] * 0.091232394870892942792
		      - theW[ c + aSize ] * 0.14125529502095420843
		      - theW[ c + 2*aSize ] * 0.030029194105147424492 );

	theVariableVector[ c ]->loadValue( theValueBuffer[ c ] + z );
      }

    setCurrentTime( aCurrentTime
		    + aStepInterval * ( 4.0 - sqrt( 6.0 ) ) / 10.0 );
    fireProcesses();

    for ( VariableVector::size_type c( 0 ); c < aSize; ++c )
      {
	aTIF[ c ] 
	  = theVariableVector[ c ]->getVelocity() * 4.3255798900631553510;
	aTIF[ c + aSize ]
	  = theVariableVector[ c ]->getVelocity() * -4.1787185915519047273;
	aTIF[ c + aSize*2 ]
	  = theVariableVector[ c ]->getVelocity() * -0.50287263494578687595;

	const Real z( theW[ c ] * 0.24171793270710701896
		      + theW[ c + aSize ] * 0.20412935229379993199
		      + theW[ c + 2*aSize ] * 0.38294211275726193779 );

	theVariableVector[ c ]->loadValue( theValueBuffer[ c ] + z );
	theVariableVector[ c ]->clearVelocity();
      }

    setCurrentTime( aCurrentTime
		    + aStepInterval * ( 4.0 + sqrt( 6.0 ) ) / 10.0 );
    fireProcesses();

    for ( VariableVector::size_type c( 0 ); c < aSize; ++c )
      {
	aTIF[ c ] 
	  += theVariableVector[ c ]->getVelocity() * 0.33919925181580986954;
	aTIF[ c + aSize ]
	  -= theVariableVector[ c ]->getVelocity() * 0.32768282076106238708;
	aTIF[ c + aSize*2 ]
	  += theVariableVector[ c ]->getVelocity() * 2.5719269498556054292;

	const Real z( theW[ c ] * 0.96604818261509293619 + theW[ c + aSize ] );

	theVariableVector[ c ]->loadValue( theValueBuffer[ c ] + z );
	theVariableVector[ c ]->clearVelocity();
      }

    setCurrentTime( aCurrentTime + aStepInterval );
    fireProcesses();

    for ( VariableVector::size_type c( 0 ); c < aSize; ++c )
      {
	aTIF[ c ]
	  += theVariableVector[ c ]->getVelocity() * 0.54177053993587487119;
	aTIF[ c + aSize ]
	  += theVariableVector[ c ]->getVelocity() * 0.47662355450055045196;
	aTIF[ c + aSize*2 ]
	  -= theVariableVector[ c ]->getVelocity() * 0.59603920482822492497;

	gsl_vector_set( theVelocityVector1, c,
			aTIF[ c ] - theW[ c ] * gammah );

	GSL_SET_COMPLEX( &comp, aTIF[ c + aSize ] - theW[ c + aSize ] * alphah + theW[ c + aSize*2 ] * betah, aTIF[ c + aSize*2 ] - theW[ c + aSize ] * betah - theW[ c + aSize*2 ] * alphah );

	gsl_vector_complex_set( theVelocityVector2, c, comp );

	// theVariableVector[ c ]->loadValue( theValueBuffer[ c ] );
	theVariableVector[ c ]->clearVelocity();
      }

    setCurrentTime( aCurrentTime );
  }

  Real DAEStepper::solve()
  {
    const VariableVector::size_type aSize( getReadOnlyVariableOffset() );

    gsl_linalg_LU_solve( theJacobianMatrix1, thePermutation1,
			 theVelocityVector1, theSolutionVector1 );
    gsl_linalg_complex_LU_solve( theJacobianMatrix2, thePermutation2,
				 theVelocityVector2, theSolutionVector2 );

    Real aNorm( 0.0 );
    Real aDeltaW( 0.0 );
    gsl_complex comp;

    //    std::cout << std::endl;

    for ( VariableVector::size_type c( 0 ); c < aSize; ++c )
      {
	Real aTolerance2( rtoler * fabs( theValueBuffer[ c ] ) + atoler );

	aTolerance2 = aTolerance2 * aTolerance2;

	aDeltaW = gsl_vector_get( theSolutionVector1, c );
	theW[ c ] += aDeltaW;
	aNorm += aDeltaW * aDeltaW / aTolerance2;

	comp = gsl_vector_complex_get( theSolutionVector2, c );

	aDeltaW = GSL_REAL( comp );
	theW[ c + aSize ] += aDeltaW;
	aNorm += aDeltaW * aDeltaW / aTolerance2;

	aDeltaW = GSL_IMAG( comp );
	theW[ c + aSize*2 ] += aDeltaW;
	aNorm += aDeltaW * aDeltaW / aTolerance2;
      }

    return sqrt( aNorm / ( 3 * aSize ) );
  }

  bool DAEStepper::calculate()
  {
    const VariableVector::size_type aSize( getReadOnlyVariableOffset() );
    const Real aStepInterval( getStepInterval() );
    Real aNewStepInterval;
    Real aNorm;
    Real theta( fabs( theJacobianRecalculateTheta ) );

    const Real c1( ( 4.0 - sqrt( 6.0 ) ) / 10.0 );
    const Real c2( ( 4.0 + sqrt( 6.0 ) ) / 10.0 );
    const Real c3q( aStepInterval / thePreviousStepInterval );
    const Real c1q( c3q * c1 );
    const Real c2q( c3q * c2 );
    for ( VariableVector::size_type c( 0 ); c < aSize; ++c )
      {
	const Real z1( c1q * ( theW[ c ] + ( c1q - c1 ) * ( theW[ c + aSize ] + ( c1q - c2 ) * theW[ c + aSize*2 ] ) ) );
	const Real z2( c2q * ( theW[ c ] + ( c2q - c1 ) * ( theW[ c + aSize ] + ( c2q - c2 ) * theW[ c + aSize*2 ] ) ) );
	const Real z3( c3q * ( theW[ c ] + ( c3q - c1 ) * ( theW[ c + aSize ] + ( c3q - c2 ) * theW[ c + aSize*2 ] ) ) );

	theW[ c ] = 4.3255798900631553510 * z1
	  + 0.33919925181580986954 * z2 + 0.54177053993587487119 * z3;
	theW[ c+aSize ] = -4.1787185915519047273 * z1
	  - 0.32768282076106238708 * z2 + 0.47662355450055045196 * z3;
	theW[ c+aSize*2 ] =  -0.50287263494578687595 * z1
	  + 2.5719269498556054292 * z2 - 0.59603920482822492497 * z3;
      }

    UnsignedInteger anIterator( 0 );

    eta = pow( std::max( eta, Uround ), 0.8 );

    while ( anIterator < getMaxIterationNumber() )
      {
	calculateVelocityVector();

	const Real aPreviousNorm( std::max( aNorm, Uround ) );
	aNorm = solve();

	if ( anIterator > 0 && ( anIterator != getMaxIterationNumber()-1 ) )
	  {
	    const Real aThetaQ = aNorm / aPreviousNorm;
	    if ( anIterator > 1 )
	      theta = sqrt( aThetaQ * theta );
	    else
	      theta = aThetaQ;

	    if ( theta < 0.99 )
	      {
		eta = theta / ( 1.0 - theta );
		const Real anIterationError( eta * aNorm * pow( theta, getMaxIterationNumber() - 2 - anIterator ) / theStoppingCriterion );

		if ( anIterationError >= 1.0 )
		  {
		    aNewStepInterval = aStepInterval * 0.8 * pow( std::max( 1e-4, std::min( 20.0, anIterationError ) ) , -1.0 / ( 4 + getMaxIterationNumber() - 2 - anIterator ) );
		    setStepInterval( aNewStepInterval );

		    return false;
		  }
	      }
	  }
	
	if ( eta * aNorm <= theStoppingCriterion )
	  {
	    break;
	  }

	anIterator++;
      }

    for ( VariableVector::size_type c( 0 ); c < aSize; ++c )
      {
	const Real w1( theW[ c ] );
	const Real w2( theW[ c + aSize ] );
	const Real w3( theW[ c + aSize*2 ] );
	    
	theW[ c ] = w1 * 0.091232394870892942792
	  - w2 * 0.14125529502095420843
	  - w3 * 0.030029194105147424492;
	theW[ c + aSize ] = w1 * 0.24171793270710701896
	  + w2 * 0.20412935229379993199
	  + w3 * 0.38294211275726193779;
	theW[ c + aSize*2 ] = w1 * 0.96604818261509293619 + w2;

	/**
	   std::cout << "Z(" << c << ") = " << theW[ c ] << std::endl;
	   std::cout << "Z(" << c+aSize << ") = "
	   << theW[ c+aSize ] << std::endl;
	   std::cout << "Z(" << c+aSize*2 << ") = "
	   << theW[ c+aSize*2 ] << std::endl;
	*/
      }

    const Real anError( estimateLocalError() );

    Real aSafetyFactor( std::min( 0.9, 0.9 * ( 1 + 2*getMaxIterationNumber() ) / ( anIterator + 1 + 2*getMaxIterationNumber() ) ) );
    aSafetyFactor = std::max( 0.125, std::min( 5.0, pow( anError, 0.25 ) / aSafetyFactor ) );

    aNewStepInterval = aStepInterval / aSafetyFactor;

    if ( anError < 1.0 )
      {
	// step is accepted

	if ( !theFirstStepFlag )
	  {
	    Real aGustafssonFactor( theAcceptedStepInterval / aStepInterval * pow( anError * anError / theAcceptedError, 0.25 ) / 0.9 );
	    aGustafssonFactor = std::max( 0.125, std::min( 5.0, aGustafssonFactor ) );

	    if ( aSafetyFactor < aGustafssonFactor )
	      {
		aSafetyFactor = aGustafssonFactor;
		aNewStepInterval = aStepInterval / aGustafssonFactor;
	      }
	  }
	
	theAcceptedStepInterval = aStepInterval;
	theAcceptedError = std::max( 1.0e-2, anError );

	if ( theRejectedStepFlag )
	  aNewStepInterval = std::min( aNewStepInterval, aStepInterval );

	theFirstStepFlag = false;

	const Real aStepIntervalRate( aNewStepInterval / aStepInterval );

	if ( theta <= theJacobianRecalculateTheta )
	    theJacobianCalculateFlag = false;
	else
	  theJacobianCalculateFlag = true;

	//	std::cout << getCurrentTime() << "\t" << theta << std::endl;
	
	if ( aStepIntervalRate >= 1.0 && aStepIntervalRate <= 1.2 )
	  {
	    setNextStepInterval( aStepInterval );
	    return true;
	  }

	setNextStepInterval( aNewStepInterval );
	return true;
      }
    else
      {
	// step is rejected

	if ( theFirstStepFlag )
	  {
	    setStepInterval( 0.1 * aStepInterval );
	  }
	else
	  {
	    setStepInterval( aNewStepInterval );
	  }
	
	return false;
      }
  }

  Real DAEStepper::estimateLocalError()
  {
    const VariableVector::size_type aSize( getReadOnlyVariableOffset() );
    const Real aStepInterval( getStepInterval() );

    Real anError;

    const Real hee1( ( -13.0 - 7.0 * sqrt( 6.0 ) ) / ( 3.0 * aStepInterval ) );
    const Real hee2( ( -13.0 + 7.0 * sqrt( 6.0 ) ) / ( 3.0 * aStepInterval ) );
    const Real hee3( -1.0 / ( 3.0 * aStepInterval ) );

    for ( VariableVector::size_type c( 0 ); c < aSize; ++c )
      {
	// theW must already be transformed to Z-form

	gsl_vector_set( theVelocityVector1, c,
			theVelocityBuffer[ c ]
			+ theW[ c ] * hee1
			+ theW[ c + aSize ] * hee2
			+ theW[ c + 2*aSize ] * hee3 );
      }

    gsl_linalg_LU_solve( theJacobianMatrix1, thePermutation1,
			 theVelocityVector1, theSolutionVector1 );

    anError = 0.0;
    for ( VariableVector::size_type c( 0 ); c < aSize; ++c )
      {
	const Real aTolerance( rtoler * fabs( theValueBuffer[ c ] ) + atoler );
	Real aDifference( gsl_vector_get( theSolutionVector1, c ) );

	// for the case ( anError >= 1.0 )
	theVariableVector[ c ]->loadValue( theValueBuffer[ c ]
					   + aDifference );

	aDifference /= aTolerance;
	anError += aDifference * aDifference;
      }

    anError = std::max( sqrt( anError / aSize ), 1e-10 );

    if ( anError < 1.0 ) return anError;

    if ( theFirstStepFlag or theRejectedStepFlag )
      {
	fireProcesses();

	for ( VariableVector::size_type c( 0 ); c < aSize; ++c )
	  {
	    gsl_vector_set( theVelocityVector1, c,
			    theVariableVector[ c ]->getVelocity()
			    + theW[ c ] * hee1
			    + theW[ c + aSize ] * hee2
			    + theW[ c + 2*aSize ] * hee3 );

	    theVariableVector[ c ]->clearVelocity();
	  }

	gsl_linalg_LU_solve( theJacobianMatrix1, thePermutation1,
			     theVelocityVector1, theSolutionVector1 );

	anError = 0.0;
	for ( VariableVector::size_type c( 0 ); c < aSize; ++c )
	  {
	    const Real aTolerance( rtoler * fabs( theValueBuffer[ c ] )
				   + atoler );

	    Real aDifference( gsl_vector_get( theSolutionVector1, c ) );
	    aDifference /= aTolerance;

	    anError += aDifference * aDifference;
	  }

	anError = std::max( sqrt( anError / aSize ), 1e-10 );
      }

    return anError;
  }

  void DAEStepper::step()
  {
    const VariableVector::size_type aSize( getReadOnlyVariableOffset() );

    theStateFlag = false;

    thePreviousStepInterval = getStepInterval();
    setStepInterval( getNextStepInterval() );
    clearVariables();
    //    interIntegrate();

    theRejectedStepFlag = false;

    fireProcesses();
    for ( VariableVector::size_type i( 0 ); i < aSize; ++i )
      {
	theVelocityBuffer[ i ] = theVariableVector[ i ]->getVelocity();
	theVariableVector[ i ]->clearVelocity();
      }

    if ( theJacobianCalculateFlag )
      {
	calculateJacobian();
	setJacobianMatrix();
      }
    else
      {
	if ( thePreviousStepInterval != getStepInterval() )
	  setJacobianMatrix();
      }

    while ( !calculate() )
      {
	theRejectedStepFlag = true;

	if ( !theJacobianCalculateFlag )
	  {
	    calculateJacobian();
	    theJacobianCalculateFlag = true;
	  }

	setJacobianMatrix();
      }

    // resetAll();

    const Real aStepInterval( getStepInterval() );

    for ( VariableVector::size_type c( 0 ); c < aSize; ++c )
      {
	theVelocityBuffer[ c ] = theW[ c + aSize*2 ];
	theVelocityBuffer[ c ] /= aStepInterval;
	
	theVariableVector[ c ]->loadValue( theValueBuffer[ c ] );
	theVariableVector[ c ]->setVelocity( theVelocityBuffer[ c ] );
      }

    const Real c1( ( 4.0 - sqrt( 6.0 ) ) / 10.0 );
    const Real c2( ( 4.0 + sqrt( 6.0 ) ) / 10.0 );

    for ( VariableVector::size_type c( 0 ); c < aSize; c++ )
      {
	theW[ c ] = theW[ c ] / c1;
	theW[ c+aSize ] = ( theW[ c+aSize ] - c2*theW[ c ] ) / ( c2 - c1 );
	theW[ c+aSize*2 ] = ( ( theW[ c+aSize*2 ] - theW[ c ] ) / ( 1 - c1 ) - theW[ c+aSize ] ) / ( 1 - c2 );
      }

    theStateFlag = true;
  }

}
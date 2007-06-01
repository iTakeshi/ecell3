//::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
//
//        This file is part of E-Cell Simulation Environment package
//
//                Copyright (C) 1996-2002 Keio University
//
//::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
//
//
// E-Cell is free software; you can redistribute it and/or
// modify it under the terms of the GNU General Public
// License as published by the Free Software Foundation; either
// version 2 of the License, or (at your option) any later version.
// 
// E-Cell is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
// See the GNU General Public License for more details.
// 
// You should have received a copy of the GNU General Public
// License along with E-Cell -- see the file COPYING.
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

#include "dmtool/ModuleMaker.hpp"

#include "libecs.hpp"

namespace libecs
{
  int const MAJOR_VERSION( ECELL_MAJOR_VERSION );
  int const MINOR_VERSION( ECELL_MINOR_VERSION );
  int const MICRO_VERSION( ECELL_MICRO_VERSION );

  char const* const VERSION_STRING( ECELL_VERSION_STRING );

  void setDMSearchPath( const std::string& path )
  {
    ModuleMaker::setSearchPath( path );
  }

  const std::string getDMSearchPath()
  {
    return ModuleMaker::getSearchPath();
  }

} // namespace libecs

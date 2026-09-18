// Copyright (C) 2012 GlavSoft LLC.
// All rights reserved.
//
//-------------------------------------------------------------------------
// This file is part of the TightVNC software.  Please visit our Web site:
//
//                       http://www.tightvnc.com/
//
// This program is free software; you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation; either version 2 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License along
// with this program; if not, write to the Free Software Foundation, Inc.,
// 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
//-------------------------------------------------------------------------
//

#include "NamingDefs.h"

// Modified by the TobonVNC fork (Daniel Tobon, 2026): product identity renamed
// from TightVNC to TobonVNC. The registry path is intentionally kept as
// "Software\TightVNC\Viewer" so that saved settings, per-host connection
// settings, and the connection history of existing installations are preserved.
const TCHAR ProductNames::PRODUCT_NAME[] = _T("TobonVNC");
const TCHAR ProductNames::VIEWER_PRODUCT_NAME[] = _T("TobonVNC Viewer");

const TCHAR LogNames::VIEWER_LOG_FILE_STUB_NAME[] = _T("TobonVNCViewer");
const TCHAR LogNames::LOG_DIR_NAME[] = _T("TobonVNC");

const TCHAR RegistryPaths::VIEWER_PATH[] = _T("Software\\TightVNC\\Viewer");

const TCHAR ApplicationNames::WINDOW_CLASS_NAME[] = 
  _T("TvnApplicationClass");

const TCHAR WindowNames::TVN_WINDOW_CLASS_NAME[] = _T("TvnWindowClass");
const TCHAR WindowNames::TVN_WINDOW_TITLE_NAME[] = _T("TobonVNC Viewer");
const TCHAR WindowNames::TVN_SUB_WINDOW_TITLE_NAME[] = _T("Viewer");


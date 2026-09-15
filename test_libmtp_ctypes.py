#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test direct access to libmtp via ctypes
libmtp is the C library that handles MTP protocol
If we can load libmtp.dll, we can get raw metadata directly from MTP
"""

import sys
import ctypes
import os
from ctypes import *

def test_libmtp_ctypes():
    """
    Try to load and use libmtp library directly via ctypes
    """
    
    print("[INFO] Attempting to load libmtp via ctypes...\n")
    
    try:
        # Common paths where libmtp might be installed
        libmtp_paths = [
            "libmtp.dll",
            "libmtp-1.dll",
            "C:\\Program Files\\libmtp\\libmtp.dll",
            "C:\\Program Files (x86)\\libmtp\\libmtp.dll",
            "C:\\msys64\\mingw64\\bin\\libmtp.dll",
            "C:\\msys64\\mingw32\\bin\\libmtp.dll",
            "C:\\mingw64\\bin\\libmtp.dll",
            "C:\\mingw32\\bin\\libmtp.dll",
        ]
        
        libmtp = None
        loaded_from = None
        
        for path in libmtp_paths:
            try:
                print(f"[TRYING] {path}...", end=" ")
                if os.path.exists(path):
                    libmtp = ctypes.CDLL(path)
                    loaded_from = path
                    print("✅ LOADED")
                    break
                else:
                    print("❌ not found")
            except Exception as e:
                print(f"❌ {str(e)[:40]}")
        
        if not libmtp:
            print("\n[ERROR] libmtp.dll not found in any standard location")
            print("[INFO] libmtp may need to be installed separately")
            return False
        
        print(f"\n[OK] libmtp loaded from: {loaded_from}\n")
        
        # Now try to use libmtp functions
        print("[INFO] Testing libmtp functions...\n")
        
        # libmtp_init() - initialize libmtp
        try:
            libmtp.libmtp_init()
            print("[OK] libmtp_init() succeeded")
        except Exception as e:
            print(f"[WARN] libmtp_init() not available: {e}")
        
        # libmtp_get_first_device() - get first MTP device
        try:
            # Create a struct for device (simplified)
            get_first_device = libmtp.libmtp_get_first_device
            get_first_device.restype = c_void_p
            
            device = get_first_device()
            if device:
                print(f"[OK] Found MTP device at address: {hex(device)}")
                
                # Now we need to know the struct layout to read properties
                # This requires libmtp header files and detailed knowledge
                print("[INFO] Device found, but reading properties requires struct definitions")
                
            else:
                print("[ERROR] No MTP device found via libmtp")
                return False
        
        except Exception as e:
            print(f"[ERROR] libmtp functions: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"[ERROR] ctypes test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 80)
    print("libmtp via ctypes Test")
    print("=" * 80)
    print()
    
    result = test_libmtp_ctypes()
    
    print("\n" + "=" * 80)
    if result:
        print("Result: ✅ libmtp is available")
    else:
        print("Result: ❌ libmtp test failed or not installed")
    print("=" * 80)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test accessing MTP files via PowerShell Get-ChildItem
If Windows internally maps MTP to filesystem, we can get raw metadata:
- CreationTime (with seconds)
- LastWriteTime (with seconds)  
- Length (in bytes)
"""

import subprocess
import json
import sys
import os
from datetime import datetime

def get_mtp_files_via_powershell():
    """
    Try to access MTP device via PowerShell Get-ChildItem
    This might give us raw file properties
    """
    
    print("[INFO] Attempting to access MTP via PowerShell...\n")
    
    try:
        # First, let's try to find MTP device paths in Windows
        print("[SCANNING] Looking for MTP device paths...\n")
        
        # PowerShell script to find MTP devices
        ps_script = """
$shell = New-Object -ComObject Shell.Application
$devices = $shell.NameSpace(17)

foreach ($device in $devices.Items()) {
    if ($device.Name -like "*motorola*" -or $device.Name -like "*android*" -or $device.Type -like "*Phone*") {
        Write-Host "[DEVICE] $($device.Name)"
        Write-Host "[PATH] $($device.Path)"
        
        # Try to access storage
        $device_ns = $shell.NameSpace($device.Path)
        
        foreach ($storage in $device_ns.Items()) {
            Write-Host "[STORAGE] $($storage.Name)"
            
            # Get the folder object
            $folder = $storage.GetFolder
            
            # Try to iterate files
            foreach ($item in $folder.Items()) {
                if ($item.Name -like "Pictures" -or $item.Name -like "DCIM") {
                    Write-Host "[FOLDER] $($item.Name)"
                    
                    # Try to get subfolder
                    $subfolder = $item.GetFolder
                    
                    $count = 0
                    foreach ($file in $subfolder.Items()) {
                        if (-not $file.IsFolder) {
                            Write-Host "  [FILE] $($file.Name)"
                            
                            # Try to get properties
                            try {
                                $name = $file.Name
                                $path = $file.Path
                                
                                Write-Host "    Path: $path"
                                
                                # Try Get-Item on the path
                                try {
                                    $item_info = Get-Item -LiteralPath $path -ErrorAction SilentlyContinue
                                    if ($item_info) {
                                        Write-Host "    Size: $($item_info.Length)"
                                        Write-Host "    Modified: $($item_info.LastWriteTime)"
                                        Write-Host "    Created: $($item_info.CreationTime)"
                                    } else {
                                        Write-Host "    [NOTE] Path is not accessible via Get-Item"
                                    }
                                } catch {
                                    Write-Host "    [ERROR] Get-Item failed: $_"
                                }
                            } catch {
                                Write-Host "    [ERROR] $_"
                            }
                            
                            $count++
                            if ($count -ge 2) { break }
                        }
                    }
                    break
                }
            }
            break
        }
        break
    }
}
"""
        
        # Run PowerShell script
        print("[RUNNING] PowerShell script...\n")
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print(result.stdout)
        if result.stderr:
            print(f"[STDERR]\n{result.stderr}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] PowerShell test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 80)
    print("PowerShell MTP Access Test")
    print("=" * 80)
    print()
    
    result = get_mtp_files_via_powershell()
    
    print("\n" + "=" * 80)
    if result:
        print("Result: ✅ PowerShell enumeration completed")
    else:
        print("Result: ❌ Test failed")
    print("=" * 80)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Windows.Devices.Portable via PowerShell + inline C# compilation
PowerShell can compile and run C# code dynamically using Add-Type
"""

import subprocess
import sys

def test_winrt_via_powershell():
    """
    Use PowerShell to compile and run C# code that accesses WinRT API
    """
    
    print("[INFO] Testing via PowerShell + .NET...\n")
    
    # PowerShell script that compiles and runs C# inline
    ps_script = r"""
Write-Host "[INFO] Loading .NET assemblies..."

# Load required assemblies
Add-Type -AssemblyName System.Runtime
Add-Type -AssemblyName Windows.Storage -ErrorAction SilentlyContinue
Add-Type -AssemblyName Windows.Devices.Portable -ErrorAction SilentlyContinue

Write-Host "[INFO] Attempting WinRT API access..."

try {
    # This requires Windows 10 and .NET Framework to support WinRT
    
    # Try using reflection to load WinRT types
    $assembly = [System.Reflection.Assembly]::LoadWithPartialName("Windows.Storage")
    if ($assembly) {
        Write-Host "[OK] Windows.Storage assembly loaded"
    }
    
    # Try Shell.NameSpace method with different approaches
    $shell = New-Object -ComObject Shell.Application
    $devices = $shell.NameSpace(17)
    
    foreach ($device in $devices.Items()) {
        if ($device.Name -like "*motorola*") {
            Write-Host "[DEVICE] $($device.Name)"
            
            $device_ns = $shell.NameSpace($device.Path)
            
            foreach ($storage in $device_ns.Items()) {
                Write-Host "[STORAGE] $($storage.Name)"
                
                $folder = $storage.GetFolder
                
                foreach ($item in $folder.Items()) {
                    if ($item.Name -like "Pictures") {
                        Write-Host "[FOLDER] $($item.Name)"
                        
                        $pics = $item.GetFolder
                        
                        $count = 0
                        foreach ($file in $pics.Items()) {
                            if (-not $file.IsFolder) {
                                Write-Host "`n  [FILE] $($file.Name)"
                                
                                # Try different methods to get raw properties
                                
                                # Method 1: GetDetailsOf with different columns (0-30)
                                Write-Host "  Methods to get properties:"
                                for ($col = 0; $col -lt 30; $col++) {
                                    $detail = $folder.GetDetailsOf($file, $col)
                                    if ($detail) {
                                        Write-Host "    Col[$col]: $detail"
                                    }
                                }
                                
                                # Method 2: Try shell.CreateShortCut pattern
                                Write-Host "`n  Trying alternative methods..."
                                
                                # Get file path
                                $file_path = $file.Path
                                Write-Host "    Path: $file_path"
                                
                                # Try to invoke methods on the file object
                                Write-Host "    File object methods:"
                                $file | Get-Member -MemberType Method | Select-Object Name | ForEach-Object {
                                    Write-Host "      - $($_.Name)"
                                }
                                
                                $count++
                                if ($count -ge 1) { break }
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
    
} catch {
    Write-Host "[ERROR] WinRT test failed: $_"
}

Write-Host "`n[DONE]"
"""
    
    try:
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
        print(f"[ERROR] PowerShell execution failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 80)
    print("PowerShell + .NET Test")
    print("=" * 80)
    print()
    
    result = test_winrt_via_powershell()
    
    print("\n" + "=" * 80)
    if result:
        print("Result: ✅ PowerShell test completed")
    else:
        print("Result: ❌ PowerShell test failed")
    print("=" * 80)

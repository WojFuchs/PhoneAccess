#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test file copy using PowerShell Copy-Item
"""
import sys
import io
import os
import subprocess
import time

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

dest_path = r"C:\Users\Wojtek\source\repos\PhoneAccess\test_ps_copy"
os.makedirs(dest_path, exist_ok=True)

# PowerShell script to find MTP device and copy files
ps_script = r"""
$dest = 'C:\Users\Wojtek\source\repos\PhoneAccess\test_ps_copy'

# Find portable device
$shell = New-Object -ComObject Shell.Application
$computerFolder = $shell.NameSpace(17)

foreach ($device in $computerFolder.Items()) {
    if ($device.Name -like '*motorola*' -or $device.Name -like '*android*') {
        Write-Host "Found device: $($device.Name)"
        
        # Get device namespace
        $deviceNS = $shell.NameSpace($device.Path)
        
        foreach ($storage in $deviceNS.Items()) {
            Write-Host "Storage: $($storage.Name)"
            $folder = $storage.GetFolder
            
            # Find Pictures
            foreach ($item in $folder.Items()) {
                if ($item.Name -eq 'Pictures') {
                    Write-Host "Found Pictures folder"
                    $picFolder = $item.GetFolder
                    
                    $count = 0
                    foreach ($file in $picFolder.Items()) {
                        if (!$file.IsFolder -and $count -lt 2) {
                            Write-Host "Copying: $($file.Name)"
                            
                            $srcPath = $file.Path
                            Write-Host "Source path: $srcPath"
                            
                            # Try to copy using file path
                            try {
                                Copy-Item -LiteralPath $srcPath -Destination $dest -Force -ErrorAction Stop
                                Write-Host "SUCCESS: Copied $($file.Name)"
                                $count++
                            } catch {
                                Write-Host "Copy failed: $_"
                            }
                        }
                    }
                    break
                }
            }
        }
        break
    }
}
"""

print("Running PowerShell copy test...")
print(f"Destination: {dest_path}\n")

try:
    result = subprocess.run(
        ['powershell', '-NoProfile', '-Command', ps_script],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    print("Output:")
    print(result.stdout)
    
    if result.stderr:
        print("Errors:")
        print(result.stderr)
    
    # Check if files were copied
    time.sleep(1)
    files = os.listdir(dest_path)
    print(f"\nFiles in destination: {files}")
    print(f"Total copied: {len(files)}")

except Exception as e:
    print(f"Error: {e}")

print("\nDone!")

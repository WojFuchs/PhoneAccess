#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Windows.Devices.Portable WinRT API via ctypes/comtypes
This is the modern Windows 10+ API for accessing portable devices
"""

import sys
import subprocess
import json
import os

def test_winrt_devices_portable():
    """
    Use C# code via subprocess to access Windows.Devices.Portable API
    This gives us direct access to device storage with raw metadata
    """
    
    print("[INFO] Testing Windows.Devices.Portable WinRT API...\n")
    
    # C# program to access portable devices
    csharp_code = r"""
using System;
using System.Collections.Generic;
using Windows.Storage;
using Windows.Devices.Portable;
using System.IO;

class Program {
    static async System.Threading.Tasks.Task Main() {
        try {
            Console.WriteLine("[INFO] Initializing StorageDevice...");
            
            // Get all portable devices (including Android phones)
            var devices = await StorageDevice.GetAllAsync();
            Console.WriteLine($"[OK] Found {devices.Count} device(s)");
            
            if (devices.Count == 0) {
                Console.WriteLine("[ERROR] No devices found");
                return;
            }
            
            foreach (var device in devices) {
                try {
                    Console.WriteLine($"\n[DEVICE] {device.Name}");
                    
                    // Try to get root folder
                    var root = device.RootFolder;
                    Console.WriteLine($"[OK] Root folder obtained");
                    
                    // List folders
                    var items = await root.GetItemsAsync();
                    Console.WriteLine($"[OK] Found {items.Count} items in root");
                    
                    foreach (var item in items) {
                        try {
                            Console.WriteLine($"\n  [{item.DisplayName}]");
                            
                            if (item.IsOfType(StorageItemTypes.Folder)) {
                                var folder = item as StorageFolder;
                                var subitems = await folder.GetItemsAsync();
                                Console.WriteLine($"    Items: {subitems.Count}");
                                
                                // Get first file
                                foreach (var subitem in subitems) {
                                    if (subitem.IsOfType(StorageItemTypes.File)) {
                                        var file = subitem as StorageFile;
                                        var props = await file.GetBasicPropertiesAsync();
                                        
                                        Console.WriteLine($"\n    [FILE] {file.Name}");
                                        Console.WriteLine($"      Size: {props.Size} bytes");
                                        Console.WriteLine($"      Modified: {props.DateModified:yyyy-MM-dd HH:mm:ss.fff}");
                                        
                                        break;  // Just first file
                                    }
                                }
                                break;  // Just first folder
                            }
                        } catch (Exception ex) {
                            Console.WriteLine($"    [ERROR] {ex.Message}");
                        }
                    }
                    break;  // Just first device
                } catch (Exception ex) {
                    Console.WriteLine($"[ERROR] Device error: {ex.Message}");
                }
            }
            
        } catch (Exception ex) {
            Console.WriteLine($"[ERROR] WinRT test failed: {ex.Message}");
            Console.WriteLine($"[INFO] Stack trace: {ex.StackTrace}");
        }
    }
}
"""
    
    # Save C# code to file
    csharp_file = "test_winrt_temp.cs"
    print(f"[WRITING] {csharp_file}...\n")
    
    try:
        with open(csharp_file, 'w', encoding='utf-8') as f:
            f.write(csharp_code)
        
        # Try to compile and run with csc.exe (C# compiler)
        print("[COMPILING] C# code...\n")
        
        compile_result = subprocess.run(
            ["csc.exe", "/target:exe", f"/out:test_winrt_temp.exe", csharp_file],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if compile_result.returncode != 0:
            print(f"[ERROR] Compilation failed:\n{compile_result.stderr}")
            return False
        
        print("[OK] Compilation succeeded")
        print("\n[RUNNING] test_winrt_temp.exe...\n")
        
        # Run the compiled program
        run_result = subprocess.run(
            ["test_winrt_temp.exe"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print(run_result.stdout)
        if run_result.stderr:
            print(f"[STDERR]\n{run_result.stderr}")
        
        # Clean up
        try:
            os.remove(csharp_file)
            os.remove("test_winrt_temp.exe")
        except:
            pass
        
        return run_result.returncode == 0
        
    except FileNotFoundError:
        print("[ERROR] csc.exe not found (C# compiler not installed)")
        print("[INFO] To use this test, install Visual Studio or .NET SDK")
        return False
    except Exception as e:
        print(f"[ERROR] C# compilation/execution failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 80)
    print("Windows.Devices.Portable (WinRT) API Test")
    print("=" * 80)
    print()
    
    result = test_winrt_devices_portable()
    
    print("\n" + "=" * 80)
    if result:
        print("Result: ✅ WinRT API is available")
    else:
        print("Result: ❌ WinRT API test failed")
    print("=" * 80)

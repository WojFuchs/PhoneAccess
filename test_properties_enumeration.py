#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test IShellItem2 interface for raw file properties
IShellItem2 can access properties via IPropertyStore which should have raw values
"""

import sys
import win32com.client
from datetime import datetime

def test_ishellitem2_properties():
    """
    Test accessing file properties via IShellItem2 and IPropertyStore
    This should give us raw property values (size in bytes, datetime with seconds)
    """
    
    try:
        shell = win32com.client.Dispatch('Shell.Application')
        devices_ns = shell.NameSpace(17)
        
        print("[DETECTING] Looking for devices...")
        
        for device in devices_ns.Items():
            if 'motorola' in device.Name.lower():
                print(f"[OK] Device found: {device.Name}\n")
                
                # Try to get device as IShellItem2
                print("[INFO] Attempting to access device properties via COM...")
                
                try:
                    # Get the device's ParentFolder to access IPropertyStore
                    parent = device.Parent
                    print(f"[OK] Parent: {parent}")
                    
                    # Try to get IPropertyStore
                    print(f"\n[INFO] Attempting to bind to IPropertyStore...")
                    
                    # Device is a FolderItem - try to get its path
                    device_path = device.Path
                    print(f"Device Path: {device_path}")
                    
                    # Get storage
                    device_ns = shell.NameSpace(device.Path)
                    
                    for storage in device_ns.Items():
                        print(f"\nStorage: {storage.Name}")
                        storage_folder = storage.GetFolder
                        
                        # Find Pictures
                        for item in storage_folder.Items():
                            if 'Pictures' in item.Name:
                                print(f"Found: {item.Name}")
                                pics_folder = item.GetFolder
                                
                                # Get first file and test different ways to access properties
                                print(f"\n[TESTING] Accessing properties...")
                                
                                for file_item in pics_folder.Items():
                                    if not file_item.IsFolder:
                                        print(f"\nFile: {file_item.Name}")
                                        
                                        # Method 1: GetDetailsOf (known to format data)
                                        print(f"\n  Method 1: GetDetailsOf (Shell API - formatted)")
                                        size_col2 = storage_folder.GetDetailsOf(file_item, 2)
                                        date_col3 = storage_folder.GetDetailsOf(file_item, 3)
                                        print(f"    Size: {size_col2}")
                                        print(f"    Date: {date_col3}")
                                        
                                        # Method 2: Try COM object attributes
                                        print(f"\n  Method 2: Direct COM properties")
                                        try:
                                            print(f"    Name: {file_item.Name}")
                                            print(f"    Type: {file_item.Type}")
                                            print(f"    Path: {file_item.Path}")
                                            print(f"    IsFolder: {file_item.IsFolder}")
                                            # These probably don't work for MTP
                                            if hasattr(file_item, 'Size'):
                                                print(f"    Size (attr): {file_item.Size}")
                                            if hasattr(file_item, 'ModifyDate'):
                                                print(f"    ModifyDate (attr): {file_item.ModifyDate}")
                                        except Exception as e:
                                            print(f"    Error: {e}")
                                        
                                        # Method 3: Try to enumerate ALL properties
                                        print(f"\n  Method 3: Enumerate ALL properties via GetDetailsOf")
                                        for col in range(30):
                                            try:
                                                value = storage_folder.GetDetailsOf(file_item, col)
                                                if value:  # Only print non-empty
                                                    print(f"    Col[{col:2d}]: {value}")
                                            except:
                                                pass
                                        
                                        return True
                        
                        return True
                
                except Exception as e:
                    print(f"[ERROR] Property access failed: {e}")
                    import traceback
                    traceback.print_exc()
                    return False
        
        print("[ERROR] No motorola device found")
        return False
        
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 80)
    print("IShellItem2 / Property Store Test")
    print("=" * 80)
    print()
    
    result = test_ishellitem2_properties()
    
    print("\n" + "=" * 80)
    if result:
        print("Result: ✅ Property enumeration completed")
    else:
        print("Result: ❌ Test failed")
    print("=" * 80)

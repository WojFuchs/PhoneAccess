#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test using GetFolder() method to access shell item as a folder
"""
import sys
import io
import win32com.client

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

shell = win32com.client.Dispatch('Shell.Application')
items_namespace = shell.NameSpace(17)

for device in items_namespace.Items():
    if 'motorola' in device.Name.lower():
        print(f"Device: {device.Name}\n")
        
        device_ns = shell.NameSpace(device.Path)
        
        for storage_item in device_ns.Items():
            print(f"Storage: {storage_item.Name}")
            print(f"Has GetFolder: {hasattr(storage_item, 'GetFolder')}")
            print(f"Methods: {[m for m in dir(storage_item) if not m.startswith('_')]}\n")
            
            # Try GetFolder
            if hasattr(storage_item, 'GetFolder'):
                try:
                    folder = storage_item.GetFolder
                    print(f"GetFolder result type: {type(folder)}")
                    print(f"GetFolder result: {folder}")
                    
                    # If it's a Folder object, try to enumerate items
                    if hasattr(folder, 'Items'):
                        print(f"Folder has Items!")
                        for file_item in folder.Items():
                            print(f"  - {file_item.Name}")
                            if file_item.Name.lower() == 'pictures' or file_item.Name.lower() == 'dcim':
                                print(f"    Found media folder!")
                                break
                except Exception as e:
                    print(f"Error with GetFolder: {e}")
                    import traceback
                    traceback.print_exc()
        
        break

print("\n[Done]")

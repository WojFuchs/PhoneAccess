#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test to inspect shell folder item properties
"""
import sys
import io
import win32com.client

# Force UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

shell = win32com.client.Dispatch('Shell.Application')
items_namespace = shell.NameSpace(17)

for device in items_namespace.Items():
    if 'motorola' in device.Name.lower():
        print(f"Device: {device.Name}\n")
        
        device_ns = shell.NameSpace(device.Path)
        
        for storage_item in device_ns.Items():
            print(f"Storage item: {storage_item.Name}")
            print(f"Type: {storage_item.Type}")
            print(f"Path: {storage_item.Path}")
            print(f"Self Path: {storage_item.Self.Path if hasattr(storage_item, 'Self') else 'N/A'}")
            
            # Check if we can get it as a folder
            try:
                folder_obj = storage_item.GetFolder if hasattr(storage_item, 'GetFolder') else None
                if folder_obj:
                    print(f"Has GetFolder method")
                    folder = folder_obj()
                    for file_item in folder.Items():
                        print(f"  - {file_item.Name}")
                        break
            except Exception as e:
                print(f"GetFolder failed: {e}")
            
            # Try to navigate using shell's navigate method
            try:
                # Create a folder object from the path
                fso = win32com.client.Dispatch("Scripting.FileSystemObject")
                path = storage_item.Path
                print(f"Trying to access path: {path}")
                
                # The path might be a shell namespace, let's try shell.ParsingName
                if hasattr(storage_item, 'ParsingName'):
                    print(f"ParsingName: {storage_item.ParsingName}")
                
            except Exception as e:
                print(f"FSO access failed: {e}")
            
            print()
        
        break

print("[Done]")

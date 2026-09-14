#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test GetDetailsOf() to get file metadata
"""
import sys
import io
import win32com.client

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

shell = win32com.client.Dispatch('Shell.Application')
items_ns = shell.NameSpace(17)

for device in items_ns.Items():
    if 'motorola' in device.Name.lower():
        print(f"Device: {device.Name}\n")
        
        device_ns = shell.NameSpace(device.Path)
        
        for storage in device_ns.Items():
            folder = storage.GetFolder
            
            print("Folder object methods and properties:")
            print([m for m in dir(folder) if not m.startswith('_')])
            
            print("\nListing first 3 files with all columns:\n")
            
            count = 0
            for file_item in folder.Items():
                if count >= 3:
                    break
                
                print(f"File: {file_item.Name}")
                
                # Try to get details using GetDetailsOf
                try:
                    # GetDetailsOf needs a FolderItem parameter
                    # Try using shell folder view
                    
                    for col in range(10):
                        try:
                            detail = file_item.GetDetailsOf(folder, col) if hasattr(file_item, 'GetDetailsOf') else "N/A"
                            if detail and detail != "N/A":
                                print(f"  Column {col}: {detail}")
                        except Exception as e:
                            pass
                
                except Exception as e:
                    print(f"  Error getting details: {e}")
                
                # Try direct properties
                print(f"  Direct - Size: {file_item.Size if hasattr(file_item, 'Size') else 'N/A'}")
                print(f"  Direct - ModifyDate: {file_item.ModifyDate if hasattr(file_item, 'ModifyDate') else 'N/A'}")
                print()
                
                count += 1
        
        break

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to explore Android phone storage
"""
import sys
import io
import win32com.client

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

shell = win32com.client.Dispatch('Shell.Application')
items_namespace = shell.NameSpace(17)

for device in items_namespace.Items():
    if 'motorola' in device.Name.lower():
        print(f"[DEVICE] {device.Name}")
        print(f"Device Path: {device.Path}\n")
        
        # Get the device folder
        try:
            device_folder = shell.NameSpace(device.Path)
            
            if device_folder:
                print("Direct items in device:")
                for item in device_folder.Items():
                    print(f"  Name: {item.Name}")
                    print(f"  Type: {item.Type}")
                    
                    try:
                        path_str = str(item.Path) if hasattr(item, 'Path') else 'N/A'
                        print(f"  Path: {path_str}")
                        
                        # Try to get the storage/folder
                        storage_folder = shell.NameSpace(item.Path)
                        if storage_folder:
                            print(f"  [OK] Can open as folder")
                            print(f"  Contents:")
                            count = 0
                            for sub_item in storage_folder.Items():
                                sub_name = str(sub_item.Name)
                                sub_type = str(sub_item.Type)
                                print(f"    - {sub_name} ({sub_type})")
                                count += 1
                                if count >= 20:
                                    print(f"    ... and more")
                                    break
                    except Exception as e:
                        print(f"  [ERROR] Cannot process: {str(e)}")
                    
                    print()
        except Exception as e:
            print(f"Error accessing device: {str(e)}")
        
        break

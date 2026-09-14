#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to explore Android phone files via COM Shell
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
        print(f"[1] Device found: {device.Name}")
        
        # Get the device namespace
        device_ns = shell.NameSpace(device.Path)
        print(f"[2] Device namespace accessed")
        
        for storage_item in device_ns.Items():
            print(f"[3] Storage item: {storage_item.Name}")
            print(f"    Type: {storage_item.Type}")
            
            # Try to get the folder items
            try:
                storage_ns = shell.NameSpace(storage_item.Path)
                print(f"    [4] Opened storage namespace")
                
                count = 0
                for folder_item in storage_ns.Items():
                    print(f"      {count}: {folder_item.Name} ({folder_item.Type})")
                    count += 1
                    if count > 30:
                        print(f"      ... and {storage_ns.Items().Count - count} more")
                        break
                        
            except Exception as e:
                print(f"    [ERROR] {str(e)[:100]}")
        
        break

print("[DONE]")

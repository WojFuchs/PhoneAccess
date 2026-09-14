#!/usr/bin/env python3
"""
Test script to explore Android phone via COM
"""
import win32com.client

shell = win32com.client.Dispatch('Shell.Application')
items = shell.NameSpace(17)

for item in items.Items():
    if 'motorola' in item.Name.lower():
        print(f"Device: {item.Name}")
        print(f"Path: {item.Path}")
        
        # Try to get the folder namespace
        try:
            folder = shell.NameSpace(item.Path)
            print(f"✓ Got folder namespace")
            
            if folder:
                print("\nFolders/Items in device:")
                for sub_item in folder.Items():
                    print(f"  - {sub_item.Name} (Type: {sub_item.Type})")
        except Exception as e:
            print(f"✗ Error getting folder: {e}")
        
        break

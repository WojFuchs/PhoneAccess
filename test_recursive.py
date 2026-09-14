#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test - recursively list all files from MTP device
"""
import sys
import io
import win32com.client

# Force UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

shell = win32com.client.Dispatch('Shell.Application')
items_namespace = shell.NameSpace(17)

def list_files_recursive(folder_obj, prefix="", max_depth=5, depth=0):
    """Recursively list all files in shell folder"""
    if depth >= max_depth:
        return
    
    try:
        items_count = folder_obj.Items().Count
        print(f"{prefix}[Folder has {items_count} items]")
        
        for item in folder_obj.Items():
            item_type = item.Type
            item_name = item.Name
            
            # Skip certain system folders
            if item_name.startswith('.'):
                continue
            
            print(f"{prefix}  {item_name} ({item_type})")
            
            # Check if it's a folder we can navigate into
            if 'Folder' in item_type or 'hierarchical' in item_type.lower():
                try:
                    # Try to get the item as a folder
                    sub_ns = shell.NameSpace(item.Path)
                    if sub_ns:
                        list_files_recursive(sub_ns, prefix + "    ", max_depth, depth + 1)
                except:
                    pass
                    
    except Exception as e:
        print(f"{prefix}[Error: {str(e)[:50]}]")

for device in items_namespace.Items():
    if 'motorola' in device.Name.lower():
        print(f"=== Device: {device.Name} ===\n")
        
        device_ns = shell.NameSpace(device.Path)
        list_files_recursive(device_ns)
        
        break

print("\n[Done]")

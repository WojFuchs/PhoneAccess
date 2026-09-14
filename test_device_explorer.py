#!/usr/bin/env python3
"""
Test script to explore Android phone and find Pictures
"""
import win32com.client

shell = win32com.client.Dispatch('Shell.Application')
items = shell.NameSpace(17)

def explore_folder(folder_item, level=0):
    """Recursively explore folder structure"""
    indent = "  " * level
    
    try:
        folder = shell.NameSpace(folder_item.Path)
        
        if folder:
            for sub_item in folder.Items():
                print(f"{indent}├─ {sub_item.Name} ({sub_item.Type})")
                
                # Recursively explore if it's a folder-like item
                if sub_item.Type in ['Folder', 'Generic hierarchical', 'Mobile Phone Storage']:
                    if level < 3:  # Limit depth
                        explore_folder(sub_item, level + 1)
    except Exception as e:
        print(f"{indent}✗ Error: {e}")

for item in items.Items():
    if 'motorola' in item.Name.lower():
        print(f"🔍 Device: {item.Name}\n")
        explore_folder(item, level=0)
        break

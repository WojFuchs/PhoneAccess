#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test file copy via Windows Explorer shell
"""
import sys
import io
import os
import shutil
import win32com.client

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

shell = win32com.client.Dispatch('Shell.Application')
items_ns = shell.NameSpace(17)

for device in items_ns.Items():
    if 'motorola' in device.Name.lower():
        device_ns = shell.NameSpace(device.Path)
        
        for storage in device_ns.Items():
            folder = storage.GetFolder
            
            # Get Pictures folder
            for item in folder.Items():
                if item.Name.lower() == 'pictures':
                    pic_folder = item.GetFolder
                    
                    # Get first file
                    for file_item in pic_folder.Items():
                        if not file_item.IsFolder:
                            print(f"File: {file_item.Name}\n")
                            
                            # Check available methods
                            print("Methods on FolderItem:")
                            methods = [m for m in dir(file_item) if not m.startswith('_')]
                            print(methods)
                            
                            # Try ParseName
                            print(f"\nParsingName: {file_item.Path if hasattr(file_item, 'Path') else 'N/A'}")
                            
                            # Try GetString or GetBlob
                            if hasattr(file_item, 'GetString'):
                                print(f"Has GetString method")
                            
                            # Try Parent
                            print(f"Parent: {file_item.Parent if hasattr(file_item, 'Parent') else 'N/A'}")
                            
                            break
                    break
        
        break

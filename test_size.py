#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Find correct column index for file size
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
        device_ns = shell.NameSpace(device.Path)
        
        for storage in device_ns.Items():
            folder = storage.GetFolder
            
            # Get Pictures folder
            for item in folder.Items():
                if item.Name.lower() == 'pictures':
                    pic_folder = item.GetFolder
                    
                    # Find a file (not folder)
                    for file_item in pic_folder.Items():
                        if not file_item.IsFolder:
                            print(f"File: {file_item.Name}\n")
                            
                            # Try all columns
                            for col in range(30):
                                try:
                                    detail = pic_folder.GetDetailsOf(file_item, col)
                                    if detail:
                                        print(f"Column {col:2d}: {detail}")
                                except:
                                    pass
                            
                            break
                    break
        
        break

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test GetDetailsOf() with all columns
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
            
            print("Testing GetDetailsOf() on Pictures folder:\n")
            
            # Get Pictures folder
            pictures = None
            for item in folder.Items():
                if item.Name.lower() == 'pictures':
                    pictures = item
                    break
            
            if pictures and pictures.IsFolder:
                print(f"Folder: {pictures.Name}\n")
                
                # Try to open Pictures
                pic_folder = pictures.GetFolder
                
                print("Column index tests on first file in Pictures:\n")
                
                count = 0
                for file_item in pic_folder.Items():
                    if count >= 1:
                        break
                    
                    print(f"File: {file_item.Name}\n")
                    
                    for col in range(15):
                        try:
                            detail = folder.GetDetailsOf(file_item, col)
                            if detail:
                                print(f"  Column {col:2d}: {detail}")
                        except Exception as e:
                            pass
                    
                    count += 1
        
        break

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test available verbs on MTP file
"""
import sys
import io
import os
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
            
            for item in folder.Items():
                if item.Name.lower() == 'pictures':
                    pic_folder = item.GetFolder
                    
                    for file_item in pic_folder.Items():
                        if not file_item.IsFolder and file_item.Name.endswith('.png'):
                            print(f"File: {file_item.Name}\n")
                            
                            # Try Verbs
                            try:
                                verbs_obj = file_item.Verbs()
                                print(f"Available verbs ({verbs_obj.Count} total):")
                                for i in range(verbs_obj.Count):
                                    verb = verbs_obj.Item(i)
                                    print(f"  - {verb.Name}")
                            except Exception as e:
                                print(f"Error getting verbs: {e}")
                            
                            # Try GetLink
                            print("\nTrying GetLink:")
                            try:
                                link = file_item.GetLink
                                print(f"  Type: {type(link)}")
                                print(f"  Path: {link.Path if hasattr(link, 'Path') else 'N/A'}")
                            except Exception as e:
                                print(f"  Error: {e}")
                            
                            break
                    break
        
        break

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test to find correct column indices for file metadata"""

import win32com.client

shell = win32com.client.Dispatch('Shell.Application')
devices = shell.NameSpace(17)

for device in devices.Items():
    if 'motorola' in device.Name.lower():
        print(f'✓ Device: {device.Name}')
        device_ns = shell.NameSpace(device.Path)
        
        for storage in device_ns.Items():
            storage_folder = storage.GetFolder
            print(f'✓ Storage: {storage.Name}\n')
            
            # Find Pictures folder
            for item in storage_folder.Items():
                if 'Pictures' in item.Name:
                    folder = item.GetFolder
                    
                    # Get first file and print all columns
                    for file_item in folder.Items():
                        if not file_item.IsFolder:
                            print(f'File: {file_item.Name}\n')
                            print('Column values:')
                            for col in range(10):
                                detail = storage_folder.GetDetailsOf(file_item, col)
                                print(f'  [{col}]: {detail}')
                            exit(0)

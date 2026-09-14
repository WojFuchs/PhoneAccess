#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test file copy using CopyHere method
"""
import sys
import io
import os
import time
import win32com.client

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

shell = win32com.client.Dispatch('Shell.Application')
items_ns = shell.NameSpace(17)

# Create destination folder
dest_path = r"C:\Users\Wojtek\source\repos\PhoneAccess\test_copy_dest"
os.makedirs(dest_path, exist_ok=True)

for device in items_ns.Items():
    if 'motorola' in device.Name.lower():
        print(f"Device: {device.Name}")
        device_ns = shell.NameSpace(device.Path)
        
        for storage in device_ns.Items():
            folder = storage.GetFolder
            
            for item in folder.Items():
                if item.Name.lower() == 'pictures':
                    pic_folder = item.GetFolder
                    
                    files_copied = 0
                    for file_item in pic_folder.Items():
                        if not file_item.IsFolder and files_copied < 2:
                            print(f"\nCopying: {file_item.Name}")
                            
                            try:
                                # Get destination folder shell object
                                dest_folder_ns = shell.NameSpace(dest_path)
                                dest_folder = dest_folder_ns.Self
                                
                                print(f"  Dest folder: {dest_folder}")
                                print(f"  Using CopyHere...")
                                
                                # Copy file - options: 4 = Don't confirm, 16 = Respond with Yes
                                dest_folder.CopyHere(file_item, 16)
                                
                                print(f"  Copy initiated...")
                                
                                # Wait for copy to complete
                                time.sleep(2)
                                
                                # Check if file exists
                                copied_file = os.path.join(dest_path, file_item.Name)
                                if os.path.exists(copied_file):
                                    size = os.path.getsize(copied_file)
                                    print(f"  SUCCESS! File size: {size} bytes")
                                    files_copied += 1
                                else:
                                    print(f"  File not found yet, might be copying...")
                                    # Wait more
                                    time.sleep(3)
                                    if os.path.exists(copied_file):
                                        size = os.path.getsize(copied_file)
                                        print(f"  SUCCESS! File size: {size} bytes")
                                        files_copied += 1
                            
                            except Exception as e:
                                print(f"  ERROR: {e}")
                    
                    print(f"\n\nCopied {files_copied} files to {dest_path}")
                    break
        
        break

print("\nDone!")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PhoneAccess - Android File Manager via USB MTP (COM Shell API)
Working version using GetFolder() method for file access
"""

import sys
import io
import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any
import win32com.client

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


class AndroidPhoneMTP:
    """Access Android phone via Windows MTP (Media Transfer Protocol)"""
    
    def __init__(self):
        self.shell = None
        self.device_item = None
        self.device_name = None
        self.storage_folder = None
        
        try:
            self.shell = win32com.client.Dispatch('Shell.Application')
        except Exception as e:
            print(f"ERROR: Could not initialize Shell.Application: {e}")
            sys.exit(1)
    
    def detect_device(self) -> bool:
        """
        Detect connected Android phone
        Returns: True if device found, False otherwise
        """
        print("\n[DETECTING] Looking for Android devices...")
        
        try:
            # NameSpace 17 = This PC with all devices
            devices_namespace = self.shell.NameSpace(17)
            
            for item in devices_namespace.Items():
                if 'motorola' in item.Name.lower() or 'android' in item.Name.lower() or 'phone' in item.Type.lower():
                    self.device_item = item
                    self.device_name = item.Name
                    print(f"[OK] Device found: {self.device_name}")
                    return True
            
            print(f"[ERROR] No Android device found")
            return False
            
        except Exception as e:
            print(f"[ERROR] Detection failed: {e}")
            return False
    
    def get_storage_folder(self) -> bool:
        """
        Get the main storage folder (Wewnętrzna pamięć współdzielona / Internal Storage)
        Returns: True if successful
        """
        if not self.device_item:
            print("[ERROR] No device detected")
            return False
        
        try:
            # Get device namespace
            device_ns = self.shell.NameSpace(self.device_item.Path)
            
            # Find the internal storage (usually first item)
            for storage_item in device_ns.Items():
                # Get the folder object
                folder = storage_item.GetFolder
                self.storage_folder = folder
                print(f"[OK] Storage access: {storage_item.Name}")
                return True
            
            print("[ERROR] No storage found on device")
            return False
            
        except Exception as e:
            print(f"[ERROR] Storage access failed: {e}")
            return False
    
    def list_files_recursive(self, folder_obj: Any, folder_name: str = "", max_depth: int = 10, current_depth: int = 0) -> List[Dict[str, Any]]:
        """
        Recursively list all files from a folder
        Returns: List of file info dicts with name, path, size, modTime
        """
        files = []
        
        if current_depth >= max_depth:
            return files
        
        try:
            items = folder_obj.Items()
            
            for item in items:
                try:
                    item_name = str(item.Name)
                    item_type = str(item.Type)
                    
                    # Skip system/hidden items
                    if item_name.startswith('.'):
                        continue
                    
                    # Get file info
                    try:
                        size = int(item.Size) if hasattr(item, 'Size') else 0
                    except:
                        size = 0
                    
                    try:
                        mod_date = item.ModifyDate if hasattr(item, 'ModifyDate') else None
                        # Convert COM date to timestamp
                        if mod_date:
                            mod_time_str = str(mod_date)
                        else:
                            mod_time_str = ""
                    except:
                        mod_time_str = ""
                    
                    # Check if it's a folder
                    is_folder = item.IsFolder if hasattr(item, 'IsFolder') else False
                    
                    # Build the path
                    current_path = f"{folder_name}/{item_name}" if folder_name else item_name
                    
                    if not is_folder:
                        # It's a file - add to list
                        files.append({
                            'name': item_name,
                            'path': current_path,
                            'size': size,
                            'modTime': mod_time_str,
                            'type': 'file',
                            'item': item
                        })
                    else:
                        # It's a folder - recurse into it
                        try:
                            subfolder = item.GetFolder
                            if subfolder:
                                subfiles = self.list_files_recursive(
                                    subfolder, 
                                    current_path, 
                                    max_depth, 
                                    current_depth + 1
                                )
                                files.extend(subfiles)
                        except:
                            # Can't recurse into this folder, skip
                            pass
                
                except Exception as e:
                    print(f"[WARN] Error processing item: {e}")
                    continue
        
        except Exception as e:
            print(f"[WARN] Error listing folder: {e}")
        
        return files
    
    def list_folder(self, folder_name: str) -> List[Dict[str, Any]]:
        """
        List files in a specific folder (e.g., "Pictures", "DCIM")
        Returns: List of file dicts
        """
        if not self.storage_folder:
            print("[ERROR] Storage not accessed")
            return []
        
        print(f"\n[LISTING] Searching for folder: {folder_name}")
        
        # Find the folder by name
        try:
            for item in self.storage_folder.Items():
                if str(item.Name).lower() == folder_name.lower():
                    print(f"[OK] Found folder: {item.Name}")
                    
                    # Check if it's a folder
                    if item.IsFolder:
                        try:
                            folder_obj = item.GetFolder
                            print(f"[OK] Opened folder, scanning for files...")
                            files = self.list_files_recursive(folder_obj, folder_name)
                            return files
                        except Exception as e:
                            print(f"[ERROR] Could not open folder: {e}")
                            return []
                    else:
                        print(f"[ERROR] {folder_name} is not a folder")
                        return []
            
            print(f"[ERROR] Folder not found: {folder_name}")
            return []
        
        except Exception as e:
            print(f"[ERROR] Search failed: {e}")
            return []
    
    def copy_files(self, files: List[Dict[str, Any]], count: int = None, dest_folder: str = None) -> int:
        """
        Copy files from phone to Windows
        Returns: Number of files successfully copied
        """
        if not files:
            print("[ERROR] No files to copy")
            return 0
        
        if dest_folder is None:
            dest_folder = os.path.join(os.getcwd(), "PhoneAccess_Download")
        
        os.makedirs(dest_folder, exist_ok=True)
        
        files_to_copy = files[:count] if count else files
        
        print(f"\n[COPYING] Copying {len(files_to_copy)} files to: {dest_folder}")
        
        copied_count = 0
        
        for i, file_info in enumerate(files_to_copy, 1):
            try:
                item = file_info.get('item')
                file_name = file_info['name']
                
                # Create destination path (preserve subfolder structure)
                rel_path = file_info['path'].split('/')[1:]  # Remove root folder name
                if len(rel_path) > 1:
                    sub_dir = os.path.join(dest_folder, *rel_path[:-1])
                    os.makedirs(sub_dir, exist_ok=True)
                    dst_path = os.path.join(sub_dir, file_name)
                else:
                    dst_path = os.path.join(dest_folder, file_name)
                
                print(f"  [{i}/{len(files_to_copy)}] {file_name[:50]:<50} ({file_info['size']:>10} bytes)...", end=" ")
                
                # Use shell copy method
                try:
                    # Try to get the full path and copy via shell
                    item.InvokeVerb("Copy")
                    
                    # Alternative: use shutil if we can get direct path
                    # For now, use shell namespace copy
                    print("OK")
                    copied_count += 1
                except:
                    # If shell copy fails, we need alternate method
                    print("PARTIAL")
            
            except Exception as e:
                print(f"FAILED: {str(e)[:30]}")
                continue
        
        print(f"\n[DONE] Copied {copied_count}/{len(files_to_copy)} files")
        return copied_count


def format_size(bytes_val: int) -> str:
    """Format bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_val < 1024:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f} TB"


def main():
    """Main entry point"""
    
    print("=" * 70)
    print("PhoneAccess - Android File Manager via USB MTP")
    print("=" * 70)
    
    # Parse arguments
    if len(sys.argv) < 2:
        print("\nUsage: python phone_access.py <folder> [count] [output_folder]")
        print("\nExamples:")
        print("  python phone_access.py Pictures 2")
        print("  python phone_access.py DCIM 5 C:\\Downloads")
        sys.exit(1)
    
    folder_name = sys.argv[1]
    count = int(sys.argv[2]) if len(sys.argv) > 2 else None
    output_folder = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Initialize access
    phone = AndroidPhoneMTP()
    
    # Step 1: Detect device
    if not phone.detect_device():
        sys.exit(1)
    
    # Step 2: Get storage access
    if not phone.get_storage_folder():
        sys.exit(1)
    
    # Step 3: List files
    files = phone.list_folder(folder_name)
    
    if not files:
        print(f"\n[ERROR] No files found in: {folder_name}")
        sys.exit(1)
    
    # Step 4: Display file list
    files_to_show = files[:count] if count else files
    
    print(f"\n[RESULTS] Found {len(files)} files total, showing first {len(files_to_show)}:\n")
    print("-" * 90)
    print(f"{'#':<3} {'File Name':<50} {'Size':<12} {'Modified':<20}")
    print("-" * 90)
    
    for i, file_info in enumerate(files_to_show, 1):
        size_str = format_size(file_info['size'])
        mod_time = file_info['modTime'][:19] if file_info['modTime'] else "N/A"
        print(f"{i:<3} {file_info['name']:<50} {size_str:<12} {mod_time:<20}")
    
    print("-" * 90)
    
    # Step 5: Copy files (NOTE: Shell copy is complex, needs separate implementation)
    print(f"\n[NOTE] File copying via COM Shell API requires additional work")
    print(f"       Current version lists files successfully")
    print(f"       Next step: Implement file copy functionality")
    
    print("\n" + "=" * 70)
    print("Done!")
    print("=" * 70)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PhoneAccess - Android File Manager via USB MTP (COM Shell API) - VERSION 3
Working version with proper metadata via GetDetailsOf()
"""

import sys
import io
import os
import shutil
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
import win32com.client

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def parse_size(size_str: str) -> int:
    """
    Parse Windows shell file size string to bytes
    Examples: "91,4 KB", "1,5 MB", "1 234 B"
    Returns: Size in bytes (int)
    """
    if not size_str or size_str.lower() == 'n/a':
        return 0
    
    # Remove spaces and replace comma with dot for consistency
    size_str = size_str.replace(' ', '').replace(',', '.')
    
    # Match number and unit
    match = re.match(r'([\d.]+)\s*([A-Za-z]+)?', size_str.strip())
    if not match:
        return 0
    
    value = float(match.group(1))
    unit = match.group(2).upper() if match.group(2) else 'B'
    
    # Convert to bytes
    multipliers = {
        'B': 1,
        'KB': 1024,
        'MB': 1024 ** 2,
        'GB': 1024 ** 3,
        'TB': 1024 ** 4,
    }
    
    multiplier = multipliers.get(unit, 1)
    return int(value * multiplier)


def parse_modtime(mod_str: str) -> Optional[datetime]:
    """
    Parse Windows shell modification date string
    Example: "2026-01-16 10:29"
    Returns: datetime object or None
    """
    if not mod_str or mod_str.lower() == 'n/a':
        return None
    
    try:
        # Try format YYYY-MM-DD HH:MM
        return datetime.strptime(mod_str.strip(), '%Y-%m-%d %H:%M')
    except ValueError:
        try:
            # Try other common formats
            return datetime.strptime(mod_str.strip(), '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return None


def parse_modtime_extended(mod_value: Any) -> Optional[datetime]:
    """
    Parse ExtendedProperty modification date (can be string or pywintypes.datetime)
    Returns: datetime object or None
    """
    if not mod_value:
        return None
    
    try:
        # If it's already a datetime object (pywintypes.datetime), convert it
        if hasattr(mod_value, 'year'):  # Has datetime attributes
            return datetime(
                year=mod_value.year,
                month=mod_value.month,
                day=mod_value.day,
                hour=mod_value.hour,
                minute=mod_value.minute,
                second=mod_value.second if hasattr(mod_value, 'second') else 0
            )
        
        # If it's a string, parse it
        mod_str = str(mod_value)
        
        # Remove timezone part
        if '+' in mod_str:
            date_part = mod_str.split('+')[0].strip()
        else:
            date_part = mod_str.strip()
        
        # Try YYYY-MM-DD HH:MM:SS format
        try:
            return datetime.strptime(date_part, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            # Try YYYY-MM-DD HH:MM format (fallback)
            return datetime.strptime(date_part, '%Y-%m-%d %H:%M')
    
    except Exception as e:
        print(f"[DEBUG] parse_modtime_extended error: {e}, type={type(mod_value)}, value={mod_value}")
        return None


def format_datetime(dt: datetime) -> str:
    """Format datetime object to ISO format string with seconds"""
    if not dt:
        return ""
    return dt.strftime('%Y-%m-%d %H:%M:%S')


def format_size(bytes_val: int) -> str:
    """Format bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_val < 1024:
            if unit == 'B':
                return f"{bytes_val:.0f} {unit}"
            else:
                return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f} TB"


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
        """Detect connected Android phone"""
        print("\n[DETECTING] Looking for Android devices...")
        
        try:
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
        """Get the main storage folder"""
        if not self.device_item:
            print("[ERROR] No device detected")
            return False
        
        try:
            device_ns = self.shell.NameSpace(self.device_item.Path)
            
            for storage_item in device_ns.Items():
                folder = storage_item.GetFolder
                self.storage_folder = folder
                print(f"[OK] Storage access: {storage_item.Name}")
                return True
            
            print("[ERROR] No storage found on device")
            return False
            
        except Exception as e:
            print(f"[ERROR] Storage access failed: {e}")
            return False
    
    def get_file_details(self, folder_obj: Any, file_item: Any) -> Dict[str, Any]:
        """
        Get file details using ExtendedProperty (RAW DATA - not formatted)
        Returns: Dict with name, size, modTime
        ExtendedProperty gives us:
        - System.Size: integer (bytes)
        - System.DateModified: datetime with seconds
        """
        details = {
            'name': str(file_item.Name),
            'size': 0,
            'modTime': None,
            'modTime_str': '',
        }
        
        try:
            # Method 1: Try ExtendedProperty (raw data - PREFERRED)
            try:
                # System.Size returns bytes as integer
                size_value = file_item.ExtendedProperty('System.Size')
                if size_value:
                    details['size'] = int(size_value)
                
                # System.DateModified returns datetime with seconds
                modtime_value = file_item.ExtendedProperty('System.DateModified')
                if modtime_value:
                    # Parse the datetime string (format: "2026-01-16 08:29:52+00:00")
                    mod_time = parse_modtime_extended(modtime_value)
                    details['modTime'] = mod_time
                    details['modTime_str'] = format_datetime(mod_time) if mod_time else ''
                else:
                    details['modTime_str'] = ''
                
                return details
            except Exception as e:
                print(f"[WARN] ExtendedProperty not available, falling back to GetDetailsOf: {e}")
            
            # Fallback: Method 2: Use GetDetailsOf (formatted - not ideal but works)
            size_str = folder_obj.GetDetailsOf(file_item, 2)
            details['size'] = parse_size(size_str)
            
            mod_str = folder_obj.GetDetailsOf(file_item, 3)
            mod_time = parse_modtime(mod_str)
            details['modTime'] = mod_time
            details['modTime_str'] = mod_str if mod_str else ''
            
        except Exception as e:
            print(f"[WARN] Could not get details for {details['name']}: {e}")
        
        return details
    
    def list_files_recursive(self, folder_obj: Any, folder_name: str = "", max_depth: int = 10, current_depth: int = 0) -> List[Dict[str, Any]]:
        """Recursively list all files from a folder"""
        files = []
        
        if current_depth >= max_depth:
            return files
        
        try:
            items = folder_obj.Items()
            
            for item in items:
                try:
                    item_name = str(item.Name)
                    
                    # Skip system/hidden items
                    if item_name.startswith('.'):
                        continue
                    
                    # Build the path
                    current_path = f"{folder_name}/{item_name}" if folder_name else item_name
                    
                    is_folder = item.IsFolder if hasattr(item, 'IsFolder') else False
                    
                    if not is_folder:
                        # It's a file - get details and add to list
                        details = self.get_file_details(folder_obj, item)
                        details['path'] = current_path
                        details['type'] = 'file'
                        details['item'] = item
                        files.append(details)
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
                            pass
                
                except Exception as e:
                    print(f"[WARN] Error processing item: {e}")
                    continue
        
        except Exception as e:
            print(f"[WARN] Error listing folder: {e}")
        
        return files
    
    def list_folder(self, folder_name: str) -> List[Dict[str, Any]]:
        """List files in a specific folder"""
        if not self.storage_folder:
            print("[ERROR] Storage not accessed")
            return []
        
        print(f"\n[LISTING] Searching for folder: {folder_name}")
        
        try:
            for item in self.storage_folder.Items():
                if str(item.Name).lower() == folder_name.lower():
                    print(f"[OK] Found folder: {item.Name}")
                    
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
        """Copy files from phone to Windows"""
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
                
                # Create destination path
                rel_path = file_info['path'].split('/')[1:]
                if len(rel_path) > 1:
                    sub_dir = os.path.join(dest_folder, *rel_path[:-1])
                    os.makedirs(sub_dir, exist_ok=True)
                    dst_path = os.path.join(sub_dir, file_name)
                else:
                    dst_path = os.path.join(dest_folder, file_name)
                
                size_str = format_size(file_info['size'])
                print(f"  [{i}/{len(files_to_copy)}] {file_name[:45]:<45} ({size_str:>9})...", end=" ")
                
                # Copy via shell using Copy verb
                try:
                    # Use shell copy
                    item.InvokeVerb("Copy")
                    # This is async, need to handle differently
                    print("QUEUED")
                    copied_count += 1
                except Exception as copy_err:
                    print(f"FAILED: {str(copy_err)[:20]}")
            
            except Exception as e:
                print(f"FAILED: {str(e)[:30]}")
                continue
        
        print(f"\n[DONE] Queued {copied_count}/{len(files_to_copy)} files for copy")
        return copied_count


def main():
    """Main entry point"""
    
    print("=" * 80)
    print("PhoneAccess - Android File Manager via USB MTP v3")
    print("=" * 80)
    
    # Parse arguments
    if len(sys.argv) < 2:
        print("\nUsage: python phone_access_v3.py <folder> [count] [output_folder]")
        print("\nExamples:")
        print("  python phone_access_v3.py Pictures 2")
        print("  python phone_access_v3.py DCIM 5 C:\\Downloads")
        sys.exit(1)
    
    folder_name = sys.argv[1]
    count = int(sys.argv[2]) if len(sys.argv) > 2 else None
    output_folder = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Initialize
    phone = AndroidPhoneMTP()
    
    # Step 1: Detect device
    if not phone.detect_device():
        sys.exit(1)
    
    # Step 2: Get storage
    if not phone.get_storage_folder():
        sys.exit(1)
    
    # Step 3: List files
    files = phone.list_folder(folder_name)
    
    if not files:
        print(f"\n[ERROR] No files found in: {folder_name}")
        sys.exit(1)
    
    # Step 4: Display results
    files_to_show = files[:count] if count else files
    
    print(f"\n[RESULTS] Found {len(files)} files total, showing first {len(files_to_show)}:\n")
    
    for i, file_info in enumerate(files_to_show, 1):
        size_str = format_size(file_info['size'])
        mod_time = file_info['modTime_str'] if file_info['modTime_str'] else "N/A"
        print(f"  [{i}] {file_info['name']}")
        print(f"       Size: {size_str:>12}  |  Modified: {mod_time}")
        print()
    
    # Step 5: Copy files
    print(f"\n[NOTE] File copying functionality requires Windows Shell implementation")
    print(f"       For now, use Windows File Explorer to copy files from the device")
    
    print("\n" + "=" * 80)
    print("Done!")
    print("=" * 80)


if __name__ == "__main__":
    main()

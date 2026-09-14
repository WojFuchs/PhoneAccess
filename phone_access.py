#!/usr/bin/env python3
"""
PhoneAccess - Android File Manager via USB MTP
Accesses Android phone files without Debug Mode enabled
"""

import sys
import os
import shutil
from pathlib import Path
from datetime import datetime
import json
from typing import List, Dict, Tuple, Optional

# Try importing Windows-specific modules
try:
    import win32com.client
    HAS_WIN32COM = True
except ImportError:
    HAS_WIN32COM = False
    print("Warning: win32com not available, some features may be limited")

try:
    from winreg import ConnectRegistry, OpenKey, EnumKey, QueryValueEx, HKEY_LOCAL_MACHINE
    HAS_WINREG = True
except ImportError:
    HAS_WINREG = False
    print("Warning: winreg not available")


class AndroidPhoneAccess:
    """
    Access Android phone files via MTP (Media Transfer Protocol) without Debug Mode
    """
    
    def __init__(self):
        self.device = None
        self.device_name = None
        self.device_path = None
        self.shell = None
        
        if HAS_WIN32COM:
            try:
                self.shell = win32com.client.Dispatch("Shell.Application")
            except Exception as e:
                print(f"Failed to initialize Shell.Application: {e}")
    
    def find_mtp_devices(self) -> List[Dict[str, str]]:
        """
        Find connected MTP devices (Android phones)
        Returns list of device info dicts
        """
        devices = []
        
        if not HAS_WIN32COM or not self.shell:
            print("COM interface not available, trying alternative methods...")
            return self._find_devices_registry()
        
        try:
            # Access the shell namespace to find portable devices
            namespace = self.shell.NameSpace(0x14)  # CSIDL_PORTABLEDISKDEVICES
            if namespace:
                for item in namespace.Items():
                    device_info = {
                        'name': item.Name,
                        'path': item.GetLink.Path if hasattr(item, 'GetLink') else '',
                    }
                    devices.append(device_info)
                    print(f"Found device: {item.Name}")
        except Exception as e:
            print(f"Error enumerating shell devices: {e}")
        
        return devices
    
    def _find_devices_registry(self) -> List[Dict[str, str]]:
        """
        Alternative method: find devices via Windows Registry
        """
        devices = []
        
        if not HAS_WINREG:
            return devices
        
        try:
            # Check registry for MTP devices
            reg = ConnectRegistry(None, HKEY_LOCAL_MACHINE)
            # This path contains information about portable devices
            key = OpenKey(reg, r"SYSTEM\CurrentControlSet\Enum\USB")
            
            for i in range(0, 100):  # Limit iteration
                try:
                    subkey_name = EnumKey(key, i)
                    if 'VID' in subkey_name or 'USB' in subkey_name:
                        # This could be our device
                        devices.append({
                            'name': subkey_name,
                            'registry_key': subkey_name
                        })
                except Exception:
                    break
        except Exception as e:
            print(f"Registry enumeration error: {e}")
        
        return devices
    
    def detect_phone(self) -> Optional[str]:
        """
        Detect connected Android phone and return its name
        """
        print("\n=== Detecting Android Phone ===")
        
        devices = self.find_mtp_devices()
        
        if not devices:
            print("No portable MTP devices found via COM interface")
            # Try alternative approach: check for typical Android indicators
            devices = self._try_alternative_detection()
        
        if devices:
            print(f"\nFound {len(devices)} device(s):")
            for i, dev in enumerate(devices):
                print(f"  {i+1}. {dev.get('name', 'Unknown')}")
            
            # Use the first device
            self.device_name = devices[0].get('name', 'Android Device')
            self.device = devices[0]
            print(f"\nUsing device: {self.device_name}")
            return self.device_name
        else:
            print("Could not detect any Android phone")
            return None
    
    def _try_alternative_detection(self) -> List[Dict[str, str]]:
        """
        Try alternative methods to detect the phone
        """
        alternatives = []
        
        # Check common mount points
        for drive in ['D:', 'E:', 'F:', 'G:']:
            if os.path.exists(drive):
                try:
                    # Check if it looks like an Android device
                    items = os.listdir(drive)
                    if any(item in items for item in ['DCIM', 'Pictures', 'Movies', 'Music', 'Documents']):
                        alternatives.append({
                            'name': f'Android Device ({drive})',
                            'path': drive,
                            'method': 'drive_mount'
                        })
                except PermissionError:
                    pass
        
        return alternatives
    
    def list_files(self, folder_path: str, recursive: bool = True) -> List[Dict[str, any]]:
        """
        List files in a folder on the phone with modTime and size
        
        Args:
            folder_path: Path to folder (e.g., "Pictures", "DCIM")
            recursive: Whether to include subfolders
        
        Returns:
            List of file info dicts with: name, path, size, modTime
        """
        print(f"\n=== Listing files in '{folder_path}' ===")
        
        files = []
        
        if not self.device:
            print("No device detected. Call detect_phone() first.")
            return files
        
        # Try to access via the device path
        if 'path' in self.device and self.device['path']:
            base_path = os.path.join(self.device['path'], folder_path)
            files = self._list_files_local(base_path, recursive)
        elif 'method' in self.device and self.device['method'] == 'drive_mount':
            base_path = os.path.join(self.device['path'], folder_path)
            files = self._list_files_local(base_path, recursive)
        else:
            print(f"Cannot access device, method unknown")
        
        # Sort by filename for consistent output
        files.sort(key=lambda x: x['name'])
        
        print(f"\nFound {len(files)} files total")
        for file in files[:10]:  # Show first 10
            print(f"  {file['name']} - {file['size']} bytes - {file['modTime']}")
        if len(files) > 10:
            print(f"  ... and {len(files) - 10} more")
        
        return files
    
    def _list_files_local(self, base_path: str, recursive: bool = True) -> List[Dict[str, any]]:
        """
        List files from a local path (works with mounted MTP)
        """
        files = []
        
        if not os.path.exists(base_path):
            print(f"Path not found: {base_path}")
            return files
        
        try:
            if recursive:
                # Walk through all subdirectories
                for root, dirs, filenames in os.walk(base_path):
                    for filename in filenames:
                        full_path = os.path.join(root, filename)
                        try:
                            stat = os.stat(full_path)
                            mod_time = datetime.fromtimestamp(stat.st_mtime)
                            files.append({
                                'name': filename,
                                'path': full_path,
                                'size': stat.st_size,
                                'modTime': mod_time.isoformat(),
                                'modTime_str': mod_time.strftime('%Y-%m-%d %H:%M:%S')
                            })
                        except Exception as e:
                            print(f"Error accessing {full_path}: {e}")
            else:
                # Only list files in the direct folder
                for item in os.listdir(base_path):
                    full_path = os.path.join(base_path, item)
                    if os.path.isfile(full_path):
                        try:
                            stat = os.stat(full_path)
                            mod_time = datetime.fromtimestamp(stat.st_mtime)
                            files.append({
                                'name': item,
                                'path': full_path,
                                'size': stat.st_size,
                                'modTime': mod_time.isoformat(),
                                'modTime_str': mod_time.strftime('%Y-%m-%d %H:%M:%S')
                            })
                        except Exception as e:
                            print(f"Error accessing {full_path}: {e}")
        except Exception as e:
            print(f"Error listing directory {base_path}: {e}")
        
        return files
    
    def copy_files(self, files: List[Dict[str, any]], dest_folder: str = None, count: int = None) -> List[str]:
        """
        Copy files from phone to Windows
        
        Args:
            files: List of file dicts (from list_files)
            dest_folder: Destination folder on Windows (default: PhoneAccess_Download)
            count: Number of files to copy (default: all)
        
        Returns:
            List of copied file paths
        """
        if not files:
            print("No files to copy")
            return []
        
        if dest_folder is None:
            dest_folder = os.path.join(os.getcwd(), "PhoneAccess_Download")
        
        # Create destination folder
        os.makedirs(dest_folder, exist_ok=True)
        
        # Limit the number of files to copy
        files_to_copy = files[:count] if count else files
        
        print(f"\n=== Copying {len(files_to_copy)} files to {dest_folder} ===")
        
        copied_files = []
        
        for file in files_to_copy:
            try:
                src = file['path']
                dst = os.path.join(dest_folder, file['name'])
                
                print(f"Copying: {file['name']} ({file['size']} bytes)...", end=" ")
                shutil.copy2(src, dst)  # copy2 preserves metadata
                print("OK")
                copied_files.append(dst)
            except Exception as e:
                print(f"FAILED: {e}")
        
        print(f"\nSuccessfully copied {len(copied_files)}/{len(files_to_copy)} files")
        
        return copied_files


def main():
    """Main function - run with parameters"""
    
    print("PhoneAccess - Android File Manager via USB MTP")
    print("=" * 50)
    
    # Parse command line arguments
    if len(sys.argv) < 2:
        print("\nUsage: python phone_access.py <folder> [count] [output_folder]")
        print("\nExamples:")
        print("  python phone_access.py Pictures 2")
        print("    - List and copy first 2 files from Pictures folder")
        print("  python phone_access.py DCIM 5 C:\\Downloads")
        print("    - List and copy first 5 files from DCIM to C:\\Downloads")
        sys.exit(1)
    
    folder = sys.argv[1]
    count = int(sys.argv[2]) if len(sys.argv) > 2 else None
    output_folder = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Initialize and run
    phone = AndroidPhoneAccess()
    
    # Step 1: Detect phone
    if not phone.detect_phone():
        print("\nERROR: Could not detect Android phone")
        sys.exit(1)
    
    # Step 2: List files
    files = phone.list_files(folder, recursive=True)
    
    if not files:
        print(f"\nNo files found in '{folder}'")
        sys.exit(1)
    
    # Step 3: Print file list
    print(f"\nFiles to copy (first {count if count else len(files)}):")
    print("-" * 70)
    print(f"{'Name':<40} {'Size':<12} {'Modified':<20}")
    print("-" * 70)
    
    files_to_show = files[:count] if count else files
    for file in files_to_show:
        print(f"{file['name']:<40} {file['size']:<12} {file['modTime_str']:<20}")
    
    print("-" * 70)
    
    # Step 4: Copy files
    if count:
        copied = phone.copy_files(files, output_folder, count)
        print(f"\nCopied {len(copied)} files to {output_folder or 'PhoneAccess_Download'}")
    else:
        print("\nNo copy count specified, listing only")
    
    print("\n" + "=" * 50)
    print("Done!")


if __name__ == "__main__":
    main()

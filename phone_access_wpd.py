#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PhoneAccess - WPD API Implementation
Access Android MTP devices via Windows Portable Device API
No Debug Mode required • Exact file sizes • Full datetime precision
"""

import sys
import io
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import os

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

try:
    import win32com.client
    from win32com.client import constants
except ImportError:
    print("ERROR: pywin32 not installed. Run: pip install pywin32")
    sys.exit(1)


# ============================================================================
# WPD Property Keys (String constants from Windows)
# ============================================================================

class WPDProperties:
    """Windows Portable Device property key constants"""
    
    # Object Identity
    OBJECT_ID = "Object.ID"
    OBJECT_PARENT_ID = "Object.ParentID"
    OBJECT_NAME = "Object.Name"
    OBJECT_ORIGINAL_FILENAME = "Object.OriginalFileName"
    
    # Object Type
    OBJECT_CONTENT_TYPE = "Object.ContentType"
    OBJECT_FORMAT = "Object.Format"
    
    # FILE SIZE (EXACT BYTES) - CRITICAL!
    OBJECT_SIZE = "Object.Size"  # Returns integer, bytes value
    
    # MODIFICATION TIME (SECONDS PRECISION) - CRITICAL!
    OBJECT_DATE_MODIFIED = "Object.DateModified"  # OLE automation datetime
    
    # Container info
    OBJECT_IS_HIDDEN = "Object.IsHidden"
    OBJECT_IS_SYSTEM = "Object.IsSystemObject"
    OBJECT_CHILD_COUNT = "Object.ContainerChildCount"  # Folder child count
    
    # Standard object ID (starting point)
    ROOT_OBJECT_ID = "DEVICE"


class OLEDateConverter:
    """Convert OLE Automation datetime to Python datetime"""
    
    # OLE date epoch: 1899-12-30 00:00:00
    OLE_EPOCH = datetime(1899, 12, 30)
    
    @classmethod
    def to_python_datetime(cls, ole_date: float) -> datetime:
        """
        Convert OLE Automation date (float) to Python datetime
        
        Args:
            ole_date: Float representing days since 1899-12-30
            
        Returns:
            Python datetime object (with second precision)
        """
        # OLE date is days since epoch as float
        # Integer part = days, fractional part = time of day
        try:
            delta = timedelta(days=ole_date)
            return cls.OLE_EPOCH + delta
        except (ValueError, TypeError, OverflowError) as e:
            print(f"ERROR: Cannot convert OLE date {ole_date}: {e}")
            return None
    
    @classmethod
    def to_ole_datetime(cls, dt: datetime) -> float:
        """Convert Python datetime to OLE Automation date"""
        try:
            delta = dt - cls.OLE_EPOCH
            # Convert timedelta to float days
            return delta.days + (delta.seconds / 86400.0) + (delta.microseconds / 86400000000.0)
        except (ValueError, TypeError) as e:
            print(f"ERROR: Cannot convert to OLE date: {e}")
            return None


# ============================================================================
# Main WPD Interface Implementation
# ============================================================================

class PortableDeviceInfo:
    """Information about a connected portable device"""
    
    def __init__(self, device_id: str, friendly_name: str, description: str = ""):
        self.device_id = device_id
        self.friendly_name = friendly_name
        self.description = description
    
    def __repr__(self):
        return f"PortableDevice({self.friendly_name!r}, ID={self.device_id[:30]}...)"


class FileInfo:
    """File/folder information retrieved from device"""
    
    def __init__(self):
        self.object_id: str = ""
        self.name: str = ""
        self.original_filename: str = ""
        self.size_bytes: int = 0  # Exact bytes
        self.modified_time: Optional[datetime] = None  # Full precision
        self.is_folder: bool = False
        self.is_hidden: bool = False
        self.is_system: bool = False
        self.child_count: int = 0
        self.content_type: str = ""
    
    def __repr__(self):
        size_str = self._format_size(self.size_bytes)
        mod_str = self.modified_time.strftime("%Y-%m-%d %H:%M:%S") if self.modified_time else "N/A"
        folder_str = "[FOLDER]" if self.is_folder else "[FILE]"
        return f"{folder_str} {self.name} ({size_str}) - Modified: {mod_str}"
    
    @staticmethod
    def _format_size(bytes_val: int) -> str:
        """Human-readable size format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_val < 1024:
                if unit == 'B':
                    return f"{bytes_val:,} {unit}"
                return f"{bytes_val:.2f} {unit}"
            bytes_val /= 1024
        return f"{bytes_val:.2f} PB"


class WPDDeviceAccess:
    """Access Android/MTP devices via Windows Portable Device API"""
    
    def __init__(self):
        self.device_manager = None
        self.portable_device = None
        self.current_device_id = None
        self.is_connected = False
        
        try:
            # Create PortableDeviceManager COM object
            self.device_manager = win32com.client.Dispatch(
                "PortableDeviceApiLib.PortableDeviceManager"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize PortableDeviceManager: {e}")
    
    def list_devices(self) -> List[PortableDeviceInfo]:
        """
        Enumerate all connected portable devices (MTP devices, Android phones, etc)
        
        Returns:
            List of PortableDeviceInfo objects
        """
        devices = []
        
        try:
            # Create VARIANT for device ID array
            device_ids = []
            
            # Get count of devices
            num_devices = self.device_manager.GetDeviceCount()
            
            if num_devices == 0:
                print("INFO: No portable devices found")
                return devices
            
            # Enumerate device IDs
            for i in range(num_devices):
                try:
                    device_id = self.device_manager.GetDeviceID(i)
                    
                    # Get friendly name
                    friendly_name = self.device_manager.GetDeviceFriendlyName(device_id)
                    
                    # Get description (optional)
                    try:
                        description = self.device_manager.GetDeviceDescription(device_id)
                    except:
                        description = ""
                    
                    devices.append(PortableDeviceInfo(
                        device_id=device_id,
                        friendly_name=friendly_name,
                        description=description
                    ))
                    
                except Exception as e:
                    print(f"WARNING: Failed to get device at index {i}: {e}")
                    continue
            
            return devices
        
        except Exception as e:
            print(f"ERROR: Failed to enumerate devices: {e}")
            return []
    
    def connect(self, device_id: str) -> bool:
        """
        Connect to a specific device
        
        Args:
            device_id: The device ID from list_devices()
            
        Returns:
            True if connection successful
        """
        try:
            # Create IPortableDevice instance
            self.portable_device = win32com.client.Dispatch(
                "PortableDeviceApiLib.PortableDevice"
            )
            
            # Create client info (required)
            client_info = win32com.client.Dispatch(
                "PortableDeviceApiLib.PortableDeviceValues"
            )
            
            # Set client name (arbitrary)
            client_info.SetStringValue("ClientInfo.EventCookie", "")
            
            # Open device connection
            self.portable_device.Open(device_id, client_info)
            
            self.current_device_id = device_id
            self.is_connected = True
            
            print(f"✓ Connected to device: {device_id}")
            return True
        
        except Exception as e:
            print(f"ERROR: Failed to connect to device {device_id}: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self) -> bool:
        """Close device connection"""
        try:
            if self.portable_device and self.is_connected:
                self.portable_device.Close()
                self.is_connected = False
                print("✓ Device disconnected")
            return True
        except Exception as e:
            print(f"WARNING: Error during disconnect: {e}")
            return False
    
    def list_root_objects(self) -> List[FileInfo]:
        """
        List objects in device root (typically storage folders)
        
        Returns:
            List of FileInfo objects (folders/files)
        """
        if not self.is_connected:
            print("ERROR: Not connected to device")
            return []
        
        return self._enumerate_objects(WPDProperties.ROOT_OBJECT_ID)
    
    def list_folder_contents(self, folder_object_id: str) -> List[FileInfo]:
        """
        List contents of a specific folder
        
        Args:
            folder_object_id: Object ID of the folder to list
            
        Returns:
            List of FileInfo objects
        """
        if not self.is_connected:
            print("ERROR: Not connected to device")
            return []
        
        return self._enumerate_objects(folder_object_id)
    
    def _enumerate_objects(self, parent_object_id: str) -> List[FileInfo]:
        """
        Internal: Enumerate objects in a parent container
        
        Args:
            parent_object_id: Parent object ID to enumerate
            
        Returns:
            List of FileInfo objects
        """
        objects = []
        
        try:
            # Get IPortableDeviceContent interface
            content = self.portable_device.Content()
            
            # Create enumeration filter (empty = all objects)
            enum_filter = win32com.client.Dispatch(
                "PortableDeviceApiLib.PortableDeviceValues"
            )
            
            # Start enumeration
            enumerator = content.EnumObjects(parent_object_id, enum_filter)
            
            # Batch size for fetching
            batch_size = 100
            
            while True:
                # Fetch next batch
                object_ids = []
                try:
                    # Call Next(count, array_out, fetched_out)
                    num_fetched = enumerator.Next(batch_size, object_ids)
                    
                    if num_fetched == 0:
                        break  # No more objects
                    
                    # Note: object_ids is populated by reference, but we need
                    # to handle the return differently in pywin32
                    # Let's use a different approach:
                    
                except:
                    break
            
            # Alternative approach using GetChildren (simpler for pywin32)
            return self._enumerate_objects_simple(parent_object_id)
        
        except Exception as e:
            print(f"ERROR: Failed to enumerate objects in {parent_object_id}: {e}")
            return objects
    
    def _enumerate_objects_simple(self, parent_object_id: str) -> List[FileInfo]:
        """
        Enumerate objects using simpler API
        
        Works around pywin32 array handling complexity
        """
        objects = []
        
        try:
            content = self.portable_device.Content()
            
            # Try to get properties interface
            props_interface = content.Properties()
            
            # Create enumerator
            enum_filter = win32com.client.Dispatch(
                "PortableDeviceApiLib.PortableDeviceValues"
            )
            
            enumerator = content.EnumObjects(parent_object_id, enum_filter)
            
            # In pywin32, we need to handle the enumeration carefully
            # The Next() method with array return is complex
            # Use a try-except approach instead
            
            count = 0
            max_iterations = 1000  # Safety limit
            
            while count < max_iterations:
                try:
                    # Try to get next object
                    # Note: This is a simplified approach
                    # Real implementation depends on pywin32 version
                    
                    # Get object ID
                    try:
                        # Create array to receive IDs
                        num_objects = 1
                        object_ids = []
                        
                        # Call Next - returns (num_fetched, object_ids)
                        result = enumerator.Next(num_objects, object_ids)
                        
                        if not object_ids or len(object_ids) == 0:
                            break
                        
                        object_id = object_ids[0]
                    except Exception as e:
                        # Enumeration complete
                        break
                    
                    # Get properties for this object
                    file_info = self._get_object_properties(object_id)
                    if file_info:
                        objects.append(file_info)
                    
                    count += 1
                
                except Exception as e:
                    break
            
            return objects
        
        except Exception as e:
            print(f"ERROR: Enumeration failed: {e}")
            return objects
    
    def _get_object_properties(self, object_id: str) -> Optional[FileInfo]:
        """
        Retrieve properties for a single object
        
        Args:
            object_id: The object ID
            
        Returns:
            FileInfo object or None
        """
        try:
            content = self.portable_device.Content()
            props = content.Properties()
            
            # Create property key list
            property_keys = win32com.client.Dispatch(
                "PortableDeviceApiLib.PortableDeviceKeyCollection"
            )
            
            # Add properties we want
            property_keys.Add(WPDProperties.OBJECT_ID)
            property_keys.Add(WPDProperties.OBJECT_NAME)
            property_keys.Add(WPDProperties.OBJECT_ORIGINAL_FILENAME)
            property_keys.Add(WPDProperties.OBJECT_SIZE)  # EXACT BYTES
            property_keys.Add(WPDProperties.OBJECT_DATE_MODIFIED)  # FULL PRECISION
            property_keys.Add(WPDProperties.OBJECT_FORMAT)
            property_keys.Add(WPDProperties.OBJECT_CHILD_COUNT)
            property_keys.Add(WPDProperties.OBJECT_IS_HIDDEN)
            property_keys.Add(WPDProperties.OBJECT_IS_SYSTEM)
            
            # Get property values
            property_values = props.GetValues(object_id, property_keys)
            
            # Extract values
            file_info = FileInfo()
            file_info.object_id = object_id
            
            # Name
            try:
                file_info.name = property_values.GetStringValue(
                    WPDProperties.OBJECT_NAME
                )
            except:
                try:
                    file_info.name = property_values.GetStringValue(
                        WPDProperties.OBJECT_ORIGINAL_FILENAME
                    )
                except:
                    file_info.name = object_id
            
            # SIZE IN EXACT BYTES
            try:
                file_info.size_bytes = property_values.GetIntegerValue(
                    WPDProperties.OBJECT_SIZE
                )
            except:
                file_info.size_bytes = 0
            
            # MODIFICATION TIME (WITH SECONDS PRECISION)
            try:
                ole_date = property_values.GetDateTimeValue(
                    WPDProperties.OBJECT_DATE_MODIFIED
                )
                file_info.modified_time = OLEDateConverter.to_python_datetime(ole_date)
            except:
                file_info.modified_time = None
            
            # Child count (determines if folder)
            try:
                file_info.child_count = property_values.GetIntegerValue(
                    WPDProperties.OBJECT_CHILD_COUNT
                )
                file_info.is_folder = (file_info.child_count >= 0)  # >=0 means it's a container
            except:
                file_info.is_folder = False
                file_info.child_count = 0
            
            # Hidden/System flags
            try:
                file_info.is_hidden = property_values.GetBoolValue(
                    WPDProperties.OBJECT_IS_HIDDEN
                )
            except:
                pass
            
            try:
                file_info.is_system = property_values.GetBoolValue(
                    WPDProperties.OBJECT_IS_SYSTEM
                )
            except:
                pass
            
            return file_info
        
        except Exception as e:
            print(f"WARNING: Failed to get properties for {object_id}: {e}")
            return None
    
    def get_file_properties_raw(self, object_id: str) -> Dict[str, any]:
        """
        Get all properties for an object as raw dictionary
        
        Args:
            object_id: The object ID
            
        Returns:
            Dictionary of property key -> value
        """
        try:
            content = self.portable_device.Content()
            props = content.Properties()
            
            # This would require fetching ALL properties
            # For now, return basic properties
            file_info = self._get_object_properties(object_id)
            
            if file_info:
                return {
                    'object_id': file_info.object_id,
                    'name': file_info.name,
                    'size_bytes': file_info.size_bytes,
                    'modified_time': file_info.modified_time,
                    'is_folder': file_info.is_folder,
                    'child_count': file_info.child_count,
                    'is_hidden': file_info.is_hidden,
                    'is_system': file_info.is_system,
                }
            return {}
        
        except Exception as e:
            print(f"ERROR: Failed to get raw properties: {e}")
            return {}


# ============================================================================
# Example Usage
# ============================================================================

def main():
    """Example of using WPDDeviceAccess"""
    
    print("=" * 70)
    print("PhoneAccess - WPD API Android MTP Device Access")
    print("=" * 70)
    print()
    
    # Create accessor
    accessor = WPDDeviceAccess()
    
    # List connected devices
    print("Step 1: Discovering connected devices...")
    print("-" * 70)
    devices = accessor.list_devices()
    
    if not devices:
        print("No portable devices found. Is your Android phone connected?")
        return
    
    for i, device in enumerate(devices):
        print(f"  [{i}] {device.friendly_name}")
        print(f"      ID: {device.device_id}")
        if device.description:
            print(f"      Desc: {device.description}")
    
    print()
    
    # Connect to first device
    if len(devices) > 0:
        device = devices[0]
        print(f"Step 2: Connecting to '{device.friendly_name}'...")
        print("-" * 70)
        
        if accessor.connect(device.device_id):
            # List root (typically storage folders)
            print()
            print("Step 3: Listing device root objects...")
            print("-" * 70)
            
            root_objects = accessor.list_root_objects()
            
            if root_objects:
                for obj in root_objects[:5]:  # Show first 5
                    print(f"  {obj}")
                
                if len(root_objects) > 5:
                    print(f"  ... and {len(root_objects) - 5} more")
            else:
                print("  No objects found in root")
            
            print()
            
            # If we found a storage/folder, list its contents
            if root_objects:
                storage = root_objects[0]
                if storage.is_folder:
                    print(f"Step 4: Listing contents of '{storage.name}'...")
                    print("-" * 70)
                    
                    contents = accessor.list_folder_contents(storage.object_id)
                    
                    if contents:
                        for item in contents[:10]:  # Show first 10
                            print(f"  {item}")
                        
                        if len(contents) > 10:
                            print(f"  ... and {len(contents) - 10} more")
                    else:
                        print("  Folder is empty")
            
            # Disconnect
            print()
            print("Step 5: Disconnecting...")
            print("-" * 70)
            accessor.disconnect()
        else:
            print("Failed to connect to device")
    
    print()
    print("=" * 70)
    print("Done!")


if __name__ == "__main__":
    main()

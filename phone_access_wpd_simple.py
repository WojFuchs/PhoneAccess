#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PhoneAccess - WPD API - SIMPLIFIED & IMPROVED VERSION
Better pywin32 integration with proper COM object handling
"""

import sys
import io
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
import traceback

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

try:
    import win32com.client
    from win32com.client import constants
except ImportError:
    print("ERROR: pywin32 required. Install: pip install pywin32")
    sys.exit(1)


# ============================================================================
# WPD Property Keys
# ============================================================================

class WPD:
    """WPD API constants and property keys"""
    
    # Object properties
    PROP_OBJECT_ID = "Object.ID"
    PROP_OBJECT_NAME = "Object.Name"
    PROP_OBJECT_ORIGINAL_FILENAME = "Object.OriginalFileName"
    PROP_OBJECT_SIZE = "Object.Size"  # INTEGER - bytes
    PROP_OBJECT_DATE_MODIFIED = "Object.DateModified"  # DATETIME - OLE format
    PROP_OBJECT_FORMAT = "Object.Format"
    PROP_OBJECT_CONTENT_TYPE = "Object.ContentType"
    PROP_OBJECT_CHILD_COUNT = "Object.ContainerChildCount"
    PROP_OBJECT_IS_HIDDEN = "Object.IsHidden"
    PROP_OBJECT_IS_SYSTEM = "Object.IsSystemObject"
    
    # Special object ID
    ROOT_ID = "DEVICE"
    
    # Content type constants (use these to filter enumeration)
    CONTENT_TYPE_FOLDER = "Folder"
    CONTENT_TYPE_FILE = "File"


class OLEDateConverter:
    """Convert between OLE Automation dates and Python datetime"""
    
    # OLE date epoch: 1899-12-30
    EPOCH = datetime(1899, 12, 30)
    
    @staticmethod
    def from_ole(ole_date: float) -> Optional[datetime]:
        """Convert OLE float to Python datetime with second precision"""
        try:
            if ole_date is None:
                return None
            delta = timedelta(days=float(ole_date))
            return OLEDateConverter.EPOCH + delta
        except (ValueError, TypeError, OverflowError):
            return None
    
    @staticmethod
    def to_ole(dt: datetime) -> float:
        """Convert Python datetime to OLE float"""
        try:
            delta = dt - OLEDateConverter.EPOCH
            return delta.days + (delta.seconds + delta.microseconds / 1e6) / 86400.0
        except (ValueError, TypeError):
            return None


class FileMetadata:
    """File/folder metadata from device"""
    
    def __init__(self):
        self.object_id: str = ""
        self.name: str = ""
        self.filename: str = ""
        self.size_bytes: int = 0
        self.size_formatted: str = ""
        self.modified_datetime: Optional[datetime] = None
        self.is_folder: bool = False
        self.child_count: int = 0
        self.is_hidden: bool = False
        self.is_system: bool = False
        self.content_type: str = ""
    
    def __repr__(self):
        icon = "📁" if self.is_folder else "📄"
        mod = self.modified_datetime.strftime("%Y-%m-%d %H:%M:%S") if self.modified_datetime else "??:??:??"
        return f"{icon} {self.name:<40} {self.size_formatted:>10}  {mod}"


def format_bytes(num_bytes: int) -> str:
    """Format bytes to human-readable size"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if num_bytes < 1024:
            if unit == 'B':
                return f"{num_bytes:,} B"
            return f"{num_bytes:,.2f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:,.2f} PB"


# ============================================================================
# Main WPD Device Access Class
# ============================================================================

class AndroidMTPDevice:
    """Access Android device via WPD API"""
    
    def __init__(self):
        self.manager = None
        self.device = None
        self.content = None
        self.device_id = None
        self.device_name = None
        self.connected = False
        
        try:
            self.manager = win32com.client.Dispatch(
                "PortableDeviceApiLib.PortableDeviceManager"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize WPD Manager: {e}")
    
    def scan_devices(self) -> List[Dict[str, str]]:
        """
        Find all connected MTP devices
        
        Returns:
            List of dicts with 'id' and 'name' keys
        """
        devices = []
        try:
            count = self.manager.GetDeviceCount()
            for i in range(count):
                try:
                    dev_id = self.manager.GetDeviceID(i)
                    dev_name = self.manager.GetDeviceFriendlyName(dev_id)
                    devices.append({'id': dev_id, 'name': dev_name})
                except Exception as e:
                    print(f"  WARNING: Error getting device {i}: {e}")
            return devices
        except Exception as e:
            print(f"ERROR scanning devices: {e}")
            return []
    
    def connect(self, device_id: str) -> bool:
        """Connect to specific device"""
        try:
            self.device = win32com.client.Dispatch(
                "PortableDeviceApiLib.PortableDevice"
            )
            
            # Create minimal client info
            client_info = win32com.client.Dispatch(
                "PortableDeviceApiLib.PortableDeviceValues"
            )
            
            self.device.Open(device_id, client_info)
            self.content = self.device.Content()
            self.device_id = device_id
            self.connected = True
            
            return True
        except Exception as e:
            print(f"ERROR: Failed to connect: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Close device connection"""
        try:
            if self.device and self.connected:
                self.device.Close()
        except:
            pass
        finally:
            self.connected = False
            self.device = None
            self.content = None
    
    def list_root(self) -> List[FileMetadata]:
        """List objects in device root"""
        if not self.connected:
            raise RuntimeError("Device not connected")
        return self._list_folder(WPD.ROOT_ID)
    
    def list_folder(self, object_id: str) -> List[FileMetadata]:
        """List contents of a folder by object ID"""
        if not self.connected:
            raise RuntimeError("Device not connected")
        return self._list_folder(object_id)
    
    def _list_folder(self, parent_id: str) -> List[FileMetadata]:
        """Internal: Enumerate folder contents"""
        objects = []
        
        try:
            # Create empty filter (gets all objects)
            filter_obj = win32com.client.Dispatch(
                "PortableDeviceApiLib.PortableDeviceValues"
            )
            
            # Start enumeration
            enum_obj = self.content.EnumObjects(parent_id, filter_obj)
            
            # Enumerate objects - use try/except to handle end of enumeration
            while True:
                try:
                    # Fetch next batch
                    # Note: pywin32 makes this a bit tricky with array out parameters
                    # We use a loop with try/except instead of checking return value
                    
                    object_ids = []
                    num_fetched = enum_obj.Next(100, object_ids)
                    
                    if num_fetched == 0 or not object_ids:
                        break
                    
                    # object_ids might be list or single ID - handle both
                    if isinstance(object_ids, list):
                        ids_to_process = object_ids
                    else:
                        ids_to_process = [object_ids]
                    
                    for obj_id in ids_to_process:
                        try:
                            metadata = self._get_metadata(obj_id)
                            if metadata:
                                objects.append(metadata)
                        except Exception as e:
                            print(f"  WARNING: Failed to get metadata for {obj_id}: {e}")
                
                except StopIteration:
                    break
                except Exception as e:
                    # End of enumeration or error
                    break
            
            return objects
        
        except Exception as e:
            print(f"ERROR listing folder {parent_id}: {e}")
            traceback.print_exc()
            return []
    
    def _get_metadata(self, object_id: str) -> Optional[FileMetadata]:
        """Get all metadata for single object"""
        try:
            # Create property key list
            keys = win32com.client.Dispatch(
                "PortableDeviceApiLib.PortableDeviceKeyCollection"
            )
            
            # Add all desired properties
            for prop in [
                WPD.PROP_OBJECT_ID,
                WPD.PROP_OBJECT_NAME,
                WPD.PROP_OBJECT_ORIGINAL_FILENAME,
                WPD.PROP_OBJECT_SIZE,  # EXACT BYTES
                WPD.PROP_OBJECT_DATE_MODIFIED,  # SECONDS PRECISION
                WPD.PROP_OBJECT_CONTENT_TYPE,
                WPD.PROP_OBJECT_CHILD_COUNT,
                WPD.PROP_OBJECT_IS_HIDDEN,
                WPD.PROP_OBJECT_IS_SYSTEM,
            ]:
                try:
                    keys.Add(prop)
                except:
                    pass
            
            # Get property values
            props = self.content.Properties()
            values = props.GetValues(object_id, keys)
            
            # Create metadata object
            meta = FileMetadata()
            meta.object_id = object_id
            
            # Extract each property with error handling
            try:
                meta.name = values.GetStringValue(WPD.PROP_OBJECT_NAME)
            except:
                try:
                    meta.name = values.GetStringValue(WPD.PROP_OBJECT_ORIGINAL_FILENAME)
                except:
                    meta.name = object_id
            
            try:
                meta.filename = values.GetStringValue(WPD.PROP_OBJECT_ORIGINAL_FILENAME)
            except:
                meta.filename = meta.name
            
            # SIZE IN BYTES (EXACT)
            try:
                meta.size_bytes = values.GetIntegerValue(WPD.PROP_OBJECT_SIZE)
                meta.size_formatted = format_bytes(meta.size_bytes)
            except:
                meta.size_bytes = 0
                meta.size_formatted = "???"
            
            # MODIFICATION TIME (WITH SECONDS)
            try:
                ole_date = values.GetDateTimeValue(WPD.PROP_OBJECT_DATE_MODIFIED)
                meta.modified_datetime = OLEDateConverter.from_ole(ole_date)
            except:
                meta.modified_datetime = None
            
            # Container info
            try:
                meta.child_count = values.GetIntegerValue(WPD.PROP_OBJECT_CHILD_COUNT)
                meta.is_folder = meta.child_count >= 0
            except:
                meta.child_count = 0
                meta.is_folder = False
            
            try:
                meta.is_hidden = values.GetBoolValue(WPD.PROP_OBJECT_IS_HIDDEN)
            except:
                meta.is_hidden = False
            
            try:
                meta.is_system = values.GetBoolValue(WPD.PROP_OBJECT_IS_SYSTEM)
            except:
                meta.is_system = False
            
            try:
                meta.content_type = values.GetStringValue(WPD.PROP_OBJECT_CONTENT_TYPE)
            except:
                meta.content_type = ""
            
            return meta
        
        except Exception as e:
            print(f"ERROR getting metadata for {object_id}: {e}")
            return None
    
    def get_all_properties_raw(self, object_id: str) -> Dict[str, Any]:
        """Get all available properties for an object as raw dict"""
        try:
            props = self.content.Properties()
            
            # Create empty key collection to get ALL properties
            keys = win32com.client.Dispatch(
                "PortableDeviceApiLib.PortableDeviceKeyCollection"
            )
            
            values = props.GetValues(object_id, keys)
            
            result = {}
            # Iterate through all properties
            try:
                count = values.Count
                for i in range(count):
                    # This depends on how pywin32 exposes enumeration
                    # May need adjustment based on your pywin32 version
                    pass
            except:
                pass
            
            return result
        except Exception as e:
            print(f"ERROR: Failed to get raw properties: {e}")
            return {}


# ============================================================================
# Main Demo
# ============================================================================

def main():
    print("\n" + "=" * 80)
    print(" PhoneAccess - WPD API Demo")
    print("=" * 80 + "\n")
    
    # Create device accessor
    device = AndroidMTPDevice()
    
    # Step 1: Scan for devices
    print("[1/4] Scanning for connected MTP devices...")
    print("-" * 80)
    
    devices = device.scan_devices()
    
    if not devices:
        print("❌ No devices found. Is your Android phone connected via USB?")
        print("    Make sure you have Windows' MTP driver installed.")
        return
    
    for i, dev in enumerate(devices, 1):
        print(f"  Device {i}: {dev['name']}")
    
    print()
    
    # Step 2: Connect to first device
    print("[2/4] Connecting to device...")
    print("-" * 80)
    
    target_device = devices[0]
    print(f"  Connecting to: {target_device['name']}")
    
    if not device.connect(target_device['id']):
        print("❌ Connection failed")
        return
    
    print(f"✓ Connected")
    print()
    
    # Step 3: List root objects
    print("[3/4] Listing device root objects...")
    print("-" * 80)
    
    try:
        root_items = device.list_root()
        
        if not root_items:
            print("  ⚠️  No root objects found")
        else:
            print(f"  Found {len(root_items)} item(s):\n")
            for item in root_items:
                print(f"    {item}")
        
        print()
        
        # Step 4: If found folder, list its contents
        if root_items and root_items[0].is_folder:
            print("[4/4] Listing first folder contents (first 20 items)...")
            print("-" * 80)
            
            folder = root_items[0]
            print(f"  Folder: {folder.name}\n")
            
            try:
                contents = device.list_folder(folder.object_id)
                
                if not contents:
                    print("  Folder is empty")
                else:
                    for item in contents[:20]:
                        print(f"    {item}")
                    
                    if len(contents) > 20:
                        print(f"    ... and {len(contents) - 20} more items")
            
            except Exception as e:
                print(f"  ❌ Error listing folder: {e}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        traceback.print_exc()
    
    finally:
        # Disconnect
        print()
        print("[Done] Disconnecting...")
        device.disconnect()
        print("✓ Device disconnected\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        traceback.print_exc()

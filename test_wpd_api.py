#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Windows Portable Devices API (WPD) for raw MTP metadata access
WPD should provide raw properties: size (bytes), modTime (timestamp with seconds)
"""

import sys
import win32com.client

def test_wpd():
    """
    Test WPD API for accessing MTP devices
    WPD is the proper API for portable devices (phones, tablets, cameras)
    """
    
    try:
        # Create WPD PortableDeviceManager
        print("[INFO] Initializing WPD PortableDeviceManager...")
        pdm = win32com.client.Dispatch('PortableDeviceManager.PortableDeviceManager')
        
        print("[OK] PortableDeviceManager created\n")
        
        # Enumerate all portable devices
        print("[SCANNING] Looking for portable devices...")
        devices_count = pdm.GetDeviceCount()
        print(f"[OK] Found {devices_count} device(s)\n")
        
        if devices_count == 0:
            print("[ERROR] No portable devices found")
            return False
        
        # Get device ID
        device_ids = pdm.GetDevices()
        print(f"Device IDs: {device_ids}")
        
        # Try to get device details
        for idx in range(devices_count):
            try:
                device_id = pdm.GetDeviceAtIndex(idx)
                print(f"\n[DEVICE {idx}] ID: {device_id}")
                
                # Get friendly name
                name = pdm.GetDeviceFriendlyName(device_id)
                print(f"  Name: {name}")
                
                # Get manufacturer
                try:
                    manufacturer = pdm.GetDeviceManufacturer(device_id)
                    print(f"  Manufacturer: {manufacturer}")
                except:
                    pass
                
                # Now try to open the device and access its properties
                print(f"\n  [OPENING] Trying to access device properties...")
                
                # Create PortableDevice object
                pd = win32com.client.Dispatch('PortableDevice.PortableDevice')
                pd.Open(device_id, pdm)
                print(f"  [OK] Device opened")
                
                # Get content of device
                content = pd.Content
                print(f"  [OK] Content object obtained")
                
                # Get root folder
                root = content.GetRootFolder()
                print(f"  [OK] Root folder: {root}")
                
                # Try to list items in root
                items = content.ListObjects(1, root, 1000)
                print(f"  [OK] Found items in root")
                
                # Examine properties of items
                if items:
                    for item in items:
                        print(f"\n  Item: {item}")
                        try:
                            # Get properties object
                            props = content.GetProperties(item)
                            print(f"    Properties object obtained")
                            
                            # Try to enumerate properties
                            props_count = props.Count
                            print(f"    Properties count: {props_count}")
                            
                            for prop_idx in range(min(10, props_count)):
                                try:
                                    key = props.GetAt(prop_idx)
                                    value = props.GetValue(key)
                                    print(f"      [{prop_idx}] {key}: {value}")
                                except Exception as e:
                                    print(f"      [{prop_idx}] Error: {e}")
                        except Exception as e:
                            print(f"    Error getting properties: {e}")
                        
                        if items.index(item) >= 1:  # Just first 2 items
                            break
                
                # Close device
                pd.Close()
                print(f"\n  [OK] Device closed")
                
            except Exception as e:
                print(f"[ERROR] Device {idx}: {e}")
                import traceback
                traceback.print_exc()
        
        return True
        
    except Exception as e:
        print(f"[ERROR] WPD test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 80)
    print("WPD API Test - Accessing raw MTP metadata")
    print("=" * 80)
    print()
    
    result = test_wpd()
    
    print("\n" + "=" * 80)
    if result:
        print("Result: ✅ WPD API is available")
    else:
        print("Result: ❌ WPD API test failed")
    print("=" * 80)

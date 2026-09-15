#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test library `mtp` for Android MTP access
Check if it provides exact file sizes (bytes) and modification times (with seconds)
"""

try:
    from mtp import MtpDevice
    print("✓ Successfully imported mtp library")
except ImportError as e:
    print(f"✗ Failed to import mtp: {e}")
    print("Try: pip install mtp")
    exit(1)

print("\nSearching for MTP devices...\n")

try:
    devices = MtpDevice.get_devices()
    print(f"Found {len(devices)} MTP device(s)\n")
    
    if not devices:
        print("No MTP devices found. Is Android connected via USB?")
        exit(1)
    
    for device in devices:
        print(f"Device: {device}")
        
        try:
            device.connect()
            print(f"✓ Connected")
            
            # Get device info
            try:
                print(f"  Device name: {device.device_name if hasattr(device, 'device_name') else 'N/A'}")
                print(f"  Device path: {device.device_path if hasattr(device, 'device_path') else 'N/A'}")
            except:
                pass
            
            # Try to get storages
            try:
                storages = device.get_storages()
                print(f"  Storages: {len(storages)}")
                
                for storage in storages:
                    print(f"\n  Storage: {storage}")
                    
                    # Try to walk storage
                    try:
                        file_count = 0
                        for root, dirs, files in storage.walk('/'):
                            for file in files:
                                if file_count < 3:  # Show first 3 files
                                    print(f"\n    File: {file.get('name', 'N/A')}")
                                    print(f"      Size (bytes): {file.get('size', 'N/A')} [TYPE: {type(file.get('size')).__name__}]")
                                    print(f"      Modified: {file.get('modification_time', 'N/A')} [TYPE: {type(file.get('modification_time')).__name__}]")
                                    file_count += 1
                                if file_count >= 3:
                                    break
                            if file_count >= 3:
                                break
                        
                        if file_count == 0:
                            print("    (no files found in root)")
                        else:
                            print(f"\n  Found and displayed {file_count} files")
                    
                    except Exception as e:
                        print(f"    Error walking storage: {e}")
            
            except Exception as e:
                print(f"  Error getting storages: {e}")
            
            device.disconnect()
            print(f"\n✓ Disconnected\n")
        
        except Exception as e:
            print(f"✗ Connection error: {e}\n")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\nTest complete.")

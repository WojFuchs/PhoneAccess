#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test ExtendedProperty method on FolderItem
This should give us access to raw MTP properties
"""

import win32com.client
import sys

def test_extended_property():
    """
    Test ExtendedProperty method on MTP file object
    """
    
    print("[INFO] Testing ExtendedProperty on MTP file object...\n")
    
    try:
        shell = win32com.client.Dispatch('Shell.Application')
        devices_ns = shell.NameSpace(17)
        
        for device in devices_ns.Items():
            if 'motorola' in device.Name.lower():
                print(f"[OK] Device: {device.Name}\n")
                
                device_ns = shell.NameSpace(device.Path)
                
                for storage in device_ns.Items():
                    print(f"[OK] Storage: {storage.Name}\n")
                    storage_folder = storage.GetFolder
                    
                    for item in storage_folder.Items():
                        if 'Pictures' in item.Name:
                            print(f"[OK] Folder: {item.Name}\n")
                            pics_folder = item.GetFolder
                            
                            for file_item in pics_folder.Items():
                                if not file_item.IsFolder:
                                    print(f"[FILE] {file_item.Name}\n")
                                    
                                    # Try ExtendedProperty method
                                    print("[TESTING] ExtendedProperty...\n")
                                    
                                    try:
                                        # ExtendedProperty takes property name as string
                                        # Known property names for files:
                                        property_names = [
                                            "System.ItemType",
                                            "System.ItemTypeText",
                                            "System.Size",
                                            "System.FileSize",
                                            "System.DateModified",
                                            "System.DateCreated",
                                            "System.DateAccessed",
                                            "System.ItemModificationDate",
                                            "System.ItemDate",
                                            "System.Image.HorizontalSize",
                                            "System.Image.VerticalSize",
                                            "System.Photo.DateTaken",
                                            "System.Photo.CameraManufacturer",
                                            "System.DRM.IsProtected",
                                            "System.Music.Artist",
                                            "System.Music.AlbumTitle",
                                            "System.Music.TrackNumber",
                                        ]
                                        
                                        for prop_name in property_names:
                                            try:
                                                value = file_item.ExtendedProperty(prop_name)
                                                if value is not None and value != "":
                                                    print(f"  {prop_name}: {value}")
                                            except Exception as e:
                                                # Silent - try next property
                                                pass
                                        
                                        print()
                                        
                                    except Exception as e:
                                        print(f"[ERROR] ExtendedProperty failed: {e}\n")
                                    
                                    # Try other methods
                                    print("[TESTING] Other methods...\n")
                                    
                                    try:
                                        # Try InvokeVerb
                                        verbs = file_item.Verbs()
                                        print(f"  Available verbs: {verbs.Count}")
                                        for i in range(verbs.Count):
                                            verb = verbs.Item(i)
                                            print(f"    - {verb.Name}")
                                    except Exception as e:
                                        print(f"  Verbs error: {e}")
                                    
                                    print()
                                    
                                    return True
                            
                            return True
                    
                    return True
        
        print("[ERROR] No device found")
        return False
        
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 80)
    print("FolderItem.ExtendedProperty Test")
    print("=" * 80)
    print()
    
    result = test_extended_property()
    
    print("\n" + "=" * 80)
    if result:
        print("Result: ✅ ExtendedProperty test completed")
    else:
        print("Result: ❌ Test failed")
    print("=" * 80)

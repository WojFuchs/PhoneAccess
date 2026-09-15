
using System;
using System.Collections.Generic;
using Windows.Storage;
using Windows.Devices.Portable;
using System.IO;

class Program {
    static async System.Threading.Tasks.Task Main() {
        try {
            Console.WriteLine("[INFO] Initializing StorageDevice...");
            
            // Get all portable devices (including Android phones)
            var devices = await StorageDevice.GetAllAsync();
            Console.WriteLine($"[OK] Found {devices.Count} device(s)");
            
            if (devices.Count == 0) {
                Console.WriteLine("[ERROR] No devices found");
                return;
            }
            
            foreach (var device in devices) {
                try {
                    Console.WriteLine($"\n[DEVICE] {device.Name}");
                    
                    // Try to get root folder
                    var root = device.RootFolder;
                    Console.WriteLine($"[OK] Root folder obtained");
                    
                    // List folders
                    var items = await root.GetItemsAsync();
                    Console.WriteLine($"[OK] Found {items.Count} items in root");
                    
                    foreach (var item in items) {
                        try {
                            Console.WriteLine($"\n  [{item.DisplayName}]");
                            
                            if (item.IsOfType(StorageItemTypes.Folder)) {
                                var folder = item as StorageFolder;
                                var subitems = await folder.GetItemsAsync();
                                Console.WriteLine($"    Items: {subitems.Count}");
                                
                                // Get first file
                                foreach (var subitem in subitems) {
                                    if (subitem.IsOfType(StorageItemTypes.File)) {
                                        var file = subitem as StorageFile;
                                        var props = await file.GetBasicPropertiesAsync();
                                        
                                        Console.WriteLine($"\n    [FILE] {file.Name}");
                                        Console.WriteLine($"      Size: {props.Size} bytes");
                                        Console.WriteLine($"      Modified: {props.DateModified:yyyy-MM-dd HH:mm:ss.fff}");
                                        
                                        break;  // Just first file
                                    }
                                }
                                break;  // Just first folder
                            }
                        } catch (Exception ex) {
                            Console.WriteLine($"    [ERROR] {ex.Message}");
                        }
                    }
                    break;  // Just first device
                } catch (Exception ex) {
                    Console.WriteLine($"[ERROR] Device error: {ex.Message}");
                }
            }
            
        } catch (Exception ex) {
            Console.WriteLine($"[ERROR] WinRT test failed: {ex.Message}");
            Console.WriteLine($"[INFO] Stack trace: {ex.StackTrace}");
        }
    }
}

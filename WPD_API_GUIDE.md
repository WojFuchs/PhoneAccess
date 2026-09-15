# Windows Portable Device (WPD) API Guide for Python pywin32

## Overview

The WPD API is the native Windows interface for MTP devices. Unlike the Shell API, it provides:
- ✅ Raw file properties (exact byte sizes, full datetime with seconds)
- ✅ Direct access to Properties Store
- ✅ No Debug Mode requirement
- ✅ No drive letter mapping needed
- ✅ Full control over COM object lifecycle

## Key COM Objects/Interfaces

### 1. **IPortableDeviceManager** (Starting Point)
```
ProgID: PortableDeviceApiLib.PortableDeviceManager
Purpose: Enumerate all connected WPD devices
Key Methods:
  - GetDevices(pDeviceIDs) -> returns device IDs
  - GetDeviceFriendlyName(deviceID) -> human-readable name
  - GetDeviceDescription(deviceID) -> device description
```

### 2. **IPortableDevice** (Main Device Interface)
```
ProgID: PortableDeviceApiLib.PortableDevice
Purpose: Connect to and communicate with a specific device
Key Methods:
  - Open(deviceID, clientInfo) -> establish connection
  - Content -> returns IPortableDeviceContent interface
  - Close() -> disconnect
```

### 3. **IPortableDeviceContent** (Content Access)
```
Accessed via: IPortableDevice.Content
Purpose: Navigate and access device objects
Key Methods:
  - EnumObjects(parentID, filter) -> returns IEnumPortableDeviceObjects
  - Properties -> returns IPortableDeviceProperties
  - GetObjectIDsFromPaths(paths) -> resolve paths to IDs
```

### 4. **IEnumPortableDeviceObjects** (Object Enumeration)
```
Purpose: Iterate through device objects
Key Methods:
  - Next(celt, objectIDs) -> fetch next batch of object IDs
  - Reset() -> start from beginning
  - Clone() -> create independent iterator
```

### 5. **IPortableDeviceProperties** (Metadata)
```
Accessed via: IPortableDeviceContent.Properties
Purpose: Retrieve file properties (size, modification time, etc)
Key Methods:
  - GetValues(objectID, keys) -> get properties for object
  - Returns IPortableDeviceValues collection
```

### 6. **IPortableDeviceValues** (Property Store)
```
Purpose: Key-value store for object properties
Key Methods:
  - GetIntegerValue(key) -> get integer property (e.g., file size)
  - GetStringValue(key) -> get string property (e.g., filename)
  - GetDateTimeValue(key) -> get datetime (returns OLE Automation date)
  - Count -> total properties
```

## Property Keys (WPD_OBJECT_*)

Critical properties for file operations:

```python
# Object Identity
WPD_OBJECT_ID = "Object.ID"
WPD_OBJECT_PARENT_ID = "Object.ParentID"
WPD_OBJECT_NAME = "Object.Name"
WPD_OBJECT_ORIGINAL_FILE_NAME = "Object.OriginalFileName"

# Type Information
WPD_OBJECT_CONTENT_TYPE = "Object.ContentType"
WPD_OBJECT_FORMAT = "Object.Format"

# File Properties (CRITICAL)
WPD_OBJECT_SIZE = "Object.Size"  # Exact size in bytes
WPD_OBJECT_DATE_MODIFIED = "Object.DateModified"  # OLE Automation date with seconds

# Container/Folder
WPD_OBJECT_IS_HIDDEN = "Object.IsHidden"
WPD_OBJECT_IS_SYSTEM = "Object.IsSystemObject"

# Container Content
WPD_OBJECT_CHILD_COUNT = "Object.ContainerChildCount"
```

## Gotchas & Special Handling

### 1. **OLE Automation DateTime Conversion**
```
- WPD returns dates as OLE Automation datetime floats
- Need to convert to Python datetime:
  
  import datetime
  ole_date = property_value  # float from GetDateTimeValue()
  # OLE date 0 = 1899-12-30
  delta = datetime.timedelta(days=ole_date)
  ole_epoch = datetime.datetime(1899, 12, 30)
  python_datetime = ole_epoch + delta
```

### 2. **VARIANT Type Mismatch**
```
- GetDateTimeValue() may return VARIANT of type VT_DATE
- Always use type-specific getters (GetIntegerValue, GetStringValue)
- Don't assume generic GetValue() works
```

### 3. **Root vs Storage Objects**
```
- Root device ID = "DEVICE"
- Storage objects (like "Internal Storage") are child objects
- Must enumerate from DEVICE first
- Then enumerate storage contents (folders/files)
```

### 4. **Folder Enumeration**
```
- Folders are "containers" with WPD_OBJECT_CHILD_COUNT property
- Must check object type before recursing
- Empty folders have ChildCount = 0 but still enumerate as container
- Use filter to get only desired object types
```

### 5. **No Cached Enumeration**
```
- IEnumPortableDeviceObjects enumerator is live
- Device may disconnect mid-enumeration
- Always wrap in try/except for robust code
```

### 6. **String Encoding**
```
- Use utf-8 for paths/names
- Device names from different vendors may have unusual characters
```

## Implementation Checklist

- [ ] Create PortableDeviceManager
- [ ] Call GetDevices() to enumerate
- [ ] Create PortableDevice for target device
- [ ] Call Open() with ClientInfo
- [ ] Access Content property
- [ ] Call Properties to get IPortableDeviceProperties
- [ ] Enumerate objects recursively with EnumObjects()
- [ ] Use GetValues() to fetch properties
- [ ] Convert OLE dates to Python datetime
- [ ] Close device connection
- [ ] Properly release COM objects

## Performance Tips

1. **Batch Property Fetching**: Get multiple properties at once with GetValues()
2. **Use Filters**: Narrow enumeration with object type filters
3. **Limit Recursion Depth**: Large folders slow down enumeration
4. **Cache Device ID**: Don't re-enumerate constantly
5. **Async Operations**: Long operations may timeout - consider async patterns

## Existing Python Implementations

### 1. **Heribert17/mtp** (⭐ RECOMMENDED)
- GitHub: https://github.com/Heribert17/mtp
- Status: ✅ Active (Python 3.9+)
- Features:
  - Pure pywin32 WPD API wrapper
  - Handles OLE datetime conversion
  - File download/upload
  - Full property access
  - **Gotcha**: Requires Python 3.9+, not 3.8

### 2. **python-portable-device-api**
- Status: Maintained but less complete
- Good for basic enumeration
- Limited property handling

### 3. **libmtp** (Windows Port)
- Requires compilation
- Heavy dependency
- Not recommended for pure Python solution

## Why Not Use Shell API?

Shell.Application limitations:
- ❌ Date returns only HH:MM (no seconds)
- ❌ File sizes as formatted strings (KB, MB)
- ❌ No raw property access
- ❌ Copying via CopyHere() doesn't work with MTP namespace
- ❌ Path operations fail with special characters

**Conclusion**: Use WPD API for your requirements.

# Notatki z testów

## Test 1: PyMTP library
- **Wynik**: ❌ BŁĄD
- **Komenda**: `python -c "import pymtp"`
- **Błąd**: `TypeError: argument of type 'NoneType' is not iterable` 
- **Przyczyna**: Brak libmtp.dll na Windows

---

## Test 2: USB Devices via PowerShell
- **Wynik**: ✅ OK
- **Komenda**: `Get-PnpDevice -Class USB`
- **Znaleziono**: `USB\VID_22B8&PID_2E76` (ThinkPhone by motorola)
- **Wnioski**: Urządzenie jest widoczne w systemie

---

## Test 3: COM Shell.Application - NameSpace 0x14 (CSIDL_PORTABLEDISKDEVICES)
- **Wynik**: ❌ BŁĄD
- **Komenda**: `shell.NameSpace(0x14)`
- **Błąd**: `Exception occurred: (-2147352567, ...)`
- **Wnioski**: Namespace 0x14 nie działa dla MTP devices

---

## Test 4: COM Shell.Application - NameSpace 17 (This PC devices)
- **Wynik**: ✅ SUKCES!
- **Komenda**: `shell.NameSpace(17)`
- **Znaleziono**: "ThinkPhone by motorola" + inne urządzenia
- **Typ**: Mobile Phone (Type)
- **Wnioski**: Prawidłowa metoda dostępu do MTP devices

---

## Test 5: Dostęp do storage namespace
- **Wynik**: ❌ BŁĄD
- **Próba**: `shell.NameSpace(storage_item.Path)`
- **Błąd**: `'NoneType' object has no attribute 'Items'`
- **Wnioski**: Bezpośrednie konwersji ścieżki MTP na namespace nie działa

---

## Test 6: GetFolder() method
- **Wynik**: ✅ SUKCES!
- **Metoda**: `storage_item.GetFolder`
- **Zwraca**: Folder COM object z dostępem do Items()
- **Znaleziono**: Pictures folder w rocie
- **Wnioski**: To jest prawidłowy sposób dostępu do plików!

---

## Test 7: Monta Azure dyski
- **Komenda**: `ls F:\`
- **Wynik**: Pokazuje zawartość dysku F: (nie Android - to backup)
- **Wnioski**: Android NIE jest zmontowany jako dysk, dostęp TYLKO przez MTP/COM

---

## Najważniejsze odkrycie
```python
shell = win32com.client.Dispatch('Shell.Application')
device_ns = shell.NameSpace(device.Path)  # NameSpace 17 dla device

for storage_item in device_ns.Items():
    folder = storage_item.GetFolder  # <-- Klucz!
    for file_item in folder.Items():
        print(f"{file_item.Name} - {file_item.Size} - {file_item.ModifyDate}")
```

Metoda GetFolder() zwraca Folder object który ma:
- `.Items()` - lista plików/folderów
- `.Size` - rozmiar pliku (NE DZIAŁA - zawsze 0)
- `.ModifyDate` - data modyfikacji (NE DZIAŁA - zwraca 1899-12-30)

---

## Test 8: List files from Pictures (v2)
- **Wynik**: ✅ CZĘŚCIOWY SUKCES!
- **Komenda**: `python phone_access_v2.py Pictures 2`
- **Znaleziono**: 240 plików w Pictures folder
- **Problem 1**: Size pokazuje 0.0 B (brak dostępu do właściwości MTP)
- **Problem 2**: ModifyDate pokazuje 1899-12-30 (błędna wartość)
- **Następny krok**: Użyć GetDetailsOf() do pobrania metadanych z shell namespace

---

## Metoda GetDetailsOf()
- Dostępna na FolderItem object
- Syntax: `item.GetDetailsOf(shell_folder_item, column_index)`
- Kolumny: 0=Nazwa, 4=Rozmiar, 3=Data modyfikacji (zależy od systemu)
- Będzie potrzebna experimentacja z indeksami kolumn

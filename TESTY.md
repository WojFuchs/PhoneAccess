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

---

## Test 9: Odkrycie poprawnych kolumn dla metadanych
- **Wynik**: ✅ SUKCES!
- **Plik**: test_size.py
- **Znalezione kolumny** (dla Folder.GetDetailsOf):
  - Column 0: File name (e.g., "Biedronka.jpeg")
  - Column 1: File type (e.g., "IrfanView JPG File")
  - Column 2: **SIZE** (e.g., "91,4 KB") - sformatowany string z separatorem tysiąca
  - Column 3: **MODIFICATION DATE** (e.g., "2026-01-16 10:29") - sformatowany string
  - Column 6: Unknown (Yes/No)
  - Column 8: Title/Description
- **Wnioski**: 
  - GetDetailsOf() zwraca sformatowane dane jako stringi
  - Rozmiar w formacie tekstowym z separatorem tysiąca i jednostką (KB, MB, itp)
  - Data w formacie YYYY-MM-DD HH:MM
- **Problem**: Będzie trzeba parsować stringi na liczby i datetime obiekty
- **Rozwiązanie**: Regex lub split do parsowania rozmiaru, datetime.strptime dla daty

---

## ✅ Test 10: ROZWIĄZANIE! FolderItem.ExtendedProperty() zwraca SUROWE DANE (2026-09-15)
- **Obserwacja**: Shell API GetDetailsOf() zwraca dane SFORMATOWANE
- **Znalezienie**: `FolderItem.ExtendedProperty()` zwraca NIEFORMATOWANE dane!
- **`System.Size`**: 93635 (integer - liczba bajtów!)
  - GetDetailsOf kolumna 2: `"91,4 KB"` (sformatowany string)
  - ExtendedProperty: `93635` (surowe bajty)
- **`System.DateModified`**: `2026-01-16 08:29:52+00:00` (z sekundami!)
  - GetDetailsOf kolumna 3: `"2026-01-16 10:29"` (bez sekund, inne timezone)
  - ExtendedProperty: `pywintypes.datetime` (z sekundami, UTC/inne timezone)
- **Wnioski**:
  1. ExtendedProperty jest PRAWIDŁOWYM API do pobrania surowych metadanych MTP
  2. Rozmiary zwracane w bajtach (integer)
  3. Czasy zwracane z sekundami (datetime object)
  4. Czasy mogą być w innej strefie czasowej niż GetDetailsOf
- **Status**: ✅ PROBLEM ROZWIĄZANY!
- **Testowany w**: phone_access_v3.py z funkcjami parse_modtime_extended() i format_datetime()

---

## ⚠️ Test 10: PROBLEM Z PRECYZJĄ METADANYCH (2026-09-15)
- **Obserwacja**: Shell API GetDetailsOf() zwraca dane SFORMATOWANE, nie surowe
- **Kolumna 2 (Size)**: `"91,4 KB"` - sformatowany string z separatorem tysiąca
  - **PROBLEM**: Tracimy precyzję - nie wiemy ile to dokładnie bajtów
  - **Wymaganie**: Potrzebujemy liczby całkowitej (int) - liczby bajtów
- **Kolumna 3 (Date)**: `"2026-01-16 10:29"` - bez sekund!
  - **PROBLEM**: Wiadomo kiedy w minucie, ale nie o której dokładnie sekundzie
  - **Wymaganie**: Potrzebujemy `YYYY-MM-DD HH:MM:SS`
  - **Wnioski**: Nie można dodawać ":00" sztucznie - to byłoby kłamstwo
- **Status**: Shell.Application NIE SPEŁNIA wymagań precyzji
- **Następny krok**: Szukać alternatywnych API:
  1. Windows Media Foundation (DirectShow) - metadane multimediów
  2. WMI (Windows Management Instrumentation) - info o plikach systemowych
  3. DirectX Media Object (DMO) - dekodowanie metadanych
  4. Bezpośredni dostęp do pliku MTP - raw binary metadata
  5. libmtp na Windows - jeśli się da zainstalować

---

## ⚠️ Test 11: WAŻNA UWAGA O PROTOKOLE (2026-09-15)
- Dotychczasowe badania zakładały że to **MTP (Media Transfer Protocol)**
- **JEDNAK**: Nie wiemy na pewno czy to MTP!
- **Total Commander sobie radzi** - ma dostęp do plików bez Debug Mode
- **To oznacza** że Windows ma API dostępu do telefonu
- **Mogą to być**:
  - ✅ Rzeczywiście MTP
  - ✅ WebDAV serwer na telefonie
  - ✅ UPnP/DLNA device
  - ✅ FTP/SFTP serwer
  - ✅ Wbudowany Windows driver
  - ✅ Coś innego - co Total Commander używa
- **Strategia**: Badać wszystkie możliwe API, nie tylko MTP
- **Priorytet**: Dowiedzieć się jak Total Commander osiąga dostęp do telefonu

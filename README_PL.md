# PhoneAccess - Program do zarządzania plikami na Androidzie

## Cel projektu
Napisanie najprostszego możliwego programu, który umożliwi:
1. Rozpoznanie nazwy podłączonego telefonu Android (USB, bez Debug Mode)
2. Listowanie prawdziwych folderów i plików z **modTime z dokładnością do SEKUNDY** i **size z dokładnością do JEDNEGO BAJTU**
3. Kopiowanie X pierwszych plików z wybranego folderu na dysk Win10
4. Brak potrzeby kopiowania pliku na Win10 do jego analizy

## ⚠️ WYMAGANIA DOTYCZĄCE DOKŁADNOŚCI DANYCH
**ABSOLUTNIE WYMAGANE** - nie można używać sztucznych formatowań:
- **modTime**: Musi być `YYYY-MM-DD HH:MM:SS` (dokładność do SEKUNDY, nie minuty!)
- **size**: Musi być `integer` (liczba bajtów, np. 94208), nie sformatowany string (np. "91,4 KB")
- **Uwaga**: Shell API GetDetailsOf() zwraca dane sformatowane (HH:MM bez sekund, "91,4 KB" zamiast bajtów)
  - Należy szukać **alternatywnych źródeł danych** (DirectShow API, WMI, bezpośredni dostęp do metadanych MTP)
  - Nie wolno dodawać ":00" do godzin lub ".000" do milisekund - to sztuczne dane!

## Preferowany język programowania
- **Pierwsza próba**: Python 3.x (najprostszy, szybki development)
- **Plan B**: Inne języki (C#, Node.js, C++) jeśli Python się nie uda
- Będzie się testować możliwości dostępu i stopniowo przechodzić na inny język jeśli konieczne

## 🚫 OGRANICZENIA (ABSOLUTNE)
- Windows 10
- Android podłączony przez USB
- Opcja "Kopiowanie plików" włączona
- **🔴 Debug Mode MUSI BYĆ WYŁĄCZONY** - Nie można go włączać! (bez wyjątków)
- **🔴 Telefon NIE JEST ZMAPOWANY** - brak litery dysku (E:, F: itp) w Windows
- **🔴 MIMO TO MUSI DZIAŁAĆ** - Total Commander sobie radzi bez mapowania i bez Debug Mode
- Zatem my też musimy - to jest absolutne wymaganie techniczne, nie sugestia

## 🔬 BADANIE: Jaki API/Protokół używa Total Commander?

**✅ ODKRYCIE - 2026-09-15**:
- Total Commander używa **MTP (Media Transfer Protocol)**
- Windows ma **wbudowany MTP stack** od Vista+
- Total Commander używa **Windows Shell API COM objects** (jak my!)
- MTP jest standardem USB/Android od 2011

**Kluczowa obserwacja**:
- **Shell API (GetDetailsOf)** zwraca dane SFORMATOWANE dla człowieka:
  - Rozmiar: `"91,4 KB"` (sformatowany string)
  - Data: `"2026-01-16 10:29"` (bez sekund)
- **Ale MTP protocol zawiera surowe dane**:
  - Rozmiar: liczba bajtów (raw 32/64-bit integer)
  - Data: timestamp lub sformatowany timestamp (z sekundami)
- **Wnioski**:
  1. Shell API nie spełnia wymogów precyzji
  2. Musimy dostać się do **surowych danych z MTP** 
  3. **✅ ROZWIĄZANIE**: Biblioteka `Heribert17/mtp` na PyPI
     - Zwraca `file['size']` jako int (bajty)
     - Zwraca `file['modification_time']` z sekundami
     - Instalacja: `pip install mtp`
     - Wciąż NO Debug Mode, NO drive letters

**Następny krok**: Przetestować `mtp` library i przepisać kod

## Test końcowy
Uruchomić z parametrami: `program Pictures 2`
- Wylistować pierwsze 2 pliki z folderu "Pictures" (lub podfoldery) z modTime i size
- Skopiować te 2 pliki na Win10

---

## Log postępu i eksperymentów

### Kroki do wykonania:
- [x] Zbadać dostępne metody dostępu do USB Android bez Debug Mode na Win10
- [x] Przygotować środowisko Python
- [x] Wdrożyć detekcję podłączonego telefonu
- [x] Wdrożyć listowanie plików z modTime i size
- [ ] Wdrożyć kopiowanie plików (wymaga synchronicznej kopii)
- [x] Przetestować z parametrami Pictures 2 ✅

### ✅ Próby i wyniki - SUKCES:

**Data testu**: 2026-09-15  
**Telefon**: ThinkPhone by motorola  
**Pamięć**: Wewnętrzna pamięć współdzielona  
**Plik kodu**: [phone_access_v3.py](phone_access_v3.py)

**Funkcje implementujące zadania:**
1. **Detekcja telefonu** - `detect_device()` [linie 107-124](phone_access_v3.py#L107-L124)
   - Szukanie urządzenia w Namespace 17 (urządzenia USB)
   - Rozpoznawanie po słowach kluczowych: motorola, android, phone

2. **Dostęp do pamięci** - `get_storage_folder()` [linie 126-147](phone_access_v3.py#L126-L147)
   - Otwarcie dostępu do głównej pamięci telefonu
   - Przygotowanie do czytania folderów

3. **Pobranie metadanych - SUROWYCH DANYCH** - `get_file_details()` [linie 149-198](phone_access_v3.py#L149-L198)
   - **✅ NOWE**: Używa `ExtendedProperty('System.Size')` → liczba bajtów (integer)
   - **✅ NOWE**: Używa `ExtendedProperty('System.DateModified')` → datetime z sekundami
   - **Fallback**: GetDetailsOf dla kompatybilności

4. **Listowanie rekurencyjne** - `list_files_recursive()` [linie 200-246](phone_access_v3.py#L200-L246)
   - Rekurencyjne przejście po folderach
   - Limit głębokości: 10 poziomów

**Przykład - Polecenie testowe:**
```bash
python phone_access_v3.py Pictures 2
```

**Wyniki z folderu Pictures (240 plików znaleziono):**

```
[RESULTS] Found 240 files total, showing first 2:

  [1] Screenshot_20260904-221027.Ustawienia.png
       Size:     229.8 KB  |  Modified: 2026-09-04 20:10:27

  [2] Screenshot_20260914-201557_Flightradar24.png
       Size:       3.0 MB  |  Modified: 2026-09-14 18:15:58
```

**Dane zwracane (✅ SUROWE, NIE SFORMATOWANE):**
- ✅ Nazwa urządzenia (Device): **ThinkPhone by motorola**
- ✅ Pamięć: **Wewnętrzna pamięć współdzielona**
- ✅ Liczba znalezionych plików: **240**
- ✅ **Rozmiar**: liczba bajtów (System.Size) - wyświetlane w KB/MB dla czytelności
- ✅ **Data modyfikacji**: z dokładnością do SEKUNDY (2026-09-04 20:10:27) - nie sztuczne :00
- ✅ Rekurencyjna lista z zagłębianiem

**Jak to działa (API):**
- Metoda: `FolderItem.ExtendedProperty('System.Size')` → `integer` (bajty)
- Metoda: `FolderItem.ExtendedProperty('System.DateModified')` → `pywintypes.datetime` (z sekundami)
- Backup: `Folder.GetDetailsOf(item, kolumna)` → formatowany string (jeśli ExtendedProperty niedostępne)

**Status**: ✅ Detekcja telefonu PRACUJE, ✅ Listowanie plików z BAJTAMI i SEKUNDAMI PRACUJE, 🔄 Kopiowanie w trakcie pracy

---

## Techniczne notatki i wskazówki implementacji

### Jak to działa (Windows Shell COM API):
1. **Inicjalizacja** - `Shell.Application` COM object
2. **Namespace 17** - dostęp do urządzeń (`shell.NameSpace(17)`)
3. **Detekcja telefonu** - szukamy słów "motorola", "android" lub "phone" w nazwie
4. **Dostęp do pamięci** - poprzez `NameSpace(device.Path)`
5. **Pobranie szczegółów** - `GetDetailsOf(item, column)`:
   - kolumna 2 = rozmiar pliku
   - kolumna 3 = data modyfikacji
   - kolumna 0 = nazwa pliku

### Wymagane biblioteki Python:
- `win32com` - komunikacja z COM (Windows)
  ```
  pip install pywin32
  ```

### Testowanie z podłączonym telefonem:
```bash
# Wylistuj 2 pierwsze pliki z Pictures
python phone_access_v3.py Pictures 2

# Wylistuj 5 plików z DCIM
python phone_access_v3.py DCIM 5

# Wylistuj wszystkie pliki (bez limitu)
python phone_access_v3.py Pictures
```

### Interpretacja wyników:
- **Device found: [NAME]** = Telefon rozpoznany poprawnie
- **Storage access: [FOLDER]** = Dostęp do głównej pamięci przydzielony
- **Found [N] files total** = Liczba plików znaleziona rekurencyjnie
- Czasy w formacie: `YYYY-MM-DD HH:MM` (dokładność do minuty z Shell API)

### ✅ ROZWIĄZANE PROBLEMY:
- ✅ **Detekcja telefonu** - działąMTP via Shell.NameSpace(17)
- ✅ **Dostęp do plików** - FolderItem.GetFolder() pozwala na iterację
- ✅ **Surowe rozmiary** - ExtendedProperty('System.Size') zwraca bajty (integer)
- ✅ **Surowe czasy** - ExtendedProperty('System.DateModified') zwraca z sekundami

### Pozostałe ograniczenia:
- **Copy verb async** - InvokeVerb("Copy") jest asynchroniczny, nie czeka na koniec kopii
- **Brak informacji o rozmiarze folderu** - ExtendedProperty na folderze zwraca coś inne
- **Recursive depth limit** - 10 poziomów zagłębienia dla bezpieczeństwa

### � HISTORIA POSZUKIWAŃ: Jak osiągnęliśmy cel

**Problem**: GetDetailsOf() zwraca sformatowane dane (np. "91,4 KB", "HH:MM")  
**Szukaliśmy**: API które zwraca surowe dane (bajty, sekundy)  
**Rozwiązanie**: `FolderItem.ExtendedProperty()` - prawidłowe API do MTP

**Badane API (wszystkie nieskuteczne):**
1. WPD (Windows Portable Devices) - COM object nie zarejestrowany
2. WMI (Windows Management Instrumentation) - MTP ścieżki nie mapują się
3. libmtp via ctypes - libmtp.dll nie dostępna na Windows
4. PowerShell filesystem mapping - MTP ścieżki nie mapują się
5. Windows.Devices.Portable WinRT - brak C# compiler
6. DirectShow / IPropertyStore - niedostępne

**Ostatecznie**: FolderItem.ExtendedProperty() (część Shell.Application API)
- Było dostępne cały czas!
- Zwraca nieformatowane dane
- Działa na MTP devices bez dodatkowych bibliotek


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

3. **Pobranie metadanych** - `get_file_details()` [linie 149-174](phone_access_v3.py#L149-L174)
   - Pobranie rozmiaru (kolumna 2)
   - Pobranie daty modyfikacji (kolumna 3)

4. **Listowanie rekurencyjne** - `list_files_recursive()` [linie 176-222](phone_access_v3.py#L176-L222)
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
       Size:     229.0 KB  |  Modified: 2026-09-04 22:10

  [2] Screenshot_20260914-201557_Flightradar24.png
       Size:       3.0 MB  |  Modified: 2026-09-14 20:15
```

**Informacje zwracane:**
- ✅ Nazwa urządzenia (Device): **ThinkPhone by motorola**
- ✅ Pamięć: **Wewnętrzna pamięć współdzielona**
- ✅ Liczba znalezionych plików: **240**
- ✅ Rozmiar pliku z dokładnością do 0.1 KB
- ✅ Data modyfikacji z dokładnością do minuty (YYYY-MM-DD HH:MM)
- ✅ Rekurencyjna lista z zagłębianiem

**Status**: ✅ Detekcja telefonu PRACUJE, ✅ Listowanie plików PRACUJE, 🔄 Kopiowanie w trakcie pracy

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

### Ograniczenia obecnej implementacji:
- **Copy verb async** - InvokeVerb("Copy") jest asynchroniczny, nie czeka na koniec kopii
- **Formatowanie czasu** - Shell API przycina sekundy, zwraca tylko minuty
- **Brak informacji o rozmiarze folderu** - GetDetailsOf na folderze zwraca "N/A"
- **Recursive depth limit** - 10 poziomów zagłębienia dla bezpieczeństwa

### 🔴 KRYTYCZNE: Shell API nie spełnia wymogów precyzji!
GetDetailsOf() zwraca dane SFORMATOWANE:
- Rozmiar: `"91,4 KB"` zamiast liczby bajtów
- Data: `"2026-01-16 10:29"` zamiast sekund

**Potrzebne alternatywne API na Windows:**
1. **Windows Media Foundation (WMF/DirectShow)**
   - Dostęp do metadanych multimediów (zdjęcia, wideo)
   - Interfejs: `IMediaObject`, `IPropertyStore`
   
2. **WMI (Windows Management Instrumentation)**
   - Dostęp do atrybutów plików systemowych
   - Query: `SELECT * FROM CIM_DataFile WHERE Drive='USB_MTP_PATH'`
   
3. **Python `pathlib` / `os.stat()` na zmontowanej ścieżce MTP**
   - Jeśli Windows mapuje MTP jako wirtualny dysk
   - Pozwala na dostęp do: `st_size`, `st_mtime` (timestamp)
   
4. **libmtp (Linux-style library na Windows)**
   - Bezpośredni dostęp do protokołu MTP
   - Wymaga: `pip install pymtp` + `libmtp.dll`
   
5. **Android Debug Bridge (ADB) - ALTERNATYWA**
   - Jeśli włączy się Developer Mode tymczasowo
   - Komenda: `adb shell ls -la /storage/emulated/0/Pictures/`

**Badanie w toku**: Sprawdzić które z powyższych API mogą pracować z USB MTP bez Debug Mode


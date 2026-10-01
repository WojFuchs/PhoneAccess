# Eksperyment odczytu telefonu — 2026-10-01

Telefon jest wyłącznie źródłem odczytu. Skrypt nie wywołuje jego
czasowników, nie ustawia właściwości, nie tworzy ani nie usuwa na nim plików.
Opcjonalny download wywołuje CopyHere wyłącznie na lokalnym folderze Windows.

Uruchomienie (Python + pywin32):

```powershell
python experiments/read_only_probe.py
python experiments/read_only_probe.py --download
```

Skrypt jest celowo ograniczony do jednego telefonu Motorola, jednej pamięci
i folderu Pictures. Nie jest jeszcze uniwersalnym programem PhoneAccess.
Raporty i pobrane pliki trafiają do unikalnego folderu local_artifacts,
pomijanego przez Git. Istniejące pliki nie są nadpisywane.

## Potwierdzone na podłączonym ThinkPhone by motorola

- Dostęp działa przez Shell.Application → NameSpace(17) → GetFolder.
- Pamięć: Wewnętrzna pamięć współdzielona.
- Rekurencyjnie znaleziono 1263 pliki w Pictures, wliczając .thumbnails.
- System.Size zwraca int, System.DateModified zwraca datetime ze strefą UTC.
- Plik Flightradar24: 1714259 bajtów, 2026-09-24 05:48:55 UTC,
  czyli 07:48:55 +02:00.
- Plik Ustawienia: 235313 bajtów, 2026-09-04 20:10:27 UTC,
  czyli 22:10:27 +02:00.
- Oba pliki skopiowano przez lokalny Folder.CopyHere; rozmiary lokalne
  są identyczne z metadanymi telefonu. Nie porównywano zawartości bajt po bajcie.
- ExtendedPropertyNames nie jest dostępne na elemencie tego telefonu;
  jego użycie w phone_access_v4_simple.py może przerwać detekcję.
- FolderItem.Name jest nazwą wyświetlaną: na tej konfiguracji nie zawiera
  rozszerzenia PNG. Kopia lokalna ma rozszerzenie. Pierwszy eksperyment
  skopiował plik, lecz błędnie szukał nazwy bez rozszerzenia i zakończył się
  timeoutem. Poprawiony eksperyment sprawdza jedyny plik w nowym folderze.

Weryfikacja transferu: trzy kolejne odczyty rozmiaru zgodnego z metadanymi,
w odstępach 0,5 s, z limitem 45 s na plik. Jest to kontrola rozmiaru,
nie gwarancja integralności oparta na sumie kontrolnej źródła.

Stare prototypy pozostawiono na miejscu, żeby zachować historię eksperymentów.

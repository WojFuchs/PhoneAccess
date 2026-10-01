# Skanowanie telefonu do TXT

```powershell
python scan_phone.py
python scan_phone.py --device ThinkPhone --output local_artifacts/moj_spis.txt
```

Wymagania: Windows, Python, pywin32 i telefon udostępniający pliki przez USB/MTP.
Telefon jest wyłącznie odczytywany. Program zapisuje metadane lokalnie,
nie kopiuje zawartości plików ani nie zmienia telefonu.

Zakres: wszystkie pliki we wszystkich pamięciach udostępnionych przez MTP,
w tym pliki ukryte. Prywatne dane aplikacji niewidoczne przez MTP nie są dostępne.
Skanowanie nie jest atomową migawką: telefon może sam zmieniać pliki podczas skanu.

Raport UTF-8 ma kolumny oddzielone tabulatorami: path, size_bytes, modTime, status.
Rozmiar jest dokładną liczbą bajtów z System.Size, a czas pochodzi z
System.DateModified, z sekundami i strefą źródłową (na testowanym telefonie UTC).
System.FileName dostarcza nazwę z rozszerzeniem; gdy nie jest dostępne,
zachowywana jest nazwa wyświetlana przez Shell.
Brakujące metadane pozostają puste i są oznaczane błędem, bez wartości zastępczych.

Po każdych 100 plikach i dla ostatniej niepełnej paczki program zapisuje do
konsoli oraz raportu timestamp, liczbę plików, sumę ich rozmiarów, czas paczki,
B/s i file/s. B/s to suma rozmiarów opisanych plików / czas skanowania paczki,
a nie prędkość transferu zawartości. Czas obejmuje nawigację między paczkami.
Pliki z niepełnymi metadanymi liczą się do liczby zapisanych pozycji;
brakujące rozmiary nie liczą się do sumy bajtów. Błędy są raportowane osobno.

Plik wyjściowy powstaje w trybie wyłącznego tworzenia: istniejący raport
nie zostanie nadpisany. Raport jest utrwalany po każdej paczce. Ctrl+C
zachowuje częściowy wynik i dopisuje status INTERRUPTED.
Status końcowy OK oznacza brak zgłoszonych błędów; ERRORS oznacza wynik niepełny
lub niepełne metadane. Kod wyjścia wynosi odpowiednio 0 lub 2.

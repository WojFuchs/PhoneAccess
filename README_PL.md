# PhoneAccess - Program do zarządzania plikami na Androidzie

## Cel projektu
Napisanie najprostszego możliwego programu, który umożliwi:
1. Rozpoznanie nazwy podłączonego telefonu Android (USB, bez Debug Mode)
2. Listowanie prawdziwych folderów i plików z modTime (dokładność do sekundy) i size
3. Kopiowanie X pierwszych plików z wybranego folderu na dysk Win10
4. Brak potrzeby kopiowania pliku na Win10 do jego analizy

## Preferowany język programowania
- **Pierwsza próba**: Python 3.x (najprostszy, szybki development)
- **Plan B**: Inne języki (C#, Node.js, C++) jeśli Python się nie uda
- Będzie się testować możliwości dostępu i stopniowo przechodzić na inny język jeśli konieczne

## Ograniczenia
- Windows 10
- Android podłączony przez USB
- Opcja "Kopiowanie plików" włączona
- Debug Mode **NIE WŁĄCZONY** (i musi tak pozostać)
- Total Commander potrafi to zrobić - więc jest wykonalne

## Test końcowy
Uruchomić z parametrami: `program Pictures 2`
- Wylistować pierwsze 2 pliki z folderu "Pictures" (lub podfoldery) z modTime i size
- Skopiować te 2 pliki na Win10

---

## Log postępu i eksperymentów

### Kroki do wykonania:
- [ ] Zbadać dostępne metody dostępu do USB Android bez Debug Mode na Win10
- [ ] Przygotować środowisko Python
- [ ] Wdrożyć detekcję podłączonego telefonu
- [ ] Wdrożyć listowanie plików z modTime i size
- [ ] Wdrożyć kopiowanie plików
- [ ] Przetestować z parametrami Pictures 2

### Próby i wyniki:
(Będą tutaj notowane wszystkie próby - zarówno te udane jak i nieudane, aby uniknąć pętli)

---

## Techniczne notatki
- Windows 10 widzi Android przez MTP (Media Transfer Protocol)
- Brak Debug Mode oznacza pracę tylko przez MTP
- Total Commander używa najprawdopodobniej Windows API do MTP


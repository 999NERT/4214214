# exUE5 - Sequence FBX Exporter

Ten folder zawiera czyste, osobne narzędzie do eksportu aktualnie otwartego Level Sequence z Unreal Engine 5.8 do FBX.

## Cel

- pobrać aktualnie otwarty Level Sequence,
- zebrać bindingi i tracki,
- utworzyć obiekt `SequencerExportFBXParams`,
- wyeksportować FBX do wskazanego folderu,
- uruchamiać to z poziomu menu Tools w UE5.

## Struktura

```text
exUE5/
├── install.py
├── menu.py
├── exporter.py
├── ui.py
├── config.json
└── README.md
```

## Jak wgrać do UE5

1. Skopiuj cały folder `exUE5` do folderu z narzędziami Python w swoim projekcie UE5.
2. Upewnij się, że w projekcie masz dostęp do skryptów Python w edytorze UE5.
3. Otwórz UE5 i uruchom w Edytorze skrypt:
   - `File > Open Level` lub po prostu otwórz projekt.
4. Uruchom `install.py` z poziomu Python Script Editor lub przez konsolę editor.
5. Po instalacji w menu `Tools` pojawi się opcja `Export Sequence FBX`.

## Uwaga

To jest wersja MVP. Jest zrobiona tak, aby była czysta i łatwa do rozszerzania.

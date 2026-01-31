# 🗑️ Bamberg Müllkalender

Eine moderne Desktop-Anwendung zur Anzeige der Abfuhrtermine für die Stadt Bamberg.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## Features

- 📅 **Live-Daten** - Ruft aktuelle Termine direkt von der Stadt Bamberg ab
- 🎨 **Moderne UI** - Übersichtliche Benutzeroberfläche mit Farbcodierung
- 🌙 **Dark Mode** - Augenfreundlicher dunkler Modus
- 📊 **Statistik** - Zeigt Anzahl der Termine pro Abfallart
- 📄 **Druckfunktion** - Termine als TXT-Datei speichern
- 📋 **Historie** - Letzte Anfragen werden gespeichert
- 🗑️ **Farbcodierung**:
  - Restmüll (schwarz/grau)
  - Biomüll (braun)
  - Papier (blau)
  - Gelber Sack (gelb)

## Screenshots

*Coming soon*

## Installation

### Voraussetzungen

- Python 3.8 oder höher
- tkinter (meist schon installiert)

### Ubuntu/Debian

```bash
# Repository klonen
git clone https://github.com/oli03ba/bamberg-muellkalender.git
cd bamberg-muellkalender

# Python und tkinter installieren
sudo apt install python3 python3-tk

# Virtual Environment erstellen (empfohlen)
python3 -m venv venv
source venv/bin/activate

# Abhängigkeiten installieren
pip install -r requirements.txt

# Programm starten
python3 bamberg_muell.py
```

### Windows

```bash
# Repository klonen
git clone https://github.com/oli03ba/bamberg-muellkalender.git
cd bamberg-muellkalender

# Virtual Environment erstellen (empfohlen)
python -m venv venv
venv\Scripts\activate

# Abhängigkeiten installieren
pip install -r requirements.txt

# Programm starten
python bamberg_muell.py
```

## Verwendung

1. **Adresse eingeben**
   - Straßenname (z.B. "Egelseestraße")
   - Hausnummer (z.B. "114")
   - Zusatz (optional, z.B. "a")

2. **Termine abrufen**
   - Klick auf "🔍 Termine abrufen"
   - Die Termine werden farbcodiert angezeigt

3. **Weitere Funktionen**
   - **Menü → Ansicht → Dark Mode**: Dunkles Design aktivieren
   - **Menü → Ansicht → Statistik**: Übersicht über Abfallarten
   - **Menü → Datei → Drucken**: Termine als TXT-Datei speichern
   - **Doppelklick auf History**: Vorherige Anfrage erneut laden

## Datenquelle

Die Daten werden direkt von der offiziellen Webseite der Stadt Bamberg abgerufen:
https://www.stadt.bamberg.de/Bürgerservice/Ämter/Bamberg-Service-/Abfallwirtschaft/Abfuhrtermine/

## Entwicklung

```bash
# Development Dependencies installieren
pip install -r requirements.txt

# Tests ausführen (falls vorhanden)
python -m pytest
```

## Lizenz

MIT License - siehe [LICENSE](LICENSE) Datei

## Autor

**Oliver Schlegel**

## Mitwirken

Beiträge sind willkommen! Bitte erstelle einen Pull Request oder öffne ein Issue.

1. Fork das Repository
2. Erstelle einen Feature Branch (`git checkout -b feature/NeuesFeature`)
3. Commit deine Änderungen (`git commit -m 'Füge neues Feature hinzu'`)
4. Push zum Branch (`git push origin feature/NeuesFeature`)
5. Öffne einen Pull Request

## Danksagung

- Stadt Bamberg für die öffentlichen Abfuhrdaten
- Python tkinter Community

## Support

Bei Problemen oder Fragen öffne bitte ein [Issue](https://github.com/DEINUSERNAME/bamberg-muellkalender/issues).

---

Made with ❤️ in Bamberg

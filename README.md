# LakuenTurismoRecomp

Eine AppImage für SteamOS (Desktop-Modus), die Gran Turismo 6 mit einem GT6-optimierten
RPCS3 startet – mit festen, stabilen Einstellungen für meinen PC und eingebautem Auto-Update.

Basiert auf [Mabec-games/Gran-Turismo-6-PC](https://github.com/Mabec-games/Gran-Turismo-6-PC)
(Stand v1.2 Beta 5). Inoffizielles Fanprojekt, keine Verbindung zu Sony oder Polyphony Digital.

## Was anders ist als beim Original

- **Nur Linux/SteamOS:** eine einzige Datei, `LakuenTurismoRecomp-x86_64.AppImage`. Keine Windows-Builds.
- **Auto-Update in der App:** Beim Start wird in diesem Repo nach einer neueren Version gesucht.
  Gibt es eine, fragt die App, ob du aktualisieren oder mit der alten Version spielen willst.
  Ein Klick lädt die neue AppImage, prüft sie per SHA-256, ersetzt die alte Datei und startet neu.
  Einstellungen, Spielstände, Firmware, Updates und Shader-Caches bleiben erhalten
  (`~/.local/share/gt6-launcher`). Abschalten für Offline-Betrieb: `LTR_NO_UPDATE_CHECK=1`.
- **Preset für meinen PC**, wird beim ersten Start automatisch gesetzt:

  | Hardware | Einstellung |
  |---|---|
  | Ryzen 7 5800X3D (8 Kerne / 16 Threads), 16 GB RAM | SPU Block Size *Mega*, OS-Scheduler |
  | Radeon RX 6600 XT, PCIe 4.0 x8 (ROG Strix B550-F) | 1080p-Ausgabe, 150 % Auflösung, Sharper MLAA, scharfe Schatten, Strict Rendering (AMD-Fix) |
  | Stabilität | ZCull-Queries aus, kein Multithreaded-RSX, Tiled Memory an, Vollbild, 60 FPS, 16x AF |

  Die alten Einstellungen lassen sich jederzeit mit *Restore previous settings* zurückholen.
  Auf einem 800p-Bildschirm (Steam Deck) greift stattdessen das Handheld-Preset.

## Benutzung

1. Neueste `LakuenTurismoRecomp-x86_64.AppImage` aus den
   [Releases](https://github.com/elkarbeenus/Gran-Turismo-6-PC/releases) laden.
2. Rechtsklick → Eigenschaften → *Ausführbar* (oder `chmod +x LakuenTurismoRecomp-x86_64.AppImage`), dann starten.
3. Im Tab **Setup**: Firmware installieren, eigene GT6-ISO hinzufügen, Updates bis 1.22 installieren.
4. **PLAY.** Der erste Start kompiliert ca. 8 Minuten, der erste Start von 1.22 dauert insgesamt ca. 30 Minuten.

Du brauchst eine eigene Kopie von Gran Turismo 6 (Disc-Image). Spiel, Firmware und Keys sind nicht enthalten;
Firmware und Spiel-Updates lädt die App direkt von Sonys Servern.

## Bauen

Der Workflow `.github/workflows/linux.yml` baut RPCS3 aus dem offiziellen Quellcode (fester Commit) plus
die Patches in `emulator/gt6-patches/`, packt die AppImage und testet sie. Ein Tag `v*` veröffentlicht
automatisch ein Release mit AppImage und `SHA256SUMS.txt`. Lokal: `packaging/build_appimage.sh`.

Tests für den Updater: `python3 -m unittest tests/test_selfupdate.py`

## Credits

Mabec-games (GT6 PC Launcher), RPCS3, AlexHaust, Nenkai, abowen, Lunard, FlexBy, Edo und das RPCS3-Wiki.
Lizenz: GPL-3.0 (siehe `LICENSE`).

# Handbuch Projekt Into the Schild (ITS)

## Hardware und Software

Eine Beschreibung der Hard- und Software die für das Projekt genutzt wurde.

Für das Projekt wurde eine virtuelle Maschine mit Ubuntu 18.04 LTS Server erzeugt. Die Hardware besteht aus einem Intel(R) Xeon(R) CPU E5-2698 v4 @ 2.20GHz und 32 Gigabyte RAM.

Als Programmiersprache wird Python in Version 3.6 eingesetzt. Die folgenden Module müssen noch zusätzlich installiert werden:

- tensorflow 
- numpy
- imageio
- requests 
- mysql-connector

Die genutzte Docker Version ist 18.06.1-ce, build e68fc7a, die unter Ubuntu durch das Paket *docker.io* installiert wird.


Als Datenbank wird MySql Server mit der Version: 5.7.24-0ubuntu0.18.04.1 (Ubuntu) genutzt. Installiert wird die Datenbank durch das Paket *mysql-server*.

## ITS Dateien und Ordner

Im folgenden werden die vom ITS Programm genutzten Dateien und Ordner beschrieben, welche standardmäßig genutzt werden.

- Ordner:
  - its_input
    - In diesem Ordner werden Bilder abgelegt, die für die Runs 1 - 3 als Grundlage dienen.
  - its_request
    - In diesem Ordner werden alle vom DCGAN generierten Bilder abgelegt. Das Format der Dateinamen besteht aus SessionNr_EpochNr_EpochHistoryId_ImgId.png
    - Die Requester Komponente greift ebenfalls auf diesen Ordner zu und sendet alle Dateien an das Klassifikationsnetzwerk der Aufgabe
  - its_dump
    - Die ImageDumper Komponente legt in diesem Ordner die Bilder mit der höchsten Konfidenz ab.
- Dateien:
  - its.ini
    - Dies ist die Konfigurationsdatei für das ITS Programm. Die genauere Beschreibung der einzelnen Parameter ist im nächsten Kapitel zu finden.
  - its_dcgan.log
    - Logging output der DCGAN Komponente.
  - its_session_manager.log
    - Logging output der SessionManager Komponente.
  - its_requester.log
    - Logging output der Requester Komponente.
  - its_image_dumper.log
  -  Logging output der Requester Komponente.

## Konfiguration - its.ini

Die Konfigurationsdatei besteht aus vier Kategorien. Im folgende werden nur die besonderen Parameter beschrieben:

1. MySql
   - Hier wird die Datenbankverbindung angegeben. Falls die Datenbank, die unter *database* angegeben wird, noch nicht existiert, wird diese automatisch mit der vom ITS Programm benötigten Struktur erzeugt.
2. Requester
   - Einstellungen für den Requester. Der Parameter *send_delay* bestimmt die eine Wartezeit in Sekunden, die ein Requesterthread warten soll, bevor er ein Bild an das Klassifikationsnetz sendet.
   - Der Parameter *queue_size*, bestimmt wie viele Bilder gleichzeitig im Speichergehalten werden.
3. ImageDumper
   - Der Parameter *top_img_cnt* bestimmt die Anzahl der Bilder pro Klasse, die aus der Datenbank geladen werden sollen. Es werden dabei Standardmäßig die besten 10 Bilder pro Klasse geladen.

## Docker Images der Abgabe

Die Abgabe besteht aus zwei Docker Images: its_untrained und its_trained. Beide Images besitzen eine MySql Datenbank mit einem Datenbankbenutzer "its" und das ITS Programm. *its_untrained* besitzt noch keinerlei Einträge in der Datenbank. *its_trained* besitzt rund 500.000 Bilder in der Tabelle its_request_history.

Die untrainierte Variante ist für einen Testlauf gedacht, um zu sehen wie sich die Bilder entwickeln. Die trainierte Varinate dient zum betrachten der bereits gefunden Bilder.

Beide Dockerimages besitzten einen symbolischen Link */outvol*. Dieser verweist auf den Ordnern, der vom ITS Programm für in- und output Zwecke genutzt wird und beinhaltet die im Kaptiel *ITS Dateien und Ordner* beschriebene Struktur.


### Empfohlene Nutzung its_untrained

Anmerkung: Es wird angenommen, dass ein Dockervolume mit den Namen *outvol* existiert.

Zum starten des ITS Programms können vier verschiedene Scripte aufgerufen werden:

1. its_first.sh - Startet den *First Run* (siehe Paper Kapitel 3.1.1)
2. its_second.sh - Startet den *Second Run* (siehe Paper Kapitel 3.1.2)
3. its_third.sh - Startet den *Third Run* (siehe Paper Kapitel 3.1.3)
4. its_auto.sh - Startet den *Fourth Run - AutoFind* (siehe Paper Kapitel 3.1.4)
5. its_img_dump.sh - Startet die ImageDumper Komponente, welche die Bilder mit der höchsten Konfidenz aus der Datenbank lädt. Die Anzahl der Bilder kann über die *its.ini* konfiguriert werden.

**Achtung:** Ein Aufruf des *its_auto* Scripts macht jedoch nur Sinn, wenn bereits Bilder in der Datenbank vorhanden sind. Dieses Script am besten nur mit its_trained nutzen.

Beispiel Aufrufe:

- docker run -v outvol:/outvol -t its_untrained ./its_first.sh
- docker run -v outvol:/outvol -t its_untrained ./its_second.sh
- docker run -v outvol:/outvol -t its_untrained ./its_third.sh

Zur Beobachtung des aktuellen Laufs, empfehlen wir drei Ansätze:

1. Betrachtung der Logging-Dateien
    - Am einfachsten ist es die Logging-Dateien mit dem Kommando *tail -f* aufzurufen. Dies kommt einem Konsolen Output sehr nah.
2. Betrachung des Request-Ordners
    - Wenn ein Run gestartet wird, werden Bilder im its_request Ordner generiert. Dies kann je nach System ein paar Minuten dauern, da die Bilder jede tausendste Epochen generiert werden.
    - Bilder, die an das Klassifikationsnetz gesendet wurden, werden aus dem Ordner gelöscht und in der ITS Datenbank abgespeichert
3. Betrachtung des Dump-Ordners
    - Sobald der Requester alle erzeugten Bilder in der Datenbank abgespeichert hat, startet der ImageDumper. Dieser speichert die besten Bilder im *its_dump* Ordner. Dies kann jedoch einige Stunden dauern.
    - Grobe zeitliche Orientierung ist: *pro input Bild etwa eine Stunde*

### Empfohlene Nutzung its_trained

Das *its_trained* Image kann prinzipiell genau so genutzt werden wie *its_untrained*. Es wird jedoch empfohlen hier nur das *its_img_dump.sh* Script auszuführen und in der Konfirgurationsdatei einen möglichst hohen *top_img_cnt* einzustellen. Im *its_trained* Image sind rund 230.000 Bilder mit einer Konfidenz von über 90% vorhanden.

Auf dem *its_trained* Image kann zwar das *its_auto.sh* Script ausgeführt werden, jedoch könnte dies (je nach System) mehrere Tage dauern.

Beispiel Aufrufe:

- docker run -v outvol:/outvol -t its_trained ./its_img_dump.sh
- docker run -v outvol:/outvol -t its_trained ./its_auto.sh

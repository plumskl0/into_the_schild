# Projekt Into the Schild (ITS)

Der Branch dient zum Zusammenführen des Requesters und des DCGANs.

- 10.12.2018
    - Zuerst wird der Requester nochmal getestet und mit dem DCGAN gemerged.
- 11.12.2018
    - Als nächstes wird der Requester so angepasst, dass er das _its_logging_ Modul nutzt.
      - Path Hack genutzt damit der Requester auch Standalone funktioniert
    - Logger in eine Klasse umgebaut
      - Erbt nun von *LoggerAdapter* 
# Projekt Into the Schild (ITS)

Der Branch dient zum Zusammenführen des Requesters und des DCGANs.

- 10.12.2018
  - Zuerst wird der Requester nochmal getestet und mit dem DCGAN gemerged.
- 11.12.2018
  - Als nächstes wird der Requester so angepasst, dass er das _its_logging_ Modul nutzt.
    - Path Hack genutzt damit der Requester auch Standalone funktioniert
  - Logger in eine Klasse umgebaut
    - Erbt nun von *LoggerAdapter* 
- 13.12.2019
  -  Umbenennung: *ItsLogger*, *ItsDcgan*
  -  Erstellung von *ItsEpochInfo*
  -  Änderungen An *ItsDcgan*:
     -  Umwandlung in Klasse
     -  Vereinfachte Nutzung durch neue Methoden:
        -  *initEpoch*: Initialisiert die Epoche mit:
           -  maximalen Epochen
           -  maximalen Generierten Bildern
           -  nach wie vielen Epochen Bilder generiert werden
           -  etc.
        -  *initDcgan*: Initialisiert *generator* und *discriminator*
           -  TODO: Anpassung von *initDcgan* um Filter, Kernel, etc. einzustellen
  - Änderung an *ItsLogger*:
    - Logger hat neue Methode *infoEpoch(itsEpochInfo)* erhalten
      - Nutzt die Klasse *ItsEpochInfo* um ein Logging für die aktuelle Epoche auszugeben
      - Dient gleichzeitig als Vorlage für weitere Logger (z.B. XmlLogger)


# TODOs
- Requester Logging erzeugen
  - Also Infos vorbereiten um sie an den *ItsSessionManager* zu geben
  - Dafür den Logger um eine Methode erweitern
  - Neue Klasse für *ItsRequesterInfo*
- Neue Klasse *ItsSessionManager*
  - Eine Session ist praktisch ein Durchlauf mit verschiedenen Parametern:
    - Mögliche Parameter werden sein:
      - *maxEpochs* (Def. 10): Wie viele Epochen pro *run*
      - *n_noise* (Def. 64): Größe des Grundnoise für den Generator 
      - *batch_size* (Def. 4): Größe des Batches beim Trainieren
        - Es muss auf die Anzahl der Basis Bilder geachtet werden
      - *stepsHistory* (Def. 50): Nach wie vielen Epochen soll eine History erzeugt werden
      - *stepsImageGeneration* (Def. 1000): Nach wie vielen Epochen werden Bilder generiert
      - *cntGenerateImages* (Def. 40): Wie viele Bilder sollen pro sollen generiert werden
      - Weitere:
        - Kernel, Strides, etc.
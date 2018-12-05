# -*- coding: utf-8 -*-
'''
    Ein DCGAN auf Basis von Code by Parag Mital (github.com/pkmital/CADL).

    Wir haben sieben Beispielbilder, die wir als Datengrundlage nutzen. Die Bilder
    werden in verschiedenen Ordnern (Kategorie) als erstes Bild abgelegt und zum
    Trainieren des Generators und Discriminators genutzt. 

    Nach einigen Epochen werden fünf Bilder aus jeder Kategorie vom Discriminator gewählt 
    und an den Requester gegeben. Der Requester schickt die generierten Daten an das 
    NeuronaleNetz der Aufgabe und gibt uns die Klassifikationswerte an.

    Im ersten Versuch wird das DCGAN nach einingen Epochen Bilder generieren, die in die
    Datengrundlage aufgenommen werden. Mithilfe dieses Durchlaufs ermitteln wir ob das 
    DCGAN mit einer möglichst simplen Methode "gute" Bilder erzeugen wird. 
    
    Gute Bilder sind Bilder die vom Klassifkationsnetz der Aufgabe mit einer möglichst 
    hohen Konfidenz bewertet.

    Es sind bereits weitere Abläufe geplant, die eine etwas voreingenommene Auswahl 
    von Bildern nutzen wird. Aber das kommt später.

    Zum nachvollziehen der Entwicklung wird eine Historie der Losswerte und 
    Bewertung des NN erzeugt. Die Aufgabe könnte jedoch im Requester implementiert
    werden. 

    Benötigte Ordnersturktur:
    its_images
        - Ordner mit den Beispielbildern
        - hier werden auch die vom DCGAN generierten Bilder abgelegt
        - Unterordner:
            - Kategorien Ordner     - Kategorie in die ein Bild fällt
                - Zunächst einfache Namensgebung mit Zahlen
                - TODO: evtl. ein Mapping der Kategorie und Ordner erstellen
            - /generated_epoch_x     - nach X Epochen generierte Bilder
            - 
    its_dcgan.ini
        - Konfigurationsdatei um später einfacher verschiedene DCGANs zu testen
        - TODO: evtl. eine Kofigurationsdatei erzeugen für Requester umd DCGAN
'''

import os
import imageio
import logging
import numpy as np

root = './'
dirItsImages = os.path.join(root, 'its_images')
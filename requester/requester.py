# -*- coding: utf-8 -*-
'''
    Der Requester sendet HTTP-Anfragen an das NN der Aufgabe.
    Maximal 60 Bilder pro Minute.

    Benötigte Ordnerstruktur:
    req_in
        - Inputordner für Dateien
        - hier werden Dateien abgelegt, die an das NN gesendet werden sollen
        - Unterordner:
            - /done         - Klassifizierte Bilder
            - /done/error   - Bilder die durch einen Fehler nicht klassifiziert wurden
            - /trash        - Dateien die keine PNGs sind
    req_out
        - Outputordner für Dateien
        - req_history.xml
            - XML-Datei für Request Historie zum nachvollziehen
            - Format:
                <request_history>
                    <request date="%H:%M:%S %d-%m-%Y">
                        <image dtype='np'> NumpyArray </image>
                        <result> JSON-Array </result>
                    </request>
                </request_history>

'''

import os
import time
import json
import logging
import imageio
import requests
import numpy as np
import configparser as cfgp
from lxml import etree
from datetime import datetime

# Ordner
root = './'
dirIn = os.path.join(root, 'req_in')
dirDone = os.path.join(dirIn, 'done')
dirTrash = os.path.join(dirIn, 'trash')
dirError = os.path.join(dirDone, 'error')
dirOut = os.path.join(root, 'req_out')

# Dateien
fileConfig = 'requester.ini'
fileHistory = 'req_history.xml'
fileLog = 'requester.log'

# Default Config Werte
PARAM_REQ = 'Requester'
PARAM_URL = 'url'
PARAM_KEY = 'key'
PARAM_DEF_KEY_VAL = 'Api-Key einfuegen'
PARAM_DELAY = 'delay'
# Alle 10 Sekunden auf neue Dateien prüfen
PARAM_DEF_DELAY_VAL = 10

# XML Elemente und Attribute
XML_ROOT = 'request_history'
XML_REQUEST = 'request'
XML_IMAGE = 'image'
XML_RESULT = 'result'

XML_ATR_DATE = 'date'
XML_ATR_DTYPE = 'dtype'
XML_ATR_DATE_FORMAT = '%d-%m-%Y %H:%M:%S'

# Prüfen ob Dateien und Ordner vorhanden sind, ggfs. anlegen


def initLogging(logFile='requester.log'):
    logging.basicConfig(
        # filename=logFile,
        level=logging.INFO,
        format='%(asctime)s:%(levelname)s:%(message)s'
    )

    log = logging.getLogger('requester')

    # ch = logging.StreamHandler()
    # ch.setLevel(logging.DEBUG)
    # log.addHandler(ch)
    return log


def getMyLogger():
    return logging.getLogger('requester')


def checkFilesFolders():
    createDir(dirIn, dirTrash, dirDone, dirError, dirOut)

    log = getMyLogger()
    if not os.path.exists(fileConfig):
        log.debug('Creating File: {}'.format(fileConfig))
        with open(fileConfig, 'w') as cfgFile:
            config = createConfigTemplate()
            config.write(cfgFile)

    if not os.path.exists(fileHistory):
        log.debug('Creating File: {}'.format(fileHistory))
        root = createHistoryTemplate()
        xmlToFile(root)


def createDir(*args):
    log = getMyLogger()
    for d in args:
        if not os.path.exists(d):
            log.debug('Creating Dir: {}'.format(d))
            os.makedirs(d)


def createConfigTemplate():
    getMyLogger().debug('Creating Config File: {}'.format(PARAM_REQ))
    config = cfgp.ConfigParser()
    config[PARAM_REQ] = {PARAM_URL: 'http://www.example.com',
                         PARAM_KEY: PARAM_DEF_KEY_VAL,
                         PARAM_DELAY: PARAM_DEF_DELAY_VAL}
    return config


def getConfig():
    config = cfgp.ConfigParser()
    with open(fileConfig, 'r') as cfgFile:
        config.read_file(cfgFile)
        return config


def getConfigParams():
    config = getConfig()

    url = None
    key = None
    delay = None

    if config.has_option(PARAM_REQ, PARAM_URL):
        url = config.get(PARAM_REQ, PARAM_URL)

    if config.has_option(PARAM_REQ, PARAM_KEY):
        key = config.get(PARAM_REQ, PARAM_KEY)

    if config.has_option(PARAM_REQ, PARAM_DELAY):
        delay = int(config.get(PARAM_REQ, PARAM_DELAY))

    return url, key, delay


def sendRequest(img):
    myUrl = url
    myData = {PARAM_KEY: key}
    myFiles = {'image': img}

    return requests.post(myUrl, data=myData, files=myFiles)


def createHistoryTemplate():
    log = getMyLogger()
    log.debug('Creating History Template: {}'.format(XML_ROOT))
    root = etree.Element(XML_ROOT)

    # Elemente erzeugen
    request = etree.SubElement(root, XML_REQUEST)
    result = etree.SubElement(request, XML_RESULT)
    image = etree.SubElement(request, XML_IMAGE)

    # Beispiel Attribute
    request.attrib[XML_ATR_DATE] = XML_ATR_DATE_FORMAT
    request.attrib['info_text'] = 'Beispieleintrag'
    image.attrib[XML_ATR_DTYPE] = 'np.int32'
    result.text = 'numpy.array([x,y])'
    return root


def addToHistory(classArr, imageArr, now):
    root = readHistory()

    # Neuen Request erzeugen
    request = etree.SubElement(root, XML_REQUEST)
    result = etree.SubElement(request, XML_RESULT)
    image = etree.SubElement(request, XML_IMAGE)

    # Attribute und Texte hinzufügen
    request.attrib[XML_ATR_DATE] = now.strftime(XML_ATR_DATE_FORMAT)
    image.attrib[XML_ATR_DTYPE] = imageArr.dtype.name
    result.text = json.dumps(classArr)
    image.text = json.dumps(imageArr.tolist())

    xmlToFile(root)


def xmlToFile(root):
    xmlString = etree.tostring(root, encoding='UTF-8', pretty_print=True)
    with open(fileHistory, 'w') as hisFile:
        hisFile.write(xmlString.decode('UTF-8'))


def readHistory():
    root = None
    with open(fileHistory, 'r') as hisFile:
        root = etree.fromstring(hisFile.read())
    return root


log = initLogging()
log.debug('Starting Folder check...')
checkFilesFolders()
log.debug('Folder check done')
# Config Einträge prüfen
# Ohne Api-Key nichts machen
run = 0
url, key, delay = getConfigParams()

# Nicht default Value und nicht leer
if not PARAM_DEF_KEY_VAL == key or not key:
    run = 1
    log.info('API-Key found')
else:
    log.error('No API-Key defined in requester.ini')
while run:

    # while True: -- Hier kommt später die Schleife hin
    # Input Ordner auf Bilder überprüfen
    _, _, files = next(os.walk(dirIn))

    log.info('Files to process {}'.format(len(files)))

    for f in files:
        # Dateiname/pfad erzeugen
        imgPath = os.path.join(dirIn, f)

        # Nur PNG Bilder einlesen
        if 'png' in imgPath.lower():
            log.info('Opening file {}'.format(imgPath))
            img = open(imgPath, 'rb')

            myData = {'key': key}
            myFiles = {'image': img}

            response = requests.post(url, data=myData, files=myFiles)
            img.close()

            dest = ''
            now = datetime.now()
            # Aktuelle Zeit für den Dateinamen nutzen
            newName = '{}.png'.format(now.strftime('%Y-%m-%d_%H_%M_%S'))

            if response.ok:
                log.info('Image sucessfully transfered')

                # Response verarbeiten
                classArr = response.json()
                # Bild als numpy Array einlesen
                imageArr = imageio.imread(imgPath)

                # Anfrage zur Historie hinzufügen
                addToHistory(classArr, imageArr, now)

                # Dateinamen für done Ordner
                dest = os.path.join(dirDone, newName)
            else:
                # Dateinamen done/error Ordner
                log.error('Request error: {}'.format(response.text))
                dest = os.path.join(dirError, newName)

            log.info('Moving file to: {}'.format(dest))
            os.rename(imgPath, dest)
        else:
            log.info('File "{}" is not an PNG moving to trash'.format(f))

            trash = os.path.join(dirTrash, f)
            os.rename(imgPath, trash)

        # Eine Sekunde warten damit die Requests nicht zu schnell bearbeitet werden.
        # Evtl. unnötig, da die verarbeitung bereits länger als eine Sekunde dauert
        time.sleep(1)

    time.sleep(delay)

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
import logging
import requests
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

# XML Elemente und Attribute
XML_ROOT = 'request_history'
XML_REQUEST = 'request'
XML_IMAGE = 'image'
XML_RESULT = 'result'

XML_ATR_DATE = 'date'
XML_ATR_DTYPE = 'dtype'
XML_ATR_DATE_FORMAT = '%H:%M:%S %d-%m-%Y'

# Prüfen ob Dateien und Ordner vorhanden sind, ggfs. anlegen


def initLogging(logFile='requester.log'):
    logging.basicConfig(
        # filename=logFile,
        level=logging.DEBUG,
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
    createFile(fileConfig, fileHistory)


def createDir(*args):
    log = getMyLogger()
    for d in args:
        if not os.path.exists(d):
            log.debug('Creating Dir: {}'.format(d))
            os.makedirs(d)


def createFile(*args):
    log = getMyLogger()
    for f in args:
        if not os.path.exists(f):
            log.debug('Creating File: {}'.format(f))
            with open(f, 'w') as myFile:
                config = createConfigTemplate()
                config.write(myFile)


def createConfigTemplate():
    getMyLogger().debug('Creating Config File: {}'.format(PARAM_REQ))
    config = cfgp.ConfigParser()
    config[PARAM_REQ] = {PARAM_URL: 'http://www.example.com',
                         PARAM_KEY: PARAM_DEF_KEY_VAL}
    return config


def getConfig():
    config = cfgp.ConfigParser()
    with open(fileConfig, 'r') as cfgFile:
        config.read_file(cfgFile)
        return config


def getUrlKey():
    config = getConfig()

    url = None
    key = None

    if config.has_option(PARAM_REQ, PARAM_URL):
        url = config.get(PARAM_REQ, PARAM_URL)

    if config.has_option(PARAM_REQ, PARAM_KEY):
        key = config.get(PARAM_REQ, PARAM_KEY)

    return url, key


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
    image = etree.SubElement(request, XML_IMAGE)
    result = etree.Subelement(request, XML_RESULT)

    # Beispiel Attribute
    request.attrib[XML_ATR_DATE] = XML_ATR_DATE_FORMAT
    image.attrib[XML_ATR_DTYPE] = 'np.int32'
    return root


log = initLogging()
log.debug('Starting Folder check...')
checkFilesFolders()
log.debug('Done')
# Config Einträge prüfen
# Ohne Api-Key nichts machen
run = 0
url, key = getUrlKey()

# Nicht default Value und nicht leer
if not PARAM_DEF_KEY_VAL == key or not key:
    run = 1
    log.info('API-Key found')
else:
    log.error('No API-Key defined in requester.ini')
# while run:

    # while True: -- Hier kommt später die Schleife hin
    # Input Ordner auf Bilder überprüfen
_, _, files = next(os.walk(dirIn))

log.info('Files to process {}'.format(len(files)))

# for f in files:

# Dateiname/pfad erzeugen
imgPath = os.path.join(dirIn, files[0])

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

        # In done Ordner verschieben
        dest = os.path.join(dirDone, newName)
    else:
        # In done/error Ordner verschieben
        log.error('Request error: {}'.format(response.text))
        dest = os.path.join(dirError, newName)

    log.info('Moving file to: {}'.format(dest))
    os.rename(imgPath, dest)

# -*- coding: utf-8 -*-
'''
    Der Requester sendet HTTP-Anfragen an das NN der Aufgabe.
    Maximal 60 Bilder pro Minute.

    Benötigte Ordnerstruktur:
    req_in
        - Inputordner für Dateien
        - hier werden Dateien abgelegt, die an das NN gesendet werden sollen
        - Unterordner:
            - /done     - Bearbeitete Bilder werden in diesen Ordner verschoben
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

# Ordner
root = './'
dirIn = os.path.join(root, 'req_in')
dirDone = os.path.join(dirIn, 'done')
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
        #filename=logFile,
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
    log = getMyLogger()
    if not os.path.exists(dirIn):
        log.debug('Creating Dir: {}'.format(dirIn))
        os.makedirs(dirIn)

    if not os.path.exists(dirDone):
        log.debug('Creating Dir: {}'.format(dirDone))
        os.makedirs(dirDone)

    if not os.path.exists(dirOut):
        log.debug('Creating Dir: {}'.format(dirOut))
        os.makedirs(dirOut)

    if not os.path.exists(fileConfig):
        log.debug('Creating File: {}'.format(fileConfig))
        with open(fileConfig, 'w') as cfgFile:
            config = createConfigTemplate()
            config.write(cfgFile)

    if not os.path.exists(fileHistory):
        log.debug('Creating File: {}'.format(fileHistory))
        with open(fileHistory, 'w') as hisFile:
            root = createHistoryTemplate()
            root.write(hisFile)

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
    myFiles = {'image':img}

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
# Config Einträge prüfen
# Ohne Api-Key nichts machen
run = 0
url, key = getUrlKey()

if not PARAM_DEF_KEY_VAL == key:
    run = 1

# while run:

    # while True: -- Hier kommt später die Schleife hin
    # Input Ordner auf Bilder überprüfen
_, _, files = next(os.walk(dirIn))

# for f in files:

# Dateinamen erzeugen
path = os.path.join(dirIn, files[0])

img = None

# Nur PNG Bilder einlesen
# if 'png' in path.lower():
#     img = open(path, 'rb')

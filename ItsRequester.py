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
import random
import imageio
import requests
import numpy as np
import configparser as cfgp
from lxml import etree
from datetime import datetime
from itslogging import ItsLogger
from itsmisc import ItsRequestInfo

# Ordner
root = './its_request'
dirIn = os.path.join(root, 'req_in')
dirDone = os.path.join(dirIn, 'done')
dirTrash = os.path.join(dirIn, 'trash')
dirError = os.path.join(dirDone, 'error')
dirOut = os.path.join(root, 'req_out')

# Dateien
fileConfig = 'requester.ini'
fileHistory = os.path.join(root, 'req_history.xml')
fileLog = 'requester.log'

# Default Config Werte
PARAM_REQ = 'Requester'
PARAM_URL = 'url'
PARAM_KEY = 'key'
PARAM_DEF_KEY_VAL = 'Api-Key einfuegen'
PARAM_DELAY = 'delay'
PARAM_XML = 'xml'
# Alle 10 Sekunden auf neue Dateien prüfen
PARAM_DEF_DELAY_VAL = 60
PARAM_DEF_XML_VAL = False

# XML Elemente und Attribute
XML_ROOT = 'request_history'
XML_REQUEST = 'request'
XML_IMAGE = 'image'
XML_RESULT = 'result'

XML_ATR_DATE = 'date'
XML_ATR_DTYPE = 'dtype'
XML_ATR_DATE_FORMAT = '%d-%m-%Y %H:%M:%S'


class ItsRequester:

    def __init__(self, debug=False):
        self.logger = ItsLogger(
            logName='its_requester',
            debug=debug)

        self.debug = debug
        # Um beim ersten Start eine Beispiel XML zu erzeugen
        self.xmlHistory = True
        self.checkFilesFolders()

        self.url, self.key, self.delay, self.xmlHistory = self.getConfigParams()
        self.httpClassification = self.checkApiKey()

    def checkApiKey(self):
        # Nicht default Value und nicht leer
        http = False
        if not PARAM_DEF_KEY_VAL == self.key or not self.key:
            self.logger.info('API-Key found. Enabling HTTP Requests.')
            http = True
        else:
            self.logger.error('No API-Key defined in requester.ini')
            self.logger.info(
                'No HTTP Requests possible. Please specify API-Key.')

        return http

    def checkFilesFolders(self):
        self.logger.debug('Starting Folder check...')
        self.createDir(dirIn, dirTrash, dirDone, dirError, dirOut)

        if not os.path.exists(fileConfig):
            self.logger.debug('Creating File: {}'.format(fileConfig))
            with open(fileConfig, 'w') as cfgFile:
                config = self.createConfigTemplate()
                config.write(cfgFile)

        if not os.path.exists(fileHistory) and self.xmlHistory:
            self.logger.debug('Creating File: {}'.format(fileHistory))
            root = self.createHistoryTemplate()
            self.xmlToFile(root)

        self.logger.debug('Folder check done.')

    def createDir(self, *args):
        for d in args:
            if not os.path.exists(d):
                self.logger.debug('Creating Dir: {}'.format(d))
                os.makedirs(d)

    def createConfigTemplate(self):
        self.logger.debug('Creating Config File: {}'.format(PARAM_REQ))
        config = cfgp.ConfigParser()
        config[PARAM_REQ] = {PARAM_URL: 'http://www.example.com',
                             PARAM_KEY: PARAM_DEF_KEY_VAL,
                             PARAM_DELAY: PARAM_DEF_DELAY_VAL,
                             PARAM_XML: PARAM_DEF_XML_VAL}
        return config

    def getConfig(self):
        config = cfgp.ConfigParser()
        with open(fileConfig, 'r') as cfgFile:
            config.read_file(cfgFile)
            return config

    def getConfigParams(self):
        config = self.getConfig()

        url = None
        key = None
        delay = None
        xmlHistory = None

        if config.has_option(PARAM_REQ, PARAM_URL):
            url = config.get(PARAM_REQ, PARAM_URL)

        if config.has_option(PARAM_REQ, PARAM_KEY):
            key = config.get(PARAM_REQ, PARAM_KEY)

        if config.has_option(PARAM_REQ, PARAM_DELAY):
            delay = config.getint(PARAM_REQ, PARAM_DELAY)

        if config.has_option(PARAM_REQ, PARAM_XML):
            xmlHistory = config.getboolean(PARAM_REQ, PARAM_XML)

        return url, key, delay, xmlHistory

    def sendRequest(self, *imgs):
        self.logger.debug('Sending request for {} Images...'.format(len(imgs)))
        results = []

        if self.httpClassification:
            myUrl = self.url
            myData = {PARAM_KEY: self.key}

            send = False
            firstWait = True
            for img in imgs:
                myFiles = {'image': img}
                time.sleep(1)
                # while not send:
                res = requests.post(myUrl, data=myData, files=myFiles)
                    # print(res.status_code)
                    # if res.status_code == requests.codes.too_many:
                    #     if firstWait:
                    #         self.logger.error('Too many requests waiting for {}s.'.format(self.delay))
                    #         time.sleep(self.delay)
                    #         firstWait = False
                    #     else:
                    #         rand = random.randint(1,10)
                    #         self.logger.error('Too many requests waiting for {}s.'.format(rand))
                    #         time.sleep(rand)
                    # if res.ok:
                    #     send = True
                    #     firstWait = True
                reqInfo = self.getRequestInfoForResult(res, img)
                results.append(res)

                if self.debug:
                    self.logger.infoRequestInfo(reqInfo)

        return results

    def getRequestInfoForResult(self, result, img):
        reqInfo = ItsRequestInfo()

        if result.ok:
            nn_class, max_confidence = self.getBestClassFromResult(result)
            reqInfo.nn_class = nn_class
            reqInfo.max_confidence = max_confidence
            reqInfo.json_result = result.json()

        reqInfo.img_array = np.fromfile(img, dtype=np.uint8)
        reqInfo.img_dtype = reqInfo.img_array.dtype.name
        return reqInfo

    def getBestClassFromResult(self, result):
        jRes = result.json()
        return jRes[0]['class'], jRes[0]['confidence']

    def createHistoryTemplate(self):
        self.logger.debug('Creating History Template: {}'.format(XML_ROOT))
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

    def addToXmlHistory(self, classArr, imageArr, now):
        root = self.readXmlHistory()

        # Neuen Request erzeugen
        request = etree.SubElement(root, XML_REQUEST)
        result = etree.SubElement(request, XML_RESULT)
        image = etree.SubElement(request, XML_IMAGE)

        # Attribute und Texte hinzufügen
        request.attrib[XML_ATR_DATE] = now.strftime(XML_ATR_DATE_FORMAT)
        image.attrib[XML_ATR_DTYPE] = imageArr.dtype.name
        result.text = json.dumps(classArr)
        image.text = json.dumps(imageArr.tolist())

        self.xmlToFile(root)

    def xmlToFile(self, root):
        xmlString = etree.tostring(root, encoding='UTF-8', pretty_print=True)
        with open(fileHistory, 'w') as hisFile:
            hisFile.write(xmlString.decode('UTF-8'))

    def readXmlHistory(self):
        root = None
        with open(fileHistory, 'r') as hisFile:
            root = etree.fromstring(hisFile.read())
        return root

    def sendDir(self):
        if self.httpClassification:
            _, _, files = next(os.walk(dirIn))

            self.logger.info('Files to process {}'.format(len(files)))
            nr = 1
            for f in files:
                # Dateiname/pfad erzeugen
                imgPath = os.path.join(dirIn, f)

                # Nur PNG Bilder einlesen
                if 'png' in imgPath.lower():
                    self.logger.debug('Opening file {}'.format(imgPath))
                    img = open(imgPath, 'rb')

                    response = self.sendRequest(img)[0]
                    img.close()

                    dest = ''
                    now = datetime.now()
                    # Aktuelle Zeit für den Dateinamen nutzen
                    newName = '{}_{}.png'.format(
                        now.strftime('%Y-%m-%d_%H_%M_%S'), nr)
                    nr += 1

                    if response.ok:
                        self.logger.debug('Image sucessfully transfered')

                        # Response verarbeiten
                        classArr = response.json()
                        # Bild als numpy Array einlesen
                        imageArr = imageio.imread(imgPath)

                        # Anfrage zur Historie hinzufügen
                        if self.xmlHistory:
                            self.addToXmlHistory(classArr, imageArr, now)

                        # Dateinamen für done Ordner
                        dest = os.path.join(dirDone, newName)
                    else:
                        # Dateinamen done/error Ordner
                        self.logger.error(
                            'Request error: {}'.format(response.text))
                        dest = os.path.join(dirError, newName)

                    self.logger.debug('Moving file to: {}'.format(dest))
                    os.rename(imgPath, dest)
                else:
                    self.logger.debug(
                        'File "{}" is not an PNG moving to trash'.format(f))

                    trash = os.path.join(dirTrash, f)
                    os.rename(imgPath, trash)


if __name__ == '__main__':
    print("Starting Debugmode Requester...")
    r = ItsRequester(debug=True)

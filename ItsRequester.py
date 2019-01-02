# -*- coding: utf-8 -*-
'''
    Der Requester sendet HTTP-Anfragen an das NN der Aufgabe.
    Maximal 60 Bilder pro Minute.

    Benötigte Ordnerstruktur:
    req_in
        - Inputordner für Dateien
        - Requester im Standalone / Ordnermodus
        - hier werden Dateien abgelegt, die an das NN gesendet werden sollen
        - Unterordner:
            - /done         - Klassifizierte Bilder
            - /done/error   - Bilder die durch einen Fehler nicht klassifiziert wurden
            - /trash        - Dateien die keine PNGs sind
'''
import os
import re
import time
import json
import random
import imageio
import requests
import numpy as np
import configparser as cfgp
from lxml import etree
from datetime import datetime
from threading import Thread
from itslogging import ItsLogger, ItsSqlLogger
from itsmisc import ItsRequestInfo, ItsConfig

# Ordner
dirItsRequests = './its_request'
dirIn = os.path.join(dirItsRequests, 'req_in')
dirDone = os.path.join(dirIn, 'done')
dirTrash = os.path.join(dirIn, 'trash')
dirError = os.path.join(dirDone, 'error')

# Dateien
fileConfig = 'requester.ini'
fileHistory = os.path.join(dirItsRequests, 'req_history.xml')
fileLog = 'requester.log'

# XML Elemente und Attribute
XML_ROOT = 'request_history'
XML_REQUEST = 'request'
XML_IMAGE = 'image'
XML_RESULT = 'result'

XML_ATR_DATE = 'date'
XML_ATR_DTYPE = 'dtype'
XML_ATR_DATE_FORMAT = '%d-%m-%Y %H:%M:%S'


class ItsRequester:

    def __init__(self, config, debug=False):
        self.logger = ItsLogger(
            logName='its_requester',
            debug=debug
        )
        self.config = config
        self.debug = debug
        # Um beim ersten Start eine Beispiel XML zu erzeugen
        self.xmlHistory = True
        self.checkFilesAndFolders()
        self.__initConfig()
        self.sessionInfo = None
        self.sqlLog = None

        # Quick'n'Dirty hardcoded
        # TODO: poll_delay evtl. in config aufnehmen
        self.poll_delay = 5
        self.isReady = True

    def __del__(self,):
        self.logger.debug('Killing ItsRequester...')
        del self.logger

    def __initConfig(self):
        self.url = self.config.url
        self.key = self.config.key
        self.delay = self.config.delay
        self.xmlHistory = self.config.xml

    def setSession(self, itsSessionInfo, sqlLog=None):
        # Evtl. Durch Property ersetzen
        self.sessionFinished = False
        self.sessionInfo = itsSessionInfo
        if sqlLog:
            self.sqlLog = sqlLog

    def classifyImgDir(self, imgDir):
        if self.sessionInfo:
            if self.debug:
                self.logger.debug('Starting classification')
            self.__startWorkerThread(imgDir)
        else:
            self.logger.error('SessionInfo is not set. Use .setSession()')

    def stopRequests(self,):
        self.sessionFinished = True
        while self.classificationThread.isAlive():
            self.logger.info('Classification still running...')
            self.classificationThread.join(self.poll_delay)

    def __startWorkerThread(self, imgDir):
        self.logger.info('Preparing classification thread for folder {}'.format(
            imgDir
        ))
        self.classificationThread = Thread(
            target=self.__runClassification,
            args=(imgDir,)
        )
        self.classificationThread.start()

    def __isSessionFinished(self, imgDir):
        self.logger.debug('Checking if Session is really finshed.')
        b = self.sessionFinished and self.__classificationFinished(imgDir)
        self.logger.info('Session really finished = {}'.format(b))
        return b

    def __classificationFinished(self, imgDir):
        # Prüfen ob es noch Dateien gibt,
        # die klassifiziert werden müssen.
        m = re.compile(r'\d\.png')
        for _, _, files in os.walk(imgDir):
            if any(m.match(f) for f in files):
                return False
        
        return True

    def __runClassification(self, imgDir):
        while not self.__isSessionFinished(imgDir):
            self.logger.info('Starting classification check on {}'
                             .format(imgDir))
            imgs = self.__collectImagePaths(imgDir)
            self.__sendGeneratedImages(imgs)
            self.logger.info('Classification waiting for {}'
                             .format(self.poll_delay))
            time.sleep(self.poll_delay)

    def __sendGeneratedImages(self, imgsPath):
        for p in imgsPath:
            with open(p, 'rb') as img:
                content = img.read()

            res = self.sendRequest(content)
            reqInfo = self.getRequestInfoForResult(res, content)

            reqInfo.epoch = self.__getEpoch(p)
            self.logger.infoRequestInfo(reqInfo, p)
            if self.sqlLog:
                self.sqlLog.logRequestInfo(reqInfo)
            self.__markImgClassified(p)

    def __markImgClassified(self, path):
        self.logger.debug('Marking file {} as classifed.'.format(path))
        newName = path.replace('.png', '_c.png')
        try:
            os.rename(path, newName)
        except WindowsError:
            os.remove(newName)
            os.rename(path, newName)

    def __getEpoch(self, img):
        # Epoche aus dem Pfad Filtern
        return int(re.search(r'epoch_(\d*)', img).group(1))

    def __collectImagePaths(self, imgDir):
        imgs = []
        # Alle nicht klassifizierten Bilder sammeln
        for root, _, files in os.walk(imgDir):
            for f in files:
                if not '_c.png' in f:
                    imgs.append(os.path.join(root, f))

        return imgs

    def checkFilesAndFolders(self):
        self.logger.debug('Starting Folder check...')
        self.createDir(dirIn, dirTrash, dirDone, dirError, dirOut)

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

    def sendRequest(self, img):
        self.logger.debug('Preparing request for Image...')
        res = None

        if self.isReady:
            myUrl = self.url
            myData = {ItsConfig.PARAM_KEY: self.key}

            send = False
            firstWait = True
            myFiles = {'image': img}
            time.sleep(1)
            # while not send:
            if self.debug:
                self.logger.debug('Sending request...')
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

        return res

    def getRequestInfoForResult(self, result, img):
        reqInfo = ItsRequestInfo()
        if result.ok:
            nn_class, max_confidence = self.getBestClassFromResult(result)
            reqInfo.nn_class = nn_class
            reqInfo.max_confidence = max_confidence
            reqInfo.json_result = result.json()
        if self.sessionInfo:
            reqInfo.sessionNr = self.sessionInfo.sessionNr
        else:
            reqInfo.sessionNr = 0
        reqInfo.epoch = 0
        reqInfo.img_array = np.frombuffer(img, dtype=np.uint8)
        reqInfo.img_dtype = reqInfo.img_array.dtype.name
        self.logger.debug('>>>>Image Array:\n{}'.format(reqInfo.img_array))
        self.logger.debug('>>>>Image dtype:\n{}'.format(reqInfo.img_dtype))
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
        if self.isReady:
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

                    response = self.sendRequest(img)

                    reqInfo = self.getRequestInfoForResult(response, img)
                    self.logger.infoRequestInfo(reqInfo)
                    if self.sqlLog:
                        self.sqlLog.logRequestInfo(reqInfo)

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
    test = ItsConfig('its.ini')
    r = ItsRequester(test.getRequesterConfig(), debug=True)

# -*- coding: utf-8 -*-
import os
import re
import time
import imageio
import requests
import numpy as np
from threading import Thread
from itsdb import ItsSqlConnection
from itslogging import ItsLogger, ItsSqlLogger
from itsmisc import ItsRequestInfo, ItsConfig


class ItsRequester:

    def __init__(self, config, debug=False):
        self.log = ItsLogger(
            logName='its_requester',
            debug=debug
        )

        self.debug = debug
        self.cfg = config
        self.sqlLog = None
        self.poll_delay = 5
        self.__initConfig()
        self.__initSqlLogger()
        self.__checkRequestDir()
        self.isReady = True

    def __initConfig(self):
        if self.cfg.isRequestValid():
            self.log.info('Config valid. Preparing Requester.')
            self.log.info('To stop the requester enter \'y\'')
            self.url = self.cfg.req_cfg.url
            self.key = self.cfg.req_cfg.key
            self.delay = self.cfg.req_cfg.delay
            self.reqDir = self.cfg.req_cfg.request_directory
        else:
            self.log.error('Invalid config.')

    def __checkRequestDir(self):
        if self.cfg.isRequestValid():
            if not os.path.exists(self.reqDir):
                self.log.debug('Request directory does not exist.')
                self.log.info(
                    'Creating requester directory \'{}\''.format(self.reqDir))
                os.makedirs(self.reqDir)

    def __initSqlLogger(self):
        self.log.info('Creating SQL connection...')
        sql = ItsSqlConnection(self.cfg.sql_cfg, log=self.log)
        if sql.dbExists:
            self.log.info('SQL connection successful.')
            self.log.info('Preparing SQL log...')
            self.sqlLog = ItsSqlLogger(sql)
        else:
            self.log.error('SQL connection failed.')

    def startClassification(self):
        self.log.info('Preparing classification thread for folder \'{}\''.format(
            self.reqDir
        ))

        self.classificationThread = Thread(
            target=self.__runClassification,
            args=(self.reqDir,)
        )

        self.classificationThread.start()

    # TODO: Evtl. rausschmeisen?
    def __isClassificationFinished(self, imgDir):
        # Prüfen ob es noch Dateien gibt,
        # die klassifiziert werden müssen.
        done = True
        m = re.compile(r'\.png')
        for _, _, files in os.walk(imgDir):
            if any(m.match(f) for f in files):
                done = False

        # Bilder vorhanden oder Requester beendet
        finished = done and self.isReady

        return finished

    def __runClassification(self, imgDir):
        if self.isReady:
            self.log.info('Classification is ready.')

        while self.isReady:
            self.log.info('Starting classification on folder \'{}\''
                          .format(imgDir))
            imgs = self.__collectImagePaths(imgDir)
            self.__sendGeneratedImages(imgs)
            self.log.info('Classification waiting for {}'
                          .format(self.poll_delay))
            if self.debug:
                self.log.info('To stop the classification enter \'y\'')
            time.sleep(self.poll_delay)

    def __sendGeneratedImages(self, imgsPath):
        for p in imgsPath:
            if self.isReady:
                with open(p, 'rb') as img:
                    content = img.read()

                res = self.sendRequest(content)
                reqInfo = self.getRequestInfoForResult(res, p)

                reqInfo.sessionNr, reqInfo.epoch, hisId = self.__getSessionEpoch(p)
                self.log.infoRequestInfo(reqInfo, p)
                if self.sqlLog:
                    self.sqlLog.logRequestInfo(reqInfo, hisId)
                self.__markImageAsClassified(p)
            else:
                self.log.info('Classification stopped...')
                break

    def __markImageAsClassified(self, img):
        # Bilder werden aus dem Ordner gelöscht
        self.log.debug('Marking file {} as classifed.'.format(img))
        os.remove(img)

    def __getSessionEpoch(self, imgPath):
        # Session und Epoche aus dem Pfad Filtern
        name = os.path.basename(imgPath)

        if '_' in name and '.png' in name:
            # PNG aus dem Namen entfernen
            name = name.split('.')[0]
            # [0] = Session, [1] = Epoche
            info = name.split('_')
        else:
            info = (0, 0, 0)

        self.log.info('Session {} - Epoch {} - History ID: {}'.format(
            info[0], info[1], info[2]))
        return int(info[0]), int(info[1]), int(info[2])

    def __collectImagePaths(self, imgDir):
        imgs = []
        # Alle nicht klassifizierten Bilder sammeln
        for root, _, files in os.walk(imgDir):
            for f in files:
                if not '_c.png' in f:
                    imgs.append(os.path.join(root, f))

        return imgs

    def sendRequest(self, img):
        self.log.debug('Preparing request for Image...')

        myUrl = self.url
        myData = {ItsConfig.PARAM_KEY: self.key}

        myFiles = {'image': img}
        # Kleines delay einbauen um 'too_many_requests' zu vermeiden
        time.sleep(1)
        if self.debug:
            self.log.debug('Sending request...')

        return requests.post(myUrl, data=myData, files=myFiles)

    def getRequestInfoForResult(self, result, imgPath):
        reqInfo = ItsRequestInfo()
        if result.ok:
            nn_class, max_confidence = self.getBestClassFromResult(result)
            reqInfo.nn_class = nn_class
            reqInfo.max_confidence = max_confidence
            reqInfo.json_result = result.json()
        reqInfo.sessionNr = 0
        reqInfo.epoch = 0
        reqInfo.img_array = imageio.imread(imgPath)
        reqInfo.img_dtype = reqInfo.img_array.dtype.name
        if self.debug:
            self.log.debug('Image Array:\t{}'.format(reqInfo.img_array.shape))
            self.log.debug('Image dtype:\t{}'.format(reqInfo.img_dtype))
        return reqInfo

    def getBestClassFromResult(self, result):
        jRes = result.json()
        return jRes[0]['class'], jRes[0]['confidence']

    def stop(self):
        self.log.info('Stopping requester...')
        self.isReady = False
        self.classificationThread.join()
        self.log.info('Requester stopped. Bye!')


if __name__ == "__main__":
    # Requester wird nur noch als Standalone genutzt
    # Der Sessionmanager legt die Bilder in den Ordner des requesters
    # Requester hat eine eigene Verbindung und speichert die Request Infos in die DB
    # Die Namen der Bilder müssen die Infos (SessionNr, Epoche etc.) beinhalten
    # Beispiel: 'session_epoch_.png'
    cfg = ItsConfig(ItsConfig.CONFIG_PATH)
    requester = ItsRequester(cfg, debug=True)
    requester.startClassification()

    while requester.isReady:
        print('Requester is running...')
        print('Too view information check the requester log file.')
        ans = input('To stop the requester enter \'y\': ')
        if ans is 'y':
            requester.stop()

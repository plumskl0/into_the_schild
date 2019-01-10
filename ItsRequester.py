# -*- coding: utf-8 -*-
import os
import re
import time
import random
import imageio
import requests
import numpy as np
from queue import Queue
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
        self.imgQueue = Queue(self.qSize)
        self.reqQueue = Queue(self.qSize)
        self.threadList = []
        self.isReady = True

    def __initConfig(self):
        if self.cfg.isRequestValid():
            self.log.info('Config valid. Preparing Requester.')
            self.log.info('To stop the requester enter \'y\'')
            self.url = self.cfg.req_cfg.url
            self.key = self.cfg.req_cfg.key
            self.delay = self.cfg.req_cfg.delay
            self.reqDir = self.cfg.req_cfg.request_directory
            self.qSize = self.cfg.req_cfg.qSize
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

        if isinstance(self.key, list):
            for k in self.key:
                self.__startThread(k)
                # Kleiner delay, da die Threads manchmal auf das selbe item zugreifen
                time.sleep(1)
        else:
            self.__startThread(self.key)

    def __startThread(self, key):
        t = Thread(
            target=self.__runClassification,
            args=(key,)
        )
        t.daemon = True
        t.start()
        self.threadList.append(t)

    def __runClassification(self, apiKey):
        if self.isReady:
            self.log.info('Classification Thread {} is ready.'.format(
                len(self.threadList)))

        while self.isReady:
            if not self.imgQueue.empty():
                img = self.imgQueue.get()
                self.__sendImage(img, apiKey)
                self.imgQueue.task_done()
            else:
                randWait = random.randrange(self.poll_delay)
                self.log.info(
                    'Queue is empty. Thread sleeping for {}s'.format(randWait))
                time.sleep(randWait)

    def __sendImage(self, imgPath, apiKey):
        if os.path.exists(imgPath):
            try:
                with open(imgPath, 'rb') as img:
                    content = img.read()

                res = self.sendRequest(content, apiKey)
                reqInfo = self.getRequestInfoForResult(res, imgPath)

                reqInfo.sessionNr, reqInfo.epoch, hisId = self.__getSessionEpoch(
                    imgPath)
                self.log.infoRequestInfo(reqInfo, imgPath)
                if self.sqlLog:
                    while self.reqQueue.full():
                        self.log.info('Request queue is full waiting..')
                        time.sleep(1)
                    self.reqQueue.put((reqInfo, hisId))
                self.__markImageAsClassified(imgPath)
            except FileNotFoundError:
                pass

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

        return imgs

    def sendRequest(self, img, apiKey):
        self.log.debug('Preparing request for Image...')

        myUrl = self.url
        myData = {ItsConfig.PARAM_KEY: apiKey}

        myFiles = {'image': img}
        # Kleines delay einbauen um 'too_many_requests' zu vermeiden
        time.sleep(self.delay)
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
        if self.debug:
            self.log.debug('Image Array:\t{}'.format(reqInfo.img_array.shape))
        return reqInfo

    def getBestClassFromResult(self, result):
        jRes = result.json()
        return jRes[0]['class'], jRes[0]['confidence']

    def stop(self):
        self.log.info('Stopping requester...')
        self.isReady = False

        self.reqQueue.join()

        for t in self.threadList:
            time.sleep(1)
            t.join()

        self.log.info('Requester stopped. Bye!')

    def startRequestQueue(self):
        t = Thread(target=self.__sendRequestQueue)
        t.daemon = True
        t.start()
        self.threadList.append(t)

    def __sendRequestQueue(self):
        while self.isReady or not self.reqQueue.empty():
            if not self.reqQueue.empty():
                reqInfo, hisId = self.reqQueue.get()
                self.sqlLog.logRequestInfo(reqInfo, hisId)
                self.reqQueue.task_done()
            else:
                self.log.info('Requester queue is empty')
                time.sleep(self.poll_delay)

    def fillImageQueue(self):
        t = Thread(target=self.__fillImageQueue)
        t.start()
        self.threadList.append(t)

    def __fillImageQueue(self):
        # Alle nicht klassifizierten Bilder sammeln
        while self.isReady:
            for root, _, files in os.walk(self.reqDir):
                for f in files:
                    img = os.path.join(root, f)
                    inQ = (img in self.imgQueue.queue)
                    fullQ = self.imgQueue.full()
                    if not inQ and not fullQ:
                        self.log.info('Adding {} to queue.'.format(img))
                        self.imgQueue.put(img, )
                    else:
                        if not self.isReady:
                            self.log.info('Classification stopped..')
                        elif inQ:
                            self.log.info(
                                'File {} already in queue.'.format(f))
                        elif fullQ:
                            self.log.info('Queue is full.')
                            break
            size = self.imgQueue.qsize()
            if size == 0:
                size = self.poll_delay
            randWait = random.randrange(size/2)
            self.log.info('Next queue fill in {}'.format(randWait))
            time.sleep(randWait)


if __name__ == "__main__":
    # Requester wird nur noch als Standalone genutzt
    # Der Sessionmanager legt die Bilder in den Ordner des requesters
    # Requester hat eine eigene Verbindung und speichert die Request Infos in die DB
    # Die Namen der Bilder müssen die Infos (SessionNr, Epoche etc.) beinhalten
    # Beispiel: 'session_epoch_.png'
    cfg = ItsConfig(ItsConfig.CONFIG_PATH)
    requester = ItsRequester(cfg, debug=True)
    requester.startClassification()
    requester.fillImageQueue()
    requester.startRequestQueue()

    while requester.isReady:
        print('Requester is running...')
        print('Too view information check the requester log file.')
        ans = input('To stop the requester enter \'y\': ')
        if ans is 'y':
            requester.stop()

# -*- coding: utf-8 -*-
import os
import re
import time
import queue
import random
import imageio
import requests
import numpy as np
from threading import Thread
from itsdb import ItsSqlConnection
from itslogging import ItsLogger, ItsSqlLogger
from itsmisc import ItsRequestInfo, ItsConfig


class ItsRequester:

    def __init__(self, config, debug=False):
        self.logName = 'its_requester'
        self.log = ItsLogger(self.logName, outDir=ItsConfig.VOLUME_FOLDER)

        self.debug = debug
        self.cfg = config
        self.sqlLog = None
        self.hardDelay = 5
        self.__initConfig()
        self.__checkRequestDir()
        self.__initSqlLogger()
        self.clsThreads = []
        self.imgQueue = queue.Queue(self.qSize)
        self.sqlThread = None
        self.collectThread = None
        self.reqQueue = queue.Queue(self.qSize)
        self.stop = False

    def __initConfig(self):
        self.log.info('Config valid. Preparing Requester.')
        self.log.info('To stop the requester enter \'y\'')
        self.url = self.cfg.req_cfg.url
        self.key = self.cfg.req_cfg.key
        self.delay = self.cfg.req_cfg.delay
        self.reqDir = self.cfg.req_cfg.request_directory
        self.qSize = self.cfg.req_cfg.qSize

    def __checkRequestDir(self):
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
            self.sqlLog = ItsSqlLogger(sql, self.log)
        else:
            self.log.error('SQL connection failed.')

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
                    send = False
                    while not send:
                        try:
                            self.reqQueue.put(
                                (reqInfo, hisId), timeout=self.hardDelay)
                            send = True
                        except queue.Full:
                            self.log.info(
                                'Request queue is full waiting... retrying')

                self.__markImageAsClassified(imgPath)
            except FileNotFoundError:
                pass

    def startRequesting(self):
        self.startImageCollectionThread()
        self.startClassificationThread()
        self.startSqlThread()

    def stopRequesting(self):
        self.log.info('Stopping requester... waiting for Jobs to be finished')

        self.imgQueue.join()
        self.reqQueue.join()

        for t in self.clsThreads:
            time.sleep(1)
            t.join()

        self.sqlThread.join()
        self.collectThread.join()

        self.log.info('Requester stopped. Bye!')

    def startClassificationThread(self):
        self.log.info('Preparing classification thread for folder \'{}\''.format(
            self.reqDir
        ))

        if isinstance(self.key, list):
            # Mehrere Keys mehrere Threads
            for k in self.key:
                self.__startClassificationThread(k)
        else:
            self.__startClassificationThread(self.key)

    def __startClassificationThread(self, key):
        t = Thread(
            target=self.__classifyImages,
            args=(key,)
        )
        t.daemon = True
        t.start()
        self.clsThreads.append(t)

    def __classifyImages(self, apiKey):
        tId = len(self.clsThreads)
        self.log.info('Classification Thread {} is ready.'.format(tId))

        # Wenn Bilder bereits aufgenommen wurden
        while not self.stop:
            try:
                img = self.imgQueue.get(timeout=self.hardDelay)
                self.__sendImage(img, apiKey)
                self.imgQueue.task_done()
            except queue.Empty:
                self.log.info('Thread {}: Image queue is empty.'.format(tId))

        self.log.info('Thread {} is terminating')

    def startImageCollectionThread(self):
        self.collectThread = Thread(target=self.__collectImages)
        self.collectThread.daemon = True
        self.collectThread.start()

    def __collectImages(self):
        while not self.stop:
            try:
                for root, _, files in os.walk(self.reqDir):
                    for f in files:
                        img = os.path.join(root, f)
                        inQ = (img in self.imgQueue.queue)
                        if not inQ:
                            self.log.info(
                                'Adding image {} to queue.'.format(img))
                            self.imgQueue.put(
                                img, timeout=self.hardDelay)
            except queue.Full:
                randWait = self.__calcRandWait()
                self.log.info(
                    'Image queue is full. Next check in {}s'.format(randWait))

        self.log.info('Image collection stopped.')

    def startSqlThread(self):
        self.sqlThread = Thread(target=self.__sendRequests)
        self.sqlThread.daemon = True
        self.sqlThread.start()

    def __sendRequests(self):
        self.log.info('SQL thread is ready..')
        while not self.stop:
            try:
                reqInfo, hisId = self.reqQueue.get(timeout=self.hardDelay)
                self.sqlLog.logRequestInfo(reqInfo, hisId)
                self.reqQueue.task_done()
            except queue.Empty:
                self.log.info('Request queue is empty retrying...')
        self.log.info('SQL thread stopped')

    def __calcRandWait(self):
        size = int(self.imgQueue.qsize()/2)
        if size == 0:
            size = self.hardDelay

        return random.randrange(size)


if __name__ == "__main__":
    req = ItsRequester(ItsConfig())
    req.startRequesting()
    while input() not in 'y':
        req.stopRequesting()

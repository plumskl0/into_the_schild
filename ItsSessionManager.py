# -*- coding: utf-8 -*-

import os
import gc
import time
import imageio
import numpy as np
import argparse
from ItsDcgan import ItsDcgan
from itsdb import ItsSqlConnection
from itsmisc import ItsSessionInfo, ItsConfig
from itslogging import ItsLogger, ItsSqlLogger
from ItsRequester import ItsRequester
from ItsImageDumper import ItsImageDumper


class ItsSessionManager():

    def __init__(self):
        self.config = self.__createConfig()
        self.logName = 'its_session_manager'
        self.log = ItsLogger(self.logName, outDir=ItsConfig.VOLUME_FOLDER)
        self.sql = self.__createConnection()
        self.sqlLog = None
        self.dcgan = None
        self.__prepareFolders()
        self.itsRequester = ItsRequester()
        self.itsImgDumper = ItsImageDumper()
        self.waitTime = 5

    def __createConfig(self):
        return ItsConfig()

    def __createConnection(self):
        self.log.info('Creating SQL connection...')
        sql = ItsSqlConnection(self.config.sql_cfg, log=self.log)

        if sql.dbExists:
            self.log.info('SQL Connection successful.')
            return sql
        else:
            self.log.error('No SQL connection.')
            return None

    def __prepareFolders(self):
        self.outDir = self.config.req_cfg.request_directory
        if not os.path.exists(self.outDir):
            self.log.info('Creating Directory: \'{}\''.format(self.outDir))
            os.makedirs(self.outDir)

        self.inDir = self.config.misc.inputDir
        if not os.path.exists(self.inDir):
            self.log.info('Creating Directory: \'{}\''.format(self.inDir))
            os.makedirs(self.inDir)

    def prepareRun(self):
        if not self.sqlLog:
            self.sqlLog = ItsSqlLogger(self.sql, self.log)

        if self.dcgan:
            del self.dcgan
        gc.collect()
        self.dcgan = ItsDcgan(self.sqlLog)
        self.dcgan.outputDir = self.outDir
        self.dcgan.initDcgan()

    def __createDefaultSession(self):
        session = ItsSessionInfo()
        session.sessionNr = 1
        session.max_epoch = 10
        session.info_text = 'Default Session'
        session.cntBaseImages = 0
        session.enableImageGeneration = True
        session.stepsHistory = 5
        session.cntGenerateImages = 2
        session.batch_size = 2
        session.debug = False
        return session

    def getImages(self):
        imgs = []
        # Alle nicht klassifizierten Bilder sammeln
        for root, _, files in os.walk(self.inDir):
            for f in files:
                if '.png' in f:
                    img = os.path.join(root, f)
                    imgs.append(imageio.imread(img))

        self.log.info('Found {} input images.'.format(len(imgs)))

        return imgs

    def firstRun(self):
        self.prepareRun()
        session = self.__createDefaultSession()
        session.sessionNr = 1
        session.max_epoch = 25001
        session.info_text = 'Erster Durchlauf mit einzelnen Bildern aus dem Input Ordner. Das trainierte DCGAN wird dabei immer beibehalten.'
        session.enableImageGeneration = True
        session.stepsHistory = 1000
        session.cntGenerateImages = 120

        imgs = self.getImages()
        session.cntBaseImages = len(imgs)

        if len(imgs) > 0:
            self.sql.insertSession(session)

            for img in imgs:
                self.dcgan.setSessionBaseImages(session.sessionNr, [img, img])
                self.dcgan.initEpoch(
                    session.max_epoch,
                    session.batch_size,
                    session.enableImageGeneration,
                    session.stepsHistory,
                    session.cntGenerateImages
                )
                self.dcgan.start()
        else:
            self.log.error('No images in input dir \'{}\''.format(self.outDir))

    def secondRun(self):
        session = self.__createDefaultSession()
        session.sessionNr = 2
        session.max_epoch = 25001
        session.info_text = 'DEBUG Zweiter Durchlauf mit allen Basisbildern und das DCGAN vergisst, was es gelernt hat.'
        session.enableImageGeneration = True
        session.stepsHistory = 1000
        session.cntGenerateImages = 120

        imgs = self.getImages()
        session.cntBaseImages = len(imgs)

        if len(imgs) > 0:
            self.sql.insertSession(session)

            for img in imgs:
                self.prepareRun()
                self.dcgan.setSessionBaseImages(session.sessionNr, [img, img])
                self.dcgan.initEpoch(
                    session.max_epoch,
                    session.batch_size,
                    session.enableImageGeneration,
                    session.stepsHistory,
                    session.cntGenerateImages
                )
                self.dcgan.start()
        else:
            self.log.error('No images in input dir \'{}\''.format(self.outDir))

    def thirdRun(self):
        self.prepareRun()
        session = self.__createDefaultSession()
        session.sessionNr = 3
        session.max_epoch = 25001
        session.info_text = 'Dritter Durchlauf mit allen Basisbildern.'
        session.enableImageGeneration = True
        session.stepsHistory = 100
        session.cntGenerateImages = 120

        imgs = self.getImages()
        session.cntBaseImages = len(imgs)

        if len(imgs) > 0:
            self.sql.insertSession(session)

            self.dcgan.setSessionBaseImages(session.sessionNr, imgs)
            self.dcgan.initEpoch(
                session.max_epoch,
                session.batch_size,
                session.enableImageGeneration,
                session.stepsHistory,
                session.cntGenerateImages
            )
            self.dcgan.start()
        else:
            self.log.error('No images in input dir \'{}\''.format(self.outDir))

    def debugRun(self):
        self.prepareRun()
        session = self.__createDefaultSession()
        session.sessionNr = 0
        session.max_epoch = 5
        session.info_text = 'DEBUG'
        session.enableImageGeneration = True
        session.stepsHistory = 2
        session.cntGenerateImages = 120

        imgs = self.getImages()
        session.cntBaseImages = len(imgs)

        if len(imgs) > 0:
            self.sql.insertSession(session)
            self.dcgan.setSessionBaseImages(session.sessionNr, imgs)
            self.dcgan.initEpoch(
                session.max_epoch,
                session.batch_size,
                session.enableImageGeneration,
                session.stepsHistory,
                session.cntGenerateImages
            )
            self.dcgan.start()
        else:
            self.log.error('No images in input dir \'{}\''.format(self.outDir))

    def startAutoFind(self):
        session = self.__createDefaultSession()
        session.sessionNr = 4
        session.max_epoch = 25001
        session.info_text = 'Autofind'
        session.enableImageGeneration = True
        session.stepsHistory = 1000
        session.cntGenerateImages = 120

        # Hier kommt eine Liste mit Tupeln
        imgs = self.itsImgDumper.getAutoFindImages()

        session.cntBaseImages = len(imgs)
        if len(imgs) > 0:
            self.sql.insertSession(session)
            for img in imgs:
                self.prepareRun()
                self.dcgan.setSessionBaseImages(
                    session.sessionNr, [img[1], img[1]])
                self.dcgan.initEpoch(
                    session.max_epoch,
                    session.batch_size,
                    session.enableImageGeneration,
                    session.stepsHistory,
                    session.cntGenerateImages
                )
                self.dcgan.start()
        else:
            self.log.error('No AutoFind images.')


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--first', help='Start first run')
    parser.add_argument('--second', help='Start second run')
    parser.add_argument('--third', help='Start third run')
    parser.add_argument('--auto', help='Start auto run')
    parser.add_argument('-d', '--debug', help='Debug run')

    args = parser.parse_args()

    if args.first:
        s = ItsSessionManager()
        s.firstRun()
    elif args.second:
        s = ItsSessionManager()
        s.secondRun()
    elif args.third:
        s = ItsSessionManager()
        s.thirdRun()
    elif args.auto:
        s = ItsSessionManager()
        s.debugRun()
    else:
        print('No argument set. Please call ItsSessionManager with option \'-h\'.')

# -*- coding: utf-8 -*-

import os
import time
import imageio
import numpy as np
from ItsDcgan import ItsDcgan
from ItsRequester import ItsRequester
from itsmisc import ItsSessionInfo, ItsConfig
from itslogging import ItsLogger, ItsSqlLogger
from itsdb import ItsSqlConnection


class ItsSessionManager():

    def __init__(self):
        self.log = ItsLogger('its_session_manager')
        self.config = self.__createConfig()
        self.sql = self.__createConnection()
        self.sqlLog = None
        self.__prepareFolders()

    def __createConfig(self):
        cfg = ItsConfig(ItsConfig.CONFIG_PATH)
        if cfg.isValid():
            self.log.info('Config is valid.')
        else:
            self.log.error('Config invalid. Please check the config file.')
        return cfg

    def __createConnection(self):
        if self.config.isValid():
            self.log.info('Creating SQL connection...')
            sql = ItsSqlConnection(self.config.sql_cfg, log=self.log)

            if sql.dbExists:
                self.log.info('SQL Connection successful.')
                return sql
            else:
                self.log.error('No SQL connection.')
                return None
        else:
            self.log.error('Invalid config. Please check the config.')

    def __prepareFolders(self):
        self.outDir = self.config.req_cfg.request_directory
        if not os.path.exists(self.outDir):
            self.log.info('Creating Directory: \'{}\''.format(self.outDir))
            os.makedirs(self.outDir)

        self.inDir = 'its_input'
        if not os.path.exists(self.inDir):
            self.log.info('Creating Directory: \'{}\''.format(self.inDir))
            os.makedirs(self.inDir)

    def prepareRun(self):
        if not self.sqlLog:
            self.sqlLog = ItsSqlLogger(self.sql)

        if self.dcgan:
            del self.dcgan

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
        session.debug = True
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
        session.stepsHistory = 100
        session.cntGenerateImages = 60

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
        session.stepsHistory = 100
        session.cntGenerateImages = 60

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
        session.cntGenerateImages = 60

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
        session.max_epoch = 10
        session.info_text = 'DEBUG'
        session.enableImageGeneration = True
        session.stepsHistory = 2
        session.cntGenerateImages = 10

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


if __name__ == "__main__":
    s = ItsSessionManager()
    # s.debugRun()
    s.firstRun()
    s.secondRun()
    s.thirdRun()

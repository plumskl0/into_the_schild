# -*- coding: utf-8 -*-

import os
import imageio
from itsmisc import ItsConfig
from itslogging import ItsLogger, ItsSqlLogger
from itsdb import ItsSqlConnection


class ItsImageDumper():

    def __init__(self):
        self.logName = 'its_image_dumper'
        self.log = ItsLogger(self.logName)
        self.config = self.__createConfig()
        self.sql_con = self.__createConnection()
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
            sql = ItsSqlConnection(self.config.sql_cfg, self.log)

            if sql.dbExists:
                self.log.info('SQL Connection successful.')
                return sql
            else:
                self.log.error('No SQL connection.')
                return None
        else:
            self.log.error('Invalid config. Please check the config.')

    def __prepareFolders(self):
        self.outDir = self.config.imgd_cfg.outDir
        if not os.path.exists(self.outDir):
            self.log.info('Creating Directory: \'{}\''.format(self.outDir))
            os.makedirs(self.outDir)

    def getAutoFindImages(self):
        # Liste mit Tupeln
        return self.sql_con.getAutoFindImages()

    def dumpBestImages(self):
        clsNames = self.sql_con.getDistinctClassNames()
        self.log.info('Found {} distinct classes.'.format(len(clsNames)))
        bestIds = []
        for c in clsNames:
            bestIds.append(self.sql_con.getMaxConfId(c, 10))
        self.log.info('Found {} IDs.'.format(len(bestIds)))

        imgTuples = []
        cnt = 0
        for i in bestIds:
            img = None
            if isinstance(i, list):
                for tid in i:
                    img = self.sql_con.getImageFromRequestHistory(tid)
                    # imgTuples.append(img)
                    self.__saveImage(img)
            else:
                img = self.sql_con.getImageFromRequestHistory(i)
                # imgTuples.append(img)
                self.__saveImage(img)

            cnt += 1

        self.log.info('Fetched {} images from DB.'.format(cnt))

    def __saveImage(self, imgTuple):
        clsName, img, maxConf = imgTuple

        # Auf % bringen
        maxConf *= 100

        imgNr = self.__getOutImgCount(clsName)
        imgName = clsName + '_{:2.4f}_{}.png'.format(maxConf, imgNr)

        self.log.info('Writing image {}'.format(imgName))
        imgPath = os.path.join(self.outDir, imgName)
        imageio.imwrite(imgPath, img)
        self.log.info('Image saved.')

    def __getOutImgCount(self, clsName):
        cnt = 0
        for _, _, files in os.walk(self.outDir):
            for f in files:
                if clsName in f:
                    cnt += 1

        return cnt


if __name__ == "__main__":
    dump = ItsImageDumper()
    dump.dumpBestImages()

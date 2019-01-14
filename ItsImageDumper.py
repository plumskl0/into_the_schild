# -*- coding: utf-8 -*-

import os
import imageio
from itsmisc import ItsConfig
from itslogging import ItsLogger, ItsSqlLogger
from itsdb import ItsSqlConnection


class ItsImageDumper():

    def __init__(self):
        self.logName = 'its_image_dumper'
        self.log = ItsLogger(self.logName, outDir=ItsConfig.VOLUME_FOLDER)
        self.config = self.__createConfig()
        self.sql_con = self.__createConnection()
        self.outDir = self.config.imgd_cfg.outDir
        self.imgCnt = self.config.imgd_cfg.topImgCnt
        self.__prepareFolders()

    def __createConfig(self):
        return ItsConfig()

    def __createConnection(self):
        self.log.info('Creating SQL connection...')
        sql = ItsSqlConnection(self.config.sql_cfg, self.log)

        if sql.dbExists:
            self.log.info('SQL Connection successful.')
            return sql
        else:
            self.log.error('No SQL connection.')
            return None

    def __prepareFolders(self):
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
            bestIds.append(self.sql_con.getMaxConfId(c, self.imgCnt))
        self.log.info('Found {} classes.'.format(len(clsNames)))

        cnt = 0
        for i in bestIds:
            img = None
            if isinstance(i, list):
                for tid in i:
                    img = self.sql_con.getImageFromRequestHistory(tid)
                    self.__saveImage(img)
                    cnt += 1
            else:
                img = self.sql_con.getImageFromRequestHistory(i)
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

# -*- coding: utf-8 -*-

import os
from itsmisc import ItsConfig
from itslogging import ItsLogger, ItsSqlLogger
from itsdb import ItsSqlConnection

class ItsImageDumper():

    def __init__(self):
        self.log = ItsLogger('its_image_dumper')
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
        self.outDir = self.config.imgd_cfg.outDir
        if not os.path.exists(self.outDir):
            self.log.info('Creating Directory: \'{}\''.format(self.outDir))
            os.makedirs(self.outDir)

    def getAutoFindImages(self):
        # Liste mit Tupeln
        return self.sql_con.getAutoFindImages()
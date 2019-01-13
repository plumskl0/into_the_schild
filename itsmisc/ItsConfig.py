# -*- coding: utf-8 -*-

import os
import configparser as cfgp
from itsmisc.itscfg.ItsMysqlConfig import ItsMysqlConfig as ItsSqlCfg
from itsmisc.itscfg.ItsRequesterConfig import ItsRequesterConfig as ItsReqCfg
from itsmisc.itscfg.ItsImageDumperConfig import ItsImageDumperConfig as ItsImgDumpCfg


class ItsConfig():

    CONFIG_PATH = 'its.ini'

    # MySql config defaults
    PARAM_MYSQL = 'MySql'
    PARAM_HOST = 'host'
    PARAM_USER = 'user'
    PARAM_PASS = 'pass'
    PARAM_DATABASE = 'database'

    DEF_HOST = '127.0.0.1'
    DEF_USER = 'its'
    DEF_PASS = '1212'
    DEF_DATABASE = 'its'

    # Requester config defaults
    PARAM_REQ = 'Requester'
    PARAM_URL = 'url'
    PARAM_KEY = 'key'
    PARAM_DELAY = 'send_delay'
    PARAM_REQ_DIR = 'directory'
    PARAM_REQ_QUEUE_SIZE = 'queue_size'

    DEF_URL = 'https://phinau.de/trasi'
    DEF_KEY = 'seix2Iel8ohGh7noshai3aingefah9qu, vaetha1mu2zo8yahr3Ietui9fohfiequ'
    DEF_DELAY = 1
    DEF_REQ_DIR = 'its_request'
    DEF_QUEUE_SIZE = 120

    # ImageDumper config defaults
    PARAM_IMGD = 'ImageDumper'
    PARAM_IMGD_CNT = 'top_img_cnt'
    PARAM_IMGD_DIR = 'directory'

    DEF_IMGD_CNT = '10'
    DEF_IMGD_DIR = 'its_dump'

    def __init__(self, cfgPath):
        self.cfgPath = cfgPath
        self.__getConfig()

    def __getConfig(self):
        self.cfg = cfgp.ConfigParser()

        # Template erstellen
        if not os.path.exists(self.cfgPath):
            self.__createConfigTemplate()
            self.__writeConfig()

        # Config lesen
        with open(self.cfgPath, 'r') as cfgFile:
            self.cfg.read_file(cfgFile)

        self.__getRequesterConfig()
        self.__getMySqlConfig()
        self.__getImageDumperConfig()

    def __writeConfig(self):
        with open(self.cfgPath, 'w') as cfgFile:
            self.cfg.write(cfgFile)

    def __createConfigTemplate(self):
        # MySql Part
        self.cfg[ItsConfig.PARAM_MYSQL] = {
            ItsConfig.PARAM_HOST: ItsConfig.DEF_HOST,
            ItsConfig.PARAM_USER: ItsConfig.DEF_USER,
            ItsConfig.PARAM_PASS: ItsConfig.DEF_PASS,
            ItsConfig.PARAM_DATABASE: ItsConfig.DEF_DATABASE
        }

        # Requester Part
        self.cfg[ItsConfig.PARAM_REQ] = {
            ItsConfig.PARAM_URL: ItsConfig.DEF_URL,
            ItsConfig.PARAM_KEY: ItsConfig.DEF_KEY,
            ItsConfig.PARAM_DELAY: ItsConfig.DEF_DELAY,
            ItsConfig.PARAM_REQ_DIR: ItsConfig.DEF_REQ_DIR,
            ItsConfig.PARAM_REQ_QUEUE_SIZE: ItsConfig.DEF_QUEUE_SIZE
        }

        # ImageDumper Part
        self.cfg[ItsConfig.PARAM_IMGD] = {
            ItsConfig.PARAM_IMGD_CNT: ItsConfig.DEF_IMGD_CNT,
            ItsConfig.PARAM_IMGD_DIR: ItsConfig.DEF_IMGD_DIR
        }

    def isValid(self):
        # Defaults prüfen
        return True

    def isRequestValid(self):
        # Defaults prüfen ohne SQL für DebugSession
        return not(self.req_cfg.url == ItsConfig.DEF_URL or
                   self.req_cfg.url == ItsConfig.DEF_KEY)

    def __getMySqlConfig(self):
        # Mysql part
        host = None
        user = None
        passw = None
        db = None

        if self.cfg.has_option(ItsConfig.PARAM_MYSQL, ItsConfig.PARAM_HOST):
            host = self.cfg.get(ItsConfig.PARAM_MYSQL, ItsConfig.PARAM_HOST)

        if self.cfg.has_option(ItsConfig.PARAM_MYSQL, ItsConfig.PARAM_USER):
            user = self.cfg.get(ItsConfig.PARAM_MYSQL, ItsConfig.PARAM_USER)

        if self.cfg.has_option(ItsConfig.PARAM_MYSQL, ItsConfig.PARAM_PASS):
            passw = self.cfg.get(ItsConfig.PARAM_MYSQL, ItsConfig.PARAM_PASS)

        if self.cfg.has_option(ItsConfig.PARAM_MYSQL, ItsConfig.PARAM_DATABASE):
            db = self.cfg.get(ItsConfig.PARAM_MYSQL, ItsConfig.PARAM_DATABASE)

        self.sql_cfg = ItsSqlCfg(host, user, passw, db)

    def __getRequesterConfig(self):
        # Requester part
        url = None
        key = None
        delay = None
        reqDir = None
        qSize = None

        if self.cfg.has_option(ItsConfig.PARAM_REQ, ItsConfig.PARAM_URL):
            url = self.cfg.get(ItsConfig.PARAM_REQ, ItsConfig.PARAM_URL)

        if self.cfg.has_option(ItsConfig.PARAM_REQ, ItsConfig.PARAM_KEY):
            key = self.cfg.get(ItsConfig.PARAM_REQ, ItsConfig.PARAM_KEY)
            if ', ' in key:
                key = key.split(', ')

        if self.cfg.has_option(ItsConfig.PARAM_REQ, ItsConfig.PARAM_DELAY):
            delay = self.cfg.getint(ItsConfig.PARAM_REQ, ItsConfig.PARAM_DELAY)

        if self.cfg.has_option(ItsConfig.PARAM_REQ, ItsConfig.PARAM_REQ_DIR):
            reqDir = self.cfg.get(ItsConfig.PARAM_REQ, ItsConfig.PARAM_REQ_DIR)

        if self.cfg.has_option(ItsConfig.PARAM_REQ, ItsConfig.PARAM_REQ_QUEUE_SIZE):
            qSize = self.cfg.getint(ItsConfig.PARAM_REQ, ItsConfig.PARAM_REQ_QUEUE_SIZE)

        self.req_cfg = ItsReqCfg(url, key, delay, reqDir, qSize)

    def __getImageDumperConfig(self):
        outDir = None

        if self.cfg.has_option(ItsConfig.PARAM_IMGD, ItsConfig.PARAM_IMGD_CNT):
            topImgCnt = self.cfg.get(ItsConfig.PARAM_IMGD, ItsConfig.PARAM_IMGD_CNT)

        if self.cfg.has_option(ItsConfig.PARAM_IMGD, ItsConfig.PARAM_IMGD_DIR):
            outDir = self.cfg.get(ItsConfig.PARAM_IMGD, ItsConfig.PARAM_IMGD_DIR)

        
        self.imgd_cfg = ItsImgDumpCfg(outDir, topImgCnt)

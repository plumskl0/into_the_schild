# -*- coding: utf-8 -*-

import os
import configparser as cfgp
from itsmisc.itscfg.ItsMysqlConfig import ItsMysqlConfig as ItsSqlCfg
from itsmisc.itscfg.ItsRequesterConfig import ItsRequesterConfig as ItsReqCfg


class ItsConfig():

    # MySql config defaults
    PARAM_MYSQL = 'MySql'
    PARAM_HOST = 'host'
    PARAM_USER = 'user'
    PARAM_PASS = 'pass'

    DEF_HOST = 'hostip'
    DEF_USER = 'user'
    DEF_PASS = 'pass'

    # Requester config defaults
    PARAM_REQ = 'Requester'
    PARAM_URL = 'url'
    PARAM_KEY = 'key'
    PARAM_DELAY = 'delay'
    PARAM_XML = 'xml'

    DEF_URL = 'http://www.example.com'
    DEF_KEY = 'apikey'
    DEF_DELAY = 60
    DEF_XML = False

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

    def __writeConfig(self):
        with open(self.cfgPath, 'w') as cfgFile:
            self.cfg.write(cfgFile)

    def __createConfigTemplate(self):
        # MySql Part
        self.cfg[ItsConfig.PARAM_MYSQL] = {
            ItsConfig.PARAM_HOST: ItsConfig.DEF_HOST,
            ItsConfig.PARAM_USER: ItsConfig.DEF_USER,
            ItsConfig.PARAM_PASS: ItsConfig.DEF_PASS
        }

        # Requester Part
        self.cfg[ItsConfig.PARAM_REQ] = {
            ItsConfig.PARAM_URL: ItsConfig.DEF_URL,
            ItsConfig.PARAM_KEY: ItsConfig.DEF_KEY,
            ItsConfig.PARAM_DELAY: ItsConfig.DEF_DELAY,
            ItsConfig.PARAM_XML: ItsConfig.DEF_XML
        }

    def isValid(self):
        # Defaults prüfen
        return not(self.sql_cfg.host == ItsConfig.DEF_HOST or
                   self.sql_cfg.user == ItsConfig.DEF_USER or
                   self.sql_cfg.passw == ItsConfig.DEF_PASS or
                   self.req_cfg.url == ItsConfig.DEF_URL or
                   self.req_cfg.url == ItsConfig.DEF_KEY)

    def isDebugValid(self):
        # Defaults prüfen ohne SQL für DebugSession
        return not(self.req_cfg.url == ItsConfig.DEF_URL or
                   self.req_cfg.url == ItsConfig.DEF_KEY)

    def __getMySqlConfig(self):
        # Mysql part
        host = None
        user = None
        passw = None

        if self.cfg.has_option(ItsConfig.PARAM_MYSQL, ItsConfig.PARAM_HOST):
            host = self.cfg.get(ItsConfig.PARAM_MYSQL, ItsConfig.PARAM_HOST)

        if self.cfg.has_option(ItsConfig.PARAM_MYSQL, ItsConfig.PARAM_USER):
            user = self.cfg.get(ItsConfig.PARAM_MYSQL, ItsConfig.PARAM_USER)

        if self.cfg.has_option(ItsConfig.PARAM_MYSQL, ItsConfig.PARAM_PASS):
            passw = self.cfg.get(ItsConfig.PARAM_MYSQL, ItsConfig.PARAM_PASS)

        self.sql_cfg = ItsSqlCfg(host, user, passw)

    def __getRequesterConfig(self):
        # Requester part
        url = None
        key = None
        delay = None
        xmlHistory = None

        if self.cfg.has_option(ItsConfig.PARAM_REQ, ItsConfig.PARAM_URL):
            url = self.cfg.get(ItsConfig.PARAM_REQ, ItsConfig.PARAM_URL)

        if self.cfg.has_option(ItsConfig.PARAM_REQ, ItsConfig.PARAM_KEY):
            key = self.cfg.get(ItsConfig.PARAM_REQ, ItsConfig.PARAM_KEY)

        if self.cfg.has_option(ItsConfig.PARAM_REQ, ItsConfig.PARAM_DELAY):
            delay = self.cfg.getint(ItsConfig.PARAM_REQ, ItsConfig.PARAM_DELAY)

        if self.cfg.has_option(ItsConfig.PARAM_REQ, ItsConfig.PARAM_XML):
            xmlHistory = self.cfg.getboolean(
                ItsConfig.PARAM_REQ, ItsConfig.PARAM_XML)

        self.req_cfg = ItsReqCfg(url, key, delay, xmlHistory)

    def getRequesterConfig(self):
        return self.req_cfg

    def getMySqlConfig(self):
        return self.sql_cfg

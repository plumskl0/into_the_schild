# -*- coding: utf-8 -*-

import os
import configparser as cfgp


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

        if not os.path.exists(self.cfgPath):
            self.__createConfigTemplate()
            self.__writeConfig()

        with open(self.cfgPath, 'r') as cfgFile:
            self.cfg.read_file(cfgFile)
            return self.cfg

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
            ItsConfig.PARAM_KEY: ,ItsConfig.DEF_KEY,
            ItsConfig.PARAM_DELAY: ItsConfig.DEF_DELAY,
            ItsConfig.PARAM_XML: ItsConfig.DEF_XML
        }

    def isConfigCorrect(self):
        #TODO: cfg auf defaults prüfen

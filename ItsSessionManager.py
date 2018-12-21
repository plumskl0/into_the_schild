# -*- coding: utf-8 -*-

'''
   Tabellen in SQL-DB:
    - session:
        - ID:int
        - max_epochs:int
        - Info_Text:String
        - cntBaseImgs:int
        - enableImageGeneration:bool
        - cntGenerateImages:int 
'''
import os
from ItsDcgan import ItsDcgan, dirItsImages
from ItsRequester import ItsRequester, dirItsRequests
from itsmisc import ItsSessionInfo, ItsConfig
from itslogging import ItsLogger, ItsSqlLogger
from itsdb import ItsSqlConnection
class ItsSessionManager():

    CONFIG_PATH = 'its.ini'

    def __init__(self):
        self.log = ItsLogger('its_session_manager')
        self.cfg = ItsConfig(ItsSessionManager.CONFIG_PATH)
        self.ses_info = self.createDebugSession()
        # Initialisierung:
        # Dcgan und Requester aufrufen um Ordnerstruktur anzulegen
        self.checkFirstRun()
        self.sql_con = self.__createConnection()

    def __createConnection(self):
        self.log.info('Creating SQL connection...')
        sql = ItsSqlConnection(self.cfg.sql_cfg, log=self.log)
        if sql.dbExists:
            self.log.info('SQL Connection successful.')
            return sql
        else:
            self.log.info('No SQL connection. Using debug output.')
            return None

    def checkFirstRun(self):
        self.log.debug('Starting first launch check...')

        if not self.cfg.isValid():
            self.log.error('Config is not valid for normal sessions. Please modify {}'.format(
                ItsSessionManager.CONFIG_PATH))

        existsDcgan = os.path.exists(dirItsImages)
        existsReq = os.path.exists(dirItsRequests)

        if not existsDcgan or not existsReq:
            self.log.info('First launch detected: Starting folder check...')
            self.initDcgan()
            self.log.info('DCGAN ready')
            self.initRequester()
            self.log.info('Requester ready')
        self.log.debug('First run check done.')

    def initDcgan(self):
        dcgan = ItsDcgan(debug=True)
        dcgan.checkFilesAndFolders()

    def initRequester(self):
        requester = ItsRequester(self.cfg.getRequesterConfig(), debug=True)
        requester.checkFilesAndFolders()

    def startSqlDebugSession(self):
        if self.cfg.isValid: 
            self.log.info('Starting sql debug session...')

            sesInfo = self.createDebugSession()

            self.sql_con.insertSession(sesInfo)
            self.sqlLog = ItsSqlLogger(self.sql_con)

            self.dcgan = ItsDcgan()
            self.dcgan.initSessionInfo(sesInfo, self.sqlLog)
            self.dcgan.initDcgan()
            genImgsDir = self.dcgan.prepareRunFolder()

            self.req = ItsRequester(
                self.cfg.getRequesterConfig(),
                sesInfo.debug
            )
            self.req.setSession(sesInfo, self.sqlLog)
            
            if self.req.isReady:
                self.req.setSession(sesInfo)
                # Startet einen Klassifikationsthread
                self.req.classifyImgDir(genImgsDir)

                # Dcgan arbeiten lassen
                self.dcgan.start()

                # Requester stoppen
                self.req.stopRequests()
                self.log.info('Session finished.')

        else:
            self.log.error('SQL Config invalid. Check ist.ini')

    def startDebugSession(self):
        if self.cfg.isDebugValid():
            self.log.info('Starting debug session...')
            # Grundsätzlicher Aufbau:
            # 1. Session Objekt erzeugen
            # 2. Session an DCGAN und Requester übergeben
            # 3. DCGAN initialisiern
            # 4. Requester initialisieren
            #       - mit Session Objekt und Pfad der generierten Bilder
            #       - Bilder umbennen in "x_c.png" für classified
            #       - Abbruch wenn keine Bilder mehr ohne c exisiteren
            #           und die Session beendet ist
            # 4. DCGAN starten (evtl. mehrere runs)
            # 5. DCGAN beenden
            # 6. Auf Requester warten
            # 7. evtl. hier direkt eine weitere Session starten
            #   ist aber denke overkill

            sesInfo = self.createDebugSession()

            self.dcgan = ItsDcgan()
            self.dcgan.initSessionInfo(sesInfo)
            self.dcgan.initDcgan()
            genImgsDir = self.dcgan.prepareRunFolder()

            self.req = ItsRequester(
                self.cfg.getRequesterConfig(), sesInfo.debug)
            if self.req.isReady:
                self.req.setSession(sesInfo)
                # Startet einen Klassifikationsthread
                self.req.classifyImgDir(genImgsDir)

                # Dcgan arbeiten lassen
                self.dcgan.start()

                # Requester stoppen
                self.req.stopRequests()
                self.log.info('Session finished.')
        else:
            self.log.error('Invalid config. Cannot start DebugSession.')

    def createDebugSession(self):
        self.log.debug('Creating debug SessionInfo.')
        info = ItsSessionInfo()

        info.sessionNr = 0
        info.max_epoch = 10
        info.info_text = 'Debug Session with no SQL connection'
        info.cntBaseImages = -1
        info.enableImageGeneration = True
        info.cntGenerateImages = 10
        info.batch_size = 2
        info.debug = True

        return info


# Debug main
if __name__ == "__main__":
    s = ItsSessionManager()
    s.startSqlDebugSession()

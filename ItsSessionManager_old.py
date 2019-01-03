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
import numpy as np
from ItsDcgan import ItsDcgan, dirItsImages
from ItsRequester import ItsRequester, dirItsRequests
from itsmisc import ItsSessionInfo, ItsConfig
from itslogging import ItsLogger, ItsSqlLogger
from itsdb import ItsSqlConnection


class ItsSessionManager():

    def __init__(self):
        self.log = ItsLogger('its_session_manager')
        self.cfg = ItsConfig(ItsConfig.CONFIG_PATH)
        self.firstRun = False
        self.ses_info = self.createDebugSession()
        # Initialisierung:
        # Dcgan und Requester aufrufen um Ordnerstruktur anzulegen
        self.checkFirstRun()
        self.sql_con = self.__createConnection()

    def __createConnection(self):
        self.log.info('Creating SQL connection...')
        sql = ItsSqlConnection(self.cfg.sql_cfg, log=self.log)
        if sql.createdDefaultDb:
            self.firstRun = True
            self.log.error(
                'Created default database. Aborting run for debug purpose.')
            return sql
        elif sql.dbExists:
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
            self.firstRun = True
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

    def checkIfSqlSessionIsReady(self):
        return (self.cfg.isValid() and not self.firstRun and self.sql_con)

    def startSqlDebugSession(self):
        if self.checkIfSqlSessionIsReady():
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
            if not self.cfg.isValid():
                self.log.error('SQL Config invalid. Check ist.ini')
            else:
                self.log.error('Run not ready. Check the logs.')

    def startDebugSession(self):
        if self.cfg.isDebugValid() and not self.firstRun:
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
            if not self.cfg.isDebugValid():
                self.log.error('Invalid config. Cannot start DebugSession.')
            elif self.firstRun:
                self.log.error('Detected first run. Aborting for debug.')
            else:
                self.log.error('Run not ready. Check the logs.')

    def createDebugSession(self):
        self.log.debug('Creating debug SessionInfo.')
        info = ItsSessionInfo()

        info.sessionNr = 0
        info.max_epoch = 10
        info.info_text = 'Debug Session with no SQL connection'
        info.cntBaseImages = -1
        info.enableImageGeneration = True
        info.stepsHistory = 5
        info.cntGenerateImages = 1
        info.batch_size = 2
        info.debug = True

        return info

    def createAutoFindSession(self):
        self.log.debug('Creating AutoFind SessionInfo.')
        info = ItsSessionInfo()

        info.sessionNr = 0
        info.max_epoch = 25001
        info.info_text = 'AutoFind Session'
        info.cntBaseImages = -1
        info.enableImageGeneration = True
        info.stepsHistory = 100
        info.cntGenerateImages = 100
        info.batch_size = 2
        info.debug = False

        return info

    def startAutoFindSession(self):
        if self.checkIfSqlSessionIsReady():
            self.log.info('Starting AutoFind session...')

            # SessionInfo erzeugen
            afSes = self.createAutoFindSession()
            self.sql_con.insertSession(afSes)
            self.sqlLog = ItsSqlLogger(self.sql_con)
            

            # Beste Klassen holen
            maxList = self.sql_con.getMaxClasses()
            bestIds = []
            bestConfs = []
            if maxList:
                # Ids und Konfidenzen sammeln
                for e in maxList:
                    bestIds.append(e[0])
                    bestConfs.append(e[2])
            
                self.log.info('Found {} classes with mean confidence of {}')

                # Bilder holen
                imgList = self.sql_con.getImageFromRequestHistory(bestIds)

                # Bilder einzeln als Grundlage für das DCGAN nutzen
                for img in imgList:
                    # Bild doppelt als Basis eintragen, sonst gibt es Probleme
                    self.dcgan.setBaseImages([img, img])
                    # TODO: generierte Bilder in den requester_in folder schreiben
                    # TODO: Requester dauerhaft auf dem order prüfen und die 
                    #       Klassifikationen in die DB schreiben
                # Sobald fertig mal alle Bilder als Grundlage nutzen

            else:
                self.log.error('No max classes found.')
        
# Debug main
if __name__ == "__main__":
    s = ItsSessionManager()
    s.startAutoFindSession()

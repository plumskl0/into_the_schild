# -*- coding: utf-8 -*-

import re
import numpy as np
import mysql.connector as mysql


class ItsSqlConnection():

    DEFAULT_DATABASE_FILE = './itsdb/sql_scripts/create_default_database.sql'

    def __init__(self, slq_cfg, log=None):
        self.sql_cfg = slq_cfg
        self.log = log
        self.dbExists = False
        self.db_con = None
        try:
            self.__createConnection()
            self.__checkDatabase()
        except:
            pass

    def __del__(self):
        if self.db_con:
            self.db_con.rollback()
            self.db_con.close()

    def __createConnection(self):
        self.__debug('Trying to connect to database...')
        self.db_con = mysql.connect(
            host=self.sql_cfg.host,
            user=self.sql_cfg.user,
            passwd=self.sql_cfg.passw
        )
        self.__debug('Connected to database.')

    def __checkDatabase(self):
        self.__debug('Checking if database \'{}\' exists...'.format(
            self.sql_cfg.database))
        c = self.db_con.cursor()
        c.execute('SHOW DATABASES')

        # Prüfen ob die eingestellte DB vorhanden ist
        for db in c:
            if self.sql_cfg.database in db:
                self.dbExists = True

        if self.dbExists:
            self.__debug('Database \'{}\' exists'.format(
                self.sql_cfg.database))
        else:
            self.createDefaultDatabase()

    def createDefaultDatabase(self,):
        self.__debug('Database does not exist. Creating database \'{}\''.format(
            self.sql_cfg.database))
        cursor = self.db_con.cursor()
        cursor.execute('CREATE DATABASE {}'.format(self.sql_cfg.database))
        self.db_con.commit()
        cursor.close()
        self.executeFile(ItsSqlConnection.DEFAULT_DATABASE_FILE)
        self.dbExists = True

    def executeFile(self, filePath):
        self.__debug('Executing {}'.format(filePath))
        statements = []

        stmt = ''
        for line in open(filePath, encoding='utf8'):
            # Zeilenweise lesen
            stmt += line
            # ; beendet ein statement
            if ';' in line:
                statements.append(stmt)
                stmt = ''

        self.__debug('Found {} statemens'.format(len(statements)))
        self.__executeStatements(statements)
        self.__debug('Database \'{}\' created.'.format(self.sql_cfg.database))

    def __executeStatements(self, statements):
        if not self.dbExists:
            for s in statements:
                print('yoo')
                print(s)
                cursor = self.db_con.cursor()
                cursor.execute('USE {}'.format(self.sql_cfg.database))
                self.__debug('Executing Statement:\n{}'.format(s))
                s = self.__formatFileStatements(s)
                cursor.execute(s)
                self.db_con.commit()
                cursor.close()

    def __formatFileStatements(self, stmt):
        # alles in eine Zeile bringen
        stmt = re.sub('\n', ' ', stmt)
        stmt = stmt.strip()
        # Doppelte Leerzeichen entfernen
        stmt = re.sub(' +', ' ', stmt)
        return stmt

    def __getHisIdForEntry(self, itsEpochInfo):
        stmt = 'SELECT id FROM its_epoch_history WHERE '
        stmt += 'session_id = {} and epoch_nr = {} '.format(
            itsEpochInfo.sessionNr,
            itsEpochInfo.epoch
        )
        stmt += 'ORDER BY insert_date DESC LIMIT 1'

        cursor = self.__getCursor()

        self.__debugStatement(stmt)
        cursor.execute(stmt)

        hisId, = cursor.fetchone()
        cursor.close()

        return hisId

    def getEntryIdForSession(self):
        # Nächste Id holen
        stmt = 'SELECT AUTO_INCREMENT'
        stmt += ' FROM information_schema.TABLES'
        stmt += ' WHERE TABLE_SCHEMA = "{}"'.format(self.sql_cfg.database)
        stmt += ' AND TABLE_NAME = "its_session"'

        self.__debug('Executing Statement:\n{}'.format(stmt))
        cursor = self.__getCursor()

        cursor.execute(stmt)
        row = cursor.fetchone()
        cursor.close()

        curId = 1
        if row:
            curId, = row
            curId -= 1

        self.__debug('Current session id = {}'.format(curId))
        return curId

    def __getHistoryIdForRequest(self, itsRequestInfo):
        curId = 0
        if itsRequestInfo.sessionNr <= 0:
            curId = self.getEntryIdForSession()

        stmt = 'SELECT ep.id FROM its_epoch_history AS ep'
        stmt += ' WHERE ep.session_id = {} AND ep.epoch_nr = {}'.format(
            itsRequestInfo.sessionNr,
            itsRequestInfo.epoch,
        )
        stmt += ' AND ep.entry_id = {}'.format(
            curId
        )

        self.__debugStatement(stmt)
        cursor = self.__getCursor()
        cursor.execute(stmt)
        row = cursor.fetchone()
        cursor.close()
        self.__debug('Fetched row:\n{}'.format(row))

        hisId = 1
        if row:
            hisId, = row

        self.__debug('Current history ID: {}'.format(hisId))
        return hisId

    def insertSession(self, itsSessionInfo):
        self.__debug('Preparing SessionInfo for insert...')

        stmt = 'INSERT INTO its_session ('
        stmt += 'session_id, max_epoch, info_text,'
        stmt += 'cnt_base_imgs, enable_img_gen,'
        stmt += 'cnt_gen_imgs) VALUES ({},{},"{}",{},{},{})'.format(
            itsSessionInfo.sessionNr,
            itsSessionInfo.max_epoch,
            itsSessionInfo.info_text,
            itsSessionInfo.cntBaseImages,
            itsSessionInfo.enableImageGeneration,
            itsSessionInfo.cntGenerateImages
        )
        self.__debugStatement(stmt)
        cursor = self.__getCursor()
        cursor.execute(stmt)
        self.db_con.commit()
        cursor.close()

    def insertEpoch(self, itsEpochInfo):
        self.__debug('Preparing EpochInfo for insert...')
        entry_id = self.getEntryIdForSession()
        stmt = 'INSERT INTO its_epoch_history ('
        stmt += 'session_id, epoch_nr,'
        stmt += 'disc_loss, gen_loss,'
        stmt += 'disc_real_loss, disc_fake_loss,'
        stmt += 'entry_id) VALUES ({},{},{},{},{},{},{})'.format(
            itsEpochInfo.sessionNr,
            itsEpochInfo.epoch,
            itsEpochInfo.d_ls,
            itsEpochInfo.g_ls,
            itsEpochInfo.d_real_ls,
            itsEpochInfo.d_fake_ls,
            entry_id
        )
        self.__debugStatement(stmt)
        cursor = self.__getCursor()
        cursor.execute(stmt)
        self.db_con.commit()
        cursor.close()
        return self.__getHisIdForEntry(itsEpochInfo)

    def insertRequest(self, itsRequestInfo, hisId):

        self.__debug('Preparing EpochInfo for insert...')

        stmt = 'INSERT INTO its_request_history ('
        stmt += 'session_id, epoch_nr, class, max_confidence,'
        stmt += 'json_result, img_blob, his_id)'
        stmt += 'VALUES ({},{},"{}",{},"{}",%s,{})'.format(
            itsRequestInfo.sessionNr,
            itsRequestInfo.epoch,
            itsRequestInfo.nn_class,
            itsRequestInfo.max_confidence,
            itsRequestInfo.json_result,
            hisId
        )

        self.__debugStatement(stmt)
        cursor = self.__getCursor()
        cursor.execute(stmt, (itsRequestInfo.img_array.tobytes(),))
        self.db_con.commit()
        cursor.close()

    def getDistinctClassNames(self):

        # Infos aus dem View holen
        stmt = 'SELECT DISTINCT class FROM its_request_history WHERE class NOT IN ("-1", "dummy")'
        self.__debugStatement(stmt)
        cursor = self.__getCursor()
        cursor.execute(stmt)

        # Alle Klassen holen
        classList = []
        for entry in cursor:
            classList.append(entry[0])
        cursor.close()

        return classList

    def getMaxConfId(self, clsName, n=1):
        stmt = 'SELECT id FROM its_request_history WHERE class = "{}" ORDER BY max_confidence DESC LIMIT {}'.format(
            clsName, n)

        self.__debugStatement(stmt)
        cursor = self.__getCursor()
        cursor.execute(stmt)

        maxIds = []
        for entry in cursor:
            maxIds.append(entry[0])

        cursor.close()

        if n == 1:
            return maxIds[0]
        else:
            return maxIds

    def getImageFromRequestHistory(self, requestId):
        stmt = 'SELECT class, img_blob, max_confidence FROM its_request_history WHERE id = {}'.format(
            requestId)

        self.__debugStatement(stmt)
        cursor = self.__getCursor()

        cursor.execute(stmt)

        row = cursor.fetchone()

        clsName = row[0]
        imgBlob = row[1]
        maxConf = row[2]
        cursor.close()

        return (clsName, self.__convertToNumpy(imgBlob), maxConf)

    def getAutoFindImages(self):
        clsNames = self.getDistinctClassNames()
        print(clsNames)
        bestIds = []
        for c in clsNames:
            bestIds.append(self.getMaxConfId(c))

        # Tupel aus (Klasse, NumpyArray, Konfidenz)
        imgs = []
        for i in bestIds:
            imgs.append(self.getImageFromRequestHistory(i))

        return imgs

    def __getCursor(self):
        cursor = self.db_con.cursor()
        cursor.execute('use {}'.format(self.sql_cfg.database))
        return cursor

    def __debugStatement(self, stmt):

        msg = 'Executing statement:\n{}'.format(stmt)

        if self.log:
            self.log.info(msg)
        else:
            print(msg)

    def __debug(self, msg):
        if self.log:
            self.log.debug(msg)
        else:
            print(msg)

    def __convertToNumpy(self, imgBlob):
        # Erst mal hardcoded, evtl. später anders
        return np.frombuffer(imgBlob, dtype=np.uint8).reshape((64, 64, 3))


if __name__ == "__main__":
    con = ItsSqlConnection('./its.ini')
    # con.createDefaultDatabase()

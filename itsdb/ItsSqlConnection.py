# -*- coding: utf-8 -*-

import re
import mysql.connector as mysql


class ItsSqlConnection():

    DEFAULT_DATABASE_FILE = './itsdb/sql_scripts/create_default_database.sql'

    def __init__(self, slq_cfg, log=None):
        self.sql_cfg = slq_cfg
        self.log = log
        self.dbExists = False
        try:
            self.__createConnection()
            self.__checkDatabase()
        except:
            pass

    def debugConnection(self, host, user, passw):
        self.__debug('Trying to connect to database...')
        self.db_con = mysql.connect(
            host=host,
            user=user,
            passwd=passw
        )
        self.__debug('Connected to database.')
        self.its_cur = self.db_con.cursor()
        self.dbExists = True

    def __createConnection(self):
        self.__debug('Trying to connect to database...')
        self.db_con = mysql.connect(
            host=self.sql_cfg.host,
            user=self.sql_cfg.user,
            passwd=self.sql_cfg.passw
        )
        self.__debug('Connected to database.')

    def __checkDatabase(self):
        self.__debug('>>>>>>>>>>>>>>>>>>><Checking if Database exists...')
        c = self.db_con.cursor()
        c.execute('SHOW DATABASES')

        # Prüfen ob die eingestellte DB vorhanden ist
        for db in c:
            if self.sql_cfg.database in db:
                self.dbExists = True
                self.its_cur = c

        if self.dbExists:
            self.__debug('USE {}'.format(self.sql_cfg.database))
            self.its_cur.execute('USE {}'.format(self.sql_cfg.database))

        self.__debug('Database exists is \'{}\''.format(self.dbExists))
        if not self.dbExists:
            self.its_cur = c
            self.createDefaultDatabase()

    def createDefaultDatabase(self,):
        self.__debug('Database does not exist. Creating default...')
        self.executeFile(ItsSqlConnection.DEFAULT_DATABASE_FILE)
        self.its_cur.execute('USE its')
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

    def __executeStatements(self, statements):
        if not self.dbExists:
            for s in statements:
                self.__debug('Executing Statement:\n{}'.format(s))
                s = self.__formatStatements(s)
                self.its_cur.execute(s)
                self.db_con.commit()

    def __formatStatements(self, stmt):
        # alles in eine Zeile bringen
        stmt = re.sub('\n', ' ', stmt)
        stmt = stmt.strip()
        # Doppelte Leerzeichen entfernen
        stmt = re.sub(' +', ' ', stmt)
        return stmt

    def __debug(self, msg):
        if self.log:
            self.log.debug(msg)
        else:
            print(msg)

    def __getHistoryIdForRequest(self, itsRequestInfo):
        curId = 0
        if itsRequestInfo.sessionNr < 0:
            curId = self.getEntryIdForSession()

        stmt = 'SELECT ep.id FROM its_epoch_history AS ep'
        stmt += ' WHERE ep.session_id = {} AND ep.epoch_nr = {}'.format(
            itsRequestInfo.sessionNr,
            itsRequestInfo.epoch,
        )
        stmt += ' AND ep.entry_id = {}'.format(
            curId
        )

        self.__debug('Executing Statement:\n{}'.format(stmt))
        self.its_cur.execute(stmt)
        row = self.its_cur.fetchone()

        hisId = 1
        if row:
            hisId, = row

        self.__debug('Current history ID: {}'.format(hisId))
        return hisId

    def getEntryIdForSession(self):
        # Nächste Id holen
        stmt = 'SELECT AUTO_INCREMENT'
        stmt += ' FROM information_schema.TABLES'
        stmt += ' WHERE TABLE_SCHEMA = "its"'
        stmt += ' AND TABLE_NAME = "its_session"'

        self.__debug('Executing Statement:\n{}'.format(stmt))
        self.its_cur.execute(stmt)
        row = self.its_cur.fetchone()

        curId = 1
        if row:
            curId, = row
            curId -= 1

        self.__debug('Current session id = {}'.format(curId))
        return curId

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
        self.__debug('Executing statement:\n{}'.format(stmt))
        self.its_cur.execute(stmt)
        self.db_con.commit()

    def insertEpoch(self, itsEpochInfo):
        self.__debug('Preparing EpochInfo for insert...')

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
            itsEpochInfo.entry_id
        )
        print('>>>>>>>>>>>>>>>>>>>>>>>>> ' + stmt)
        self.__debug('Executing statement:\n{}'.format(stmt))
        self.its_cur.execute(stmt)
        self.db_con.commit()

    def insertRequest(self, itsRequestInfo):

        self.__debug('Preparing EpochInfo for insert...')

        # Zunächst History ID über SessionEntry ermitteln
        his_id = self.__getHistoryIdForRequest(itsRequestInfo)

        stmt = 'INSERT INTO its.its_request_history ('
        stmt += 'session_id, epoch_nr, class, max_confidence,'
        stmt += 'json_result, img_array, dtype_img, his_id)'
        stmt += 'VALUES ({},{},"{}",{},"{}","{}","{}",{})'.format(
            itsRequestInfo.sessionNr,
            itsRequestInfo.epoch,
            itsRequestInfo.nn_class,
            itsRequestInfo.max_confidence,
            itsRequestInfo.json_result,
            itsRequestInfo.img_array,
            itsRequestInfo.img_dtyp,
            his_id
        )

        self.__debug('Executing statement:\n{}'.format(stmt))
        self.its_cur.execute(stmt)
        self.db_con.commit()


if __name__ == "__main__":
    con = ItsSqlConnection(None)
    con.debugConnection('192.168.88.129', 'root', '1212')
    # con.createDefaultDatabase()

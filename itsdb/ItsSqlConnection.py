# -*- coding: utf-8 -*-

import re
import mysql.connector as mysql


class ItsSqlConnection():

    DEFAULT_DATABASE_FILE = './sql_scripts/create_default_database.sql'

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
        self.db = mysql.connect(
            host=host,
            user=user,
            passwd=passw
        )
        self.__debug('Connected to database.')
        self.its_cur = self.db.cursor()
        self.dbExists = True

    def __createConnection(self):
        self.__debug('Trying to connect to database...')
        self.db = mysql.connect(
            host=self.sql_cfg.host,
            user=self.sql_cfg.user,
            passwd=self.sql_cfg.passw
        )
        self.__debug('Connected to database.')

    def __checkDatabase(self):
        self.__debug('Checking if Database exists...')
        c = self.db.cursor()
        c.execute('SHOW DATABASES')

        # Prüfen ob die eingestellte DB vorhanden ist
        for db in c:
            if self.sql_cfg.database in db:
                self.dbExists = True
                self.its_cur = c.execute(
                    'USE {}'.format(self.sql_cfg.database))

        self.__debug('Database exists is \'{}\''.format(self.dbExists))
        if not self.dbExists:
            self.createDefaultDatabase()

    def createDefaultDatabase(self,):
        self.__debug('Database does not exist. Creating default...')
        self.executeFile(ItsSqlConnection.DEFAULT_DATABASE_FILE)

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
        if self.dbExists:
            for s in statements:
                self.__debug('Executing Statement:\n{}'.format(s))
                s = self.__formatStatements(s)
                self.its_cur.execute(s)
                self.db.commit()

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


if __name__ == "__main__":
    con = ItsSqlConnection(None)
    # con.debugConnection('127.0.0.1', 'user', 'pass')
    # con.createDefaultDatabase()

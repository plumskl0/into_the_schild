# -*- coding: utf-8 -*-

from itslogging.ItsLogger import ItsLogger


class ItsSqlLogger():

    def __init__(self, db_con, log):
        self.log = log
        self.db_con = db_con

    def logSessionInfo(self, itsSessionInfo):
        self.log.debugSessionInfo(itsSessionInfo)

        self.db_con.insertSession(itsSessionInfo)

    def logEpochInfo(self, itsEpochInfo):
        self.log.debug('Logging EpochInfo...')
        self.log.debugEpochInfo(itsEpochInfo)

        return self.db_con.insertEpoch(itsEpochInfo)

    def logRequestInfo(self, itsRequestInfo, hisId):
        self.log.debug('Logging RequestInfo...')
        self.log.infoRequestInfo(itsRequestInfo, hisId)
        
        self.db_con.insertRequest(itsRequestInfo, hisId)


if __name__ == '__main__':
    print('Debugging mode for SQL-Logger')

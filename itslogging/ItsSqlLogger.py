# -*- coding: utf-8 -*-

from itslogging.ItsLogger import ItsLogger


class ItsSqlLogger(ItsLogger):

    def __init__(self, db_con, logName='its_sql'):
        super().__init__(logName=logName)
        
        self.db_con = db_con

    def logSessionInfo(self, itsSessionInfo):
        self.debugSessionInfo(itsSessionInfo)

        self.db_con.insertSession(itsSessionInfo)

    def logEpochInfo(self, itsEpochInfo):
        self.debug('Logging EpochInfo...')
        self.debugEpochInfo(itsEpochInfo)

        return self.db_con.insertEpoch(itsEpochInfo)

    def logRequestInfo(self, itsRequestInfo, hisId):
        self.debug('Logging RequestInfo...')
        self.infoRequestInfo(itsRequestInfo, hisId)
        
        self.db_con.insertRequest(itsRequestInfo, hisId)


if __name__ == '__main__':
    print('Debugging mode for SQL-Logger')

# -*- coding: utf-8 -*-

from itslogging.ItsLogger import ItsLogger


class ItsSqlLogger(ItsLogger):

    def __init__(self, db_con):
        super().__init__(logName='its_sql', debug=False)
        
        self.db_con = db_con

    def logSessionInfo(self, itsSessionInfo):

        if itsSessionInfo.debug:
            self.debugSessionInfo(itsSessionInfo)

        self.db_con.insertSession(itsSessionInfo)

    def logEpochInfo(self, itsEpochInfo):
        self.debug('Logging EpochInfo...')

        if self.debug:
            self.debugEpochInfo(itsEpochInfo)

        self.db_con.insertEpoch(itsEpochInfo)

    def logRequestInfo(self, itsRequestInfo):
        self.debug('Logging RequestInfo...')

        if self.debug:
            self.infoRequestInfo(itsRequestInfo)
        
        self.db_con.insertRequest(itsRequestInfo)


if __name__ == '__main__':
    print('Debugging mode for SQL-Logger')

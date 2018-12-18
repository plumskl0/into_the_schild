# -*- coding: utf-8 -*-
'''
    SQL Logger Prototyp

    Tabellen in SQL-DB:
    - session:
        - ID:int
        - max_epochs:int
        - Info_Text:String
        - cntBaseImgs:int
        - enableImageGeneration:boolean
        - cntGenerateImages:int
    - epoch_history:
        - id_session:int
        - epoch:int
        - d_ls:float
        - g_ls:float
        - d_real_ls:float
        - d_fake_ls:floast
    - request_history:
        - id_session:int
        - epoch:int
        - json_result:string
        - max_confidence:float
        - img_array:string
        - img_dtype:string
'''

from itslogging.ItsLogger import ItsLogger


class ItsSqlLogger(ItsLogger):

    def logSessionInfo(self, itsSessionInfo):
        pass

    def logEpochInfo(self, itsEpochInfo):
        self.debug('Logging EpochInfo...')

        # Hier kommt der SQL-Teil rein
        # Debugmodus Output:
        if self.debug:
            self.debugEpochInfo(itsEpochInfo)

    def logRequestInfo(self, itsRequestInfo):
        self.debug('Logging RequestInfo...')

        # Hier kommt der SQL-Teil rein

        # Debugmodus Output:
        if self.debug:
            self.debugRequestInfo(itsRequestInfo)


if __name__ == '__main__':
    print('Debugging mode for SQL-Logger')

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


class ItsSessionInfo():

    def __init__(
        self,
        sessionNr = -1,
        max_epoch = -1,
        info_text = -1,
        enableImageGeneration = -1,
        cntGenerateImages = -1
    ):
        self.sessionNr = sessionNr
        self.max_epoch = max_epoch
        self.info_text = info_text
        self.enableImageGeneration = enableImageGeneration
        self.cntGenerateImages = cntGenerateImages

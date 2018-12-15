# -*- coding: utf-8 -*-
'''
    Tabellen in SQL-DB:
    - request_history:
        - id_session:int
        - epoch:int
        - json_result:string
        - max_confidence:float
        - img_array:string
        - img_dtype:string
'''


class ItsRequestInfo():

    def __init__(
        self,
        sessionNr = -1,
        epoch = -1,
        json_result = -1,
        max_confidence = -1,
        img_array = -1,
        img_dtype = -1
    ):
        self.sessionNr = sessionNr
        self.epoch = epoch
        self.json_result = json_result
        self.max_confidence = max_confidence
        self.img_array = img_array
        self.img_dtyp = img_dtype

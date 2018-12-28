# -*- coding: utf-8 -*-
'''
    Tabellen in SQL-DB:
    - request_history:
        - id_session:int
        - epoch:int
        - nn_class:string
        - max_confidence:float
        - json_result:string
        - img_array:string
        - img_dtype:string
'''


class ItsRequestInfo():

    def __init__(
        self,
        sessionNr=-1,
        epoch=-1,
        nn_class=-1,
        max_confidence=-1,
        json_result=-1,
        img_array=-1,
        img_dtype=-1
    ):
        self.sessionNr = sessionNr
        self.epoch = epoch
        self.nn_class = nn_class
        self.max_confidence = max_confidence
        self.json_result = json_result
        self.img_array = img_array
        self.img_dtype = img_dtype

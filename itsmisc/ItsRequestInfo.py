# -*- coding: utf-8 -*-

class ItsRequestInfo():

    def __init__(
        self,
        sessionNr=-1,
        epoch=-1,
        nn_class=-1,
        max_confidence=-1,
        json_result=-1,
        img_blob=-1,
    ):
        self.sessionNr = sessionNr
        self.epoch = epoch
        self.nn_class = nn_class
        self.max_confidence = max_confidence
        self.json_result = json_result
        self.img_blob = img_blob

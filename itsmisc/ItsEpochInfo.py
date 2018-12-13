# -*- coding: utf-8 -*-

class ItsEpochInfo():

    def __init__(
        self,
        sessionNr,
        max_epochs,
        n_noise,
        cntBaseImages,
        cntGenerateImages,
    ):
        self.sessionNr = sessionNr
        self.max_epochs = max_epochs
        self.n_noise = n_noise
        self.cntBaseImages = cntBaseImages
        self.cntGenerateImages = cntGenerateImages

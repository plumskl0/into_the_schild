# -*- coding: utf-8 -*-

class ItsEpochInfo():

    # max_epochs = property(get_x, set_x)
    # n_noise = property(get_x, set_x)
    # cntBaseImages = property(get_x, set_x)
    # cntGenerateImages = property(get_x, set_x)

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

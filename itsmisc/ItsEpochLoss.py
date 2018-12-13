# -*- coding: utf-8 -*-


class ItsEpochLoss():

    def __init__(
        self,
        sessionNr,
        epoch,
        d_ls,
        g_ls,
        d_real_ls,
        d_fake_ls
    ):
        self.sessionNr = sessionNr
        self.epoch = epoch
        self.d_ls = d_ls
        self.g_ls = g_ls
        self.d_real_ls = d_real_ls
        self.d_fake_ls = d_fake_ls

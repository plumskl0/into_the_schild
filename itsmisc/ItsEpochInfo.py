# -*- coding: utf-8 -*-
'''
    Tabelle in SQL-DB:
    - epoch_history:
        - id_session:int
        - epoch:int
        - d_ls:float
        - g_ls:float
        - d_real_ls:float
        - d_fake_ls:float
'''


class ItsEpochInfo():

    def __init__(
        self,
        sessionNr=-1,
        epoch=-1,
        batch_size=-1,
        d_ls=-1,
        g_ls=-1,
        d_real_ls=-1,
        d_fake_ls=-1
    ):
        self.sessionNr = sessionNr
        self.epoch = epoch
        self.batch_size = batch_size
        self.d_ls = d_ls
        self.g_ls = g_ls
        self.d_real_ls = d_real_ls
        self.d_fake_ls = d_fake_ls

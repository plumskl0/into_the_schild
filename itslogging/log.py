# -*- coding: utf-8 -*-
'''
    Logger für unser Projekt.
'''
import logging


class ItsLogger(logging.LoggerAdapter):

    def __init__(self, logName='its_log', level=logging.INFO, debug=True):

        logFormat = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s')

        self.handler = None
        if debug:
            # Beim Debugging alles im Terminal ausgeben
            level = logging.DEBUG
            self.handler = logging.StreamHandler()
            self.handler.setFormatter(logFormat)
        else:
            # Ohne Debugging INFO Level in Datei schreiben
            self.handler = logging.FileHandler(logName+'.log')

        # Logger erzeugen
        self.lgr = logging.getLogger(logName)
        self.lgr.setLevel(level)
        self.lgr.addHandler(self.handler)
        super().__init__(self.lgr, {})


    def __del__(self):
        self.lgr.removeHandler(self.handler)
        self.handler.close()
    

    def infoEpoch(self, itsEpochInfo):
        self.lgr.debug('Preparing epcoh info...')
        msg = 'Session {} : Max Epochs: {}, Image base: {}, Image Generation: {}'.format(
            itsEpochInfo.sessionNr,
            itsEpochInfo.max_epochs,
            itsEpochInfo.cntBaseImages,
            itsEpochInfo.cntGenerateImages
        )
        self.lgr.info(msg)


if __name__ == '__main__':
    print('Debugging mode for Logger')

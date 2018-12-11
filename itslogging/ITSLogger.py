# -*- coding: utf-8 -*-
'''
    Logger für unser Projekt.
'''
import logging


class ITSLogger(logging.LoggerAdapter):

    def __init__(self, logName='its_log', level=logging.INFO, debug=True):

        logFormat = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s')

        handler = None
        if debug:
            # Beim Debugging alles im Terminal ausgeben
            level = logging.DEBUG
            handler = logging.StreamHandler()
            handler.setFormatter(logFormat)
        else:
            # Ohne Debugging INFO Level in Datei schreiben
            handler = logging.FileHandler(logName+'.log')

        # Logger erzeugen
        lgr = logging.getLogger(logName)
        lgr.setLevel(level)
        lgr.addHandler(handler)
        super().__init__(lgr, {})


if __name__ == '__main__':
    print('Debugging mode for Logger')

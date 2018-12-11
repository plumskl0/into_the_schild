# -*- coding: utf-8 -*-
'''
    Logger für unser Projekt.
'''

import logging

logFormatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

def initLogger(logName='ist_log', level=logging.INFO, debug=True):

    handler = None
    
    if debug:
        # Beim Debugging alles im Terminal ausgeben
        level = logging.DEBUG
        handler = logging.StreamHandler()
        handler.setFormatter(logFormatter)
    else:
        # Ohne Debugging INFO Level in Datei schreiben
        handler = logging.FileHandler(logName+'.log')
        
    # Logger erzeugen
    log = logging.getLogger(logName)
    log.setLevel(level)
    log.addHandler(handler)
    
    return log
    
if __name__ == '__main__':
    print('Debugging mode for Logger')

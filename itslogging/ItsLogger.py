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
        else:
            # Ohne Debugging INFO Level in Datei schreiben
            self.handler = logging.FileHandler(logName+'.log')

        self.handler.setFormatter(logFormat)
        
        # Logger erzeugen
        self.lgr = logging.getLogger(logName)
        self.lgr.setLevel(level)
        self.lgr.addHandler(self.handler)
        super().__init__(self.lgr, {})

    def __del__(self):
        self.lgr.removeHandler(self.handler)
        self.handler.close()

    def infoEpoch(self, itsEpochInfo):
        self.lgr.debug('Preparing EpochInfo...')
        msg = 'Session: {}, Max Epochs: {}, Image base: {}, Image Generation: {}'.format(
            itsEpochInfo.sessionNr,
            itsEpochInfo.max_epochs,
            itsEpochInfo.cntBaseImages,
            itsEpochInfo.cntGenerateImages
        )
        self.lgr.info(msg)

    def debugEpochLosses(self, epochLoss):
        self.lgr.debug('Preparing epoch loss..')

        self.lgr.debug(' Session {}, Epoch {}:'.rjust(24, ' ').format(
            epochLoss.sessionNr,
            epochLoss.epoch
        ))

        self.lgr.debug('Discriminator loss:'.rjust(22, ' ') + '\t{}'.format(
            epochLoss.d_ls
        ))

        self.lgr.debug('Generator loss:'.rjust(22, ' ') + '\t{}'.format(
            epochLoss.g_ls
        ))

        self.lgr.debug('Disc real loss:'.rjust(22, ' ') + '\t{}'.format(
            epochLoss.d_real_ls
        ))

        self.lgr.debug('Disc fake loss:'.rjust(22, ' ') + '\t{}'.format(
            epochLoss.d_fake_ls
        ))


if __name__ == '__main__':
    print('Debugging mode for Logger')

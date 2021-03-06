# -*- coding: utf-8 -*-
'''
    Dummy Logger für unser Projekt.
'''
import logging


class ItsLogger(logging.LoggerAdapter):

    def __init__(self, logName='its_log', level=logging.DEBUG, outDir=None):

        logFormat = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s')

        if outDir:
            logFile = outDir + '/' + logName + '.log' 
        else:
            logFile = logName + '.log'

        # Ohne Debugging INFO Level in Datei schreiben
        self.handler = logging.FileHandler(logFile)

        self.handler.setFormatter(logFormat)

        # Logger erzeugen
        self.lgr = logging.getLogger(logName)
        self.lgr.setLevel(level)
        self.lgr.addHandler(self.handler)
        super().__init__(self.lgr, {})

    def __del__(self):
        self.lgr.removeHandler(self.handler)
        self.handler.close()

    def debugSessionInfo(self, itsSessionInfo):
        self.debug('Creating Session Info...')

        msg = 'Session {} Settings:\n'
        msg += '\tInfo: \t{}\n'
        msg += '\tGen. images: \t{}\n'
        msg += '\tBatch size: \t{}\n'
        msg += '\tDebug: \t{}\n'

        msg.format(
            itsSessionInfo.sessionNr,
            itsSessionInfo.max_epoch,
            itsSessionInfo.info_text,
            itsSessionInfo.enableImageGeneration,
            itsSessionInfo.cntGenerateImages,
            itsSessionInfo.batch_siz,
            itsSessionInfo.debug
        )

        self.debug(msg)

    def infoRequestInfo(self, itsRequestInfo, hisId=None):

        if hisId:
            self.lgr.info('Classification for His ID {}:'.format(hisId))
        self.lgr.info('{}\t{:2.2f}%'.format(
            itsRequestInfo.nn_class,
            itsRequestInfo.max_confidence*100
        ))

    def debugEpochInfo(self, itsEpochInfo):
        self.lgr.debug(' Session {}, Epoch {}:'.rjust(24, ' ').format(
            itsEpochInfo.sessionNr,
            itsEpochInfo.epoch
        ))

        self.lgr.debug('Batch size:'.rjust(22, ' ') + '\t{:1d}'.format(
            itsEpochInfo.batch_size
        ))

        self.lgr.debug('Discriminator loss:'.rjust(22, ' ') + '\t{}'.format(
            itsEpochInfo.d_ls
        ))

        self.lgr.debug('Generator loss:'.rjust(22, ' ') + '\t{}'.format(
            itsEpochInfo.g_ls
        ))

        self.lgr.debug('Disc real loss:'.rjust(22, ' ') + '\t{}'.format(
            itsEpochInfo.d_real_ls
        ))

        self.lgr.debug('Disc fake loss:'.rjust(22, ' ') + '\t{}'.format(
            itsEpochInfo.d_fake_ls
        ))


if __name__ == '__main__':
    print('Debugging mode for Logger')

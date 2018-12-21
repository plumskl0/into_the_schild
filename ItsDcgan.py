# -*- coding: utf-8 -*-
from itsmisc import ItsSessionInfo
'''
    Ein DCGAN auf Basis von Code by Parag Mital (github.com/pkmital/CADL).

    Wir haben sieben Beispielbilder, die wir als Datengrundlage nutzen. Die Bilder
    werden in verschiedenen Ordnern (Kategorie) als erstes Bild abgelegt und zum
    Trainieren des Generators und Discriminators genutzt.

    Nach einigen Epochen werden fünf Bilder aus jeder Kategorie vom Discriminator gewählt
    und an den Requester gegeben. Der Requester schickt die generierten Daten an das
    NeuronaleNetz der Aufgabe und gibt uns die Klassifikationswerte an.

    Im ersten Versuch wird das DCGAN nach einingen Epochen Bilder generieren, die in die
    Datengrundlage aufgenommen werden. Mithilfe dieses Durchlaufs ermitteln wir ob das
    DCGAN mit einer möglichst simplen Methode "gute" Bilder erzeugen wird.

    Gute Bilder sind Bilder die vom Klassifkationsnetz der Aufgabe mit einer möglichst
    hohen Konfidenz bewertet.

    Es sind bereits weitere Abläufe geplant, die eine etwas voreingenommene Auswahl
    von Bildern nutzen wird. Aber das kommt später.

    Zum nachvollziehen der Entwicklung wird eine Historie der Losswerte und
    Bewertung des NN erzeugt. Die Aufgabe könnte jedoch im Requester implementiert
    werden.

    Benötigte Ordnersturktur:
    its_images
        - Ordner mit den Beispielbildern
        - hier werden auch die vom DCGAN generierten Bilder abgelegt
        - Unterordner:
            - Kategorien Ordner     - Kategorie in die ein Bild fällt
                - Zunächst einfache Namensgebung mit Zahlen
                - TODO: evtl. ein Mapping der Kategorie und Ordner erstellen
            - /generated_epoch_x     - nach X Epochen generierte Bilder
            -
    its_dcgan.ini
        - Konfigurationsdatei um später einfacher verschiedene DCGANs zu testen
        - TODO: evtl. eine Kofigurationsdatei erzeugen für Requester umd DCGAN
'''

import os
import time
import imageio
import logging
import numpy as np
import tensorflow as tf
from itslogging import ItsLogger, ItsSqlLogger
from itsmisc import ItsEpochInfo

dirItsImages = './its_images'


class ItsDcgan():

    def __init__(self, sessionNr='0', debug=True):
        self.logName = 'its_dcgan'
        self.log = ItsLogger(logName=self.logName, debug=debug)
        self.cnt_runs = 0
        self.sessionNr = sessionNr
        self.readyDcgan = False
        self.readyEpoch = False
        self.readyRunFolder = False

        # Ordner
        self.dirItsImages = './its_images'
        self.dirSession = os.path.join(
            self.dirItsImages,
            'session_{}'.format(self.sessionNr)
        )
        self.dirBaseImgs = os.path.join(self.dirItsImages, 'base_images')

        self.sess = None
        self.sqlLog = None

    def __del__(self):
        self.log.debug('Killing Itsdcgan...')
        if self.sess:
            self.sess.close()
            del self.sess
        self.log.debug('Itsdcgan killed.')
        del self.log

    def initSessionInfo(self, itsSessionInfo, sqlLog=None):
        self.__init__(
            itsSessionInfo.sessionNr
        )

        if sqlLog:
            self.sqlLog = sqlLog

        self.initEpoch(
            epochs=itsSessionInfo.max_epoch,
            batch_size=itsSessionInfo.batch_size,
            enableImageGeneration=itsSessionInfo.enableImageGeneration,
            cntGenerateImages=itsSessionInfo.cntGenerateImages
        )

    def initEpoch(
        self, epochs=10, n_noise=64, batch_size=2,
        stepsHistory=50, enableImageGeneration=False,
        cntGenerateImages=40
    ):
        self.log.info('Initializing epoch...')
        self.max_epochs = epochs
        self.n_noise = n_noise
        self.index_in_epoch = 0
        self.epochs_completed = 0
        self.epochPrintSteps = 2

        # Batchsize ist am Anfang so groß wie die Datenbasis
        self.batch_size = batch_size

        # Informationsoutput alle Epochen
        self.stepsHistory = stepsHistory
        # Anzahl der Generierten Bilder pro ImageGeneration
        self.enableImageGeneration = enableImageGeneration
        if self.enableImageGeneration:
            self.cntGenerateImages = cntGenerateImages
        else:
            self.cntGenerateImages = 0

        self.checkFilesAndFolders()

        self.images, self.labels = self.generateBaseData()
        # Erst mal noch hardcoded
        self.imgShape = [None, 64, 64, 3]

        # Anzahl der Bilder in der Basis
        self.cntBaseImages = len(self.images)
        if self.cntBaseImages:
            self.log.info('Epoch initialized.')
            # Fehler abfangen falls man weniger Bilder als Batchsize hat
            if self.batch_size > self.cntBaseImages:
                self.batch_size = self.cntBaseImages

            self.log.debugEpochInfo(self.getEpochInfo())
            self.readyEpoch = True
        else:
            self.log.error(
                'Epoch could not be initalized: No BaseImages found')

    def checkFilesAndFolders(self):
        if not os.path.exists(self.dirBaseImgs):
            self.createDir(self.dirBaseImgs)

    def getEpochInfo(
        self, epoch=-1, d_ls=-1,
        g_ls=-1, d_real_ls=-1,
        d_fake_ls=-1, entry_id=1
    ):
        self.log.info('Generating EpochInfo...')
        return ItsEpochInfo(
            self.sessionNr, epoch,
            self.batch_size,
            d_ls, g_ls,
            d_real_ls, d_fake_ls,
            entry_id
        )

    def initDcgan(self):
        if self.readyEpoch:
            self.log.info('Initializing DCGAN...')
            tf.reset_default_graph()

            self.x_in = tf.placeholder(
                dtype=tf.float32, shape=self.imgShape, name='x_in')
            self.noise = tf.placeholder(
                dtype=tf.float32, shape=[None, self.n_noise])

            self.keep_prob = tf.placeholder(dtype=tf.float32, name='keep_prob')
            self.is_training = tf.placeholder(
                dtype=tf.bool, name='is_training')

            self.g = self.generator(self.noise)
            d_real = self.discriminator(self.x_in)
            d_fake = self.discriminator(self.g, reuse=True)

            vars_g = [var for var in tf.trainable_variables(
            ) if var.name.startswith("generator")]
            vars_d = [var for var in tf.trainable_variables(
            ) if var.name.startswith("discriminator")]

            d_reg = tf.contrib.layers.apply_regularization(
                tf.contrib.layers.l2_regularizer(1e-6), vars_d)
            g_reg = tf.contrib.layers.apply_regularization(
                tf.contrib.layers.l2_regularizer(1e-6), vars_g)

            self.loss_d_real = self.binary_cross_entropy(
                tf.ones_like(d_real), d_real)
            self.loss_d_fake = self.binary_cross_entropy(
                tf.zeros_like(d_fake), d_fake)

            self.loss_g = tf.reduce_mean(self.binary_cross_entropy(
                tf.ones_like(d_fake), d_fake))
            self.loss_d = tf.reduce_mean(
                0.5 * (self.loss_d_real + self.loss_d_fake))

            update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS)
            with tf.control_dependencies(update_ops):
                self.optimizer_d = tf.train.RMSPropOptimizer(
                    learning_rate=0.00015).minimize(self.loss_d + d_reg, var_list=vars_d)
                self.optimizer_g = tf.train.RMSPropOptimizer(
                    learning_rate=0.00015).minimize(self.loss_g + g_reg, var_list=vars_g)

            self.sess = tf.Session()
            self.sess.run(tf.global_variables_initializer())
            self.readyDcgan = True
            self.log.info('DCGAN initialized.')
        else:
            self.log.error('DCGAN not initialized. Epoch not yet ready.')

    def createRunFolder(self):
        self.log.info('Creating Session/Run Folder...')

        name = 'gen_imgs_run_{}'.format(self.cnt_runs)
        self.dirRunImages = os.path.join(self.dirSession, name)
        self.createDir(self.dirItsImages, self.dirRunImages, self.dirBaseImgs)
        return self.dirRunImages

    def createDir(self, *args):
        for d in args:
            if not os.path.exists(d):
                self.log.debug('Creating Dir: {}'.format(d))
                os.makedirs(d)

    def generateBaseData(self):
        self.log.info('Loading base images...')
        imgs, lbls = self.loadBaseDir()
        self.log.info('Loaded {} images.'.format(len(imgs)))

        # Bilder von 0-255 auf 0-1 bringen
        imgs = np.array(imgs)
        imgs = imgs.astype(np.float32)
        imgs = np.multiply(imgs, 1.0 / 255.0)

        return imgs, np.array(lbls)

    def loadBaseDir(self):

        imgs = []
        lbls = []

        for root, _, files in os.walk(self.dirBaseImgs):
            for f in files:
                imgPath = os.path.join(root, f)
                img, lbl = self.loadImage(imgPath)

                imgs += img
                lbls += lbl

        return imgs, lbls

    def loadImage(self, imgPath):
        img = []
        lbl = []
        if '.png' in str.lower(imgPath):
            self.log.debug('Loading Image {}'.format(imgPath))

            # Bild als Numpy-Array einlesen
            imgArr = imageio.imread(imgPath)
            img.append(imgArr)
            lbl.append(1)

        return img, lbl

    def next_batch(self):
        start = self.index_in_epoch
        self.index_in_epoch += self.batch_size
        if self.index_in_epoch > self.cntBaseImages:
            # Finished epoch
            self.epochs_completed += 1

            # Shuffle data
            perm = np.arange(self.cntBaseImages)
            np.random.shuffle(perm)
            self.images = self.images[perm]
            self.labels = self.labels[perm]

            # Start next epoch
            start = 0
            self.index_in_epoch = self.batch_size
            assert self.batch_size <= self.cntBaseImages
        end = self.index_in_epoch
        return self.images[start:end], self.labels[start:end]

    def lrelu(self, x):
        return tf.maximum(x, tf.multiply(x, 0.2))

    def binary_cross_entropy(self, x, z):
        eps = 1e-12
        return (-(x * tf.log(z + eps) + (1. - x) * tf.log(1. - z + eps)))

    def discriminator(self, img_in, reuse=None):
        activation = self.lrelu
        with tf.variable_scope('discriminator', reuse=reuse):
            self.log.debug('img_in : {}'.format(img_in))
            x = tf.reshape(img_in, shape=[-1, 64, 64, 3])
            self.log.debug('reshaped img_in : {}'.format(x))
            x = tf.layers.conv2d(x, kernel_size=5, filters=64, strides=2,
                                 padding='same', activation=activation)
            x = tf.layers.dropout(x, self.keep_prob)
            x = tf.layers.conv2d(x, kernel_size=5, filters=64, strides=1,
                                 padding='same', activation=activation)
            x = tf.layers.dropout(x, self.keep_prob)
            x = tf.layers.conv2d(x, kernel_size=5, filters=64, strides=1,
                                 padding='same', activation=activation)
            x = tf.layers.dropout(x, self.keep_prob)
            x = tf.layers.dense(x, units=128, activation=activation)
            x = tf.layers.dense(x, units=1, activation=tf.nn.sigmoid)
        return x

    def generator(self, z):
        activation = self.lrelu
        momentum = 0.99
        with tf.variable_scope('generator', reuse=None):
            x = z
            d1 = 4
            d2 = 3
            x = tf.layers.dense(x, units=d1*d1*d2, activation=activation)
            x = tf.layers.dropout(x, self.keep_prob)
            x = tf.contrib.layers.batch_norm(x, is_training=self.is_training,
                                             decay=momentum)
            x = tf.reshape(x, shape=[-1, d1, d1, d2])

            # Hier hat man ein 8x8 Grundbild
            x = tf.image.resize_images(x, size=[8, 8])

            # Größe auf 16x16
            x = tf.layers.conv2d_transpose(x, kernel_size=5, filters=64,
                                           strides=2, padding='same',
                                           activation=activation)
            x = tf.layers.dropout(x, self.keep_prob)
            x = tf.contrib.layers.batch_norm(x, is_training=self.is_training,
                                             decay=momentum)

            # 32x32
            x = tf.layers.conv2d_transpose(x, kernel_size=5, filters=64,
                                           strides=2, padding='same',
                                           activation=activation)
            x = tf.layers.dropout(x, self.keep_prob)
            x = tf.contrib.layers.batch_norm(x, is_training=self.is_training,
                                             decay=momentum)

            # 64x64
            x = tf.layers.conv2d_transpose(x, kernel_size=5, filters=64,
                                           strides=2, padding='same',
                                           activation=activation)
            x = tf.layers.dropout(x, self.keep_prob)
            x = tf.contrib.layers.batch_norm(x, is_training=self.is_training,
                                             decay=momentum)

            x = tf.layers.conv2d_transpose(x, kernel_size=5, filters=64,
                                           strides=1, padding='same',
                                           activation=activation)
            x = tf.layers.dropout(x, self.keep_prob)
            x = tf.contrib.layers.batch_norm(x, is_training=self.is_training,
                                             decay=momentum)
            x = tf.layers.conv2d_transpose(x, kernel_size=5, filters=3,
                                           strides=1, padding='same',
                                           activation=tf.nn.sigmoid)
            return x

    def generateImages(self, cnt):
        n = self.createNoise(cnt, self.n_noise)

        # Bild vom Generator erzeugen lassen
        gen_img = self.sess.run(self.g, feed_dict={
            self.noise: n, self.keep_prob: 1.0, self.is_training: False
        })

        return gen_img

    def saveEpochImages(self, imgs, epoch):
        dirEpoch = os.path.join(self.dirRunImages, 'epoch_{}'.format(epoch))

        self.createDir(dirEpoch)
        self.log.info('Generating {} images in folder {}'.format(
            len(imgs), dirEpoch))
        # Konvertierung der Bilder
        imgs = (imgs * 255).round().astype(np.uint8)

        for i in range(len(imgs)):
            imgName = '{}.png'.format(i)
            imgPath = os.path.join(dirEpoch, imgName)
            self.log.debug('Generating image {}'.format(imgPath))
            imageio.imwrite(imgPath, imgs[i])

    def createNoise(self, batch_size, n_noise):
        return np.random.uniform(0.0, 1.0, [batch_size, n_noise]).astype(np.float32)

    def prepareRunFolder(self):
        self.readyRunFolder = True
        return self.createRunFolder()

    def start(self):
        if self.readyEpoch and self.readyDcgan:
            if not self.readyRunFolder:
                self.createRunFolder()
            self.log.info('Starting Run {}'.format(self.cnt_runs))
            start, end = None, None
            for i in range(self.max_epochs):
                if i % self.epochPrintSteps:
                    self.log.info('Starting Epoch {}'.format(i))
                    start = time.time()

                train_d = True
                train_g = True,
                keep_prob_train = 0.6

                n = self.createNoise(self.batch_size, self.n_noise)

                batch = self.next_batch()[0]

                d_real_ls, d_fake_ls, g_ls, d_ls = self.sess.run(
                    [self.loss_d_real, self.loss_d_fake,
                     self.loss_g, self.loss_d],
                    feed_dict={
                        self.x_in: batch,
                        self.noise: n,
                        self.keep_prob: keep_prob_train,
                        self.is_training: True
                    })

                d_real_ls = np.mean(d_real_ls)
                d_fake_ls = np.mean(d_fake_ls)

                # TODO: Warum gibt es die folgenden Zeilen
                # die ergeben irgendwie keinen Sinn
                # zumindest gerade
                g_ls = g_ls
                d_ls = d_ls

                if g_ls * 1.5 < d_ls:
                    train_g = False
                    pass

                if d_ls * 2 < g_ls:
                    train_d = False
                    pass

                if train_d:
                    self.log.debug('Training: Discriminator')
                    self.sess.run(self.optimizer_d, feed_dict={
                        self.noise: n,
                        self.x_in: batch,
                        self.keep_prob: keep_prob_train,
                        self.is_training: True
                    })

                if train_g:
                    self.log.debug('Training: Generator')
                    self.sess.run(self.optimizer_g, feed_dict={
                        self.noise: n,
                        self.keep_prob: keep_prob_train,
                        self.is_training: True
                    })

                if not i % self.stepsHistory:

                    eLoss = self.getEpochInfo(
                        i, d_ls, g_ls,
                        d_real_ls, d_fake_ls
                    )

                    self.log.debugEpochInfo(eLoss)

                    print('1 >>>>>>>>>>>>>>>>>>>>>>>>> {}'.format(self.sqlLog))
                    if self.sqlLog:
                        print('2 >>>>>>>>>>>>>>>>>>>>>>>>>')
                        self.sqlLog.logEpochInfo(eLoss)

                    # Bilder generieren
                    if self.enableImageGeneration:
                        self.log.info('Epoch {}: Generating {} images'.format(
                            i, self.cntGenerateImages))
                        imgs = self.generateImages(self.cntGenerateImages)
                        self.saveEpochImages(imgs, i)

                if i % self.epochPrintSteps:
                    end = time.time() - start
                    self.log.info(
                        'Epoch {} completed in {:2.3f}s.'.format(i, end))

            self.log.info('Run {} completed.'.format(self.cnt_runs))
            self.cnt_runs += 1
        else:
            if not self.readyEpoch:
                self.log.error('Start error: Epoch not initialized.')

            self.log.error('Start error: DCGAN not initialized')


# Fürs Debugging und Testen
if __name__ == "__main__":
    print('Debugingmode ItsDcgan.')

    info = ItsSessionInfo()

    info.sessionNr = 1
    info.max_epoch = 10
    info.info_text = 'Debug Session with no SQL connection'
    info.enableImageGeneration = True
    info.cntGenerateImages = 10
    info.batch_size = 3

    g = ItsDcgan(info)

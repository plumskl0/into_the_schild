# -*- coding: utf-8 -*-

import os
import time
import imageio
import logging
import numpy as np
import tensorflow as tf
from itslogging import ItsLogger, ItsSqlLogger
from itsmisc import ItsEpochInfo, ItsSessionInfo


class ItsDcgan():

    def __init__(self, itsSqlLog=None):
        # TODO: Debugmodus abschalten
        self.log = ItsLogger(logName='its_dcgan', debug=True)
        self.sqlLog = itsSqlLog
        self.isDcganReady = False
        self.isEpochReady = False

        self.n_noise = 64
        self.imgShape = [None, 64, 64, 3]
        self.outputDir = None
        self.tfSession = None
        # {Session}_{Epoch}_{HisId}_{ImgNr}.png
        self.imageNameFormat = '{}_{}_{}_{}.png'

    def initEpoch(
        self, max_epochs=10, batch_size=2,
        enableImageGeneration=False, stepsHistory=1000,
        cntGenerateImages=10
    ):
        self.log.info('Initializing epoch...')
        self.index_in_epoch = 0
        self.epochs_completed = 0
        self.debugOutputSteps = 100

        # Batchsize ist am Anfang so groß wie die Datenbasis
        self.max_epochs = max_epochs
        self.batch_size = batch_size

        # Informationsoutput alle Epochen
        self.stepsHistory = stepsHistory
        # Anzahl der Generierten Bilder pro ImageGeneration
        self.enableImageGeneration = enableImageGeneration
        # Erst mal noch hardcoded
        if self.enableImageGeneration:
            self.cntGenerateImages = cntGenerateImages
        else:
            self.cntGenerateImages = 0

        self.isEpochReady = True

    def initDcgan(self):
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

        self.tfSession = tf.Session()
        self.tfSession.run(tf.global_variables_initializer())
        self.isDcganReady = True
        self.log.info('DCGAN initialized.')

    def __allReady(self):
        ready = False

        self.log.debug('All ready check:')
        self.log.debug('Epoch ready? \t{}'.format(self.isEpochReady))
        self.log.debug('Dcgan ready? \t{}'.format(self.isDcganReady))
        self.log.debug('Images ready? \t{}'.format(len(self.images)))
        self.log.debug('Labels ready? \t{}'.format(len(self.labels)))

        if (self.isEpochReady and
            self.isDcganReady and
            self.images.any() and
                self.labels.any()):
            ready = True

        return ready

    def __del__(self):
        self.log.debug('Killing Itsdcgan...')
        if self.tfSession:
            self.tfSession.close()
            del self.tfSession
        tf.reset_default_graph()
        self.log.debug('Itsdcgan killed.')
        del self.log

    def lrelu(self, x):
        return tf.maximum(x, tf.multiply(x, 0.2))

    def binary_cross_entropy(self, x, z):
        eps = 1e-12
        return (-(x * tf.log(z + eps) + (1. - x) * tf.log(1. - z + eps)))

    def createNoise(self, batch_size, n_noise):
        return np.random.uniform(0.0, 1.0, [batch_size, n_noise]).astype(np.float32)

    def setSessionBaseImages(self, sessionNr, imgs):
        self.sessionNr = sessionNr
        self.images = np.array(imgs)
        self.labels = np.ones(len(imgs))
        self.cntBaseImages = len(imgs)

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

    def saveEpochImages(self, imgs, epoch, hisId):
        if self.outputDir:
            self.log.info('Generating {} images in folder {}'.format(
                len(imgs), self.outputDir))
            # Konvertierung der Bilder
            imgs = (imgs * 255).round().astype(np.uint8)

            for i in range(len(imgs)):
                imgName = self.imageNameFormat.format(self.sessionNr, epoch, hisId, i)
                imgPath = os.path.join(self.outputDir, imgName)
                self.log.debug('Generating image {}'.format(imgPath))
                imageio.imwrite(imgPath, imgs[i])
        else:
            self.log.error('No output directory specified.')

    def getEpochInfo(
        self, epoch=-1, d_ls=-1,
        g_ls=-1, d_real_ls=-1,
        d_fake_ls=-1
    ):
        self.log.info('Generating EpochInfo...')
        return ItsEpochInfo(
            self.sessionNr, epoch,
            self.batch_size,
            d_ls, g_ls,
            d_real_ls, d_fake_ls
        )

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
        gen_img = self.tfSession.run(self.g, feed_dict={
            self.noise: n, self.keep_prob: 1.0, self.is_training: False
        })

        return gen_img

    def start(self):
        if self.__allReady():
            self.log.info(
                'Starting DCGAN for {} epochs...'.format(self.max_epochs))
            start, end = None, None
            for i in range(self.max_epochs):
                if not i % self.debugOutputSteps:
                    self.log.info('Starting Epoch {}'.format(i))
                    start = time.time()

                train_d = True
                train_g = True,
                keep_prob_train = 0.6

                n = self.createNoise(self.batch_size, self.n_noise)

                batch = self.next_batch()[0]

                d_real_ls, d_fake_ls, g_ls, d_ls = self.tfSession.run(
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

                if g_ls * 1.5 < d_ls:
                    train_g = False
                    pass

                if d_ls * 2 < g_ls:
                    train_d = False
                    pass

                if train_d:
                    if not i % self.debugOutputSteps:
                        self.log.debug('Training: Discriminator')
                    self.tfSession.run(self.optimizer_d, feed_dict={
                        self.noise: n,
                        self.x_in: batch,
                        self.keep_prob: keep_prob_train,
                        self.is_training: True
                    })

                if train_g:
                    if not i % self.debugOutputSteps:
                        self.log.debug('Training: Generator')
                    self.tfSession.run(self.optimizer_g, feed_dict={
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
                    hisId = self.sqlLog.logEpochInfo(eLoss)

                    # Bilder generieren
                    if self.enableImageGeneration:
                        self.log.info('Epoch {}: Generating {} images'.format(
                            i, self.cntGenerateImages))
                        imgs = self.generateImages(self.cntGenerateImages)
                        self.saveEpochImages(imgs, i, hisId)

                if not i % self.debugOutputSteps:
                    end = time.time() - start
                    self.log.info(
                        'Epoch {} completed in {:2.3f}s.'.format(i, end))

            self.log.info('Run {} completed.'.format(i))
        else:
            if not self.isEpochReady:
                self.log.error('Start error: Epoch not initialized.')
            elif not self.isDcganReady:
                self.log.error('Start error: DCGAN not initialized')
            elif not self.images:
                self.log.error('Start error: No base images defined.')
            
            self.log.error('Start error: Check the logs.')

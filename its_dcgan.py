# -*- coding: utf-8 -*-
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
import imageio
import logging
import numpy as np
import tensorflow as tf
from itslogging import ITSLogger

# Debugmodus
debug = True


class ITSdcgan():

    def __init__(self):

        # Dateien
        self.fileConfig = 'its_dcgan.ini'
        self.logName = 'its_dcgan'

        self.log = ITSLogger(logName=self.logName, debug=debug)

        # Ordner
        self.root = './'
        self.dirItsImages = os.path.join(self.root, 'its_images')
        self.dirRunImages = self.createRunFolderName()

        # Default Config Werte
        # TODO: Configwerte einbauen

        self.checkFilesFolders()
        self.initEpoch()

    def initEpoch(self, epochs=10, n_noise=64):
        self.max_epochs = epochs
        self.n_noise = 64
        self.index_in_epoch = 0
        self.epochs_completed = 0

        # Batchsize ist am Anfang so groß wie die Datenbasis
        self.batch_size = 8

        # Informationsoutput alle Epochen
        self.stepsHistory = 50
        self.stepsImageGeneration = 1000

        # Anzahl der Generierten Bilder pro ImageGeneration
        self.cntGenerateImages = 35

        self.images, self.labels = self.generateData()
        self.imgShape = [None, 64, 64, 3]
        
        # Anzahl der Bilder in der Basis
        self.num_examples = len(self.images)

    def initDcgan(self):
        tf.reset_default_graph()

        self.x_in = tf.placeholder(
            dtype=tf.float32, shape=self.imgShape, name='x_in')
        self.noise = tf.placeholder(
            dtype=tf.float32, shape=[None, self.n_noise])

        self.keep_prob = tf.placeholder(dtype=tf.float32, name='keep_prob')
        self.is_training = tf.placeholder(dtype=tf.bool, name='is_training')

        g = self.generator(self.noise, self.keep_prob, self.is_training)
        d_real = self.discriminator(self.x_in)
        d_fake = self.discriminator(g, reuse=True)

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

    def createRunFolderName(self):
        folders = []

        if os.path.exists(self.dirItsImages):
            _, folders, _ = next(os.walk(self.dirItsImages))

        name = 'gen_imgs_run_{}'.format(len(folders))
        dirPath = os.path.join(self.dirItsImages, name)
        return dirPath

    def checkFilesFolders(self):
        self.log.info('Checking Files and Folders...')
        self.createDir(self.dirItsImages, self.dirRunImages)

        if not os.path.exists(self.fileConfig):
            self.log.info('Creating File: {}'.format(self.fileConfig))
            # with open(fileConfig, 'w') as cfgFile:
            # config = createConfigTemplate()
            # config.write(cfgFile)

        self.log.info('Files and Folders check completed.')

    def createDir(self, *args):
        for d in args:
            if not os.path.exists(d):
                self.log.debug('Creating Dir: {}'.format(d))
                os.makedirs(d)

    def generateData(self):
        _, folders, files = next(os.walk(self.dirItsImages))

        self.log.info('Found {} files in directory {}'.format(
            len(files), self.dirItsImages))

        imgs = []
        lbls = []

        # Zunächst nur die Bilder
        for f in files:
            imgPath = os.path.join(self.dirItsImages, f)
            self.log.debug('Loading file {}'.format(imgPath))
            # Bild als Numpy-Array einlesen
            imgArr = imageio.imread(imgPath)
            imgs.append(imgArr)
            lbls.append(1)

        imgs = np.array(imgs)

        # Bilder von 0-255 auf 0-1 bringen
        imgs = imgs.astype(np.float32)
        imgs = np.multiply(imgs, 1.0 / 255.0)

        return imgs, np.array(lbls)

    def next_batch(self, batch_size):
        start = self.index_in_epoch
        self.index_in_epoch += batch_size
        if self.index_in_epoch > self.num_examples:
            # Finished epoch
            self.epochs_completed += 1

            # Shuffle data
            perm = np.arange(self.num_examples)
            np.random.shuffle(perm)
            images = self.images[perm]
            labels = self.labels[perm]

            # Start next epoch
            start = 0
            index_in_epoch = batch_size
            assert batch_size <= self.num_examples
        end = index_in_epoch
        return images[start:end], labels[start:end]

    def lrelu(self, x):
        return tf.maximum(x, tf.multiply(x, 0.2))

    def binary_cross_entropy(self, x, z):
        eps = 1e-12
        return (-(x * tf.log(z + eps) + (1. - x) * tf.log(1. - z + eps)))

    def discriminator(self, img_in, reuse=None, keep_prob=self.keep_prob):
        activation = self.lrelu
        with tf.variable_scope('discriminator', reuse=reuse):
            self.log.debug('img_in : {}'.format(img_in))
            x = tf.reshape(img_in, shape=[-1, 64, 64, 3])
            self.log.debug('reshaped img_in : {}'.format(x))
            x = tf.layers.conv2d(x, kernel_size=5, filters=64, strides=2,
                                 padding='same', activation=activation)
            x = tf.layers.dropout(x, keep_prob)
            x = tf.layers.conv2d(x, kernel_size=5, filters=64, strides=1,
                                 padding='same', activation=activation)
            x = tf.layers.dropout(x, keep_prob)
            x = tf.layers.conv2d(x, kernel_size=5, filters=64, strides=1,
                                 padding='same', activation=activation)
            x = tf.layers.dropout(x, keep_prob)
            x = tf.layers.dense(x, units=128, activation=activation)
            x = tf.layers.dense(x, units=1, activation=tf.nn.sigmoid)
        return x

    def generator(self, z, keep_prob=self.keep_prob, is_training=self.is_training):
        activation = self.lrelu
        momentum = 0.99
        with tf.variable_scope('generator', reuse=None):
            x = z
            d1 = 4
            d2 = 3
            x = tf.layers.dense(x, units=d1*d1*d2, activation=activation)
            x = tf.layers.dropout(x, keep_prob)
            x = tf.contrib.layers.batch_norm(x, is_training=is_training,
                                             decay=momentum)
            x = tf.reshape(x, shape=[-1, d1, d1, d2])

            # Hier hat man ein 8x8 Grundbild
            x = tf.image.resize_images(x, size=[8, 8])

            # Größe auf 16x16
            x = tf.layers.conv2d_transpose(x, kernel_size=5, filters=64,
                                           strides=2, padding='same',
                                           activation=activation)
            x = tf.layers.dropout(x, keep_prob)
            x = tf.contrib.layers.batch_norm(x, is_training=is_training,
                                             decay=momentum)

            # 32x32
            x = tf.layers.conv2d_transpose(x, kernel_size=5, filters=64,
                                           strides=2, padding='same',
                                           activation=activation)
            x = tf.layers.dropout(x, keep_prob)
            x = tf.contrib.layers.batch_norm(x, is_training=is_training,
                                             decay=momentum)

            # 64x64
            x = tf.layers.conv2d_transpose(x, kernel_size=5, filters=64,
                                           strides=2, padding='same',
                                           activation=activation)
            x = tf.layers.dropout(x, keep_prob)
            x = tf.contrib.layers.batch_norm(x, is_training=is_training,
                                             decay=momentum)

            x = tf.layers.conv2d_transpose(x, kernel_size=5, filters=64,
                                           strides=1, padding='same',
                                           activation=activation)
            x = tf.layers.dropout(x, keep_prob)
            x = tf.contrib.layers.batch_norm(x, is_training=is_training,
                                             decay=momentum)
            x = tf.layers.conv2d_transpose(x, kernel_size=5, filters=3,
                                           strides=1, padding='same',
                                           activation=tf.nn.sigmoid)
            return x

    def generateImages(self, cnt):

        n = self.createNoise(cnt, self.n_noise)

        # Bild vom Generator erzeugen lassen
        gen_img = sess.run(self.g, feed_dict={
            self.noise: n, self.keep_prob: 1.0, self.is_training: False
        })

        return gen_img

    def saveEpochImages(self, imgs, epoch):
        dirEpoch = os.path.join(self.dirRunImages, 'epoch_{}'.format(epoch))

        self.createDir(dirEpoch)

        self.log.info('Generating {} images in folder {}'.format(len(imgs), dirEpoch))
        # Konvertierung der Bilder
        imgs = (imgs * 255).round().astype(np.uint8)

        for i in range(len(imgs)):
            imgName = '{}.png'.format(i)
            imgPath = os.path.join(dirEpoch, imgName)
            self.log.debug('Generating image {}'.format(imgPath))
            imageio.imwrite(imgPath, imgs[i])

    def createNoise(self, batch_size, n_noise):
        return np.random.uniform(0.0, 1.0, [batch_size, n_noise]).astype(np.float32)

    def runDcganSession(self):
        sess = tf.Session()
        sess.run(tf.global_variables_initializer())

        for i in range(self.max_epochs):

            train_d = True
            train_g = True,
            keep_prob_train = 0.6

            n = self.createNoise(self.batch_size, self.n_noise)

            batch = self.next_batch(self.batch_size)[0]

            d_real_ls, d_fake_ls, g_ls, d_ls = sess.run(
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
                sess.run(self.optimizer_d, feed_dict={
                    self.noise: n,
                    self.x_in: batch,
                    self.keep_prob: keep_prob_train,
                    self.is_training: True
                })

            if train_g:
                self.log.debug('Training: Generator')
                sess.run(self.optimizer_g, feed_dict={
                    self.noise: n,
                    self.keep_prob: keep_prob_train,
                    self.is_training: True
                })

            if not i % stepsHistory:
                # TODO: Hier kann eine Historienfunktion eingebaut werden
                self.log.debug(
                    'Epoch: {}, d_ls: {}, g_ls: {}, d_real_ls: {}, d_fake_ls: {}'.format(
                        i, d_ls, g_ls, d_real_ls, d_fake_ls
                    ))

            if not i % stepsImageGeneration:
                # Bilder generieren
                self.log.info('Epoch {}: Generating {} images'.format(
                    i, cntGenerateImages))
                imgs = self.generateImages(cntGenerateImages)
                self.saveEpochImages(imgs, i)

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
from istlogging import istLogger

# Debugmodus
debug = True

# Dateien
fileConfig = 'its_dcgan.ini'
logName = 'its_dcgan'

log = istLogger.initLogger(logName=logName, debug=debug)


# Ordner
root = './'
dirItsImages = os.path.join(root, 'its_images')

def createRunFolderName():
    folders = []

    if os.path.exists(dirItsImages):
        _, folders, _ = next(os.walk(dirItsImages))

    name = 'gen_imgs_run_{}'.format(len(folders))
    dirPath = os.path.join(dirItsImages, name)
    return dirPath

dirRunImages = createRunFolderName()

def checkFilesFolders():
    log.info('Checking Files and Folders...')
    createDir(dirItsImages, dirRunImages)

    if not os.path.exists(fileConfig):
        log.info('Creating File: {}'.format(fileConfig))
        # with open(fileConfig, 'w') as cfgFile:
        # config = createConfigTemplate()
        # config.write(cfgFile)

    log.info('Files and Folders check completed.')

def createDir(*args):
    for d in args:
        if not os.path.exists(d):
            log.debug('Creating Dir: {}'.format(d))
            os.makedirs(d)


# Default Config Werte
# TODO: Configwerte einbauen

checkFilesFolders()

# Bilder laden


def generateData():
    _, folders, files = next(os.walk(dirItsImages))

    log.info('Found {} files in directory {}'.format(len(files), dirItsImages))

    imgs = []
    lbls = []

    # Zunächst nur die Bilder
    for f in files:
        imgPath = os.path.join(dirItsImages, f)
        log.debug('Loading file {}'.format(imgPath))
        # Bild als Numpy-Array einlesen
        imgArr = imageio.imread(imgPath)
        imgs.append(imgArr)
        lbls.append(1)

    return np.array(imgs), np.array(lbls)


images, labels = generateData()
imgShape = [None, 64, 64, 3]

# Bilder von 0-255 auf 0-1 bringen
images = images.astype(np.float32)
images = np.multiply(images, 1.0 / 255.0)

tf.reset_default_graph()
# Batchsize ist am Anfang so groß wie die Datenbasis
batch_size = 8
n_noise = 64

x_in = tf.placeholder(dtype=tf.float32, shape=imgShape, name='x_in')
noise = tf.placeholder(dtype=tf.float32, shape=[None, n_noise])

keep_prob = tf.placeholder(dtype=tf.float32, name='keep_prob')
is_training = tf.placeholder(dtype=tf.bool, name='is_training')

epochs = 1
index_in_epoch = 0
epochs_completed = 0
num_examples = len(images)

# Informationsoutput alle Epochen
stepsHistory = 50
stepsImageGeneration = 1000

# Anzahl der Generierten Bilder pro ImageGeneration
cntGenerateImages = 35


def next_batch(batch_size):
    global images
    global labels
    global index_in_epoch
    global epochs_completed

    start = index_in_epoch
    index_in_epoch += batch_size
    if index_in_epoch > num_examples:
        # Finished epoch
        epochs_completed += 1

        # Shuffle data
        perm = np.arange(num_examples)
        np.random.shuffle(perm)
        images = images[perm]
        labels = labels[perm]

        # Start next epoch
        start = 0
        index_in_epoch = batch_size
        assert batch_size <= num_examples
    end = index_in_epoch
    return images[start:end], labels[start:end]


def lrelu(x):
    return tf.maximum(x, tf.multiply(x, 0.2))


def binary_cross_entropy(x, z):
    eps = 1e-12
    return (-(x * tf.log(z + eps) + (1. - x) * tf.log(1. - z + eps)))


def discriminator(img_in, reuse=None, keep_prob=keep_prob):
    activation = lrelu
    with tf.variable_scope('discriminator', reuse=reuse):
        log.debug('img_in : {}'.format(img_in))
        x = tf.reshape(img_in, shape=[-1, 64, 64, 3])
        log.debug('reshaped img_in : {}'.format(x))
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


def generator(z, keep_prob=keep_prob, is_training=is_training):
    activation = lrelu
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


g = generator(noise, keep_prob, is_training)
d_real = discriminator(x_in)
d_fake = discriminator(g, reuse=True)

vars_g = [var for var in tf.trainable_variables(
) if var.name.startswith("generator")]
vars_d = [var for var in tf.trainable_variables(
) if var.name.startswith("discriminator")]

d_reg = tf.contrib.layers.apply_regularization(
    tf.contrib.layers.l2_regularizer(1e-6), vars_d)
g_reg = tf.contrib.layers.apply_regularization(
    tf.contrib.layers.l2_regularizer(1e-6), vars_g)

loss_d_real = binary_cross_entropy(tf.ones_like(d_real), d_real)
loss_d_fake = binary_cross_entropy(tf.zeros_like(d_fake), d_fake)

loss_g = tf.reduce_mean(binary_cross_entropy(tf.ones_like(d_fake), d_fake))
loss_d = tf.reduce_mean(0.5 * (loss_d_real + loss_d_fake))

update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS)
with tf.control_dependencies(update_ops):
    optimizer_d = tf.train.RMSPropOptimizer(
        learning_rate=0.00015).minimize(loss_d + d_reg, var_list=vars_d)
    optimizer_g = tf.train.RMSPropOptimizer(
        learning_rate=0.00015).minimize(loss_g + g_reg, var_list=vars_g)

sess = tf.Session()
sess.run(tf.global_variables_initializer())


def generateImages(cnt):

    n = createNoise(cnt, n_noise)

    # Bild vom Generator erzeugen lassen
    gen_img = sess.run(g, feed_dict={
        noise: n, keep_prob: 1.0, is_training: False
    })

    return gen_img


def saveEpochImages(imgs, epoch):
    dirEpoch = os.path.join(dirRunImages, 'epoch_{}'.format(epoch))

    createDir(dirEpoch)

    log.info('Generating {} images in folder {}'.format(len(imgs), dirEpoch))
    # Konvertierung der Bilder
    imgs = (imgs * 255).round().astype(np.uint8)

    for i in range(len(imgs)):
        imgName = '{}.png'.format(i)
        imgPath = os.path.join(dirEpoch, imgName)
        log.debug('Generating image {}'.format(imgPath))
        imageio.imwrite(imgPath, imgs[i])


def createNoise(batch_size, n_noise):
    return np.random.uniform(0.0, 1.0, [batch_size, n_noise]).astype(np.float32)


for i in range(epochs):
    # Zum Debuggen:
    # i = 0

    train_d = True
    train_g = True,
    keep_prob_train = 0.6

    n = createNoise(batch_size, n_noise)

    batch = next_batch(batch_size)[0]

    d_real_ls, d_fake_ls, g_ls, d_ls = sess.run([loss_d_real, loss_d_fake,
                                                 loss_g, loss_d],
                                                feed_dict={
        x_in: batch,
        noise: n,
        keep_prob: keep_prob_train,
        is_training: True
    })

    d_real_ls = np.mean(d_real_ls)
    d_fake_ls = np.mean(d_fake_ls)

    # TODO: Warum gibt es die folgenden Zeilen die ergeben irgendwie keinen Sinn
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
        log.debug('Training: Discriminator')
        sess.run(optimizer_d, feed_dict={
            noise: n,
            x_in: batch,
            keep_prob: keep_prob_train,
            is_training: True
        })

    if train_g:
        log.debug('Training: Generator')
        sess.run(optimizer_g, feed_dict={
            noise: n,
            keep_prob: keep_prob_train,
            is_training: True
        })

    if not i % stepsHistory:
        # TODO: Hier kann eine Historienfunktion eingebaut werden
        log.debug(
            'Epoch: {}, d_ls: {}, g_ls: {}, d_real_ls: {}, d_fake_ls: {}'.format(
                i, d_ls, g_ls, d_real_ls, d_fake_ls
            ))

    if not i % stepsImageGeneration:
        # Bilder generieren
        log.info('Epoch {}: Generating {} images'.format(i, cntGenerateImages))
        imgs = generateImages(cntGenerateImages)
        saveEpochImages(imgs, i)


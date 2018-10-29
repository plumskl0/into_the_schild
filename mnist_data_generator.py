# -*- coding: utf-8 -*-
import os
import math
import argparse
import numpy as np
from tensorflow.keras.datasets import mnist

'''
    Da die VM Probleme hat die MNIST-Daten zu laden nutzen wir einen Konvertierer.
    Die MNIST Daten werden in einer CSV-Datei gespeichert um sie dann auf den Server zu laden.

    Standard dtype = numpy.uint8
'''


def create_files():
    data_folder = 'data'

    data_x_train = 'x_train.gz'
    data_y_train = 'y_train.gz'

    data_x_test = 'x_test.gz'
    data_y_test = 'y_test.gz'

    # Prüfen ob der Ordner vorhanden ist
    print('Checking {} folder...'.format(data_folder))
    if not os.path.exists(data_folder):
        # Erstellen falls nicht vorhanden
        print("Creating {} folder...".format(data_folder))
        os.makedirs(data_folder)

    # Dateipfade erzeugen
    file_x_train = os.path.join(data_folder, data_x_train)
    file_y_train = os.path.join(data_folder, data_y_train)

    file_x_test = os.path.join(data_folder, data_x_test)
    file_y_test = os.path.join(data_folder, data_y_test)
    return (file_x_train, file_y_train), (file_x_test, file_y_test)


def generate_data():
    # MNIST Daten laden
    print('Loading MNIST data...')
    (x_train, y_train), (x_test, y_test) = mnist.load_data()
    print('Done\n')

    (file_x_train, file_y_train), (file_x_test, file_y_test) = create_files()

    # Reshape der Daten
    print('Reshape x_train...')
    cnt, x, y = x_train.shape
    x_train = x_train.reshape((cnt, x*y))
    print('Done\n')

    print('Reshape x_train...')
    cnt, x, y = x_test.shape
    x_test = x_test.reshape((cnt, x*y))
    print('Done\n')

    # Speichern der Daten in den Ordner
    print('Saving file {}'.format(file_x_train))
    np.savetxt(file_x_train, x_train, delimiter=',')

    print('Saving file {}'.format(file_y_train))
    np.savetxt(file_y_train, y_train, delimiter=',')

    print('Saving file {}'.format(file_x_test))
    np.savetxt(file_x_test, x_test, delimiter=',')

    print('Saving file {}'.format(file_y_test))
    np.savetxt(file_y_test, y_test, delimiter=',')

    print('Done')


def load_data():
    dtype = np.uint8
    (file_x_train, file_y_train), (file_x_test, file_y_test) = create_files()

    print('Loading file {}'.format(file_x_train))
    x_train = np.loadtxt(file_x_train, dtype=dtype, delimiter=',')

    print('Loading file {}'.format(file_y_train))
    y_train = np.loadtxt(file_y_train, dtype=dtype, delimiter=',')

    print('Loading file {}'.format(file_x_test))
    x_test = np.loadtxt(file_x_test, dtype=dtype, delimiter=',')

    print('Loading file {}'.format(file_y_test))
    y_test = np.loadtxt(file_y_test, dtype=dtype, delimiter=',')

    # Reshape der Daten
    cnt, x = x_train.shape
    x = y = int(math.sqrt(x))
    x_train = x_train.reshape((cnt, x, y))

    cnt, x = x_test.shape
    x = y = int(math.sqrt(x))
    x_test = x_test.reshape((cnt, x , y))

    return (x_train, y_train), (x_test, y_test)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', help='Debug mode: disables data generation',
                        action='store_true')

    args = parser.parse_args()

    if args.debug:
        print('Debug mode')
    else:
        print('Starting data generation...\n')
        generate_data()

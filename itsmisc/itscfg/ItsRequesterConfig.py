# -*- coding: utf-8 -*-


class ItsRequesterConfig():

    def __init__(self, url, key, delay, request_directory):
        self.url = url
        self.key = key
        self.delay = delay
        self.request_directory = request_directory

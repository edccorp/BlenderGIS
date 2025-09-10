# -*- coding:utf-8 -*-
import os
import json

from .checkdeps import HAS_GDAL, HAS_PYPROJ, HAS_IMGIO, HAS_PIL

def getAvailableProjEngines():
        engines = ['AUTO', 'BUILTIN']
        #if EPSGIO.ping():
        engines.append('EPSGIO')
        if HAS_GDAL:
                engines.append('GDAL')
        if HAS_PYPROJ:
                engines.append('PYPROJ')
        return engines

def getAvailableImgEngines():
        engines = ['AUTO']
        if HAS_GDAL:
                engines.append('GDAL')
        if HAS_IMGIO:
                engines.append('IMGIO')
        if HAS_PIL:
                engines.append('PIL')
        return engines


class Settings():

        def __init__(self, **kwargs):
                self._proj_engine = kwargs['proj_engine']
                self._img_engine = kwargs['img_engine']
                self.user_agent = kwargs['user_agent']
                # Optional API key for EPSG reprojection service
                self.epsgio_key = kwargs.get('epsgio_key', '')
                # Base URLs for external web services
                self.epsgio_url = kwargs.get('epsgio_url', 'https://epsg.io')
                self.maptiler_url = kwargs.get('maptiler_url', 'https://api.maptiler.com')

        @property
        def proj_engine(self):
                return self._proj_engine

        @proj_engine.setter
        def proj_engine(self, engine):
                if engine not in getAvailableProjEngines():
                        raise IOError
                else:
                        self._proj_engine = engine

        @property
        def img_engine(self):
                return self._img_engine

        @img_engine.setter
        def img_engine(self, engine):
                if engine not in getAvailableImgEngines():
                        raise IOError
                else:
                        self._img_engine = engine

        def save(self):
                data = {
                        'proj_engine': self.proj_engine,
                        'img_engine': self.img_engine,
                        'user_agent': self.user_agent,
                        'epsgio_key': self.epsgio_key,
                        'epsgio_url': self.epsgio_url,
                        'maptiler_url': self.maptiler_url,
                }
                with open(cfgFile, 'w') as cfg:
                        json.dump(data, cfg, indent=8)


cfgFile = os.path.join(os.path.dirname(__file__), "settings.json")

with open(cfgFile, 'r') as cfg:
                prefs = json.load(cfg)

settings = Settings(**prefs)

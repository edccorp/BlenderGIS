# -*- coding:utf-8 -*-

#  ***** GPL LICENSE BLOCK *****
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#  All rights reserved.
#  ***** GPL LICENSE BLOCK *****
import logging
log = logging.getLogger(__name__)

from functools import lru_cache

from urllib.request import (
        Request,
        urlopen,
        build_opener,
        HTTPSHandler,
        HTTPRedirectHandler,
)
from urllib.error import URLError, HTTPError
import ssl
import json

from ..errors import ReprojError
from .. import settings

USER_AGENT = settings.user_agent

DEFAULT_TIMEOUT = 2
REPROJ_TIMEOUT = 60

######################################
# EPSG web service


class EPSGIO():
        MAX_POINTS = 1000

        @staticmethod
        def _open(url, timeout):
                key = getattr(settings, 'epsgio_key', '')
                if key:
                        url += ('&' if '?' in url else '?') + 'key=' + key
                rq = Request(url, headers={'User-Agent': USER_AGENT})
                context = ssl.create_default_context()
                opener = build_opener(HTTPSHandler(context=context), HTTPRedirectHandler())
                return opener.open(rq, timeout=timeout)

        @staticmethod
        def ping():

                url = settings.epsgio_url

                try:
                        EPSGIO._open(url, DEFAULT_TIMEOUT)
                        return True
                except HTTPError as e:
                        log.error('Cannot ping {} web service, http error {}'.format(url, e.code))
                        return False
                except URLError as e:
                        reason = e.reason
                        if isinstance(reason, ssl.SSLError):
                                log.error('Cannot ping {} web service, SSL error {}'.format(url, reason))
                        else:
                                log.error('Cannot ping {} web service, {}'.format(url, reason))
                        return False
                except ssl.SSLError as e:
                        log.error('Cannot ping {} web service, SSL error {}'.format(url, e))
                        return False


        @staticmethod
        @lru_cache(maxsize=1024)
        def reprojPt(epsg1, epsg2, x1, y1):

                base = settings.epsgio_url.rstrip('/')
                url = base + "/trans?x={X}&y={Y}&z={Z}&s_srs={CRS1}&t_srs={CRS2}"


                url = url.replace("{X}", str(x1))
                url = url.replace("{Y}", str(y1))
                url = url.replace("{Z}", '0')
                url = url.replace("{CRS1}", str(epsg1))
                url = url.replace("{CRS2}", str(epsg2))

                log.debug(url)

                try:
                        response = EPSGIO._open(url, REPROJ_TIMEOUT).read().decode('utf8')
                except HTTPError as err:
                        if err.code in (401, 403):
                                raise ReprojError('{} access denied: {} {}'.format(settings.epsgio_url, err.code, err.reason))
                        log.error('Http request fails url:{}, code:{}, error:{}'.format(url, err.code, err.reason))
                        raise
                except URLError as err:
                        reason = err.reason
                        if isinstance(reason, ssl.SSLError):
                                log.error('Http request fails url:{}, SSL error:{}'.format(url, reason))
                        else:
                                log.error('Http request fails url:{}, error:{}'.format(url, reason))
                        raise
                except ssl.SSLError as err:
                        log.error('Http request fails url:{}, SSL error:{}'.format(url, err))
                        raise

                obj = json.loads(response)

                if isinstance(obj, dict):
                        if 'x' in obj and 'y' in obj:
                                return (float(obj['x']), float(obj['y']))
                        results = obj.get('results') or obj.get('points')
                        if results:
                                res = results[0]
                                return (float(res['x']), float(res['y']))
                raise ReprojError('Unexpected response from epsg.io: {}'.format(obj))

        @staticmethod
        def reprojPts(epsg1, epsg2, points):
                pts_key = tuple((float(x), float(y)) for x, y in points)
                return EPSGIO._reprojPts_cached(epsg1, epsg2, pts_key)

        @staticmethod
        @lru_cache(maxsize=128)
        def _reprojPts_cached(epsg1, epsg2, pts_key):
                points = list(pts_key)

                if len(points) == 1:
                        x, y = points[0]
                        return [EPSGIO.reprojPt(epsg1, epsg2, x, y)]

                base = settings.epsgio_url.rstrip('/')
                urlTemplate = base + "/trans?data={POINTS}&s_srs={CRS1}&t_srs={CRS2}"

                urlTemplate = urlTemplate.replace("{CRS1}", str(epsg1))
                urlTemplate = urlTemplate.replace("{CRS2}", str(epsg2))

                precision = 4
                data = [','.join([str(round(v, precision)) for v in p]) for p in points]
                part, parts = [], []
                for i, p in enumerate(data):
                        l = sum(len(pt) for pt in part) + len(';' * len(part))
                        if l + len(p) < 4000 and len(part) < EPSGIO.MAX_POINTS:
                                part.append(p)
                        else:
                                parts.append(part)
                                part = [p]
                        if i == len(data) - 1:
                                parts.append(part)
                parts = [';'.join(part) for part in parts]

                result = []
                for part in parts:
                        url = urlTemplate.replace("{POINTS}", part)
                        log.debug(url)

                        try:
                                response = EPSGIO._open(url, REPROJ_TIMEOUT).read().decode('utf8')
                        except HTTPError as err:
                                if err.code in (401, 403):
                                        raise ReprojError('{} access denied: {} {}'.format(settings.epsgio_url, err.code, err.reason))
                                log.error('Http request fails url:{}, code:{}, error:{}'.format(url, err.code, err.reason))
                                raise
                        except URLError as err:
                                reason = err.reason
                                if isinstance(reason, ssl.SSLError):
                                        log.error('Http request fails url:{}, SSL error:{}'.format(url, reason))
                                else:
                                        log.error('Http request fails url:{}, error:{}'.format(url, reason))
                                raise
                        except ssl.SSLError as err:
                                log.error('Http request fails url:{}, SSL error:{}'.format(url, err))
                                raise

                        obj = json.loads(response)
                        if isinstance(obj, dict):
                                data = obj.get('results') or obj.get('points') or []
                        else:
                                data = obj
                        result.extend([(float(p['x']), float(p['y'])) for p in data])

                return result

        @staticmethod
        @lru_cache(maxsize=256)
        def search(query):
                query = str(query).replace(' ', '+')

                base = settings.epsgio_url.rstrip('/')
                url = base + "/?q={QUERY}&format=json"

                url = url.replace("{QUERY}", query)
                log.debug('Search crs : {}'.format(url))
                try:
                        response = EPSGIO._open(url, DEFAULT_TIMEOUT).read().decode('utf8')
                except HTTPError as err:
                        log.error('Http request fails url:{}, code:{}, error:{}'.format(url, err.code, err.reason))
                        raise
                except URLError as err:
                        reason = err.reason
                        if isinstance(reason, ssl.SSLError):
                                log.error('Http request fails url:{}, SSL error:{}'.format(url, reason))
                        else:
                                log.error('Http request fails url:{}, error:{}'.format(url, reason))
                        raise
                except ssl.SSLError as err:
                        log.error('Http request fails url:{}, SSL error:{}'.format(url, err))
                        raise
                obj = json.loads(response)
                log.debug('Search results : {}'.format([ (r['code'], r['name']) for r in obj.get('results', []) ]))
                return obj.get('results', [])

        @staticmethod
        @lru_cache(maxsize=256)
        def getEsriWkt(epsg):

                base = settings.epsgio_url.rstrip('/')
                url = base + "/{CODE}.esriwkt"

                url = url.replace("{CODE}", str(epsg))
                log.debug(url)
                try:
                        wkt = EPSGIO._open(url, DEFAULT_TIMEOUT).read().decode('utf8')
                except HTTPError as err:
                        log.error('Http request fails url:{}, code:{}, error:{}'.format(url, err.code, err.reason))
                        raise
                except URLError as err:
                        reason = err.reason
                        if isinstance(reason, ssl.SSLError):
                                log.error('Http request fails url:{}, SSL error:{}'.format(url, reason))
                        else:
                                log.error('Http request fails url:{}, error:{}'.format(url, reason))
                        raise
                except ssl.SSLError as err:
                        log.error('Http request fails url:{}, SSL error:{}'.format(url, err))
                        raise
                return wkt

        @staticmethod
        def clear_cache():
                EPSGIO.reprojPt.cache_clear()
                EPSGIO._reprojPts_cached.cache_clear()
                EPSGIO.search.cache_clear()
                EPSGIO.getEsriWkt.cache_clear()




######################################
# World Coordinate Converter
# https://github.com/ClemRz/TWCC

class TWCC():

        @staticmethod
        def reprojPt(epsg1, epsg2, x1, y1):

                url = "http://twcc.fr/en/ws/?fmt=json&x={X}&y={Y}&in=EPSG:{CRS1}&out=EPSG:{CRS2}"

                url = url.replace("{X}", str(x1))
                url = url.replace("{Y}", str(y1))
                url = url.replace("{Z}", '0')
                url = url.replace("{CRS1}", str(epsg1))
                url = url.replace("{CRS2}", str(epsg2))

                rq = Request(url, headers={'User-Agent': USER_AGENT})
                response = urlopen(rq, timeout=REPROJ_TIMEOUT).read().decode('utf8')
                obj = json.loads(response)

                return (float(obj['point']['x']), float(obj['point']['y']))


######################################
#http://spatialreference.org/ref/epsg/2154/esriwkt/

#class SpatialRefOrg():



######################################
#http://prj2epsg.org/search

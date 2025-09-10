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
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	 See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#  All rights reserved.
#  ***** GPL LICENSE BLOCK *****
import logging
import ssl
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json

log = logging.getLogger(__name__)

from .. import settings

USER_AGENT = settings.user_agent

DEFAULT_TIMEOUT = 2
REPROJ_TIMEOUT = 60

######################################
# EPSG.io
# https://github.com/klokantech/epsg.io


class EPSGIO():

	@staticmethod
	def ping():
		url = "https://epsg.io"
		try:
			rq = Request(url, headers={'User-Agent': USER_AGENT})
			urlopen(rq, timeout=DEFAULT_TIMEOUT)
			return True
		except (URLError, ssl.SSLError) as e:
			log.error('Cannot ping {} web service, {}'.format(url, getattr(e, 'reason', e)))
			return False
		except HTTPError as e:
			# urlopen handles redirects but we still log HTTP errors
			log.error('Cannot ping {} web service, http error {}'.format(url, e.code))
			return False
		except Exception:
			raise


	@staticmethod
	def reprojPt(epsg1, epsg2, x1, y1):

		params = {
			'x': x1,
			'y': y1,
			'z': 0,
			'source': epsg1,
			'target': epsg2
		}

		url = "https://epsg.io/trans?" + urlencode(params)
		log.debug(url)

		try:
			rq = Request(url, headers={'User-Agent': USER_AGENT})
			response = urlopen(rq, timeout=REPROJ_TIMEOUT).read().decode('utf8')
		except (URLError, HTTPError, ssl.SSLError) as err:
			reason = getattr(err, 'reason', err)
			code = getattr(err, 'code', 'n/a')
			log.error('Http request fails url:{}, code:{}, error:{}'.format(url, code, reason))
			raise

		obj = json.loads(response)
		res = obj.get('result') or obj.get('results') or obj
		if isinstance(res, list):
			res = res[0]

		return (float(res['x']), float(res['y']))

	@staticmethod
	def reprojPts(epsg1, epsg2, points):

		if len(points) == 1:
			x, y = points[0]
			return [EPSGIO.reprojPt(epsg1, epsg2, x, y)]

		paramsTemplate = {
			'source': epsg1,
			'target': epsg2,
			'points': None
		}

		precision = 4
		data = [','.join([str(round(v, precision)) for v in p]) for p in points]
		part, parts = [], []
		for i, p in enumerate(data):
			l = sum([len(p) for p in part]) + len(';' * len(part))
			if l + len(p) < 4000:  # limit is 4094
				part.append(p)
			else:
				parts.append(part)
				part = [p]
			if i == len(data) - 1:
				parts.append(part)
		parts = [';'.join(part) for part in parts]

		result = []
		for part in parts:
			paramsTemplate['points'] = part
			url = "https://epsg.io/trans?" + urlencode(paramsTemplate)
			log.debug(url)

			try:
				rq = Request(url, headers={'User-Agent': USER_AGENT})
				response = urlopen(rq, timeout=REPROJ_TIMEOUT).read().decode('utf8')
			except (URLError, HTTPError, ssl.SSLError) as err:
				reason = getattr(err, 'reason', err)
				code = getattr(err, 'code', 'n/a')
				log.error('Http request fails url:{}, code:{}, error:{}'.format(url, code, reason))
				raise

			obj = json.loads(response)
			pts = obj.get('results') or obj.get('result') or obj
			result.extend([(float(p['x']), float(p['y'])) for p in pts])

		return result

	@staticmethod
	def search(query):
		query = str(query).strip()
		params = {'query': query, 'format': 'json'}
		url = "https://epsg.io/?" + urlencode(params)
		log.debug('Search crs : {}'.format(url))
		try:
			rq = Request(url, headers={'User-Agent': USER_AGENT})
			response = urlopen(rq, timeout=DEFAULT_TIMEOUT).read().decode('utf8')
		except (URLError, HTTPError, ssl.SSLError) as err:
			reason = getattr(err, 'reason', err)
			code = getattr(err, 'code', 'n/a')
			log.error('Http request fails url:{}, code:{}, error:{}'.format(url, code, reason))
			raise
		obj = json.loads(response)
		results = obj.get('results') or obj.get('result') or obj.get('data', [])
		log.debug('Search results : {}'.format([(r.get('code'), r.get('name')) for r in results]))
		return results

	@staticmethod
	def getEsriWkt(epsg):
		url = "https://epsg.io/{CODE}.esriwkt"
		url = url.replace("{CODE}", str(epsg))
		log.debug(url)
		try:
			rq = Request(url, headers={'User-Agent': USER_AGENT})
			wkt = urlopen(rq, timeout=DEFAULT_TIMEOUT).read().decode('utf8')
		except (URLError, HTTPError, ssl.SSLError) as err:
			reason = getattr(err, 'reason', err)
			code = getattr(err, 'code', 'n/a')
			log.error('Http request fails url:{}, code:{}, error:{}'.format(url, code, reason))
			raise
		return wkt




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

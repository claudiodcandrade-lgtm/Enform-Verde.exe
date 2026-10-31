"""Paginated Copernicus STAC discovery with acquisition provenance.

Discovery is not a crop classifier or a calibrated SAR time series.
"""
import json
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ENDPOINT = 'https://stac.dataspace.copernicus.eu/v1/search'
HOST = 'stac.dataspace.copernicus.eu'


def search_sentinel1(aoi, days=90, *, now=None, page_size=100, max_pages=20, opener=urlopen):
    if not isinstance(aoi, dict) or aoi.get('type') not in ('Polygon', 'MultiPolygon') or not aoi.get('coordinates'):
        raise ValueError('AOI GeoJSON Polygon/MultiPolygon required (EPSG:4326)')
    if not isinstance(days, int) or not 1 <= days <= 730:
        raise ValueError('days must be 1..730')
    if not isinstance(page_size, int) or not 1 <= page_size <= 100:
        raise ValueError('page_size must be 1..100')
    if not isinstance(max_pages, int) or not 1 <= max_pages <= 100:
        raise ValueError('max_pages must be 1..100')
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError('now must be timezone-aware')
    start = now - timedelta(days=days)
    payload = {'collections': ['sentinel-1-grd'], 'intersects': aoi,
               'datetime': start.isoformat() + '/' + now.isoformat(), 'limit': page_size}
    url, method, headers = ENDPOINT, 'POST', {'Content-Type': 'application/json', 'Accept': 'application/geo+json'}
    results, seen, pages = [], set(), 0
    while url and pages < max_pages:
        if urlparse(url).hostname != HOST or urlparse(url).scheme != 'https':
            raise ValueError('Untrusted STAC pagination URL')
        request = Request(url, data=json.dumps(payload).encode() if method == 'POST' else None,
                          headers=headers, method=method)
        with opener(request, timeout=60) as response:
            data = json.load(response)
        pages += 1
        for item in data.get('features', []):
            ident = item.get('id')
            if not ident or ident in seen:
                continue
            seen.add(ident)
            p = item.get('properties') or {}
            results.append({'id': ident, 'acquisition_utc': p.get('datetime') or p.get('start_datetime'),
                            'published_utc': p.get('published') or p.get('created'),
                            'platform': p.get('platform'), 'polarizations': p.get('sar:polarizations'),
                            'orbit_state': p.get('sat:orbit_state'), 'relative_orbit': p.get('sat:relative_orbit'),
                            'incidence_angle': p.get('view:incidence_angle'),
                            'assets': item.get('assets', {}), 'source': ENDPOINT})
        link = next((x for x in data.get('links', []) if x.get('rel') == 'next'), None)
        if link:
            url = link['href']
            method = link.get('method', 'GET').upper()
            if method not in ('GET', 'POST'):
                raise ValueError('Unsupported pagination method')
            payload = link.get('body', {}) if method == 'POST' else None
            headers = {'Content-Type': 'application/json', 'Accept': 'application/geo+json'}
        else:
            url = None
    return {'scenes': results, 'pages': pages, 'truncated': bool(url),
            'query_utc': now.isoformat(), 'source': ENDPOINT,
            'status': 'discovery_only', 'classification_performed': False}

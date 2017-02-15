import json

import bs4
import requests

from django.conf import settings
from django.core.cache import cache

IA_DOWNLOAD_URL = 'https://archive.org/download'
IA_SEGMENT_CACHE_KEY = 'ARCHIVE:segment-meta:%s'
IA_SEGMENT_CACHE_TIMEOUT = settings.IA_SEGMENT_CACHE_TIMEOUT

# https://archive.org/download/ddr-densho-1003-1-24/ddr-densho-1003-1-24_files.xml
SEGMENT_XML_URL = '{base}/{segmentid}/{segmentid}_files.xml'

# https://archive.org/download/ddr-densho-1003-1-24/ddr-densho-1003-1-24-mezzanine-2b247c16c0.mp4
FILE_DOWNLOAD_URL = '{base}/{segmentid}/{fileid}'


def segment_download_meta(sid):
    """Get segment file metadata from Archive.org
    """
    key = IA_SEGMENT_CACHE_KEY % sid
    cached = cache.get(key)
    if not cached:
        FORMATS = ['mp3', 'mp4', 'mpg', 'ogv', 'png',]
        data = {
            'xml_url': SEGMENT_XML_URL.format(base=IA_DOWNLOAD_URL, segmentid=sid),
        }
        r = requests.get(data['xml_url'])
        if r.status_code != 200:
            return data
        soup = bs4.BeautifulSoup(r.text)
        for tag in soup.files.children:
            if isinstance(tag, bs4.element.Tag):
                for f in FORMATS:
                    if f in tag['name']:
                        data[f] = {
                            'url': FILE_DOWNLOAD_URL.format(
                                base=IA_DOWNLOAD_URL,
                                segmentid=sid,
                                fileid=tag['name']
                            ),
                            'size': tag.size.contents[0],
                        }
        text = json.dumps(data)
        cache.set(key, text, IA_SEGMENT_CACHE_TIMEOUT)
        return data
    return json.loads(cached)
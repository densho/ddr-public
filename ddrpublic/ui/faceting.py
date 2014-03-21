import json
import re

from django.conf import settings
from django.core.cache import cache
from django.core.urlresolvers import reverse

from DDR import docstore

CACHE_TIMEOUT = 60 * 60 * 24 # 1 day


def facets_list():
    """Returns a list of facets in alphabetical order, with URLs
    """
    key = 'facets:list'
    cached = cache.get(key)
    if not cached:
        facets_list = []
        for name in docstore.list_facets():
            document = docstore.get(settings.DOCSTORE_HOSTS, index=settings.DOCSTORE_INDEX,
                                    model='facet', document_id=name)
            f = document['_source']
            f['name'] = name
            f['url'] = reverse('ui-browse-facet', args=[name])
            facets_list.append(f)
        cached = facets_list
        cache.set(key, cached, CACHE_TIMEOUT)
    return cached

def get_facet(name):
    """
    TODO Rethink this: we are getting all the terms and then throwing them away
         except for the one we want; just get the one we want.
    """
    key = 'facets:%s' % name
    cached = cache.get(key)
    if not cached:
        for f in facets_list():
            if f['name'] == name:
                if f['name'] in ['facility', 'topics']:
                    f['terms'] = sorted(f['terms'], key=lambda x: x['title'])
                cached = f
                cache.set(key, cached, CACHE_TIMEOUT)
    return cached

INT_IN_STRING = re.compile(r'^\d+$')

def extract_term_id( text ):
    """
    >>> extract_term_id('Manzanar [7]')
    '7'
    >>> extract_term_id('[7]')
    '7'
    >>> extract_term_id('7')
    '7'
    >>> extract_term_id(7)
    '7'
    """
    if ('[' in text) and (']' in text):
        term_id = text.split('[')[1].split(']')[0]
    elif re.match(INT_IN_STRING, text):
        term_id = text
    else:
        term_id = text
    return term_id

def facet_terms(facet):
    """
    If term is precoordinate all the terms are listed, with count of number of occurances (if any).
    If term is postcoordinate, all the terms come from the index, but there is not title/description.
    """
    facetterms = []
    results = docstore.facet_terms(settings.DOCSTORE_HOSTS,
                                   settings.DOCSTORE_INDEX, facet['name'], order='term')
    if facet.get('terms', []):
        # precoordinate
        # IMPORTANT: topics and facility term IDs are int. All others are str.
        term_counts = {}
        for t in results['terms']:
            term_id = extract_term_id(t['term'])
            term_count = t['count']
            if term_id and term_count:
                term_counts[term_id] = term_count
        # make URLs for terms
        for term in facet['terms']:
            term['url'] = reverse('ui-search-term-query', args=(facet['id'], term['id']))
        # add counts to terms
        for term in facet['terms']:
            term_id = term['id']
            if isinstance(term_id, int):
                term_id = str(term_id)
            term['count'] = term_counts.get(term_id, 0)
            facetterms.append(term)
    else:
        # postcoordinate
        for t in results['terms']:
            t['title'] = t['term']
            t['description'] = ''
            t['url'] = '/search/%s:%s/' % (facet['id'], t['term'])
            facetterms.append(t)
    return facetterms

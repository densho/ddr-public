from copy import deepcopy
from datetime import datetime
import json
import logging
logger = logging.getLogger(__name__)

from dateutil import parser
import requests

from django.conf import settings
from django.core.cache import cache
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import Http404, get_object_or_404, render_to_response
from django.template import RequestContext
from django.utils.http import urlquote  as django_urlquote

from DDR import docstore
from ui.identifier import Identifier, MODEL_CLASSES
from ui import domain_org
from ui import faceting
from ui import models
from ui.forms import SearchForm
from ui import api

# TODO We should have a whitelist of chars we *do* accept, not this.
SEARCH_INPUT_BLACKLIST = ('{', '}', '[', ']')


# helpers --------------------------------------------------------------

def kosher( query ):
    for char in SEARCH_INPUT_BLACKLIST:
        if char in query:
            return False
    return True

def force_list(terms):
    if isinstance(terms, list):
        return terms
    elif isinstance(terms, basestring):
        return [terms]
    raise Exception('Not a list or a string')


# views ----------------------------------------------------------------

def index( request ):
    return render_to_response(
        'ui/search/index.html',
        {
            'hide_header_search': True,
            'search_form': SearchForm,
        },
        context_instance=RequestContext(request, processors=[])
    )

def results(request):
    """Results of a search query or a DDR ID query.
    """
    form = SearchForm(request.GET)
    form.is_valid()
    
    thispage = int(request.GET.get('page', 1))
    pagesize = settings.RESULTS_PER_PAGE
    
    # query dict
    query = {
        'fulltext': form.cleaned_data.get('fulltext', ''),
        'must': [],
        'models': form.cleaned_data.get('models', []),
        'offset': thispage - 1,
        'limit': pagesize,
    }
    if form.cleaned_data.get('language'):
        query['must'].append(
            {"terms": {"language": force_list(form.cleaned_data['language'])}}
        )
    if form.cleaned_data.get('topics'):
        query['must'].append(
            {"terms": {"topics": force_list(form.cleaned_data['topics'])}}
        )
    
    # remove match _all from must, keeping fulltext arg
    for item in query['must']:
        if item.get('match') \
        and item['match'].get('_all') \
        and (item['match']['_all'] == query.get('fulltext')):
            query['must'].remove(item)
    
    # run query
    paginator = None
    page = None
    if query['fulltext'] or query['must']:
        r = requests.post("http://192.168.56.120/api/0.2/search/", data=query)
        results = json.loads(r.text)
        objects = api.pad_results(results, pagesize, thispage)
        paginator = Paginator(objects, pagesize)
        page = paginator.page(thispage)
    
    return render_to_response(
        'ui/search/results.html',
        {
            'query': query,
            'search_form': form,
            'paginator': paginator,
            'page': page,
        },
        context_instance=RequestContext(request, processors=[])
    )

def term_query( request, field, term ):
    """Results of what ElasticSearch calls a 'term query'.
    """
    terms_display = {'field':field, 'term':term}
    filters = {}
    
    # silently strip out bad chars
    for char in SEARCH_INPUT_BLACKLIST:
        field = field.replace(char, '')
        term = term.replace(char, '')
    
    # prep query for elasticsearch
    terms = {field:term}
    facet = faceting.get_facet(field)
    for t in facet['terms']:
        if t['id'] == term:
            try:
                terms_display['term'] = t['title_display']
            except:
                terms_display['term'] = t['title']
            break
    
    # filter by partner
    repo,org = domain_org(request)
    if repo and org:
        filters['repo'] = repo
        filters['org'] = org
    
    fields = models.all_list_fields()
    sort = {'record_created': request.GET.get('record_created', ''),
            'record_lastmod': request.GET.get('record_lastmod', ''),}
    
    # do the query
    results = models.cached_query(settings.DOCSTORE_HOSTS, settings.DOCSTORE_INDEX,
                                  terms=terms, filters=filters,
                                  fields=fields, sort=sort)
    thispage = request.GET.get('page', 1)
    massaged = models.massage_query_results(results, thispage, settings.RESULTS_PER_PAGE)
    objects = models.instantiate_query_objects(massaged)
    paginator = Paginator(objects, settings.RESULTS_PER_PAGE)
    page = paginator.page(request.GET.get('page', 1))
    return render_to_response(
        'ui/search/results.html',
        {
            'hide_header_search': True,
            'paginator': paginator,
            'page': page,
            'terms': terms_display,
            'filters': filters,
            'sort': sort,
        },
        context_instance=RequestContext(request, processors=[])
    )

import json
from urllib2 import urlparse

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404, redirect, render_to_response
from django.template import RequestContext
from django.views.decorators.http import require_http_methods

from names.forms import SearchForm, FlexiSearchForm
from names import models

HOSTS = settings.NAMESDB_DOCSTORE_HOSTS
INDEX = models.set_hosts_index(HOSTS, settings.NAMESDB_DOCSTORE_INDEX)


@require_http_methods(['GET',])
def index(request, template_name='names/index.html'):
    body = None
    records = []
    if 'query' in request.GET:
        form = SearchForm(request.GET, hosts=HOSTS, index=INDEX)
        if form.is_valid():
            filters = form.cleaned_data
            query = filters.pop('query')
            body,records = models.search(
                HOSTS, INDEX,
                query=query,
                filters=filters,
            )
            if body:
                body = json.dumps(body, indent=4, separators=(',', ': '), sort_keys=True)
    else:
        form = SearchForm(hosts=HOSTS, index=INDEX)
    return render_to_response(
        template_name,
        {
            'form': form,
            'body': body,
            'records': records,
        },
        context_instance=RequestContext(request)
    )


@require_http_methods(['GET',])
def search(request, template_name='names/search.html'):
    """
    specify filter field names and optional values in URL/request.GET
    form constructs itself with those fields
    each field has aggregation (list of choices with counts)
    form contains the list of fields
    flexible: lets user construct "impossible" forms (e.g. both FAR and WRA fields)
    """
    qs = request.META['QUERY_STRING']
    # list of filter fields from URL
    # used to build form
    default_filters = ['m_dataset', 'm_camp', 'm_originalstate',]
    non_filter_fields = ['query']
    filters = [
        field
        for field in urlparse.parse_qs(qs, keep_blank_values=1).iterkeys()
        if field not in non_filter_fields
    ]
    if not filters:
        filters = default_filters
    # kwargs for display to user
    kwargsdict = urlparse.parse_qs(qs, keep_blank_values=1)
    kwargs = [
        [key,val]
        for key,val in kwargsdict.iteritems()
    ]
    
    body = None
    records = []
    if 'query' in request.GET:
        form = FlexiSearchForm(request.GET, hosts=HOSTS, index=INDEX, filters=filters)
        if form.is_valid():
            filters = form.cleaned_data
            query = filters.pop('query')
            body,records = models.search(
                HOSTS, INDEX,
                query=query,
                filters=filters,
            )
            if body:
                body = json.dumps(body, indent=4, separators=(',', ': '), sort_keys=True)
    else:
        form = FlexiSearchForm(hosts=HOSTS, index=INDEX, filters=filters)
    return render_to_response(
        template_name,
        {
            'kwargs': kwargs,
            'form': form,
            'body': body,
            'records': records,
        },
        context_instance=RequestContext(request)
    )


@require_http_methods(['GET',])
def detail(request, id, template_name='names/detail.html'):
    record = models.Rcrd.get(id=id)
    record.other_datasets = models.other_datasets(HOSTS, INDEX, record)
    record.family_members = models.same_familyno(HOSTS, INDEX, record)
    return render_to_response(
        template_name,
        {
            'record': record,
        },
        context_instance=RequestContext(request)
    )

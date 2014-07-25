import logging
logger = logging.getLogger(__name__)

from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import Http404, get_object_or_404, render_to_response
from django.template import RequestContext

from ui import domain_org
from ui.models import Repository, Organization, Collection, Entity, File
from ui.models import DEFAULT_SIZE


# views ----------------------------------------------------------------

def detail( request, repo, org, cid, eid ):
    partner = domain_org(request)
    if partner and (org != partner):
        raise Http404
    entity = Entity.get(repo, org, cid, eid)
    if not entity:
        raise Http404
    organization = Organization.get(entity.repo, entity.org)
    thispage = 1
    objects = entity.files(thispage, DEFAULT_SIZE)
    paginator = Paginator(objects, DEFAULT_SIZE)
    page = paginator.page(thispage)
    return render_to_response(
        'ui/entities/detail.html',
        {
            'repo': repo,
            'org': org,
            'cid': cid,
            'eid': eid,
            'object': entity,
            'organization': organization,
            'paginator': paginator,
            'page': page,
        },
        context_instance=RequestContext(request, processors=[])
    )

def files( request, repo, org, cid, eid ):
    """Lists all the files in an entity.
    """
    partner = domain_org(request)
    if partner and (org != partner):
        raise Http404
    entity = Entity.get(repo, org, cid, eid)
    if not entity:
        raise Http404
    thispage = request.GET.get('page', 1)
    objects = entity.files(thispage, settings.RESULTS_PER_PAGE)
    paginator = Paginator(objects, settings.RESULTS_PER_PAGE)
    page = paginator.page(thispage)
    return render_to_response(
        'ui/entities/files.html',
        {
            'repo': repo,
            'org': org,
            'cid': cid,
            'eid': eid,
            'object': entity,
            'paginator': paginator,
            'page': page,
        },
        context_instance=RequestContext(request, processors=[])
    )

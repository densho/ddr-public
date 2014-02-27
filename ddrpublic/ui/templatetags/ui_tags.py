import datetime
from django import template

register = template.Library()


def collection( obj ):
    """list-view collection template
    """
    t = template.loader.get_template('ui/collections/list-object.html')
    return t.render(template.Context({'object':obj}))

def entity( obj ):
    """list-view entity template
    """
    t = template.loader.get_template('ui/entities/list-object.html')
    return t.render(template.Context({'object':obj}))

def file( obj ):
    """list-view file template
    """
    t = template.loader.get_template('ui/files/list-object.html')
    return t.render(template.Context({'object':obj}))


def addthis():
    """AddThis button
    """
    t = template.loader.get_template('ui/addthis.html')
    return t.render(template.Context({}))

def cite( url ):
    """Citation tag
    """
    t = template.loader.get_template('ui/cite-tag.html')
    c = template.Context({'url':url})
    return t.render(c)

register.simple_tag(collection)
register.simple_tag(entity)
register.simple_tag(file)
register.simple_tag(addthis)
register.simple_tag(cite)

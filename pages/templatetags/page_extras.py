from django import template
from django.template.defaultfilters import stringfilter

register=template.Library()

@register.filter(name="highlighttext", is_safe=True)
@stringfilter
def highlighttext(text,target):
    print ("Doing stuff")
    return text.replace(target,'<span style="color: #AA0000; bg-color: AAAA00;">%s</span>'%target)


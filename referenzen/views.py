from django.shortcuts import render
from .models import Referenz
from abschnitte.utils import render_textabschnitte

# Create your views here.
def tree(request):
    referenz_items = Referenz.objects.all()
    return render(request, 'referenz_tree.html', {'referenzen': referenz_items})


def detail(request, refid):
    referenz_item = Referenz.objects.get(id=refid)
    referenz_item.erklaerung = render_textabschnitte(referenz_item.referenzerklaerung_set.order_by("order"))
    referenz_item.children = list(referenz_item.get_descendants(include_self=True))
    for child in referenz_item.children:
        child.referenziertvon = child.vorgabe_set.all()
    if not referenz_item.is_root_node():
        referenz_item.ParentID = referenz_item.get_ancestors(ascending=True)[0].id
    return render(request, 'referenz_detail.html', {'referenz': referenz_item})



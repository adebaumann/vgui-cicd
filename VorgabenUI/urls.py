"""
URL configuration for VorgabenUI project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path, re_path
from django.conf import settings
from django.conf.urls.static import static
from diagramm_proxy.views import DiagrammProxyView
import dokumente.views
import pages.views
import referenzen.views

admin.site.site_header="Autorenumgebung"

urlpatterns = [
    path('',pages.views.startseite),
    path('search/',pages.views.search),
    path('dokumente/', include("dokumente.urls")),
    path('autorenumgebung/', admin.site.urls),
    path('stichworte/', include("stichworte.urls")),
    path('referenzen/', referenzen.views.tree, name="referenz_tree"),
    path('referenzen/<str:refid>/', referenzen.views.detail, name="referenz_detail"),
    re_path(r'^diagramm/(?P<path>.*)$', DiagrammProxyView.as_view()),
]

# Serve static files
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Serve media files (including cached diagrams)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

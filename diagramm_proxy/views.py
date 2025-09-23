from revproxy.views import ProxyView

class DiagrammProxyView(ProxyView):
    upstream = "http://kroki:8000/"

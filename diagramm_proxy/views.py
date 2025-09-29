from revproxy.views import ProxyView

class DiagrammProxyView(ProxyView):
    upstream = "http://svckroki:8000/"

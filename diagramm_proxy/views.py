from revproxy.views import ProxyView

class DiagrammProxyView(ProxyView):
    upstream = "http://localhost:8001/"

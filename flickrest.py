import md5, urllib
from twisted.internet import defer
from twisted.python.failure import Failure
from twisted.web import client
from elementtree import ElementTree

class FlickrError(Exception):
    def __init__(self, code, message):
        Exception.__init__(self)
        self.code = int(code)
        self.message = message
    
    def __str__(self):
        return "%d: %s" % (self.code, self.message)

class FlickREST:
    endpoint = "http://api.flickr.com/services/rest/?"
    
    def __init__(self, api_key, secret, perms="read"):
        self.__methods = {}
        self.api_key = api_key
        self.secret = secret
        self.perms = perms
        self.token = None
    
    def __sign(self, kwargs):
        kwargs['api_key'] = self.api_key
        # If authenticating we don't yet have a token
        if self.token:
            kwargs['auth_token'] = self.token
        s = []
        for key in kwargs.keys():
            s.append("%s%s" % (key, kwargs[key]))
        s.sort()
        sig = md5.new(self.secret + ''.join(s)).hexdigest()
        kwargs['api_sig'] = sig

    def __getattr__(self, method, **kwargs):
        if not self.__methods.has_key(method):
            real_method = "flickr." + method.replace("_", ".")
            def proxy(method=real_method, **kwargs):
                kwargs["method"] = method
                self.__sign(kwargs)
                d = defer.Deferred()
                def cb(data):
                    xml = ElementTree.XML(data.encode("utf-8"))
                    if xml.get("stat") == "ok":
                        d.callback(xml)
                    else:
                        err = xml.find("err")
                        d.errback(Failure(FlickrError(err.get("code"), err.get("msg"))))
                def errcb(fault):
                    d.errback(fault)
                client.getPage(FlickREST.endpoint, method="POST",
                               headers={"Content-Type": "application/x-www-form-urlencoded"},
                               postdata=urllib.urlencode(kwargs)).addCallbacks(cb, errcb)
                return d
            self.__methods[method] = proxy
        return self.__methods[method]
        
if __name__ == "__main__":
    from twisted.internet import reactor
    flickr = FlickREST("c53cebd15ed936073134cec858036f1d", "7db1b8ef68979779", "read")
    d = flickr.auth_getFrob()
    def foo(p):
        print ElementTree.dump(p)
    def error(failure):
        print failure
    d.addCallbacks(foo, error)
    reactor.run()

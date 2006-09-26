import md5, urllib
from twisted.internet import defer
from twisted.web import client
from elementtree import ElementTree

class FlickREST:
    endpoint = "http://api.flickr.com/services/rest/?"
    
    def __init__(self, api_key, secret, perms="read"):
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

    def call(self, method, **kwargs):
        kwargs["method"] = method
        self.__sign(kwargs)
        d = defer.Deferred()
        def cb(data):
            xml = ElementTree.XML(data.encode("utf-8"))
            d.callback(xml)
            client.getPage(FlickREST.endpoint, method="POST",
                           headers={"Content-Type": "application/x-www-form-urlencoded"},
                           postdata=urllib.urlencode(kwargs)).addCallback(cb)
        return d
        
if __name__ == "__main__":
    from twisted.internet import reactor
    flickr = FlickREST("c53cebd15ed936073134cec858036f1d", "7db1b8ef68979779", "read")
    d = flickr.call("flickr.auth.getFrob")
    def foo(p):
        print p
    d.addCallback(foo)
    reactor.run()

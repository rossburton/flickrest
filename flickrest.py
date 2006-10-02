import md5, os, urllib
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

class Flickr:
    endpoint = "http://api.flickr.com/services/rest/?"
    
    def __init__(self, api_key, secret, perms="read"):
        self.__methods = {}
        self.api_key = api_key
        self.secret = secret
        self.perms = perms
        self.token = None

    def __repr__(self):
        return "<FlickREST>"
    
    def __getTokenFile(self):
        """Get the filename that contains the authentication token for the API key"""
        return os.path.expanduser(os.path.join("~", ".flickr", self.api_key, "auth.xml"))
    
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

    def __call(self, method, kwargs):
        kwargs["method"] = method
        self.__sign(kwargs)
        return client.getPage(Flickr.endpoint, method="POST",
                              headers={"Content-Type": "application/x-www-form-urlencoded"},
                              postdata=urllib.urlencode(kwargs))
        
    def __getattr__(self, method, **kwargs):
        method = "flickr." + method.replace("_", ".")
        if not self.__methods.has_key(method):
            def proxy(method=method, **kwargs):
                d = defer.Deferred()
                def cb(data):
                    xml = ElementTree.XML(data)
                    if xml.tag == "rsp" and xml.get("stat") == "ok":
                        d.callback(xml)
                    elif xml.tag == "rsp" and xml.get("stat") == "fail":
                        err = xml.find("err")
                        d.errback(Failure(FlickrError(err.get("code"), err.get("msg"))))
                    else:
                        # Fake an error in this case
                        d.errback(Failure(FlickrError(0, "Invalid response")))
                self.__call(method, kwargs).addCallbacks(cb, lambda fault: d.errback(fault))
                return d
            self.__methods[method] = proxy
        return self.__methods[method]

    def authenticate(self):
        """Attemps to log in to Flickr.  This will open a web browser if
        required. The return value is a Twisted Deferred object that callbacks
        when authentication is complete."""
        filename = self.__getTokenFile()
        if os.path.exists(filename):
            e = ElementTree.parse(filename).getroot()
            self.token = e.find("token").text
            return defer.succeed(True)
        
        d = defer.Deferred()
        def gotFrob(xml):
            frob = xml.text
            keys = { 'perms': self.perms,
                     'frob': frob }
            self.__sign(keys)
            url = "http://flickr.com/services/auth/?api_key=%(api_key)s&perms=%(perms)s&frob=%(frob)s&api_sig=%(api_sig)s" % keys
            # TODO: signal or something
            os.spawnlp(os.P_WAIT, "epiphany", "epiphany", "-p", url)
            
            def gotToken(e):
                # Set the token
                self.token = e.find("token").text
                # Cache the authentication
                filename = self.__getTokenFile()
                path = os.path.dirname(filename)
                if not os.path.exists(path):
                    os.makedirs(path, 0700)
                f = file(filename, "w")
                f.write(ElementTree.tostring(e.find("auth")))
                f.close()
                # Callback to the user
                d.callback(True)
            # TODO: chain up the error callbacks too
            self.auth_getToken(frob=frob).addCallback(gotToken)
        
        # TODO: chain up the error callbacks too
        flickr.auth_getFrob().addCallback(gotFrob)
        return d

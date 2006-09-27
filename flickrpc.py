from twisted.python.failure import Failure
from twisted.internet import defer
from twisted.web.xmlrpc import Proxy
from elementtree import ElementTree
import os, md5, xmlrpclib

class FlickrError(Exception):
    def __init__(self, code, message):
        Exception.__init__(self)
        self.code = int(code)
        self.message = message
    
    def __str__(self):
        return "%d: %s" % (self.code, self.message)

class FlickRPC:    
    def __init__(self, api_key, secret, perms="read"):
        self.__methods = {}
        self.proxy = Proxy("http://api.flickr.com/services/xmlrpc/")
        self.api_key = api_key
        self.secret = secret
        self.perms = perms
        self.token = None

    def __repr__(self):
        return self.__str__()
    def __str__(self):
        return "FlickRPC"
    
    @staticmethod
    def __failure(exception):
        """Take a xmlrpclib.Fault object and return a new Twisted Failure object."""
        if isinstance(exception, xmlrpclib.Fault):
            return Failure(FlickrError(exception.faultCode,
                                       exception.faultString))
        else:
            return Failure(FlickrError(0, str(exception)))
    
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
    
    def __getTokenFile(self):
        """Get the filename that contains the authentication token for the API key"""
        return os.path.expanduser(os.path.join("~", ".flickr", self.api_key, "auth.xml"))
    
    def __getattr__(self, method, **kwargs):
        """Magic automatic method generation. Take the Flickr method name
        (flickr.favorites.getList), remove the flickr. prefix
        (favorites.getList) and replace all . with _ (favorite_getList).  Then
        pass keyword arguments as required.  The return value is a Twisted
        Deferred object"""
        method = "flickr." + method.replace("_", ".")
        if not self.__methods.has_key(method):
            def proxy(method=method, **kwargs):
                d = defer.Deferred()
                self.__sign(kwargs)
                # TODO: do I have to convert a Unicode string to UTF-8 to parse it?
                self.proxy.callRemote(method, kwargs).addCallbacks(
                    lambda data: d.callback(ElementTree.XML(data.encode("utf-8"))),
                    lambda fault: d.errback(FlickRPC.__failure(fault.value)))
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
                f.write(ElementTree.tostring(e))
                f.close()
                # Callback to the user
                d.callback(True)
            # TODO: chain up the error callbacks too
            self.auth_getToken(frob=frob).addCallback(gotToken)
        
        # TODO: chain up the error callbacks too
        flickr.auth_getFrob().addCallback(gotFrob)
        return d

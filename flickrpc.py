#! /usr/bin/python

from twisted.internet import reactor, defer
from twisted.web.xmlrpc import Proxy
from elementtree import ElementTree
import os, md5

class FlickRPC:    
    def __init__(self, api_key, secret, perms="read"):
        self.proxy = Proxy("http://api.flickr.com/services/xmlrpc/")
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
        
    def __getTokenFile(self):
        return os.path.expanduser(os.path.join("~", ".flickr", self.api_key, "auth.xml"))

    def call(self, method, **kwargs):
        d = defer.Deferred()
        self.__sign(kwargs)
        # TODO: do I have to convert a Unicode string to UTF-8 to parse it?
        self.proxy.callRemote(method, kwargs).addCallback(
            lambda data: d.callback(ElementTree.XML(data.encode("utf-8"))))
        return d

    
    def authenticate(self):
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
            self.call("flickr.auth.getToken", frob=frob).addCallback(gotToken)
        
        flickr.call("flickr.auth.getFrob").addCallback(gotFrob)
        return d


if __name__ == "__main__":
    flickr = FlickRPC("c53cebd15ed936073134cec858036f1d", "7db1b8ef68979779", "read")
    def done(authenticated):
        def gotInfo(p):
            print p.find("title").text
        def gotFavs(p):
            for photo in p.findall("photo"):
                print photo.get('title')
            reactor.stop()
        flickr.call("flickr.favorites.getList").addCallback(gotFavs)
        #flickr.call("flickr.photos.getInfo", photo_id="209423026").addCallback(gotInfo)
    
    flickr.authenticate().addCallback(done)
    reactor.run()

#! /usr/bin/python

from twisted.internet import reactor
from flickrpc import FlickRPC

if __name__ == "__main__":
    flickr = FlickRPC("c53cebd15ed936073134cec858036f1d", "7db1b8ef68979779", "read")
    def connected(authenticated):
        def gotInfo(p):
            print "Got photo title '%s'" % p.find("title").text
        def gotFavs(p):
            print "Got favourites:"
            for photo in p.findall("photo"):
                print "  %s" % photo.get('title')        
        flickr.favorites_getList().addCallback(gotFavs)
        flickr.photos_getInfo(photo_id="209423026").addCallback(gotInfo)

    flickr.authenticate().addCallback(connected)
    reactor.run()

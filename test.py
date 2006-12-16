#! /usr/bin/python

from twisted.internet import reactor
#from flickrpc import Flickr
from flickrest import Flickr

if __name__ == "__main__":
    flickr = Flickr("c53cebd15ed936073134cec858036f1d", "7db1b8ef68979779", "write")
    def connected(authenticated):
        def gotInfo(p):
            print "Got photo title '%s'" % p.find("photo/title").text
        def gotFavs(p):
            print "Got favourites:"
            for photo in p.findall("photos/photo"):
                print "  %s" % photo.get('title')
        def uploaded(p):
            print p
        flickr.photos_getInfo(photo_id="209423026").addCallback(gotInfo)
        #flickr.favorites_getList().addCallback(gotFavs)
        #flickr.upload(filename="/home/ross/Pictures/Photos/Artwork/snow-grass.jpg", title="Snow Grass", desc="some grass", tags="test green grass").addCallback(uploaded)
    flickr.authenticate().addCallback(connected)
    reactor.run()

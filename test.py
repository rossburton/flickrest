#! /usr/bin/python

from twisted.internet import reactor
from flickrest import Flickr

if __name__ == "__main__":
    flickr = Flickr("c53cebd15ed936073134cec858036f1d", "7db1b8ef68979779", "write")

    def error(failure):
        print failure.getErrorMessage()
        reactor.stop()
    
    def connected(authenticated):
        def gotInfo(p):
            print "Got photo title '%s'" % p.find("photo/title").text
        flickr.photos_getInfo(photo_id="209423026").addCallbacks(gotInfo, error)
        
        def gotFavs(p):
            print "Got favourites:"
            for photo in p.findall("photos/photo"):
                print "  %s" % photo.get('title')
        #flickr.favorites_getList().addCallbacks(gotFavs, error)
        
        def uploaded(p):
            print p
        #flickr.upload(filename="/home/ross/Pictures/Photos/Artwork/snow-grass.jpg",
        #              title="Snow Grass",
        #              desc="some grass",
        #              tags="test green grass").addCallbacks(uploaded, error)
    
    def auth_open_url(state):
        # If the URL to open is None, then we have cached authentication tokens
        # available.
        if state is None:
            connected(True)
        # Otherwise, open the URL and call authenticate_2 once the user has
        # authenticated us.
        else:
            os.spawnlp(os.P_WAIT, "epiphany", "epiphany", "-p", state['url'])
            self.authenticate_2(state).addCallbacks(connected, error)

    flickr.authenticate_1().addCallbacks(auth_open_url, error)
    reactor.run()

#! /usr/bin/python

# flickrpc -- a Flickr client library.
#
# Copyright (C) 2007 Ross Burton <ross@burtonini.com>
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51 Franklin
# St, Fifth Floor, Boston, MA 02110-1301 USA

from twisted.internet import reactor
from flickrest import Flickr

import logging
logging.basicConfig(level=logging.DEBUG)

if __name__ == "__main__":
    flickr = Flickr("c53cebd15ed936073134cec858036f1d", "7db1b8ef68979779", "write")

    def error(failure):
        print failure.getErrorMessage()
        reactor.stop()
    
    def connected(authenticated):
        def gotInfo(p):
            print "Got photo title '%s'" % p.find("photo/title").text
        flickr.photos_getInfo(photo_id="351812586").addCallbacks(gotInfo, error)
        
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
        # If the state is None, then we have cached authentication tokens
        # available, so call the connected callback.
        if state is None:
            connected(True)
        # Otherwise, open the URL and call authenticate_2 once the user has
        # authenticated us.
        else:
            # In a GUI app, we'd pop up a dialog asking the user to press a
            # button once they have authenticated. However, this blocking call
            # will do the job here.
            import os
            os.spawnlp(os.P_WAIT, "epiphany", "epiphany", "-p", state['url'])
            flickr.authenticate_2(state).addCallbacks(connected, error)
    
    flickr.authenticate_1().addCallbacks(auth_open_url, error)
    reactor.run()

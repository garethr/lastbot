#!/usr/bin/python

"""
A jabber bot that sits and waits for you to ask it questions
then goes off to Last.fm to get some information about the track
it thinks you mentioned.
"""

import sys
import re
import htmllib
from xml.dom import minidom

import ext.pylast as pylast
from jabberbot import JabberBot

# remember to setup your settings file
try:
    from settings import USERNAME, PASSWORD, API_KEY, API_SECRET, SESSION_KEY    
except ImportError, error:
    print "You have to create a local settings file (Error: %s)" % error
    sys.exit(1)

def unescape(input_string):
    "Helper to unescape html entities and other encoding"
    parser = htmllib.HTMLParser(None)
    parser.save_bgn()
    parser.feed(input_string)
    return parser.save_end()

class LastFmJabberBot(JabberBot):
    """Personal LastFM search bot. Useful for looking for tracks you can't 
remember the full name of. Or for findind out who sung a track."""

    def _display_track_details(self):
        "Display details about the track"
        try:
            # get any info we can from the cache
            track = self.results[self.pointer]
            title = track.getTitle()
            url = track.getURL()
            artist = track.getArtist()
            artist_bio = artist.getBioSummary()
            artist_name = artist.getName()

            # if it's the first result lets be more certain
            if self.pointer == 0:
                intro = "you probably mean"
            else:
                intro = "you might have meant"

            # dipslay a nice message if we found something
            return """
%s %s by %s
%s

%s
""" % (intro, title, artist_name, url.replace("%2B","_"),
            unescape(re.sub(r'<[^>]*?>', '', artist_bio)))
        except IndexError:
            return "We didn't find anything!"    

    def bot_next(self, mess, args):
        "get details about the next track in the list"
        try:
            # we need to check we have already done a search
            self.pointer = self.pointer + 1
            return self._display_track_details()
        except AttributeError:
            return "You have to search for something first"

    def bot_prev(self, mess, args):
        "get details about the previous track in the list"
        try:
            # we need to check we have already done a search
            self.pointer = self.pointer - 1
            return self._display_track_details()
        except AttributeError:
            return "You have to search for something first"

    def bot_search(self, mess, args):
        "do a search for tracks"
        # it's a new search so lets reset the pointer
        self.pointer = 0
        
        try:
            # parse the message
            dom = minidom.parseString(str(mess))
            # get the first body element
            body = dom.getElementsByTagName('body')[0]
            # grab the data after the search command
            search_for = body.childNodes[0].data[7:]
        except:
            # something went horribly wrong
            return "A problem occured"
        
        if not search_for:
            return "You have to search for something"
        
        # we can now do a search
        search = pylast.TrackSearch(search_for, None, API_KEY, \
            API_SECRET, SESSION_KEY)
        # and get the results
        self.results = search.getResults()
        
        # and then display the results back to the sender
        return self._display_track_details()

def main():
    "Connect to the server and run the bot forever"
    jabber_bot = LastFmJabberBot(USERNAME, PASSWORD)
    jabber_bot.serve_forever()

if __name__ == '__main__':    
    main()
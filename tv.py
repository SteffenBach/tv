#!/usr/bin/env python
# -*- coding: utf-8 -*-

from contextlib import closing
import datetime
import os
import urllib

ATTEMPTS = 3
CACHE = {}
COLS = 65
CONF_DIR = os.environ["HOME"] + "/.config/tv/"
FILE_RUNNING = CONF_DIR + "running"
FILE_SHOWS = CONF_DIR + "shows"
FILE_TIMESTAMPS = CONF_DIR + "ts"
MONTHS = {  'Jan': 1,  'Feb': 2,  'Mar': 3,
            'Apr': 4,  'May': 5,  'Jun': 6,
            'Jul': 7,  'Aug': 8,  'Sep': 9,
            'Oct': 10, 'Nov': 11, 'Dec': 12}

def __align__(head, val):
    return (u"│ %s:%" + str(COLS - len(head) - 3) + u"s │\n") % (head, val)

def __end__():
    return u"└" + u"─"*COLS + u"┘\n"

def __heading__(title):
    return u"┌─ " + title + " " + u"─"*(COLS - 3 -len(title)) + u"┐\n"

def __subheading__(title):
    return u"├─ " + title + " " + u"─"*(COLS - 3 -len(title)) + u"┤\n"

def __center__(value):
    return u"│ " + value.center(COLS - 2) + u" │\n"

class Show:
    def __cmp__(self, other):
        if isinstance(other, Show):
            return cmp(self.name, other.name)
        elif isinstance(other, basestring):
            return 1
        else:
            return -1
        
    def __is_new__(self):
        return hasattr(self, "prev") and self.prev and self.prev_ep.date >= self.prev.date()

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        val = __heading__(self.name)
        val += __align__("URL", self.url)
        val += __align__("Status", self.status)
        if hasattr(self, "prev_ep"):
            if self.__is_new__():
                val += __center__("!! NEW EPISODE!!")
            val += __subheading__("Previous episode")
            val += unicode(self.prev_ep)
        if hasattr(self, "next_ep"):
            val += __subheading__("Next episode")
            val += unicode(self.next_ep)
        val += __end__()
        return val

class Episode:
    def __init__(self, number, title, date, prefix):
        self.number = number
        self.title = title
        self.prefix = prefix
        vals = date.split("/")
        if len(vals) == 3:
            self.date = datetime.date(int(vals[2]), MONTHS[vals[0]], int(vals[1]))
        elif len(vals) == 2:
            self.date = "%s-%02d" % (vals[1], MONTHS[vals[0]])
        else:
            self.date = vals[0]

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        if isinstance(self.date, datetime.date):
            days = abs((self.date - datetime.date.today()).days)
        else:
            days = "N/A"

        return __align__("Number", self.number) \
                + __align__("Title", self.title) \
                + __align__("Air Date", self.date) \
                + __align__(self.prefix, days)

def __fetch__(path):
    url = "http://services.tvrage.com/tools/quickinfo.php?show=%s" % path
    for i in xrange(1, ATTEMPTS + 1):
        try:
            with closing(urllib.urlopen(url)) as f:
                lines = [line.strip() for line in f.readlines()]
                break
        except:
            if i == ATTEMPTS:
                return "Failed to retrieve info for '%s' in %d attempts" % (path, ATTEMPTS)
            else:
                pass

    if len(lines) == 1 and lines[0].startswith("No Show Results Were"):
        return "No results found for '%s'" % path

    return lines

def __fetch_and_parse__(path):
    lines = __fetch__(path)

    if isinstance(lines, basestring):
        return lines

    parsed = {}
    for line in lines:
        split = line.split("@", 1)
        key = split[0]
        value = split[1::]
        parsed[key] = value if len(value) > 1 else [] if len(value) == 0 else value[0]

    return __parse_map__(parsed)

def __parse_map__(entries):
    entry = Show()
    if entries.has_key("Show Name"): entry.name = entries["Show Name"]
    if entries.has_key("Show URL"): entry.url = entries["Show URL"]
    if entries.has_key("Latest Episode"):
        parsed = entries["Latest Episode"].split("^")
        entry.prev_ep = Episode(parsed[0], unicode(parsed[1], "UTF-8"), parsed[2], "Days since")
    if entries.has_key("Next Episode"):
        parsed = entries["Next Episode"].split("^")
        entry.next_ep = Episode(parsed[0], unicode(parsed[1], "UTF-8"), parsed[2], "Days remaining")
    if entries.has_key("Status"): entry.status = entries["Status"]
#    if entries.has_key("Show ID"): entry.show_id = int(entries["Show ID"])
#    if entries.has_key("Premiered"): entry.premiered = entries["Premiered"]
#    if entries.has_key("Started"): entry.started = entries["Started"]
#    if entries.has_key("Ended"): entry.ended = entries["Ended"]
#    if entries.has_key("Country"): entry.country = entries["Country"]
#    if entries.has_key("RFC3339"): entry.rfc3339 = entries["RFC3339"]
#    if entries.has_key("GMT+0 NODST"): entry.gmt0 = entries["GMT+0 NODST"]
#    if entries.has_key("Classification"): entry.classfication = entries["Classification"]
#    if entries.has_key("Genres"): entry.genres = entries["Genres"].split(" | ")
#    if entries.has_key("Network"): entry.network = entries["Network"]
#    if entries.has_key("Airtime"): entry.airtime = entries["Airtime"]
#    if entries.has_key("Runtime"): entry.runtime = entries["Runtime"]

    # load timestamp from when this show was last fetched
    if CACHE.has_key(entry.name):
        entry.prev = CACHE[entry.name]
        # Update time stamps for fetched shows
        CACHE[entry.name] = datetime.datetime.now()

    return entry

def __read_config__():
    with open(FILE_SHOWS) as f:
        lines = [line.strip() for line in f.readlines()]

    return [line for line in lines if len(line) > 0 and not '#' in line]

def __progress__(name):
    progress = "\rFetching info for %s" % name.upper()
    sys.stdout.write(progress)
    sys.stdout.flush()
    sys.stdout.write("\r" + " "*(len(progress) + 3) + "\r")
    return __fetch_and_parse__(name)

if __name__ == "__main__":
    import sys

    # Create configuration folder if missing
    if not os.path.exists(CONF_DIR):
        os.makedirs(CONF_DIR)

    # Check if already running
    if os.path.exists(FILE_RUNNING):
        print("Another instance is already running")
        sys.exit(1)

    try:
        import cPickle
        # Mark as running
        open(FILE_RUNNING, 'w').close()

        # Load time stamps
        if os.path.exists(FILE_TIMESTAMPS):
            with open(FILE_TIMESTAMPS) as h:
                CACHE = cPickle.load(h)

        # Load show names, either from command line or configuration file
        names = []
        if len(sys.argv) > 1:
            names = sys.argv[1::]
        else:
            try:
                names = __read_config__()
            except:
                print("No arguments given and '%s' does not exist!" % FILE_SHOWS)

        # Actually fetch show info
        if len(names) > 0:
            shows = [__progress__(name) for name in names]
            shows.sort()

            print "\n".join(str(show) for show in shows),
            
            # Store time stamps
            with open(FILE_TIMESTAMPS, 'w') as h:
                cPickle.dump(CACHE, h)
    except:
        print '>>> traceback <<<'
        import traceback
        traceback.print_exc()
        print '>>> end of traceback <<<'

    # Removing running indicator
    os.remove(FILE_RUNNING)


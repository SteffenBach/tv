#!/usr/bin/env python3

import datetime, os, sys
import urllib.request, urllib.parse, urllib.error

ATTEMPTS = 3
CACHE = {}
COLS = 65
CONF_DIR = os.environ["HOME"] + "/.config/tv/"
FILE_RUNNING = CONF_DIR + "running"
FILE_SHOWS = CONF_DIR + "shows"
FILE_TIMESTAMPS = CONF_DIR + "timestamp_cache"
MONTHS = {  'Jan': 1,  'Feb': 2,  'Mar': 3,
            'Apr': 4,  'May': 5,  'Jun': 6,
            'Jul': 7,  'Aug': 8,  'Sep': 9,
            'Oct': 10, 'Nov': 11, 'Dec': 12}

def __align__(head, val):
    return ("│ %s:%" + str(COLS - len(head) - 3) + "s │\n") % (head, val)

def __end__():
    return "└" + "─"*COLS + "┘\n"

def __heading__(title):
    return "┌─ " + title + " " + "─"*(COLS - 3 -len(title)) + "┐\n"

def __subheading__(title):
    return "├─ " + title + " " + "─"*(COLS - 3 -len(title)) + "┤\n"

def __center__(value):
    return "│ " + value.center(COLS - 2) + " │\n"

class Show:
    def __lt__(self, other):
        if isinstance(other, Show):
            return (self.name < other.name)
        elif isinstance(other, str):
            return 1
        else:
            return -1
        
    def __is_new__(self):
        return hasattr(self, "prev") and self.prev and self.prev_ep.date >= self.prev.date()

    def __str__(self):
        val = __heading__(self.name)
        val += __align__("URL", self.url)
        val += __align__("Status", self.status)
        if hasattr(self, "prev_ep"):
            if self.__is_new__():
                val += __center__("!! NEW EPISODE!!")
            val += __subheading__("Previous episode")
            val += str(self.prev_ep)
        if hasattr(self, "next_ep"):
            val += __subheading__("Next episode")
            val += str(self.next_ep)
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
        if isinstance(self.date, datetime.date):
            days = abs((self.date - datetime.date.today()).days)
        else:
            days = "N/A"

        return __align__("Number", self.number) \
                + __align__("Title", self.title) \
                + __align__("Air Date", self.date) \
                + __align__(self.prefix, days)

def __fetch__(path):
    url = "http://services.tvrage.com/tools/quickinfo.php?%s" % urllib.parse.urlencode({'show': path})
    for i in range(1, ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(url) as f:
                lines = [line.decode('utf-8').strip() for line in f.readlines()]
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

    if isinstance(lines, str):
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
    if "Show Name" in entries: entry.name = entries["Show Name"]
    if "Show URL" in entries: entry.url = entries["Show URL"]
    if "Latest Episode" in entries:
        parsed = entries["Latest Episode"].split("^")
        entry.prev_ep = Episode(parsed[0], parsed[1], parsed[2], "Days since")
    if "Next Episode" in entries:
        parsed = entries["Next Episode"].split("^")
        entry.next_ep = Episode(parsed[0], parsed[1], parsed[2], "Days remaining")
    if "Status" in entries: entry.status = entries["Status"]

    # load timestamp from when this show was last fetched
    if entry.name in CACHE:
        entry.prev = datetime.datetime.fromtimestamp(CACHE[entry.name])

    # Update time stamps for fetched shows
    CACHE[entry.name] = datetime.datetime.now().timestamp()

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
    # Create configuration folder if missing
    if not os.path.exists(CONF_DIR):
        os.makedirs(CONF_DIR)

    # Check if already running
    if os.path.exists(FILE_RUNNING):
        print("Another instance is already running")
        sys.exit(1)

    try:
        import json
        # Mark as running
        open(FILE_RUNNING, 'w').close()

        # Load time stamps
        if os.path.exists(FILE_TIMESTAMPS):
            with open(FILE_TIMESTAMPS) as h:
                CACHE = json.load(h)

        # Load show names, either from command line or configuration file
        names = []
        if len(sys.argv) > 1:
            names = sys.argv[1::]
        else:
            try:
                names = __read_config__()
            except:
                print(("No arguments given and '%s' does not exist!" % FILE_SHOWS))

        # Actually fetch show info
        if len(names) > 0:
            shows = [__progress__(name) for name in names]
            shows.sort()

            print("\n".join(str(show) for show in shows), end='')

            # Store time stamps
            with open(FILE_TIMESTAMPS, 'w') as h:
                json.dump(CACHE, h, indent=2)
    except:
        print('>>> traceback <<<')
        import traceback
        traceback.print_exc()
        print('>>> end of traceback <<<')

    # Removing running indicator
    os.remove(FILE_RUNNING)


# TV

A small Python 3 command-line tool for checking the air date of TV shows
using the [TVRage](http://tvrage.com/) API.


## Usage

*tv* produces an output like the one seen here:
```
┌─ Game of Thrones ───────────────────────────────────────────────┐
│ URL:                      http://www.tvrage.com/Game_of_Thrones │
│ Status:                                        Returning Series │
├─ Previous episode ──────────────────────────────────────────────┤
│ Number:                                                   04x10 │
│ Title:                                             The Children │
│ Air Date:                                            2014-06-15 │
│ Days since:                                                  29 │
├─ Next episode ──────────────────────────────────────────────────┤
│ Number:                                                   05x01 │
│ Title:                                      Season 5, Episode 1 │
│ Air Date:                                               2015-04 │
│ Days remaining:                                             N/A │
└─────────────────────────────────────────────────────────────────┘

┌─ Sherlock ──────────────────────────────────────────────────────┐
│ URL:                             http://www.tvrage.com/Sherlock │
│ Status:                                        Returning Series │
├─ Previous episode ──────────────────────────────────────────────┤
│ Number:                                                   03x03 │
│ Title:                                             His Last Vow │
│ Air Date:                                            2014-01-12 │
│ Days since:                                                 183 │
└─────────────────────────────────────────────────────────────────┘
```

### Configuration file

You can save your favourite shows in the `$HOME/.config/tv/shows` file, one
show per line, and then invoke *tv* without parameters, like so: `tv.py`.

```
#Dramas
game of thrones
sherlock
```

Lines containing `#` will be ignored.


### Specifying parameters

The show names can also be given as parameters by invoking `tv.py "game of
thrones" sherlock`.

When invoked with parameters no show names will be read from the configuration
file.


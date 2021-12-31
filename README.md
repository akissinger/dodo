Dodo is a graphical email client based on the command line email swiss-army-knife [notmuch](https://notmuchmail.org/) written in Python/PyQt5. It's main goals are to:

* offer efficient, keyboard-oriented mail reading, sorting, and composing
* give a mostly text-based email experience by default, but with HTML support a few keystrokes a way
* offload as much work as possible on existing, excellent command-line tools (UNIX philosphy-style)
* be simple enough to customise and hack on yourself

Much of its design and general look-and-feel is inspired by two existing notmuch-based clients: [alot](https://github.com/pazz/alot) and [astroid](https://github.com/astroidmail/astroid).

# Prerequisites

If you have already used `notmuch` for email, there's not much to do here :). If not, you'll need to set up some other programs first:

* something to check mail and sync with a local Maildir ([offlineimap](http://www.offlineimap.org/) is the default, but others like [mbsync](https://isync.sourceforge.io/) should work fine)
* a sendmail-compatible SMTP client to send mail ([msmtp](https://marlam.de/msmtp/) is the default)
* [w3m](http://w3m.sourceforge.net/) for translating HTML messages into plaintext
* [notmuch](https://notmuchmail.org/)

All of this is pretty standard stuff, and should be installable via your package manager on Linux/Mac/etc. It should also be possible in principle to get this stuff working in Windows (e.g. with WSL or Cygwin), but I haven't tried it.


# Install

Installing Dodo is just a matter of cloning the repo and installing the python dependencies. The only hard dependency is [PyQt5](https://riverbankcomputing.com/software/pyqt/intro). Optional dependencies are [html2text](https://pypi.org/project/html2text/) and [lxml](https://lxml.de/) for native-python HTML-to-text conversion and HTML sanitization, respectively. These are both off by default.

Then, simply clone Dodo with:

    git clone https://github.com/akissinger/dodo.git
    
Dodo can be run by calling `python3 -m dodo`, or (if you add the `bin/` subdirectory to your `PATH`), simply `dodo`.

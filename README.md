# Dodo

Dodo is a graphical email client written in Python/PyQt5, based on the command line email swiss-army-knife [notmuch](https://notmuchmail.org/). It's main goals are to:

* offer efficient, keyboard-oriented mail reading, sorting, and composing
* give a mostly text-based email experience by default, but with HTML support a few keystrokes a way
* offload as much work as possible on existing, excellent command-line tools (UNIX philosphy-style)
* be simple enough to customise and hack on yourself

Much of its design and general look-and-feel is inspired by two existing notmuch-based clients: [alot](https://github.com/pazz/alot) and [astroid](https://github.com/astroidmail/astroid).

This README has instructions on installation, usage, and basic configuration. For API decumentation (which is also useful for configuration), check out the [Read the Docs](https://dodomail.readthedocs.io/en/latest/) page.

## Prerequisites

If you have already used `notmuch` for email, there's not much to do here :). If not, you'll need to set up some other programs first:

* something to check mail and sync with a local Maildir ([offlineimap](http://www.offlineimap.org/) is the default, but others like [mbsync](https://isync.sourceforge.io/) should work fine)
* a sendmail-compatible SMTP client to send mail ([msmtp](https://marlam.de/msmtp/) is the default)
* [w3m](http://w3m.sourceforge.net/) for translating HTML messages into plaintext
* [notmuch](https://notmuchmail.org/) for email searching and tagging

All of this is pretty standard stuff, and should be installable via your package manager on Linux/Mac/etc. If you don't know how to set these things up already, see the respective websites or the "Setting up the prerequisites" section below for a quick reference.


## Install and run

Make sure you have Python 3.7+ and [PyQt5](https://riverbankcomputing.com/software/pyqt/intro). Clone Dodo with:

    % git clone https://github.com/akissinger/dodo.git
    
Then, add the `bin/` subdirectory to your `PATH` and run with:

    % dodo

An optional Python dependency is [lxml](https://lxml.de/) for some limited HTML sanitization, which is off by default (see the next section for switching it on).


## Configuration

Dodo is configured via `~/.config/dodo/config.py`. This is just a Python file that gets `eval`-ed right before the main window is shown.

Most settings have reasonable defaults (assuming your are using offlineimap/msmtp), which can be found in [settings.py](https://github.com/akissinger/dodo/blob/master/dodo/settings.py). The only two things that must be set for Dodo to work properly are your email address and the location of your sent mail folder. Some things you probably also want to set up are the text editor (for composing messages) and the file browser (for viewing attachments).

Here is an example `config.py`, with some settings similar to the ones I use:

```python
import dodo

# required
dodo.settings.email_address = 'First Last <me@domain.com>'
dodo.settings.sent_dir = '/home/user/mail/Work/Sent'

# optional
dodo.settings.theme = dodo.themes.nord
dodo.settings.editor_command = ['kitty', 'nvim']
dodo.settings.file_browser_command = ['fman', '/home/user/Documents/']
```

A theme is just a Python dictionary mapping some fixed color names to HTML color codes. Currently, the themes implemented in [themes.py](https://github.com/akissinger/dodo/blob/master/dodo/themes.py) are `nord`, `solarized_light` and `solarized_dark`. If you want more, feel free to roll your own, or (better) send me a pull request!

All of the settings of the form `..._command` are given as a list consisting of the command and its arguments. Additional arguments, such as the relevant folder or file are appended to this list.

The settings above replace the default text editor (`xterm -e vim`) with [neovim](https://neovim.io/) run inside a new [kitty](https://sw.kovidgoyal.net/kitty/) terminal. I am also using Michael Herrmann's excellent dual-pane file manager [fman](https://fman.io/) instead of the default (`nautilus`). With these settings, showing attachments will open `fman` with a fixed directory in the left pane (`/home/user/Documents`) and a directory containing the attachments on the right. A similar effect can be obtained with [ranger](https://github.com/ranger/ranger) using the `multipane` view mode.

While Javascript is disabled in the HTML email viewer, you may want to set up a custom HTML sanitizer function as follows:

    dodo.util.html2html = dodo.util.clean_html2html

The above function passes the HTML through the `Cleaner` object of the [lxml](https://lxml.de/) library. Note this still allows some dodgy stuff, such as calling home via embedded `img` tags. Fully safe and private HTML email from untrusted sources should be considered a work-in-progress.

Key mappings can be customised by changing the dictionaries defined in [keymap.py](https://github.com/akissinger/dodo/blob/master/dodo/keymap.py). These map a key to a pair consisting of a description string and a Python function. For the `global_keymap`, this function takes the `Dodo` object defined in [app.py](https://github.com/akissinger/dodo/blob/master/dodo/app.py) as its argument. The other maps take the relevant "local" widget (SearchView, ThreadView, ComposeView, or CommandBar).

## Basic use

Most functionality in Dodo comes from keyboard shortcuts. Press `?` to get a full list of the key mappings at any time.

Dodo has 3 different kinds of view: search views, thread views, and compose views. It opens initially with a search view with the query `tag:inbox`. Pressing enter or double-clicking a thread with open that thread in the thread view. Pressing `c` at any time or `r` while looking at a message in the thread view will open the compose view.

In the compose view, press `<enter>` to edit the message on your chosen editor. Once you save and exit, the message will be updated. Press `a` to add attachments (or use the special `A:` header). Press `S` to send.


## Setting up the prerequisites

Since there's a lot of little bits to configure, I've also included some minimal configurations for offlineimap, msmtp, and notmuch, just to have it all in one place.

Note the offlineimap and msmtp configurations below simply read the password from a plaintext file. More secure options are available, which are explained in the respective docs.

### Incoming mail

Assuming your system configuration directory is `~/.config/`, the configuration file for offlineimap is located in `~/.config/offlineimap/config`. Here is a template for syncing one IMAP account named "Work":

    [general]
    accounts = Work

    [Account Work]
    localrepository = WorkLocal
    remoterepository = WorkRemote

    [Repository WorkLocal]
    type = Maildir
    localfolders = ~/mail/Work

    [Repository WorkRemote]
    type = IMAP
    remotehost = (IMAP SERVER)
    remoteuser = (USER NAME)
    remotepassfile = (PASSWORD FILE)
    sslcacertfile = OS-DEFAULT

If you want to set up multiple IMAP accounts, just put them all in the `~/mail` folder and set `~/mail` as your database path for notmuch.

### Outgoing mail

Here is a sample `~/.config/msmtp/config`, setting up a single SMTP server (also named "Work") with TLS:

    defaults
    auth           on
    tls            on
    tls_trust_file /etc/ssl/certs/ca-certificates.crt
    logfile        ~/.msmtp.log
    account        Work
    host           (SMTP SERVER)
    port           587
    from           (EMAIL ADRESS)
    user           (USER NAME)
    passwordeval   cat (PASSWORD FILE)
    account        default : Work

You may need to change the 4th line if your system stores CA certificates in a different location.

### Mail indexing

Once offlineimap is set up, just run `notmuch` from the command line to do some initial setup, which gets saved in `~/.notmuch-config` by default. You can set `~/mail` as your database path. notmuch has lots of options, the ability to set up various hooks and filters, and to sync certain IMAP markers with notmuch tags.

Here's a `~/.notmuch-config` which is roughly like the one I use:

    [database]
    path=/home/user/mail

    [user]
    name=First Last
    primary_email=me@domain.com

    [new]
    tags=new
    ignore=

    [search]
    exclude_tags=deleted;killed;spam;

    [maildir]
    synchronize_flags=true

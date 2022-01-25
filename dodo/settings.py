#     Dodo - A graphical, hackable email client based on notmuch
#     Copyright (C) 2021 - Aleks Kissinger
#
# This file is part of Dodo
#
# Dodo is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Dodo is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Dodo. If not, see <https://www.gnu.org/licenses/>.

"""
This module holds settings and sets their default values. The values set
here should be overridden by the user in `~/.config/dodo/config.py`. This
can be done as follows:

.. code-block:: python

  import dodo
  dodo.settings.email_address = 'First Last <me@domain.com>''
  dodo.settings.sent_dir = '~/mail/work/Sent'

The settings :func:`~dodo.settings.email_address` and
:func:`~dodo.settings.sent_dir` are required. Dodo may not work correctly
unless you set them properly. The rest of the settings have reasonable
defaults, as detailed below.
"""

from . import themes

# functional
email_address = ''
"""Your email address (REQUIRED)

This is used both to populate the 'From' field of emails and to (mostly)
avoid CC'ing yourself when replying to all. It can be given as 'NAME <ADDRESS@DOMAIN>'
format."""

sent_dir = ''
"""Where to store sent messages (REQUIRED)

This will usually be a subdirectory of the Maildir sync'ed with
:func:`~dodo.settings.sync_mail_command`."""

editor_command = "xterm -e vim '{file}'"
"""Command used to launch external text editor

This is a shell command, which additionally takes the `{file}` placeholder,
which is passed the name of a temp file being edited while composing an email.
"""

file_browser_command = "nautilus '{dir}'"
"""Command used to launch external text editor

This is a shell command, which additionally takes the `{file}` placeholder,
which is passed the name of a temp file being edited while composing an email.
"""

web_browser_command = ''
send_mail_command = 'msmtp -t'

sync_mail_command = 'offlineimap'
"""Command used to sync IMAP with local Maildir"""

sync_mail_interval = 300 # seconds
default_to_html = False
remove_temp_dirs = 'ask' # should be 'always', 'never', or 'ask'

# security
html_block_remote_requests = True
html_confirm_open_links = True

# visual
theme = themes.nord
search_font = 'DejaVu Sans Mono'
search_font_size = 13
message_font = 'DejaVu Sans Mono'
message_font_size = 12

search_view_padding = 1
tag_icons = {
  'inbox': '',
  'unread': '',
  'attachment': '',
  'sent': '>',
  'replied': '',
  'flagged': '',
  'marked': '',
  'signed': '',
}

# css used in view and compose window. Placeholders may be included in
# curly brackets for any color named in the current theme, as well as
# {message_font} and {message_font_size}.
message_css = """
pre {{
  font-family: {message_font};
  font-size: {message_font_size}pt;
}}

pre .quoted {{
  color: {fg_dim};
}}

pre .headername {{
  color: {fg_bright};
  font-weight: bold;
}}

pre .headertext {{
  color: {fg_bright};
}}

body {{
  background-color: {bg};
  color: {fg};
}}

::-webkit-scrollbar {{
  background: {bg};
}}

::-webkit-scrollbar-thumb {{
  background: {bg_button};
}}

::selection {{
  color: {bg};
  background: {fg};
}}

a {{
  color: {fg_bright};
}}
"""

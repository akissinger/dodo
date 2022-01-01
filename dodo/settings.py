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

from . import themes

# functional
email_address = ''
sent_dir = ''
editor_command = ['xterm', '-e', 'vim']
file_browser_command = ['nautilus']
send_mail_command = ['msmtp', '-t']
sync_mail_command = ['offlineimap']
sync_mail_interval = 300 # seconds
default_to_html = False

# visual
theme = themes.nord
search_font = 'DejaVu Sans Mono'
search_font_size = 13
search_view_padding = 1
tag_icons = {
  'inbox': '',
  'unread': '',
  'attachment': '',
  'sent': '>',
  'replied': '',
  'flagged': '',
  'marked': '',
}

# css used in view and compose window. Colour names in curly braces
# are substituted using the current theme.
message_css = """
pre {{
  font-family: DejaVu Sans Mono;
  font-size: 12pt;
}}

body {{
  background-color: {bg};
  color: {fg};
  font-family: DejaVu Sans;
}}

::-webkit-scrollbar {{
  background: {bg};
}}

::-webkit-scrollbar-thumb {{
  background: {bg_button};
}}

a {{
  color: {fg_bright};
}}
"""

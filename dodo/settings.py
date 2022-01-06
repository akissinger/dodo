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
remove_temp_dirs = 'ask' # should be 'always', 'never', or 'ask'

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

a {{
  color: {fg_bright};
}}
"""

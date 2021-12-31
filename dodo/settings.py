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
search_font = 'Fira Code'
search_font_size = 14
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
  font-family: Fira Code;
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

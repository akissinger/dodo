from . import themes

# functional
email_address = ''
sent_dir = ''
editor_command = ['xterm', 'vim']
send_mail_command = ['msmtp', '-t']
sync_mail_command = ['offlineimap']

# visual
theme = themes.nord
search_font = 'Fira Code'
search_font_size = 14
message_css = f"""
pre {{
  font-family: Fira Code;
  font-size: 12pt;
}}

body {{
  background-color: {theme["bg"]};
  color: {theme["fg"]};
  font-family: DejaVu Sans;
}}

a {{
  color: {theme["fg_bright"]};
}}
"""

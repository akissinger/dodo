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

from PyQt5.QtGui import QPalette, QColor

# palettes used in theme definitions
nord_p = {
  'polar0':  '#2e3440',
  'polar1':  '#3b4252',
  'polar2':  '#434c5e',
  'polar3':  '#4c566a',
  'snow0':   '#d8dee9',
  'snow1':   '#e5e9f0',
  'snow2':   '#eceff4',
  'frost0':  '#8fbcbb',
  'frost1':  '#88c0d0',
  'frost2':  '#81a1c1',
  'frost3':  '#5e81ac',
  'aurora0': '#bf616a',
  'aurora1': '#d08770',
  'aurora2': '#ebcb8b',
  'aurora3': '#a3be8c',
  'aurora4': '#b48ead',
}

solarized_p = {
  'base03':    '#002b36',
  'base02':    '#073642',
  'base01':    '#586e75',
  'base00':    '#657b83',
  'base0':     '#839496',
  'base1':     '#93a1a1',
  'base2':     '#eee8d5',
  'base3':     '#fdf6e3',
  'yellow':    '#b58900',
  'orange':    '#cb4b16',
  'red':       '#dc322f',
  'magenta':   '#d33682',
  'violet':    '#6c71c4',
  'blue':      '#268bd2',
  'cyan':      '#2aa198',
  'green':     '#859900',
}

solarized_dark = {
  'bg': solarized_p['base02'],
  'fg': solarized_p['base1'],
  'fg_bright': solarized_p['violet'],
  'fg_good': solarized_p['green'],
  'fg_bad': solarized_p['red'],
  'bg_alt': solarized_p['base03'],
  'bg_button': solarized_p['base03'],
  'fg_button': solarized_p['base01'],
  'fg_link': solarized_p['violet'],
  'bg_highlight': solarized_p['yellow'],
  'fg_highlight': solarized_p['base03'],
  'fg_subject': solarized_p['base0'],
  'fg_subject_unread': solarized_p['orange'],
  'fg_from': solarized_p['blue'],
  'fg_date': solarized_p['cyan'],
  'fg_tags': solarized_p['violet'],
}

solarized_light = {
  'bg': solarized_p['base3'],
  'fg': solarized_p['base01'],
  'fg_bright': solarized_p['violet'],
  'fg_good': solarized_p['green'],
  'fg_bad': solarized_p['red'],
  'bg_alt': solarized_p['base3'],
  'bg_button': solarized_p['base3'],
  'fg_button': solarized_p['base1'],
  'fg_link': solarized_p['violet'],
  'bg_highlight': solarized_p['base02'],
  'fg_highlight': solarized_p['base1'],
  'fg_subject': solarized_p['base0'],
  'fg_subject_unread': solarized_p['base02'],
  'fg_from': solarized_p['blue'],
  'fg_date': solarized_p['cyan'],
  'fg_tags': solarized_p['violet'],
  'bg_message_text': '#ffffff',
  'fg_message_text': '#000000',
}

nord = {
  'bg': nord_p['polar0'],
  'fg': nord_p['snow0'],
  'fg_bright': nord_p['aurora4'],
  'fg_good': nord_p['aurora3'],
  'fg_bad': nord_p['aurora0'],
  'bg_alt': nord_p['polar1'],
  'bg_button': nord_p['polar3'],
  'fg_button': nord_p['snow2'],
  'fg_link': nord_p['frost2'],
  'bg_highlight': nord_p['aurora3'],
  'fg_highlight': nord_p['polar0'],
  'fg_subject': nord_p['snow0'],
  'fg_subject_unread': nord_p['aurora4'],
  'fg_from': nord_p['frost3'],
  'fg_date': nord_p['polar3'],
  'fg_tags': nord_p['aurora2'],
  'bg_message_text': '#ffffff',
  'fg_message_text': '#000000',
}

def apply_theme(app, theme):
    # Force the style to be the same on all OSs:
    app.setStyle("Fusion")
    # Now use a palette to switch to dark colors:
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(theme['bg']))
    palette.setColor(QPalette.WindowText, QColor(theme['fg']))
    palette.setColor(QPalette.Base, QColor(theme['bg']))
    palette.setColor(QPalette.AlternateBase, QColor(theme['bg_alt']))
    palette.setColor(QPalette.ToolTipBase, QColor(theme['fg']))
    palette.setColor(QPalette.ToolTipText, QColor(theme['fg']))
    palette.setColor(QPalette.Text, QColor(theme['fg']))
    palette.setColor(QPalette.Button, QColor(theme['bg_button']))
    palette.setColor(QPalette.ButtonText, QColor(theme['fg_button']))
    palette.setColor(QPalette.BrightText, QColor(theme['fg_bright']))
    palette.setColor(QPalette.Link, QColor(theme['fg_link']))
    palette.setColor(QPalette.Highlight, QColor(theme['bg_highlight']))
    palette.setColor(QPalette.HighlightedText, QColor(theme['fg_highlight']))
    app.setPalette(palette)

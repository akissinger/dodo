from PyQt5.QtGui import QPalette, QColor
# from PyQt5.QtCore import Qt

# nord palettes
# polar =  ["#2e3440", "#3b4252", "#434c5e", "#4c566a"]
# snow =   ["#d8dee9", "#e5e9f0", "#eceff4"]
# frost =  ["#8fbcbb", "#88c0d0", "#81a1c1", "#5e81ac"]
# aurora = ["#bf616a", "#d08770", "#ebcb8b", "#a3be8c", "#b48ead"]

theme_nord = {
        'bg': '#2e3440',
        'fg': '#d8dee8',
        'fg_bright': '#b48ead',
        'bg_alt': '#3b4252',
        'button_bg': '#4c566a',
        'button_fg': '#eceff4',
        'link': '#81a1c1',
        'highlight_bg': '#a3be8c',
        'highlight_fg': '#2e3440',
        'fg_subject': '#d8dee8',
        'fg_subject_unread': '#b48ead',
        'fg_from': '#5e81ac',
        'fg_date': '#4c566a',
        'fg_tags': '#ebcb8b',
        }

theme = theme_nord

def apply_style(app):
    global theme
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
    palette.setColor(QPalette.Button, QColor(theme['button_bg']))
    palette.setColor(QPalette.ButtonText, QColor(theme['button_fg']))
    palette.setColor(QPalette.BrightText, QColor(theme['fg_bright']))
    palette.setColor(QPalette.Link, QColor(theme['link']))
    palette.setColor(QPalette.Highlight, QColor(theme['highlight_bg']))
    palette.setColor(QPalette.HighlightedText, QColor(theme['highlight_fg']))
    app.setPalette(palette)

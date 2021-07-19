from PyQt5.QtGui import QPalette, QColor
# from PyQt5.QtCore import Qt

# nord palettes
polar =  ["#2e3440", "#3b4252", "#434c5e", "#4c566a"]
snow =   ["#d8dee9", "#e5e9f0", "#eceff4"]
frost =  ["#8fbcbb", "#88c0d0", "#81a1c1", "#5e81ac"]
aurora = ["#bf616a", "#d08770", "#ebcb8b", "#a3be8c", "#b48ead"]

def apply_style(app):
    # Force the style to be the same on all OSs:
    app.setStyle("Fusion")
    # Now use a palette to switch to dark colors:
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#2e3440"))
    palette.setColor(QPalette.WindowText, QColor("#d8dee9"))
    palette.setColor(QPalette.Base, QColor("#2e3440"))
    palette.setColor(QPalette.AlternateBase, QColor("#4c566a"))
    palette.setColor(QPalette.ToolTipBase, QColor("#d8dee9"))
    palette.setColor(QPalette.ToolTipText, QColor("#d8dee9"))
    palette.setColor(QPalette.Text, QColor("#d8dee9"))
    palette.setColor(QPalette.Button, QColor("#81a1c1"))
    palette.setColor(QPalette.ButtonText, QColor("#2e3440"))
    palette.setColor(QPalette.BrightText, QColor("#ebcb8b"))
    palette.setColor(QPalette.Link, QColor("#81a1c1"))
    palette.setColor(QPalette.Highlight, QColor("#a3be8c"))
    palette.setColor(QPalette.HighlightedText, QColor("#2e3440"))
    app.setPalette(palette)

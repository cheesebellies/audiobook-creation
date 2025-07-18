import os
import unified_gui

os.chdir(os.path.dirname(os.path.abspath(__file__)))

app = unified_gui.AudiobookApplication()
app.run()

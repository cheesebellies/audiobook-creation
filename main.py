import os
os.environ["TKINTER_DISABLE"] = "1"
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import unified_gui

app = unified_gui.AudiobookApplication()
app.run()

import os
import unified_gui

os.environ["TQDM_DISABLE"] = "1"
os.chdir(os.path.dirname(os.path.abspath(__file__)))

app = unified_gui.AudiobookApplication()
app.run()

import os
import sys
import importlib.util

nested_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kindred-minds")
os.chdir(nested_dir)
sys.path.insert(0, nested_dir)

spec = importlib.util.spec_from_file_location("kindred_app", os.path.join(nested_dir, "app.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

mod.DB_PATH = "/tmp/kindred.db"
mod.init_db()

app = mod.app

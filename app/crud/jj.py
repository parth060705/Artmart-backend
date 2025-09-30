import os
import shutil

def remove_readonly(func, path, excinfo):
    os.chmod(path, 0o777)
    func(path)

shutil.rmtree(
    r"c:\users\ghara\onedrive\desktop\parth\fastapi\venv\Lib\site-packages\scipy\cluster\tests\__pycache__",
    onerror=remove_readonly
)

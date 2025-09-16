import sys
sys.stdout.reconfigure(encoding="utf-8")
from qfluentwidgets import FluentIcon as FIF

print("Số lượng icon có sẵn:", len([name for name in dir(FIF) if name.isupper()]))
print([name for name in dir(FIF) if name.isupper()])

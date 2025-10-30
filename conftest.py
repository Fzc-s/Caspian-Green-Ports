import os
import sys

# Добавляем корневую папку в PYTHONPATH, чтобы pytest мог импортировать app
sys.path.insert(0, os.path.abspath('.'))
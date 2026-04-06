import sys
from pathlib import Path

# clear parent project's 'src' module so our local src/ takes priority
for key in list(sys.modules):
    if key == "src" or key.startswith("src."):
        del sys.modules[key]

sys.path.insert(0, str(Path(__file__).parent.parent))

import os
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "web.settings")

from django.core.asgi import get_asgi_application

application = get_asgi_application()

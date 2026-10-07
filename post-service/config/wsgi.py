import os

from common.chunked import ChunkedBodyAdapter
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
application = ChunkedBodyAdapter(get_wsgi_application())

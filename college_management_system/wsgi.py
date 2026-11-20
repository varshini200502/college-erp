"""
WSGI config for college_management_system project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os
import sys
from pathlib import Path

# Ensure project root is in sys.path for serverless execution
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_management_system.settings')

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

# Vercel serverless entrypoint
app = application

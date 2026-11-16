import os
from django.conf import settings


def recaptcha_context(request):
    """
    Exposes the Google reCAPTCHA site key to all templates.
    Loaded securely from environment variables / Django settings.
    """
    site_key = getattr(settings, 'RECAPTCHA_SITE_KEY', '') or os.environ.get('RECAPTCHA_SITE_KEY', '')
    return {
        'recaptcha_site_key': site_key,
        'RECAPTCHA_SITE_KEY': site_key,
    }

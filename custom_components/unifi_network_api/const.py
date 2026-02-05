"""Constants for the UniFi Network API integration."""

from datetime import timedelta

DOMAIN = "unifi_network_api"
CONF_API_KEY = "api_key"
CONF_VERIFY_SSL = "verify_ssl"
CONF_SITE_ID = "site_id"
CONF_SITE_NAME = "site_name"
DEFAULT_PORT = 443
UPDATE_INTERVAL = timedelta(seconds=30)

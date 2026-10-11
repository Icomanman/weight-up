"""Endpoints and identifiers shared by the Xiaomi cloud modules."""

ACCOUNT_URL = "https://account.xiaomi.com"
STS_URL_PREFIX = "https://sts.api.io.mi.com/sts"

# The Mi Home service identifier. The scale endpoint accepts tokens issued for it.
SERVICE_ID = "xiaomiio"

# Regions that serve scale data through getUserDataByPage.
SCALE_REGIONS = ("de", "i2", "ru", "sg", "us")

# Regions with a known api.io.mi.com host. cn has no region prefix.
API_REGIONS = ("cn", *SCALE_REGIONS, "tw", "in")

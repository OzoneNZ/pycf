import os
import sys
import json
import urllib.request
import ipaddress


def info(text):
    return print("[INFO] " + text)


def warning(text):
    return print("[WARNING] " + text)


def error(text):
    return sys.exit("[ERROR] " + text)


# Init
info("pycf starting...")

if sys.version_info[0] != 3:
    error("pycf requires Python 3")

# Required configuration keys
categories = {
    "cloudflare": ["api", "checkip"],
    "account": ["email", "key", "zone"],
    "zone": ["name", "proxy", "type", "ttl"]
}

# Check pycf.json configuration file exists
if not os.path.isfile("pycf.json"):
    error("pycf.json configuration file does not exist or could not be read")
# Load + parse JSON contents
else:
    with open("pycf.json") as configuration:
        try:
            configuration = json.load(configuration)
            info("Successfully loaded CloudFlare configuration")
        except json.decoder.JSONDecodeError:
            error("pycf.json configuration file has invalid contents (not JSON)")

# Check top-level configuration keys
if set(configuration.keys()) < set(categories.keys()):
    error("Some settings are missing")

# Check second-level configuration keys
for category in categories.keys():
    for setting in categories[category]:
        if setting not in configuration[category]:
            error(str(setting) + "' setting is missing from section [" + str(category) + "]")

# Fetch IP address from specified "checkip" resource
try:
    # Check a valid IPv4 address was supplied
    try:
        ip_address = urllib.request.urlopen(configuration["cloudflare"]["checkip"]).read()
        ip_address = ip_address.decode("utf-8").rstrip("\n")
        ipaddress.ip_address(ip_address)
    except ValueError:
        error("IP address resource returned invalid IPv4 or IPv6 address")
except urllib.error.URLError:
    error("Could not fetch IP address from resource '" + configuration["cloudflare"]["checkip"] + "'")

# Construct initial cURL command
command = "curl -s {0} -d 'a=rec_load_all' -d 'tkn={1}' -d 'email={2}' -d 'z={3}';"
command = command.format(
    configuration["cloudflare"]["api"],
    configuration["account"]["key"],
    configuration["account"]["email"],
    configuration["account"]["zone"]
)

# Execute record fetcher
info("Executing record fetch query...")
records = os.popen(command).read()

# Quit if cURL is not operating
if not len(records):
    error("Received invalid response from system cURL command")

# Check that CloudFlare API returned valid JSON
try:
    records = json.loads(records)
except json.decoder.JSONDecodeError:
    error("Invalid JSON response from CloudFlare API @ " + configuration["cloudflare"]["api"])

info("Received records")

# Invalid DNS zone
if records["result"] == "error":
    error("CloudFlare account does not own zone '" + configuration["account"]["zone"] + "'")

info("Searching for record ID...")

# Find specified record ID
zone_record = None

for record in records["response"]["recs"]["objs"]:
    if record["name"] == configuration["zone"]["name"]:
        zone_record = record

# Check that a record was found
if zone_record is None:
    error("Existing record for '" + configuration["zone"]["name"] + "' not found - please create it first!")

info("Found record ID: '" + configuration["zone"]["name"] + "' => '" + zone_record["rec_id"] + "'")

# Check for a change in IP address - save useless API queries
if zone_record["content"] == ip_address:
    info("'" + configuration["zone"]["type"] + "' record is unchanged from '" + ip_address + "'")
    info("pycf quitting...")
# Record has changed
else:
    # Construct record update query
    command = "curl -s {0} -d 'a=rec_edit' -d 'tkn={1}' -d 'id={2}' -d 'email={3}' -d 'z={4}' "
    command += "-d 'type={5}' -d 'name={6}' -d 'content={7}' -d 'service_mode={8}' -d 'ttl={9}'"
    command = command.format(
        configuration["cloudflare"]["api"],
        configuration["account"]["key"],
        zone_record["rec_id"],
        configuration["account"]["email"],
        configuration["account"]["zone"],
        configuration["zone"]["type"],
        configuration["zone"]["name"],
        ip_address,
        int(configuration["zone"]["proxy"]),
        configuration["zone"]["ttl"]
    )

    # Update record
    info("Executing update query...")
    response = os.popen(command).read()

    # Check that valid JSON was returned
    try:
        response = json.loads(response)
    except json.decoder.JSONDecodeError:
        error("Invalid JSON response from CloudFlare API @ " + configuration["cloudflare"]["api"])

    # Update query succeeded
    if response["result"] == "success":
        info("Update succeeded!")
        info("pycf quitting...")
    else:
        error("Failed to update - output: " + response["msg"])
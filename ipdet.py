#!/usr/bin/env -S runvenv .venv
#
# (c) 2025, Ryan A. Colyer
# Made available under the GPLv3 license
#

import maxminddb
import whoisit
import sys
import os

script_dir = os.path.dirname(os.path.realpath(__file__))
db = maxminddb.open_database(os.path.join(script_dir, 'GeoLite2-City.mmdb'))

if len(sys.argv) < 2:
  print(sys.argv[0], '<ip_address>')
  print(sys.argv[0], '<hostname>')
  sys.exit(-1)

ipaddr = sys.argv[1]
hostname = None

try:
  res = db.get(ipaddr)
except ValueError:
  # raised if maxminddb thinks this is not an ip address.
  import socket
  try:
    # Fall back to treating it like a hostname.
    hostname = ipaddr
    ipaddr = socket.gethostbyname(hostname)
  except Exception:
    print('Not an ip address, and could not resolve as a hostname.')
    sys.exit(-1)
  res = db.get(ipaddr)


d = {}
# Check for all the useful entries, failing gracefully on every missing one.
try:
  d.update({'continent': res['continent']['names']['en']})
except Exception:
  pass
try:
  d.update({'country': res['country']['names']['en']})
except Exception:
  try:
    d.update({'registered_country': res['registered_country']['names']['en']})
  except Exception:
    pass
try:
  d.update({'subdivision':
    ', '.join([e['names']['en'] for e in res['subdivisions']])})
except Exception:
  pass
try:
  d.update({'city': res['city']['names']['en']})
except Exception:
  pass
try:
  d.update({'geo_id': str(res['city']['geoname_id'])})
except Exception:
  pass
try:
  d.update({'location':
    f'{res["location"]["latitude"]}, {res["location"]["longitude"]}'})
except Exception:
  pass
try:
  d.update({'timezone': res['location']['time_zone']})
except Exception:
  pass

whoisit.bootstrap()
rdap = whoisit.ip(ipaddr)
try:
  d.update({'ip_registrant': rdap['entities']['registrant'][0]['name']})
except Exception:
  pass
try:
  d.update({'ip_abuse': rdap['entities']['abuse'][0]['url']})
except Exception:
  pass
try:
  d.update({'net_handle': rdap['handle']})
except Exception:
  pass
try:
  d.update({'network': str(rdap['network'])})
except Exception:
  pass

if hostname is not None:
  # e.g. convert a.b.c.foo.co.uk to foo.co.uk
  while hostname.count('.') > 2:
    hostname = hostname[hostname.index('.')+1:]
  while True:
    try:
      hrdap = whoisit.domain(hostname)
      break
    except Exception:
      # Pop off the left bit and try again as foo.com
      if hostname.count('.') > 1:
        hostname = hostname[hostname.index('.')+1:]
      else:
        break

  try:
    d.update({'registrar': hrdap['entities']['registrar'][0]['name']})
  except Exception:
    pass
  try:
    d.update({'domain_abuse': hrdap['entities']['abuse'][0]['email']})
  except Exception:
    pass
  try:
    d.update({'nameservers': ', '.join(hrdap['nameservers'])})
  except Exception:
    pass

# Filter out empty-string results.
d = {k:v for k,v in d.items() if v}

if len(d) == 0:
  print('Address not found.')
else:
  maxlen = max(len(k) for k in d)
  print('\n'.join(f'{k}:'.ljust(maxlen+3)+str(v) for k,v in d.items()))


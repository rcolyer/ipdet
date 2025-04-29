#!/usr/bin/env -S runvenv .venv
#
# (c) 2025, Ryan A. Colyer
# Made available under the GPLv3 license
#

import maxminddb
import inspect
import pprint
import sys
import os

script_dir = os.path.dirname(os.path.realpath(__file__))
db = maxminddb.open_database(os.path.join(script_dir, 'GeoLite2-City.mmdb'))

run_as_geo = os.path.splitext(os.path.basename(sys.argv[0]))[0] == 'geoinfo'
debmodes = ['--debug', '--stacktraces']
if len(sys.argv) < 2 or '--help' in sys.argv[1:] or \
    all(s.startswith('-') for s in sys.argv[1:]):
  print('Run as:' if run_as_geo else 'Full information with remote lookup:')
  print(f'  {sys.argv[0]} <ip_address>')
  print(f'  {sys.argv[0]} <hostname>')
  if not run_as_geo:
    print('Geographic data via local database query only:')
    print(f'  geoinfo <ip_address>')
    print(f'  geoinfo <hostname>')
    print('  Or use option: --geo')

  print('Debugging options: ' + ', '.join(debmodes + ['--rawdata']))
  sys.exit(0 if '--help' in sys.argv[1:] else -1)

debug = False
stacktraces = False
show_raw_data = False
do_remote = True


def ArgsPop(s):
  if s in sys.argv[1:]:
    arg_ind = sys.argv[1:].index(s)
    sys.argv = sys.argv[:arg_ind+1]+sys.argv[arg_ind+2:]

if '--rawdata' in sys.argv[1:]:
  show_raw_data = True
  ArgsPop('--rawdata')
if any(dm in sys.argv[1:] for dm in debmodes):
  debug = True
  error_cnt = 0
  if '--stacktraces' in sys.argv[1:]:
    stacktraces = True
    import traceback
    rawdata_id_set = set()
    rawdata_list = []
  for dm in debmodes:
    ArgsPop(dm)

if '--geo' in sys.argv[1:] or run_as_geo:
  ArgsPop('--geo')
  do_remote = False


def DebPrint(e, linenum, info='', rawdata=None):
  if debug:
    if info:
      info += ', '
    print(f'Line_{linenum}: {info}{repr(e)}')
    if stacktraces:
      print(''.join(traceback.format_exception(type(e), e, e.__traceback__)))
      if rawdata is not None:
        if id(rawdata) not in globals()['rawdata_id_set']:
          globals()['rawdata_id_set'].add(id(rawdata))
          globals()['rawdata_list'].append(rawdata)
    globals()['error_cnt'] += 1

if len(sys.argv) > 2:
  argv_extra = ' '.join(sys.argv[2:])
  argv_s = 's' if len(sys.argv)>3 else ''
  print(f'Unprocessed command-line argument{argv_s}:  {argv_extra}\n')
ipaddr = sys.argv[1]
hostname = None

try:
  geo = db.get(ipaddr)
except ValueError:
  # raised if maxminddb thinks this is not an ip address.
  import socket
  try:
    # Fall back to treating it like a hostname.
    hostname = ipaddr
    ipaddr = socket.gethostbyname(hostname)
  except Exception as e:
    DebPrint(e, inspect.currentframe().f_lineno, hostname)
    print('Not an ip address, and could not resolve as a hostname.')
    sys.exit(-1)
  geo = db.get(ipaddr)


d = {}
# Check for all the useful entries, failing gracefully on every missing one.
try:
  d.update({'continent': geo['continent']['names']['en']})
except Exception as e:
  DebPrint(e, inspect.currentframe().f_lineno, 'continent', geo)
try:
  d.update({'country': geo['country']['names']['en']})
except Exception as e:
  DebPrint(e, inspect.currentframe().f_lineno, 'country', geo)
  try:
    d.update({'registered_country': geo['registered_country']['names']['en']})
  except Exception as e:
    DebPrint(e, inspect.currentframe().f_lineno, 'registered_country', geo)
try:
  d.update({'subdivision':
    ', '.join([e['names']['en'] for e in geo['subdivisions']])})
except Exception as e:
  DebPrint(e, inspect.currentframe().f_lineno, 'subdivision', geo)
try:
  d.update({'city': geo['city']['names']['en']})
except Exception as e:
  DebPrint(e, inspect.currentframe().f_lineno, 'city', geo)
try:
  d.update({'geo_id': str(geo['city']['geoname_id'])})
except Exception as e:
  DebPrint(e, inspect.currentframe().f_lineno, 'geo_id')
try:
  d.update({'location':
    f'{geo["location"]["latitude"]}, {geo["location"]["longitude"]}'})
except Exception as e:
  DebPrint(e, inspect.currentframe().f_lineno, 'location', geo)
try:
  d.update({'timezone': geo['location']['time_zone']})
except Exception as e:
  DebPrint(e, inspect.currentframe().f_lineno, 'timezone', geo)

rdap = None
hrdap = None

if do_remote:
  import whoisit
  try:
    whoisit.bootstrap()
    rdap = whoisit.ip(ipaddr)
  except Exception as e:
    DebPrint(e, inspect.currentframe().f_lineno, 'whoisit')

  if rdap is not None:
    try:
      d.update({'ip_registrant': rdap['entities']['registrant'][0]['name']})
    except Exception as e:
      DebPrint(e, inspect.currentframe().f_lineno, 'ip_registrant', rdap)
    try:
      d.update({'ip_abuse': rdap['entities']['abuse'][0]['url']})
    except Exception as e:
      DebPrint(e, inspect.currentframe().f_lineno, 'ip_abuse', rdap)
      try:
        d.update({'ip_abuse': rdap['entities']['abuse'][0]['email']})
      except Exception as e:
        DebPrint(e, inspect.currentframe().f_lineno, 'ip_abuse', rdap)
    try:
      d.update({'net_handle': rdap['handle']})
    except Exception as e:
      DebPrint(e, inspect.currentframe().f_lineno, 'net_handle', rdap)
    try:
      d.update({'net_name': rdap['name']})
    except Exception as e:
      DebPrint(e, inspect.currentframe().f_lineno, 'net_name', rdap)
    try:
      d.update({'network': str(rdap['network'])})
    except Exception as e:
      DebPrint(e, inspect.currentframe().f_lineno, 'network', rdap)

  if hostname is not None:
    # e.g. convert a.b.c.foo.co.uk to foo.co.uk
    pass_errors = 0
    while hostname.count('.') > 2:
      hostname = hostname[hostname.index('.')+1:]
    while True:
      try:
        try:
          hrdap = whoisit.domain(hostname)
          if debug and pass_errors>0:
            print(f'Line_{inspect.currentframe().f_lineno}: But succeeded with {hostname}')
          raw = False
        except whoisit.errors.ResourceDoesNotExist as e:
          raise
        # UnboundLocalError too due to typo in latest whoisit, 3.0.4, issue #42
        except (whoisit.errors.QueryError, UnboundLocalError) as e:
          DebPrint(e, inspect.currentframe().f_lineno, hostname)
          # Desperate fallback to raw mode.
          hrdap = whoisit.domain(hostname, raw=True)
          if debug:
            print(f'Line_{inspect.currentframe().f_lineno}: But switched to raw mode with {hostname}')
          raw = True
        break
      except Exception as e:
        DebPrint(e, inspect.currentframe().f_lineno, hostname)
        pass_errors += 1
        # Pop off the left bit and try again as foo.com
        if hostname.count('.') > 1:
          hostname = hostname[hostname.index('.')+1:]
        else:
          break

    if hrdap is not None:
      try:
        d.update({'registrar':
          [v[-1] for e in hrdap['entities'] if 'registrar' in e['roles']
            for v in e['vcardArray'][1] if v[0] == 'fn'][0] if raw else
          hrdap['entities']['registrar'][0]['name']})
      except Exception as e:
        DebPrint(e, inspect.currentframe().f_lineno, f'registrar, raw={raw}', hrdap)
      try:
        d.update({'domain_abuse':
          [a[-1] for e in [e['entities'] for e in hrdap['entities'] if 'entities' in e][0]
            for a in e['vcardArray'][1] if a[0] in ['email']][0] if raw else
          hrdap['entities']['abuse'][0]['email']})
      except Exception as e:
        DebPrint(e, inspect.currentframe().f_lineno, f'domain_abuse, raw={raw}', hrdap)
      try:
        d.update({'nameservers':
          ', '.join([e['ldhName'] for e in hrdap['nameservers']]) if raw else
          ', '.join(hrdap['nameservers'])})
      except Exception as e:
        DebPrint(e, inspect.currentframe().f_lineno, f'nameservers, raw={raw}', hrdap)

# Filter out empty-string results.
d = {k:v for k,v in d.items() if v}

rawdata_noterrored = [e for e in [geo, rdap, hrdap] if e is not None]
if stacktraces and rawdata_list:
  for rd in rawdata_list:
    find_var = [k for k,v in locals().items() if v is rd]
    label = find_var[0] if find_var else 'raw_data'
    print(f'\n--- erroring {label} start ---')
    pprint.pprint(rd)
    print(f'--- erroring {label} end ---')
    if rd in rawdata_noterrored:
      rawdata_noterrored.remove(rd)
if show_raw_data:
  for rd in rawdata_noterrored:
    find_var = [k for k,v in locals().items() if v is rd]
    label = find_var[0] if find_var else 'raw_data'
    print(f'\n--- {label} start ---')
    pprint.pprint(rd)
    print(f'--- {label} end ---')

if debug and error_cnt>0 or show_raw_data:
  print()

if len(d) == 0:
  print('Address not found.')
else:
  maxlen = max(len(k) for k in d)
  print('\n'.join(f'{k}:'.ljust(maxlen+3)+str(v) for k,v in d.items()))


# ipdet

This repository provides a python script, `ipdet`, which provides geographic
location information and select registration details for ip addresses and
hostnames.  The geographic location information sources from a download of the
MaxMind GeoLite2-City.mmdb database grabbed by the install script, while the
additional registration information is queried actively via the rdap protocol
with the whoisit package.  The core goal is to provide a compact report,
combining these two information sources, while remaining focused on the
information useful for identification of an ip address or hostname.

Note that not all categories of information are available for all ip addresses
or hostnames.  ipdet will fail gracefully, and include the available
information in its report.


# Installing

Use git to clone this repository:

```
git clone https://github.com/rcolyer/ipdet.git
```

Then run the install script:

```
cd ipdet
bash install.sh
```


# Examples

```
~$ ipdet 3.3.3.3
continent:      North America
country:        United States
subdivision:    Virginia
city:           Ashburn
geo_id:         4744870
location:       39.0469, -77.4903
timezone:       America/New_York
ip_registrant:  Amazon Technologies Inc.
ip_abuse:       https://rdap.arin.net/registry/entity/AEA8-ARIN
net_handle:     NET-3-0-0-0-1
net_name:       AT-88-Z
network:        3.0.0.0/9
```

```
~$ ipdet www.bbc.co.uk
continent:      North America
country:        United States
subdivision:    New York
city:           New York
geo_id:         5128581
location:       40.7126, -74.0066
timezone:       America/New_York
ip_registrant:  Fastly, Inc.
ip_abuse:       https://rdap.arin.net/registry/entity/ABUSE4771-ARIN
net_handle:     NET-151-101-0-0-1
net_name:       SKYCA-3
network:        151.101.0.0/16
registrar:      British Broadcasting Corporation
domain_abuse:   nominet.admins@bbc.co.uk
nameservers:    ddns0.bbc.co.uk., ddns0.bbc.com., ddns1.bbc.co.uk., ddns1.bbc.com., dns0.bbc.co.uk., dns0.bbc.com., dns1.bbc.co.uk., dns1.bbc.com.
```


# License

ipdet is licensed under the GPLv3.


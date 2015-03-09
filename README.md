# pycf

pycf is a basic dynamic DNS updater that operates only with the CloudFlare API to update hosts.

# Why?

I got sick of ddclient not working with CloudFlare - even the latest version packaged with "Debian Unstable" will not work with CloudFlare's API, and I'm not holding my breath for a working version.

# Requirements

* Python 3 and above
* cURL installed and accessible by "cURL" (most Linux distros)
* pycf.json file - **rename pycf-dist.json to pycf.json and configure it first**
* crontab or similar system - you'll want to run this at set intervals
  * e.g. `*/5 * * * * python pycf.py` will run every 5 minutes

# Configuration

A basic configuration is supplied with pycf (includes all supported settings):

```json
{
   "cloudflare": {
      "checkip":"http:\/\/checkip.proxycha.in",
      "api":"https:\/\/www.cloudflare.com\/api_json.html"
   },
   "account": {
      "email":"email address",
      "key":"api key",
      "zone":"top level domain"
   },
   "zone": {
      "name":"domain to update",
      "proxy":false,
      "type":"A",
      "ttl":300
   }
}
```

You'll want to replace the following settings:

* `Account`
  * `email` - your CloudFlare email address
  * `key` - your [CloudFlare API key](https://support.cloudflare.com/hc/en-us/articles/200167836-Where-do-I-find-my-CloudFlare-API-key-)
  * `zone` - your **top level domain (e.g. domain.com), not your dynamic domain name (e.g. myip.domain.com)** 
* `Zone`
  * `name` - your dynamic DNS domain (e.g. myip.domain.com)
  * `proxy` - if you use CloudFlare for DDoS/caching, **set this to true**
  * `type` - DNS record type, by default this is "A" (for IPv4 addresses) - should work with "AAAA" records too (for IPv6 addresses)
  * `ttl` - time-to-live value of the DNS record - 5 minutes is good for dynamic hosts
  
Optionally, you can also change:

* `CloudFlare`
  * `checkip` - any HTTP resource (or really anything that cURL can handle) which returns JUST the current IP address (see: [example resource](http://checkip.proxycha.in/))
  * `api` - CloudFlare API URI - not sure why this would change (..ever), but can't hurt to have this be easily changed
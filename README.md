BART API
===

Python implementation of the BART API

http://api.bart.gov/docs/overview/index.aspx

Installation
---

```sh
$ virtualenv env
$ source env/bin/activate
(env)$ python setup.py install
```

Usage
---

A simple example to use the API:

```py
from bart.api import BartApi

API_KEY='MW9S-E7SL-26DU-VV8V`
client = BartApi(API_KEY)
print client.get_schedules()
```

API Keys
---

Please note that the API key above is an example provided by the documentation:

http://api.bart.gov/docs/overview/examples.aspx

You will want to get your own key here:

http://api.bart.gov/api/register.aspx

Development
---

For development you'll want to install necessary requirements separately:

```sh
$ virtualenv env
$ source env/bin/activate
(env)$ pip install -r requirements.txt
```

You can also use the `Makefile` to test building the package:

```sh
$ make clean default dist
```

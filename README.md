# 💧 Regenmaschine: A Simple Python Library for RainMachine™

[![Travis CI](https://travis-ci.org/bachya/regenmaschine.svg?branch=master)](https://travis-ci.org/bachya/regenmaschine)
[![PyPi](https://img.shields.io/pypi/v/regenmaschine.svg)](https://pypi.python.org/pypi/regenmaschine)
[![Version](https://img.shields.io/pypi/pyversions/regenmaschine.svg)](https://pypi.python.org/pypi/regenmaschine)
[![License](https://img.shields.io/pypi/l/regenmaschine.svg)](https://github.com/bachya/regenmaschine/blob/master/LICENSE)
[![Code Coverage](https://codecov.io/gh/bachya/regenmaschine/branch/master/graph/badge.svg)](https://codecov.io/gh/bachya/regenmaschine)
[![Maintainability](https://api.codeclimate.com/v1/badges/a99a88d28ad37a79dbf6/maintainability)](https://codeclimate.com/github/bachya/regenmaschine/maintainability)
[![Say Thanks](https://img.shields.io/badge/SayThanks-!-1EAEDB.svg)](https://saythanks.io/to/bachya)

`regenmaschine` (German for "rain machine") is a simple, clean, well-tested Python
library for interacting with
[RainMachine™ smart sprinkler controllers](http://www.rainmachine.com/).
It gives developers an easy API to manage their
controllers over their local LAN.

# PLEASE READ: Version 1.0.0 and Beyond

Version 1.0.0 of `regenmaschine` makes several breaking, but necessary changes:

* Moves the underlying library from
  [Requests](http://docs.python-requests.org/en/master/) to
  [aiohttp](https://aiohttp.readthedocs.io/en/stable/)
* Changes the entire library to use `asyncio`
* Makes 3.6 the minimum version of Python required

If you wish to continue using the previous, synchronous version of
`regenmaschine`, make sure to pin version 0.4.2.

# Installation

```python
pip install regenmaschine
```

# Example

`regenmaschine` starts within an
[aiohttp](https://aiohttp.readthedocs.io/en/stable/) `ClientSession`:

```python
import asyncio

from aiohttp import ClientSession

from regenmaschine import Client


async def main() -> None:
    """Create the aiohttp session and run the example."""
    async with ClientSession() as websession:
      # YOUR CODE HERE


asyncio.get_event_loop().run_until_complete(main())
```

A `regenmaschine` `Client` can be created manually:

```python
import asyncio

from aiohttp import ClientSession

from regenmaschine import Client


async def main() -> None:
    """Create the aiohttp session and run the example."""
    async with ClientSession() as websession:
      client = Client('192.168.1.100', websession, port=9999)


asyncio.get_event_loop().run_until_complete(main())
```

...or you can attempt to discover one on your local network:

```python
import asyncio

from aiohttp import ClientSession

from regenmaschine import Client, scan
from regenmaschine.errors import DiscoveryFailedError


async def main() -> None:
    """Create the aiohttp session and run the example."""
    async with ClientSession() as websession:

      try:
        client = scan(websession)
      except DiscoveryFailedError:
        print("Couldn't find a valid RainMachine unit via discovery")


asyncio.get_event_loop().run_until_complete(main())
```

Once you have a client, authenticate it by using your RainMachine password and
get to work:

```python
import asyncio

from aiohttp import ClientSession

from regenmaschine import Client


async def main() -> None:
    """Create the aiohttp session and run the example."""
    async with ClientSession() as websession:
      client = Client('192.168.1.100', websession, port=9999)

      # Authenticate using your password:
      await client.authenticate('my_password_123')

      # Print some client properties:
      print('Name: {0}'.format(client.name))
      print('Host: {0}'.format(client.host))
      print('MAC Address: {0}'.format(client.mac))

      # Get all diagnostic information:
      diagnostics = await client.diagnostics.current()

      # Get all weather parsers:
      parsers = await client.parsers.current():

      # Get all programs:
      programs = await client.programs.all():

      # Get a specific program:
      program_1 = await client.programs.get(1)

      # Get the next run time for all programs:
      runs = await client.programs.next()

      # Get all running programs:
      programs = await client.programs.running()

      # Start and stop a program:
      await client.programs.start(1)
      await client.programs.stop(1)

      # Get the device name:
      name = await client.provisioning.device_name

      # Get all provisioning settings:
      settings = await client.provisioning.settings()

      # Get all networking info related to the device:
      wifi = await client.provisioning.wifi()

      # Get various types of active watering restrictions:
      current = await client.restrictions.current()
      universal = await client.restrictions.universal()
      hourly = await client.restrictions.hourly():
      raindelay = await client.restrictions.raindelay()

      # Get watering stats:
      today = await client.stats.on_date(date=datetime.date.today())
      upcoming_days = await client.stats.upcoming(details=True):

      # Get info on various watering activities not already covered:
      log_2_day = await client.watering.log(date=datetime.date.today(), 2):
      queue = await client.watering.queue()
      runs = await client.watering.runs(date=datetime.date.today())

      # Stop all watering activities:
      await client.watering.stop_all()


asyncio.get_event_loop().run_until_complete(main())
```

Check out `example.py`, the tests, and the source files themselves for method
signatures and more examples.

# Contributing

1. [Check for open features/bugs](https://github.com/bachya/regenmaschine/issues)
  or [initiate a discussion on one](https://github.com/bachya/regenmaschine/issues/new).
2. [Fork the repository](https://github.com/bachya/regenmaschine/fork).
3. Install the dev environment: `make init`.
4. Enter the virtual environment: `pipenv shell`
5. Code your new feature or bug fix.
6. Write a test that covers your new functionality.
7. Run tests and ensure 100% code coverage: `make coverage`
8. Add yourself to `AUTHORS.md`.
9. Submit a pull request!
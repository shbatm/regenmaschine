"""Define an object to interact with generic watering data/actions."""
import datetime
from typing import Awaitable, Callable


class Watering(object):
    """Define a watering object."""

    def __init__(self, request: Callable[..., Awaitable[dict]]) -> None:
        """Initialize."""
        self._request = request

    async def log(
            self,
            date: datetime.date = None,
            days: int = None,
            details: bool = False) -> list:
        """Get watering information for X days from Y date."""
        endpoint = 'watering/log'
        if details:
            endpoint += '/details'

        if date and days:
            endpoint = '{0}/{1}/{2}'.format(
                endpoint, date.strftime('%Y-%m-%d'), days)

        data = await self._request('get', endpoint)
        return data['waterLog']['days']

    async def queue(self) -> list:
        """Return the queue of active watering activities."""
        data = await self._request('get', 'watering/queue')
        return data['queue']

    async def runs(self, date: datetime.date = None, days: int = None) -> list:
        """Return all program runs for X days from Y date."""
        endpoint = 'watering/past'

        if date and days:
            endpoint = '{0}/{1}/{2}'.format(
                endpoint, date.strftime('%Y-%m-%d'), days)

        data = await self._request('get', endpoint)
        return data['pastValues']

    async def stop_all(self) -> dict:
        """Stop all programs and zones from running."""
        return await self._request('post', 'watering/stopall')

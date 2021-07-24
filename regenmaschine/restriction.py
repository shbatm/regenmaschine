"""Define an object to interact with restriction info."""
from typing import Any, Awaitable, Callable, Dict, List, cast


class Restriction:
    """Define a restriction object."""

    def __init__(self, request: Callable[..., Awaitable[Dict[str, Any]]]) -> None:
        """Initialize."""
        self._request = request

    async def current(self) -> Dict[str, Any]:
        """Get currently active restrictions."""
        return await self._request("get", "restrictions/currently")

    async def hourly(self) -> List[Dict[str, Any]]:
        """Get a list of restrictions that are active over the next hour."""
        data = await self._request("get", "restrictions/hourly")
        return cast(List[Dict[str, Any]], data["hourlyRestrictions"])

    async def raindelay(self) -> Dict[str, Any]:
        """Get restriction info related to rain delays."""
        return await self._request("get", "restrictions/raindelay")

    async def universal(self) -> Dict[str, Any]:
        """Get global (always active) restrictions."""
        return await self._request("get", "restrictions/global")

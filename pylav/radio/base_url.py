from __future__ import annotations

import asyncio
import random
import socket

import aiodns
from red_commons.logging import getLogger

LOGGER = getLogger("red.PyLink.pyradios")
DNS_RESOLVER = aiodns.DNSResolver()


class Error(Exception):
    """Base class for all exceptions raised by this module."""


class RDNSLookupError(Error):
    def __init__(self, ip):
        self.ip = ip
        self.error_msg = f"There was a problem with performing " f"reverse dns lookup for ip: {ip}"
        super().__init__(self.error_msg)


async def fetch_servers():
    """
    Get IP of all currently available `Radiob Browser` servers.
    Returns:
        list: List of IPs
    """
    ips = []
    try:
        data = await asyncio.to_thread(socket.getaddrinfo, "all.api.radio-browser.info", 80, 0, 0, socket.IPPROTO_TCP)
    except socket.gaierror:
        LOGGER.exception("Network failure")
        raise
    else:
        if data and isinstance(data[0][4], tuple):
            for ip in data:
                ips.append(ip[4][0])
    return ips


async def rdns_lookup(ip: str) -> str:
    """
    Reverse DNS lookup.
    Returns:
        str: hostname
    """

    try:
        p = await DNS_RESOLVER.gethostbyaddr(ip)
        hostname = p.name
    except socket.herror as exc:
        raise RDNSLookupError(ip) from exc
    return hostname


async def fetch_hosts() -> list[str]:
    names = []
    servers = await fetch_servers()

    for ip in servers:
        try:
            host_name = await rdns_lookup(ip)
        except RDNSLookupError as exc:
            LOGGER.exception(exc.error_msg)
        else:
            names.append(host_name)
    return names


async def pick_base_url() -> str:
    hosts = await fetch_hosts()
    url = random.choice(sorted(hosts))
    return f"https://{url}/"

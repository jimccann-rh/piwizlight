#!/usr/bin/env python3
"""Control WizLight bulb to show Claude Code status."""
import asyncio
import sys
from pathlib import Path
from pywizlight import wizlight, PilotBuilder, discovery

BULB_IP_FILE = Path.home() / "blubip.txt"

async def discover_and_save_bulb():
    """Discover WizLight bulb on the network and save its IP."""
    bulbs = await discovery.discover_lights(broadcast_space="192.168.0.255")
    if not bulbs:
        print("No WizLight bulbs found on the network", file=sys.stderr)
        return None
    bulb_ip = bulbs[0].ip
    # Save to file for future use
    BULB_IP_FILE.write_text(bulb_ip)
    return bulb_ip

async def get_bulb_ip():
    """Get bulb IP from cache file or discover if not available."""
    if BULB_IP_FILE.exists():
        return BULB_IP_FILE.read_text().strip()
    # No cached IP, run discovery
    bulb_ip = await discover_and_save_bulb()
    if bulb_ip is None:
        sys.exit(1)
    return bulb_ip

async def set_status(status: str):
    """Set the bulb color based on Claude's status.

    Args:
        status: One of 'working', 'idle', 'input', 'warm', 'flash', 'off'
    """
    bulb_ip = await get_bulb_ip()
    light = wizlight(bulb_ip)

    try:
        if status == "working":
            # Red - needs user input
            await light.turn_on(PilotBuilder(rgb=(255, 0, 0), brightness=255))
        elif status == "idle":
            # Yellow - processing
            await light.turn_on(PilotBuilder(rgb=(255, 255, 0), brightness=255))
        elif status == "input":
            # Green - ready
            await light.turn_on(PilotBuilder(rgb=(0, 255, 0), brightness=255))
        elif status == "warm":
            # Warm white at 20% brightness - goodbye/session ending
            await light.turn_on(PilotBuilder(warm_white=255, brightness=51))
        elif status == "flash":
            # Bright white flash - file written/edited
            await light.turn_on(PilotBuilder(rgb=(255, 255, 255), brightness=255))
        elif status == "off":
            # Turn off - session ended
            await light.turn_off()
        else:
            print(f"Unknown status: {status}", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        # If connection failed, try rediscovering the bulb
        print(f"Connection error with cached IP {bulb_ip}, rediscovering bulb...", file=sys.stderr)
        await light.async_close()

        # Rediscover and retry
        bulb_ip = await discover_and_save_bulb()
        if bulb_ip is None:
            sys.exit(1)
        light = wizlight(bulb_ip)

        try:
            if status == "working":
                await light.turn_on(PilotBuilder(rgb=(255, 0, 0), brightness=255))
            elif status == "idle":
                await light.turn_on(PilotBuilder(rgb=(255, 255, 0), brightness=255))
            elif status == "input":
                await light.turn_on(PilotBuilder(rgb=(0, 255, 0), brightness=255))
            elif status == "warm":
                await light.turn_on(PilotBuilder(warm_white=255, brightness=51))
            elif status == "flash":
                await light.turn_on(PilotBuilder(rgb=(255, 255, 255), brightness=255))
            elif status == "off":
                await light.turn_off()
        except Exception as retry_error:
            print(f"Error controlling light after rediscovery: {retry_error}", file=sys.stderr)
            sys.exit(1)
        finally:
            await light.async_close()
    else:
        # Properly close the connection to avoid cleanup warnings
        await light.async_close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: pi_status_light.py <working|idle|input|warm|flash|off>", file=sys.stderr)
        sys.exit(1)

    asyncio.run(set_status(sys.argv[1]))

from aiohttp import ClientSession
import json
from collections import namedtuple
import logging

_LOGGER = logging.getLogger(__name__)

API_APP_ID = 'zHtVqXt8k4yFyk2QGmgp48D9xZr2G94xWYnF4dak'
API_BASE_URL = 'https://cloud.plejd.com'
API_LOGIN_URL = '/parse/login'
API_SITE_LIST_URL = '/parse/functions/getSiteList'
API_SITE_DETAILS_URL = '/parse/functions/getSiteById'

Device = namedtuple("Device", ["model", "type", "dimmable"])

LIGHT = "light"
SENSOR = "sensor"
SWITCH = "switch"

HARDWARE_ID = {
    "0": Device("-unknown-", LIGHT, False),
    "1": Device("DIM-01", LIGHT, True),
    "2": Device("DIM-02", LIGHT, True),
    "3": Device("CTR-01", LIGHT, False),
    "4": Device("GWY-01", SENSOR, False),
    "5": Device("LED-10", LIGHT, True),
    "6": Device("WPH-01", SWITCH, False),
    "7": Device("REL-01", SWITCH, False),
    "8": Device("-unknown-", LIGHT, False),
    "9": Device("-unknown-", LIGHT, False),
    "10": Device("-unknown-", LIGHT, False),
    "11": Device("DIM-01", LIGHT, True),
    "12": Device("-unknown-", LIGHT, False),
    "13": Device("Generic", LIGHT, False),
    "14": Device("-unknown-", LIGHT, False),
    "15": Device("-unknown-", LIGHT, False),
    "16": Device("-unknown-", LIGHT, False),
    "17": Device("REL-01", SWITCH, False),
    "18": Device("REL-02", SWITCH, False),
    "19": Device("-unknown-", LIGHT, False),
    "20": Device("SPR-01", SWITCH, False),
}


headers = {
        "X-Parse-Application-Id": API_APP_ID,
        "Content-Type": "application/json",
    }

async def _login(session, username, password):
    body = {
        "username": username,
        "password": password,
    }

    async with session.post(API_LOGIN_URL, json=body, raise_for_status=True) as resp:
        data = await resp.json()
        return data.get("sessionToken")

async def _get_sites(session):
    resp = await session.post(API_SITE_LIST_URL, raise_for_status=True)
    return await resp.json()

async def _get_site_details(session, siteId):
    async with session.post(
                API_SITE_DETAILS_URL,
                params={"siteId": siteId},
                raise_for_status=True
                ) as resp:
        data = await resp.json()
        data = data.get("result")
        data = data[0]
        # with open("site_details.json", "w") as fp:
        #     fp.write(json.dumps(data))
        return data

async def get_site_data(username, password, siteId):
    # TODO: Memoize this somehow?
    async with ClientSession(base_url=API_BASE_URL, headers=headers) as session:
        session_token = await _login(session, username, password)
        _LOGGER.debug("Session token: %s", session_token)
        session.headers["X-Parse-Session-Token"] = session_token
        details = await _get_site_details(session, siteId)
        return details

async def get_sites(username, password):
    async with ClientSession(base_url=API_BASE_URL, headers=headers) as session:
        session_token = await _login(session, username, password)
        _LOGGER.debug("Session token: %s", session_token)
        session.headers["X-Parse-Session-Token"] = session_token
        sites = await _get_sites(session)
        _LOGGER.debug("Sites: %s", sites)
        return sites["result"]


async def get_cryptokey(**credentials):
    sitedata = await get_site_data(**credentials)
    return sitedata["plejdMesh"]["cryptoKey"]

async def get_devices(**credentials):
    site_data = await get_site_data(**credentials)

    retval = {}
    for device in site_data["devices"]:
        BLE_address = device["deviceId"]

        def find_deviceId(d):
            return next((s for s in d if s["deviceId"] == BLE_address), None)

        address = site_data["deviceAddress"][BLE_address]

        settings = find_deviceId(site_data["outputSettings"])
        if settings is not None:
            outputs = site_data["outputAddress"][BLE_address]
            address = outputs[str(settings["output"])]

        plejdDevice = find_deviceId(site_data["plejdDevices"])
        deviceType = HARDWARE_ID.get(plejdDevice["hardwareId"], HARDWARE_ID["0"])
        firmware = plejdDevice["firmware"]["version"]

        dimmable = deviceType.dimmable
        if settings is not None:
            dimmable = settings["dimCurve"] != "NonDimmable"

        room = next((r for r in site_data["rooms"] if r["roomId"] == device["roomId"]), {})

        retval[address] = {
            "address": address,
            "BLE_address": BLE_address,
            "name": device["title"],
            "type": deviceType.type,
            "model": deviceType.model,
            "dimmable": dimmable,
            "room": room.get("title"),
            "firmware": firmware,
        }

    return retval

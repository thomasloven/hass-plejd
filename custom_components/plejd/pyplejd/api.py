from aiohttp import ClientSession
import json
import logging

_LOGGER = logging.getLogger(__name__)

API_APP_ID = 'zHtVqXt8k4yFyk2QGmgp48D9xZr2G94xWYnF4dak'
API_BASE_URL = 'https://cloud.plejd.com'
API_LOGIN_URL = '/parse/login'
API_SITE_LIST_URL = '/parse/functions/getSiteList'
API_SITE_DETAILS_URL = '/parse/functions/getSiteById'


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

site_data = {}
async def get_site_data(username, password, siteId, **_):
    global site_data
    if site_data.get(siteId) is not None:
        return site_data.get(siteId)
    async with ClientSession(base_url=API_BASE_URL, headers=headers) as session:
        session_token = await _login(session, username, password)
        session.headers["X-Parse-Session-Token"] = session_token
        details = await _get_site_details(session, siteId)
        site_data[siteId] = details
        return details

async def get_sites(username, password, **_):
    async with ClientSession(base_url=API_BASE_URL, headers=headers) as session:
        session_token = await _login(session, username, password)
        session.headers["X-Parse-Session-Token"] = session_token
        sites = await _get_sites(session)
        return sites["result"]


async def get_cryptokey(**credentials):
    sitedata = await get_site_data(**credentials)
    return sitedata["plejdMesh"]["cryptoKey"]

async def get_devices(**credentials):
    site_data = await get_site_data(**credentials)

    retval = {}
    for device in site_data["devices"]:
        BLE_address = device["deviceId"]

        address = site_data["deviceAddress"][BLE_address]
        dimmable = None

        settings = next((s for s in site_data["outputSettings"] 
            if s["deviceParseId"] == device["objectId"]), None)

        if settings is not None and "output" in settings:
            outputs = site_data["outputAddress"][BLE_address]
            address = outputs[str(settings["output"])]

        if settings is not None:
            if settings.get("dimCurve") is not None:
                if settings.get("dimCurve") in ["nonDimmable", "RelayNormal"]:
                    dimmable = False
                else:
                    dimmable = True
            if settings.get("predefinedLoad",{}).get("loadType") == "No load":
                continue

        plejdDevice = next((s for s in site_data["plejdDevices"]
                if s["deviceId"] == BLE_address), None)
        room = next((r for r in site_data["rooms"] if r["roomId"] == device["roomId"]), {})

        retval[address] = {
            "address": address,
            "BLE_address": BLE_address,
            "data": {
                "name": device["title"],
                "hardwareId": plejdDevice["hardwareId"],
                "dimmable": dimmable,
                "outputType": convertType(device.get("outputType")),
                "room": room.get("title"),
                "firmware": plejdDevice["firmware"]["version"],
            }
        }

    return retval

def convertType(outputType):
    if (outputType == "LIGHT"):
        return "light"
    elif (outputType == "RELAY"):
        return "switch"
    return None

async def get_scenes(**credentials):
    site_data = await get_site_data(**credentials)
    retval = {}
    for scene in site_data["scenes"]:
        sceneId = scene["sceneId"]
        index = site_data["sceneIndex"].get(sceneId)

        retval[index] = {
            "index": index,
            "title": scene["title"],
            "visible": not scene["hiddenFromSceneList"],
        }
        
    return retval

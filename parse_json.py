from pyplejd.cloud import PlejdCloudSite, site_details as sd
from pyplejd.interface import outputDeviceClass, inputDeviceClass, sceneDeviceClass
import json
import sys

fn = "site_details_wms01.json"
fn = "site_details_wms01.json"
fn = "site_details_gwy.json"


def main(filename):
    site = PlejdCloudSite("", "", "")
    with open(filename, "r") as fp:
        details = json.load(fp)
        if "data" in details:
            details = details["data"]
        site._details_raw = details
        site.details = sd.SiteDetails(**site._details_raw)

    print("Output Devices:")
    for output in site.outputs:
        cls = outputDeviceClass(output)
        # pprint.pp(output)
        print(cls(mesh=None, **output))
        # print("")

    print("Input Devices:")
    for input in site.inputs:
        cls = inputDeviceClass(input)
        # pprint.pp(input)
        print(cls(mesh=None, **input))
        # print("")

    print("Scenes:")
    for scene in site.scenes:
        cls = sceneDeviceClass(scene)
        # pprint.pp(input)
        print(cls(mesh=None, **scene))


def usage():
    print(f"usage: {sys.argv[0]} <filename>")
    print("  Filename is the diagnostics data file (.json)")


if __name__ == "__main__":
    if not len(sys.argv) == 2:
        usage()
        sys.exit()
    filename = sys.argv[1]
    main(filename)

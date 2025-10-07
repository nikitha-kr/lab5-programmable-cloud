#!/usr/bin/env python3
import socket, httplib2, google.auth, time
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_httplib2 import AuthorizedHttp

PROJECT   = "lab5-474301"
ZONE      = "us-west1-b"
NAME      = "lab5-flaskr"
MACHINE   = "f1-micro"            # during dev: "e2-medium" (remember to delete!)
FAMILY    = "ubuntu-2204-lts"     # Ubuntu 22.04 LTS image family
IMG_PROJ  = "ubuntu-os-cloud"
TAG       = "allow-5000"
PORT      = 5000
STARTUP   = r"""<PASTE THE STARTUP SCRIPT FROM STEP 2 HERE>"""

def build_compute():
    socket.setdefaulttimeout(60)
    creds, _ = google.auth.default()  # Cloud Shell & GCE auto-provide creds
    http = AuthorizedHttp(creds, http=httplib2.Http(timeout=60))
    return build("compute", "v1", http=http)

def ensure_firewall(compute):
    # Create a rule once: open TCP:5000 to instances with TAG only
    try:
        compute.firewalls().get(project=PROJECT, firewall="allow-5000").execute()
        return
    except HttpError as e:
        if e.resp.status != 404:
            raise
    body = {
        "name": "allow-5000",
        "direction": "INGRESS",
        "allowed": [{"IPProtocol": "tcp", "ports": [str(PORT)]}],
        "sourceRanges": ["0.0.0.0/0"],
        "targetTags": [TAG],
        "network": "global/networks/default"
    }
    compute.firewalls().insert(project=PROJECT, body=body).execute()
    # Target tags scope a firewall rule to only those VMs carrying the tag. :contentReference[oaicite:3]{index=3}

def get_image_link(compute):
    # Latest, non-deprecated image from the family
    img = compute.images().getFromFamily(project=IMG_PROJ, family=FAMILY).execute()
    return img["selfLink"]  # images.getFromFamily returns newest in family. :contentReference[oaicite:4]{index=4}

def wait_zone_op(compute, op):
    name = op["name"]
    while True:
        res = compute.zoneOperations().get(project=PROJECT, zone=ZONE, operation=name).execute()
        if res.get("status") == "DONE":
            if "error" in res: raise RuntimeError(res["error"])
            return
        time.sleep(2)

def create_instance(compute, image_link):
    body = {
        "name": NAME,
        "machineType": f"zones/{ZONE}/machineTypes/{MACHINE}",
        "disks": [{
            "boot": True, "autoDelete": True,
            "initializeParams": {"sourceImage": image_link}
        }],
        "networkInterfaces": [{
            "network": "global/networks/default",
            "accessConfigs": [{"type": "ONE_TO_ONE_NAT", "name": "External NAT"}]
        }],
        "metadata": {"items": [{"key": "startup-script", "value": STARTUP}]},
        "tags": {"items": [TAG]}  # tag now; we’ll also setTags to demonstrate fingerprint use
    }
    op = compute.instances().insert(project=PROJECT, zone=ZONE, body=body).execute()  # instances.insert :contentReference[oaicite:5]{index=5}
    wait_zone_op(compute, op)

def apply_tag(compute):
    inst = compute.instances().get(project=PROJECT, zone=ZONE, instance=NAME).execute()
    tags = inst.get("tags", {}).get("items", [])
    fp   = inst.get("tags", {}).get("fingerprint")
    if TAG not in tags: tags.append(TAG)
    op = compute.instances().setTags(
        project=PROJECT, zone=ZONE, instance=NAME,
        body={"items": tags, "fingerprint": fp}
    ).execute()  # requires up-to-date fingerprint; fetch via instances.get :contentReference[oaicite:6]{index=6}
    wait_zone_op(compute, op)

def external_ip(compute):
    inst = compute.instances().get(project=PROJECT, zone=ZONE, instance=NAME).execute()
    nics = inst.get("networkInterfaces", [])
    return nics[0]["accessConfigs"][0]["natIP"]

def main():
    compute = build_compute()
    ensure_firewall(compute)
    image = get_image_link(compute)
    create_instance(compute, image)
    apply_tag(compute)
    ip = external_ip(compute)
    print(f"\n✅ VM ready (startup still finishing). Visit: http://{ip}:{PORT}\n")

if __name__ == "__main__":
    main()

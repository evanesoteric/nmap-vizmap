import xml.etree.ElementTree as ET
import json, sys

infile  = sys.argv[1] if len(sys.argv) > 1 else "scans/scan.xml"
outfile = sys.argv[2] if len(sys.argv) > 2 else "scans/hosts.json"

tree = ET.parse(infile)
root = tree.getroot()

# Top-level scan metadata
runstats = root.find("runstats")
scan_info = {
    "nmap_version": root.get("version"),
    "args":         root.get("args"),
    "start":        root.get("startstr"),
    "finished":     runstats.find("finished").get("timestr") if runstats is not None and runstats.find("finished") is not None else None,
    "elapsed":      runstats.find("finished").get("elapsed") if runstats is not None and runstats.find("finished") is not None else None,
    "hosts_up":     runstats.find("hosts").get("up") if runstats is not None else None,
    "hosts_total":  runstats.find("hosts").get("total") if runstats is not None else None,
}

hosts = []
for host in root.findall("host"):
    status = host.find("status")
    if status is not None and status.get("state") != "up":
        continue

    # --- Addresses ---
    ip = mac = vendor = None
    for addr in host.findall("address"):
        if addr.get("addrtype") == "ipv4":
            ip = addr.get("addr")
        elif addr.get("addrtype") == "mac":
            mac = addr.get("addr")
            vendor = addr.get("vendor")

    # --- Hostnames ---
    hostnames = [h.get("name") for h in host.findall("hostnames/hostname") if h.get("name")]
    primary_hostname = hostnames[0] if hostnames else None

    # --- Ports (open + closed + filtered) ---
    ports = []
    for port in host.findall("ports/port"):
        state_el   = port.find("state")
        service_el = port.find("service")

        # Collect CPEs (Common Platform Enumeration) for version fingerprinting
        cpes = [c.text for c in port.findall("service/cpe") if c.text]

        ports.append({
            "port":      port.get("portid"),
            "protocol":  port.get("protocol"),
            "state":     state_el.get("state")       if state_el is not None else None,
            "reason":    state_el.get("reason")      if state_el is not None else None,
            "service":   service_el.get("name")      if service_el is not None else None,
            "product":   service_el.get("product")   if service_el is not None else None,
            "version":   service_el.get("version")   if service_el is not None else None,
            "extrainfo": service_el.get("extrainfo") if service_el is not None else None,
            "tunnel":    service_el.get("tunnel")    if service_el is not None else None,
            "cpe":       cpes,
        })

    # Bulk-closed/filtered ports summary (the "Not shown" line)
    extraports = []
    for ep in host.findall("ports/extraports"):
        extraports.append({
            "state": ep.get("state"),
            "count": ep.get("count"),
        })

    # --- OS detection ---
    os_data = {"matches": [], "fingerprint": None, "uptime": None}
    uptime_el = host.find("uptime")
    if uptime_el is not None:
        os_data["uptime"] = {
            "seconds": uptime_el.get("seconds"),
            "lastboot": uptime_el.get("lastboot"),
        }
    osmatch_el = host.find("os/osmatch")
    for m in host.findall("os/osmatch"):
        os_data["matches"].append({
            "name":     m.get("name"),
            "accuracy": m.get("accuracy"),
            "line":     m.get("line"),
            "classes": [
                {
                    "type":     c.get("type"),
                    "vendor":   c.get("vendor"),
                    "osfamily": c.get("osfamily"),
                    "osgen":    c.get("osgen"),
                    "accuracy": c.get("accuracy"),
                }
                for c in m.findall("osclass")
            ],
            "cpe": [c.text for c in m.findall("cpe") if c.text],
        })
    fp_el = host.find("os/osfingerprint")
    if fp_el is not None:
        os_data["fingerprint"] = fp_el.get("fingerprint")

    hosts.append({
        "ip":        ip,
        "mac":       mac,
        "vendor":    vendor,
        "hostname":  primary_hostname,
        "hostnames": hostnames,
        "ports":     ports,
        "extraports": extraports,
        "os":        os_data,
    })

with open(outfile, "w") as f:
    json.dump({"scan": scan_info, "hosts": hosts}, f, indent=2)

print(f"Wrote {len(hosts)} hosts to {outfile}")
print(f"Scan args: {scan_info['args']}")

# Nmap LAN Visualizer

Turn an `nmap` XML scan into an interactive, clickable network topology
diagram — no npm, no Node.js, no build step. Just Python 3 (which ships
with everything you need) and a browser.

---

## What It Does

1. **Parses** an nmap XML scan into a clean JSON file.
2. **Renders** that JSON as a force-directed graph in your browser:
   - Gateway node in the center, one node per discovered host.
   - Hosts with open ports are blue; hosts with none are grey.
   - **Click any node** to see full details in a sidebar: IP, MAC, vendor,
     hostnames, OS match (type/vendor/family/generation), uptime, every
     open port with service/version strings, and bulk port-state counts.
   - **Click the gateway node** to see scan metadata (nmap version, args,
     timing, host counts).
   - **Drag nodes** to rearrange. **Scroll to zoom**. **Click empty space**
     to deselect.

Everything runs locally. No data leaves your machine.

---

## Requirements

| Thing | Why | Notes |
|-------|-----|-------|
| **Python 3** | Parses nmap XML and serves the HTML | Preinstalled on most Linux/macOS. Check with `python3 --version`. |
| **nmap** | Produces the XML scan | `sudo apt install nmap` / `brew install nmap` / [nmap.org/download](https://nmap.org/download) |
| **A modern browser** | Renders the D3 graph | Firefox, Chrome, Safari, Edge all fine. |
| **D3.js** | The graph library | Bundled locally in `vendor/d3.v7.min.js`. No internet needed. |

**No `pip install` needed. No `npm install` needed.** The parser uses only
Python's standard library (`xml.etree.ElementTree` and `json`).

---

## Step 0 — Get D3.js (one-time setup)

The visualization uses D3 v7. If `vendor/d3.v7.min.js` doesn't exist yet,
download it once:

    mkdir -p vendor
    curl -O https://d3js.org/d3.v7.min.js
    mv d3.v7.min.js vendor/

Verify the download — it should be roughly 280-290 KB and start with a
comment (`// https://d3js.org ...`), not `<!DOCTYPE html>`:

    ls -la vendor/d3.v7.min.js
    head -c 80 vendor/d3.v7.min.js

To pin a specific version instead of the moving `v7` target:

- v7.9.0 — https://d3js.org/d3.v7.9.0.min.js
- v7.8.5 — https://d3js.org/d3.v7.8.5.min.js

Any v7.x works with the code in `index.html`.

---

## Step 1 — Run the nmap scan

The parser needs XML output, and to get rich OS/service data you need the
right flags. Best command (requires `sudo` for the SYN scan and OS detection):

    sudo nmap -sS -sV -O --osscan-guess -oX scans/scan.xml 192.168.0.0/24

**What each flag does:**

| Flag | Meaning |
|------|---------|
| `-sS` | SYN "half-open" scan — fast, needs root |
| `-sV` | Service/version detection — fills `product`, `version`, `cpe` |
| `-O` | OS detection — fills the OS match block |
| `--osscan-guess` | Show best-guess OS even at low confidence |
| `-oX scans/scan.xml` | Write results to `scans/scan.xml` — **required** |

**Adjust the target** (`192.168.0.0/24`) to your own subnet.
`192.168.0.1-254` also works.

Because `sudo` writes the file as root, hand ownership back so you can
overwrite it next time:

    sudo chown "$USER:$USER" scans/scan.xml

### If you can't use sudo

`-sS` and `-O` need raw sockets. Fall back to a TCP connect scan:

    nmap -sT -sV -oX scans/scan.xml 192.168.0.0/24

You'll lose OS detection, but you'll still get ports and service versions.

### Quick single-host test

    sudo nmap -sS -sV -O -oX scans/scan.xml 192.168.0.158
    sudo chown "$USER:$USER" scans/scan.xml

Handy for confirming the pipeline works before scanning your whole LAN.

> **Important:** `-oX` is not optional. Without it, there's no XML file, and
> the parser has nothing to read. If you ran nmap without `-oX`, re-run it.

> **Tip:** `-oA scans/scan` writes `scan.xml`, `scan.nmap`, and `scan.gnmap`
> all at once. If you use it, feed the **`.xml`** file to the parser — not
> `.nmap` or `.gnmap`.

---

## Step 2 — Parse the XML into JSON

With `parse_nmap.py` in the project root and `scans/scan.xml` in place, run
from the project root:

    python3 parse_nmap.py

The defaults are `scans/scan.xml` (input) and `scans/hosts.json` (output),
so no arguments are needed. You can override either:

    python3 parse_nmap.py my-scan.xml my-hosts.json

Expected output:

    Wrote 7 hosts to scans/hosts.json
    Scan args: nmap -sS -sV -O --osscan-guess -oX scans/scan.xml 192.168.0.0/24

### Sanity-check the result

Confirm the JSON actually contains what you expect before opening the
browser. This prints each host and its open ports:

    python3 -c "
    import json
    d = json.load(open('scans/hosts.json'))
    print(len(d['hosts']), 'hosts')
    for h in d['hosts']:
        open_ports = [p['port'] for p in h['ports'] if p['state'] == 'open']
        print(' ', h['ip'], h.get('hostname') or '', '->', open_ports or '(no open ports)')
    "

If you see your open ports here, the HTML will show them too.

---

## Step 3 — Serve the folder and open the map

Browsers block `file://` pages from loading local JSON (CORS), so serve the
project root with Python's built-in web server:

    cd ~/Desktop/x
    python3 -m http.server 8000

Then open:

**http://localhost:8000/**

The `index.html` loads automatically — no filename needed.

The server logs every request, so you can watch the page load. A healthy
load looks like this:

    127.0.0.1 - - [24/Sep/2026 19:12:03] "GET / HTTP/1.1" 200 -
    127.0.0.1 - - [24/Sep/2026 19:12:03] "GET /vendor/d3.v7.min.js HTTP/1.1" 200 -
    127.0.0.1 - - [24/Sep/2026 19:12:03] "GET /scans/hosts.json HTTP/1.1" 200 -

Three `200`s = good. A `404` tells you exactly which path to fix.

Press **Ctrl+C** in the terminal to stop the server when you're done.

---

## Using the Interface

| Action | Result |
|--------|--------|
| **Click a host node** | Sidebar shows IP, MAC, vendor, hostnames, OS, uptime, and all ports. |
| **Click the gateway node** | Sidebar shows scan metadata (nmap version, args, timing, host counts). |
| **Click empty space** | Clears the sidebar and deselects. |
| **Drag a node** | Pins it where you drop it (until the simulation relaxes). |
| **Scroll wheel** | Zoom in/out. |
| **Drag empty space** | Pan the canvas. |

**Colors:**

- Orange — gateway (synthetic, not a real host)
- Blue — host with at least one open port
- Grey — host with no open ports detected

---

## Full Walkthrough (Copy-Paste)

    # 0. One-time: create layout and fetch D3
    mkdir -p ~/Desktop/x/vendor ~/Desktop/x/scans
    cd ~/Desktop/x
    curl -O https://d3js.org/d3.v7.min.js && mv d3.v7.min.js vendor/

    # 1. Scan your LAN (adjust the subnet)
    sudo nmap -sS -sV -O --osscan-guess -oX scans/scan.xml 192.168.0.0/24
    sudo chown "$USER:$USER" scans/scan.xml

    # 2. Parse it
    python3 parse_nmap.py

    # 3. Verify
    python3 -c "
    import json
    d = json.load(open('scans/hosts.json'))
    print(len(d['hosts']), 'hosts parsed')
    "

    # 4. Serve and open in browser
    python3 -m http.server 8000
    # -> visit http://localhost:8000/

---

## Re-running After a New Scan

The pipeline is stateless — re-run steps 1 and 2, then refresh the browser.

    sudo nmap -sS -sV -O -oX scans/scan.xml 192.168.0.0/24
    sudo chown "$USER:$USER" scans/scan.xml
    python3 parse_nmap.py

**Hard-refresh the browser** with **Ctrl+Shift+R** (Linux/Windows) or
**Cmd+Shift+R** (macOS). Browsers cache JSON aggressively and will happily
show you the old scan otherwise.

---

## Keeping a Scan History (Optional)

Instead of overwriting `scan.xml` every time, timestamp each scan:

    TS=$(date +%Y-%m-%d-%H%M)
    sudo nmap -sS -sV -O -oX "scans/scan-$TS.xml" 192.168.0.0/24
    sudo chown "$USER:$USER" "scans/scan-$TS.xml"
    python3 parse_nmap.py "scans/scan-$TS.xml" "scans/hosts-$TS.json"
    ln -sf "hosts-$TS.json" scans/hosts.json   # latest -> hosts.json

The `ln -sf` makes `scans/hosts.json` a symlink to the newest parsed scan,
so `index.html` always loads the latest without any path changes. You can
then diff two scans to see what changed between them.

---

## Troubleshooting

### "No open ports" on hosts that clearly have open ports

Almost always one of these:

1. **You didn't use `-oX`.** Check that `scans/scan.xml` exists and is fresh:

       ls -la scans/scan.xml
       head -5 scans/scan.xml

   It should show `<?xml ...` and `<nmaprun ...`.

2. **You're viewing a cached page.** Hard-refresh with **Ctrl+Shift+R**.

3. **You scanned without `-sV`.** Ports will still appear, but the
   `service`, `product`, and `version` columns will be blank.

4. **The host was reported as `down`.** The parser skips hosts whose
   `<status state="...">` isn't `up`. Check with:

       grep -B1 '<status' scans/scan.xml | head -20

### Parser says "Wrote 0 hosts"

Your XML has no `<host>` elements with `state="up"`. Usually means the scan
found nothing (wrong subnet? firewall?) or the file is from a different
tool. Open `scans/scan.xml` and look at the top — it should start with
`<?xml version="1.0"?><nmaprun ...>`.

### Permission denied writing scans/scan.xml on re-scan

`scan.xml` is owned by root because `sudo nmap` wrote it. Either delete it
first (`sudo rm scans/scan.xml`) or chown it back after each scan:

    sudo chown "$USER:$USER" scans/scan.xml

### d3.json() fails / graph is blank / CORS error in console

You opened the HTML with `file://`. You **must** serve over HTTP:

    python3 -m http.server 8000

Then use `http://localhost:8000/` — not `file:///...`.

### `python3: command not found`

Try `python` instead. On Windows, use `py`:

    py parse_nmap.py
    py -m http.server 8000

### OS block says "No OS match"

The scan was run without `-O`, without `sudo`, or the host didn't respond to
OS probes. OS detection is best-effort — many hosts (especially IoT devices
and firewalled servers) simply don't answer.

### Port shows state `open|filtered` or `filtered`

That's nmap being honest — it can't tell whether the port is open or being
silently dropped. The sidebar lists these under "Other Ports" (not "Open
Ports") and colors them orange.

### Sidebar is empty after clicking

Open the browser console (F12) and look for a JavaScript error. The most
common cause is `hosts.json` in the old flat-array format (from an earlier
version of the parser). Re-run `parse_nmap.py` to regenerate it in the
`{ "scan": ..., "hosts": [...] }` format.

---

## What the JSON Contains

For reference — the shape of `scans/hosts.json`:

    {
      "scan": {
        "nmap_version": "7.991",
        "args": "nmap -sS -sV -O ...",
        "start": "...",
        "finished": "...",
        "elapsed": "12.34",
        "hosts_up": "7",
        "hosts_total": "256"
      },
      "hosts": [
        {
          "ip": "192.168.0.158",
          "mac": "AA:BB:CC:DD:EE:FF",
          "vendor": "Raspberry Pi Foundation",
          "hostname": "pi.local",
          "hostnames": ["pi.local"],
          "ports": [
            {
              "port": "53",
              "protocol": "tcp",
              "state": "open",
              "reason": "syn-ack",
              "service": "domain",
              "product": "dnsmasq",
              "version": "2.86",
              "extrainfo": "",
              "tunnel": null,
              "cpe": ["cpe:/a:thekelleys:dnsmasq:2.86"]
            }
          ],
          "extraports": [
            { "state": "closed", "count": "999" }
          ],
          "os": {
            "uptime": { "seconds": "86400", "lastboot": "..." },
            "matches": [
              {
                "name": "Linux 5.4 - 5.15",
                "accuracy": "95",
                "line": "...",
                "classes": [
                  {
                    "type": "general purpose",
                    "vendor": "Linux",
                    "osfamily": "Linux",
                    "osgen": "5.X",
                    "accuracy": "95"
                  }
                ],
                "cpe": ["cpe:/o:linux:linux_kernel:5"]
              }
            ],
            "fingerprint": "..."
          }
        }
      ]
    }

You can post-process this file however you like — feed it to other tools,
diff two scans to see what changed, grep for specific services, etc. The
HTML is just one possible consumer.

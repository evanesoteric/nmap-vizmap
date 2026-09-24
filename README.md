cat > README.md << 'READMEEOF'
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


The `scans/` directory keeps generated artifacts separate from the tool
itself, and makes it easy to keep a history of scans for later comparison.

---

## Step 0 — Get D3.js (one-time setup)

The visualization uses D3 v7. If `vendor/d3.v7.min.js` doesn't exist yet,
download it once:

```bash
mkdir -p vendor
curl -O https://d3js.org/d3.v7.min.js
mv d3.v7.min.js vendor/

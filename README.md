# qgis-geoaudit-dashboard
Plugin para QGIS focado em auditoria vetorial em tempo real, com dashboard integrado, cálculo de tolerância e exportação automatizada de dados.
# GeoAudit Dashboard for QGIS 

A professional QGIS plugin designed to track, audit, and report vector layer modifications in real-time. This tool was developed to solve the challenge of quality control in large-scale digitization projects.

##  Key Features

- **Live Dashboard:** Floating side panel that tracks edits as they happen.
- **Intelligent Classification:** Automatically distinguishes between "Fine Tuning", "Reductions", and "Major Edits" based on a dynamic mathematical tolerance model.
- **Audit Trail:** Every deletion requires a reason, ensuring accountability.
- **Session Management:** Detects existing logs and allows users to resume or create unique timestamped files.
- **One-Click Reporting:** -  **Copy Text:** Formatted list for quick status updates (Slack/Teams/WhatsApp).
  -  **Copy for Excel:** Structured tab-separated data ready to be pasted directly into spreadsheets.
- **Database Backend:** All logs are saved into a high-performance GeoPackage (.gpkg) file on the Desktop.

##  How it Works

The plugin uses a **"Photographic Memory"** logic:
1. When activated, it stores the original geometry of all features in the memory.
2. It monitors the QGIS Edit Buffer for changes.
3. It compares the edited geometry with the original one using a **Symmetric Difference** algorithm to calculate exactly how much area was changed.
4. It applies a sliding tolerance scale (e.g., smaller features have a higher percentage tolerance than larger ones).

##  Installation

1. Open QGIS.
2. Go to **Plugins** -> **Python Console**.
3. Create a new script or add to your local plugin folder (`AppData/Roaming/QGIS/QGIS3/profiles/default/python/plugins`).
4. Paste the `plugin_code.py` content.
5. The **"GeoAudit Tool"** menu will appear in the top menu bar.

##  Usage

1. Select your target vector layer in the Layers Panel.
2. Click **GeoAudit: Toggle Dashboard** in the menu.
3. Perform your edits (Add, Modify, or Delete features).
4. Watch the Dashboard update in real-time.
5. Use the "Copy" buttons at the bottom to export your results.

##  License

This project is licensed under the MIT License - feel free to use it for personal or commercial projects.

---
*Bruno Henrique dos Santos Lima /www.linkedin.com/in/bruno-lima-460217271]*

# Generalized Plugin Code (v5.1 - GitHub/Portfolio Edition)
plugin_code = """import os
from datetime import datetime
from qgis.core import (QgsProject, Qgis, QgsVectorLayer, QgsFeature, 
                       QgsVectorFileWriter, QgsRasterLayer, QgsFeatureRequest, 
                       QgsDistanceArea, QgsGeometry)
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QAction, QInputDialog, QMessageBox, QDockWidget, 
                             QVBoxLayout, QWidget, QLabel, QTextEdit, QPushButton, QApplication)

class GeoAuditDashboard:
    \"\"\"
    GeoAudit Dashboard - A QGIS Plugin for Real-time Vector Auditing.
    Generalized version for public portfolio.
    \"\"\"
    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.dock_widget = None
        self.layer = None
        self.t_log = None
        self.is_active = False
        self.gpkg_path = ""
        self.original_geoms = {}

    def initGui(self):
        # Setup Plugin Action
        self.action = QAction("GeoAudit: Toggle Dashboard", self.iface.mainWindow())
        self.action.setCheckable(True)
        self.action.triggered.connect(self.toggle_monitoring)
        self.iface.addPluginToMenu("&GeoAudit Tool", self.action)
        self.iface.addToolBarIcon(self.action)
        
        self.setup_ui_panel()

    def setup_ui_panel(self):
        \"\"\"Initializes the side panel (Dashboard).\"\"\"
        self.dock_widget = QDockWidget("GeoAudit Live Dashboard", self.iface.mainWindow())
        self.dock_widget.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        
        container = QWidget()
        layout = QVBoxLayout()
        
        self.lbl_stats = QLabel("No active session.")
        self.lbl_stats.setStyleSheet("font-weight: bold; font-size: 11pt; color: #2c3e50;")
        layout.addWidget(self.lbl_stats)
        
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setStyleSheet("font-family: 'Courier New'; font-size: 9pt;")
        layout.addWidget(self.log_display)
        
        self.btn_copy_text = QPushButton("📋 Copy Text Report")
        self.btn_copy_text.clicked.connect(self.copy_to_clipboard_text)
        layout.addWidget(self.btn_copy_text)
        
        self.btn_copy_excel = QPushButton("📊 Copy for Excel (TSV)")
        self.btn_copy_excel.clicked.connect(self.copy_to_clipboard_excel)
        layout.addWidget(self.btn_copy_excel)
        
        container.setLayout(layout)
        self.dock_widget.setWidget(container)
        self.dock_widget.hide()
        self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dock_widget)

    def unload(self):
        self.iface.removePluginMenu("&GeoAudit Tool", self.action)
        self.iface.removeToolBarIcon(self.action)
        self.stop_listeners()
        if self.dock_widget:
            self.iface.removeDockWidget(self.dock_widget)

    def toggle_monitoring(self, checked):
        if checked:
            layer_name = self.get_active_layer_name()
            if not layer_name:
                self.iface.messageBar().pushMessage("Error", "No raster/active reference layer found.", level=Qgis.Warning)
                self.action.setChecked(False)
                return
            
            # Use Desktop but avoid specific user paths in code (dynamic path)
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            base_name = f"Audit_Log_{layer_name}.gpkg"
            target_path = os.path.join(desktop, base_name)

            if not self.gpkg_path: 
                if os.path.exists(target_path):
                    res = QMessageBox.question(
                        self.iface.mainWindow(), "Resume Session?",
                        f"Existing log found: {base_name}.\\n\\nContinue existing session? (Yes)\\nCreate new unique log? (No)",
                        QMessageBox.Yes | QMessageBox.No
                    )
                    if res == QMessageBox.No:
                        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                        self.gpkg_path = os.path.join(desktop, f"Audit_Log_{layer_name}_{ts}.gpkg")
                    else:
                        self.gpkg_path = target_path
                else:
                    self.gpkg_path = target_path

            active_layer = self.iface.activeLayer()
            if not isinstance(active_layer, QgsVectorLayer):
                self.iface.messageBar().pushMessage("Wait", "Select the vector layer to audit.", level=Qgis.Warning)
                self.action.setChecked(False)
                return

            self.layer = active_layer
            self.is_active = True
            
            # Snap Original Geometries
            self.original_geoms.clear()
            for f in self.layer.getFeatures():
                self.original_geoms[f.id()] = QgsGeometry(f.geometry())

            self.init_geopackage()
            self.start_listeners()
            self.dock_widget.show()
            self.update_dashboard()
            self.iface.messageBar().pushMessage("GeoAudit On", f"Logging to: {os.path.basename(self.gpkg_path)}", level=Qgis.Success)
        else:
            self.is_active = False
            self.stop_listeners()
            self.dock_widget.hide()
            self.iface.messageBar().pushMessage("GeoAudit Off", "Monitoring paused.", level=Qgis.Info)

    def update_dashboard(self):
        \"\"\"Updates UI statistics in real-time.\"\"\"
        if not self.t_log or not self.t_log.isValid(): return

        adj, rem, add = [], [], []
        for feat in self.t_log.getFeatures():
            cat = feat["Category"]
            msg = f"ID {feat['ID']} ({feat['Reason']})"
            if cat == "Adjustment": adj.append(msg)
            elif cat == "Deleted": rem.append(f"ID {feat['ID']} - {feat['Reason']}")
            elif cat == "New": add.append(f"ID {feat['ID']}")

        self.lbl_stats.setText(f"Adj: {len(adj)} | New: {len(add)} | Del: {len(rem)}")
        content = "=== ADJUSTMENTS ===\\n" + ("\\n".join(adj) if adj else "-") + "\\n\\n"
        content += "=== ADDITIONS ===\\n" + ("\\n".join(add) if add else "-") + "\\n\\n"
        content += "=== DELETIONS ===\\n" + ("\\n".join(rem) if rem else "-")
        self.log_display.setText(content)

    def calculate_tolerance(self, area):
        \"\"\"
        Generic Tolerance Model (Replace with your own logic).
        Example: Sliding scale based on area.
        \"\"\"
        if area <= 10.0: return 5.0
        elif area <= 100.0: return 3.5
        return 2.0

    def copy_to_clipboard_text(self):
        QApplication.clipboard().setText(self.log_display.toPlainText())
        self.iface.messageBar().pushMessage("Success", "Report copied to clipboard.", level=Qgis.Success)

    def copy_to_clipboard_excel(self):
        if not self.t_log or not self.t_log.isValid(): return
        headers = ["ID", "Category", "Reason", "Initial_Area", "Final_Area", "Change_%", "Tolerance_Used"]
        rows = ["\\t".join(headers)]
        for f in self.t_log.getFeatures():
            rows.append(f"{f['ID']}\\t{f['Category']}\\t{f['Reason']}\\t{f['Area_In']}\\t{f['Area_Out']}\\t{f['Change_Pct']}\\t{f['Tol_Limit']}")
        QApplication.clipboard().setText("\\n".join(rows))
        self.iface.messageBar().pushMessage("Success", "Tab-separated data ready for Excel.", level=Qgis.Success)

    def get_active_layer_name(self):
        layers = QgsProject.instance().mapLayers().values()
        for lyr in layers:
            if isinstance(lyr, QgsRasterLayer): return lyr.name().split('.')[0]
        return "Generic"

    def init_geopackage(self):
        if not os.path.exists(self.gpkg_path):
            fields = "None?field=ID:integer&field=Category:string&field=Reason:string"
            fields += "&field=Area_In:string&field=Area_Out:string"
            fields += "&field=Change_Pct:string&field=Tol_Limit:string"
            vl = QgsVectorLayer(fields, "temp", "memory")
            opts = QgsVectorFileWriter.SaveVectorOptions()
            opts.driverName, opts.layerName = "GPKG", "audit_trail"
            QgsVectorFileWriter.writeAsVectorFormatV3(vl, self.gpkg_path, QgsProject.instance().transformContext(), opts)

        vname = f"Log_{os.path.basename(self.gpkg_path)}"
        existing = QgsProject.instance().mapLayersByName(vname)
        if existing: self.t_log = existing[0]
        else:
            self.t_log = QgsVectorLayer(f"{self.gpkg_path}|layername=audit_trail", vname, "ogr")
            QgsProject.instance().addMapLayer(self.t_log)

    def start_listeners(self):
        if self.layer:
            self.stop_listeners()
            self.layer.featuresDeleted.connect(self.on_delete)
            self.layer.committedFeaturesAdded.connect(self.on_added)
            self.layer.editingStarted.connect(self.start_buffer_watch)
            if self.layer.isEditable(): self.start_buffer_watch()

    def start_buffer_watch(self):
        if self.layer and self.layer.editBuffer():
            try: self.layer.editBuffer().geometryChanged.disconnect(self.on_geometry_edit)
            except: pass
            self.layer.editBuffer().geometryChanged.connect(self.on_geometry_edit)

    def stop_listeners(self):
        if self.layer:
            try: self.layer.featuresDeleted.disconnect(self.on_delete)
            except: pass
            try: self.layer.committedFeaturesAdded.disconnect(self.on_added)
            except: pass
            if self.layer.editBuffer():
                try: self.layer.editBuffer().geometryChanged.disconnect(self.on_geometry_edit)
                except: pass

    def clear_id_log(self, fid):
        try:
            if not self.t_log or not self.t_log.isValid(): return
            req = QgsFeatureRequest().setFilterExpression(f"\\\"ID\\\" = {fid}")
            ids = [f.id() for f in self.t_log.getFeatures(req)]
            if ids: self.t_log.dataProvider().deleteFeatures(ids)
        except: pass

    def log_event(self, fid, cat, reason, ain=0, aout=0, chg=0, tol=0):
        if not self.t_log or not self.t_log.isValid(): return
        try:
            f = QgsFeature(self.t_log.fields())
            f.setAttribute("ID", fid)
            f.setAttribute("Category", cat)
            f.setAttribute("Reason", reason)
            f.setAttribute("Area_In", f"{round(ain,2)} m2")
            f.setAttribute("Area_Out", f"{round(aout,2)} m2")
            f.setAttribute("Change_Pct", f"{round(chg,2)}%")
            f.setAttribute("Tol_Limit", f"{round(tol,2)}%")
            self.t_log.dataProvider().addFeature(f)
            self.t_log.triggerRepaint()
            self.update_dashboard()
        except Exception as e:
            self.iface.messageBar().pushMessage("Log Error", str(e), level=Qgis.Critical)

    def on_delete(self, fids):
        if not self.is_active: return
        valid_fids = [id for id in fids if id >= 0]
        options = ["Overlap", "Shadow/Tree", "Wrong Class", "Duplicate", "Invalid Feature"]
        for fid in valid_fids:
            reason, ok = QInputDialog.getItem(None, f"Delete ID {fid}", "Select Reason:", options, 0, True)
            if ok:
                self.clear_id_log(fid)
                self.log_event(fid, "Deleted", reason)

    def on_added(self, layer_id, feats):
        if not self.is_active: return
        m = QgsDistanceArea()
        m.setSourceCrs(self.layer.crs(), QgsProject.instance().transformContext())
        for f in feats:
            area = m.measureArea(f.geometry())
            self.clear_id_log(f.id())
            self.log_event(f.id(), "New", "Feature Added", 0, area, 100, 0)

    def on_geometry_edit(self, fid, geom):
        if not self.is_active or fid < 0: return
        m = QgsDistanceArea()
        m.setSourceCrs(self.layer.crs(), QgsProject.instance().transformContext())
        
        if fid not in self.original_geoms:
            a_out = m.measureArea(geom)
            self.clear_id_log(fid)
            self.log_event(fid, "New", "Feature Added", 0, a_out, 100, 0)
            return

        old_g = self.original_geoms[fid]
        a_in, a_out = m.measureArea(old_g), m.measureArea(geom)
        diff_area = m.measureArea(geom.symDifference(old_g))
        
        if a_in <= 0: return
        chg_pct = (diff_area / a_in) * 100.0
        tol = self.calculate_tolerance(a_in)
        
        if a_out < a_in: reason = "Area Reduction"
        elif chg_pct <= tol: reason = "Fine Tuning"
        else: reason = "Expansion / Incomplete"

        self.clear_id_log(fid)
        self.log_event(fid, "Adjustment", reason, a_in, a_out, chg_pct, tol)
"""

# Professional README.md
readme_content = """# GeoAudit Dashboard for QGIS 🚀

A professional QGIS plugin designed to track, audit, and report vector layer modifications in real-time. This tool was developed to solve the challenge of quality control in large-scale digitization projects.

## 🌟 Key Features

- **Live Dashboard:** Floating side panel that tracks edits as they happen.
- **Intelligent Classification:** Automatically distinguishes between "Fine Tuning", "Reductions", and "Major Edits" based on a dynamic mathematical tolerance model.
- **Audit Trail:** Every deletion requires a reason, ensuring accountability.
- **Session Management:** Detects existing logs and allows users to resume or create unique timestamped files.
- **One-Click Reporting:** - 📋 **Copy Text:** Formatted list for quick status updates (Slack/Teams/WhatsApp).
  - 📊 **Copy for Excel:** Structured tab-separated data ready to be pasted directly into spreadsheets.
- **Database Backend:** All logs are saved into a high-performance GeoPackage (.gpkg) file on the Desktop.

## 🛠️ How it Works

The plugin uses a **"Photographic Memory"** logic:
1. When activated, it stores the original geometry of all features in the memory.
2. It monitors the QGIS Edit Buffer for changes.
3. It compares the edited geometry with the original one using a **Symmetric Difference** algorithm to calculate exactly how much area was changed.
4. It applies a sliding tolerance scale (e.g., smaller features have a higher percentage tolerance than larger ones).

## 🚀 Installation

1. Open QGIS.
2. Go to **Plugins** -> **Python Console**.
3. Create a new script or add to your local plugin folder (`AppData/Roaming/QGIS/QGIS3/profiles/default/python/plugins`).
4. Paste the `plugin_code.py` content.
5. The **"GeoAudit Tool"** menu will appear in the top menu bar.

## 📖 Usage

1. Select your target vector layer in the Layers Panel.
2. Click **GeoAudit: Toggle Dashboard** in the menu.
3. Perform your edits (Add, Modify, or Delete features).
4. Watch the Dashboard update in real-time.
5. Use the "Copy" buttons at the bottom to export your results.

## ⚖️ License

This project is licensed under the MIT License - feel free to use it for personal or commercial projects.

---
*Created by [Your Name/GitHub Username]*
"""

# Write to files
with open("qgis_audit_dashboard.py", "w", encoding="utf-8") as f:
    f.write(plugin_code)

with open("README.md", "w", encoding="utf-8") as f:
    f.write(readme_content)
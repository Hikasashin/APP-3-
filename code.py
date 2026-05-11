"""
=============================================================================
  Interface Graphique PyQt6 — Calculateur d'itinéraires avec carte interactive
  ESME Sudria — Module Algorithmique Avancée 3 (AAP3)
=============================================================================
  Prérequis :  pip install PyQt6 PyQt6-WebEngine
  Lancement :  python interface_pyqt6.py
  JSON files : placez les fichiers *.json dans le même dossier que ce script
=============================================================================
"""

import sys
import os
import json
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QTextEdit, QFrame,
    QGroupBox, QCompleter, QLineEdit, QListWidget, QListWidgetItem,
    QTabWidget, QScrollArea, QMessageBox, QSplitter
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QStringListModel, QUrl
from PyQt6.QtGui import QFont, QColor, QPalette, QTextCursor
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtCore import QObject, pyqtSlot

from calculateur_itineraires import (
    ReseauTransport, dijkstra, bfs, dfs,
    afficher_itineraire, formater_temps,
    verifier_connexite, identifier_correspondances,
    decouvrir_fichiers_json
)

# =============================================================================
#  PALETTE DE COULEURS & STYLE
# =============================================================================

STYLE_GLOBAL = """
QMainWindow { background-color: #1a1a2e; }
QWidget#central { background-color: #1a1a2e; }

QFrame#sidebar {
    background-color: #16213e;
    border-right: 2px solid #0f3460;
    min-width: 300px;
    max-width: 360px;
}

QLabel#titre_app { color: #e94560; font-size: 18px; font-weight: bold; padding: 8px 0px; }
QLabel#sous_titre { color: #a8b2d8; font-size: 11px; padding-bottom: 8px; }

QGroupBox {
    color: #ccd6f6; font-size: 12px; font-weight: bold;
    border: 1px solid #0f3460; border-radius: 8px;
    margin-top: 12px; padding-top: 10px;
    background-color: #0d1b2a;
}
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; color: #64ffda; }

QLabel { color: #ccd6f6; font-size: 12px; }

QComboBox {
    background-color: #0f3460; color: #ccd6f6;
    border: 1px solid #1a4a7a; border-radius: 6px;
    padding: 6px 10px; font-size: 12px; min-height: 30px;
}
QComboBox:hover { border: 1px solid #64ffda; }
QComboBox::drop-down { border: none; width: 24px; }
QComboBox QAbstractItemView {
    background-color: #0f3460; color: #ccd6f6;
    selection-background-color: #e94560; border: 1px solid #1a4a7a;
}

QLineEdit {
    background-color: #0f3460; color: #ccd6f6;
    border: 1px solid #1a4a7a; border-radius: 6px;
    padding: 6px 10px; font-size: 12px; min-height: 30px;
}
QLineEdit:focus { border: 1px solid #64ffda; background-color: #1a4a7a; }

QPushButton#btn_calculer {
    background-color: #e94560; color: white; border: none;
    border-radius: 8px; padding: 10px 20px;
    font-size: 14px; font-weight: bold; min-height: 42px;
}
QPushButton#btn_calculer:hover { background-color: #ff6b81; }
QPushButton#btn_calculer:pressed { background-color: #c0392b; }
QPushButton#btn_calculer:disabled { background-color: #4a4a6a; color: #8888aa; }

QPushButton#btn_bfs {
    background-color: #0f3460; color: #64ffda;
    border: 1px solid #64ffda; border-radius: 6px;
    padding: 7px 14px; font-size: 12px; font-weight: bold;
}
QPushButton#btn_bfs:hover { background-color: #1a4a7a; }

QPushButton#btn_dfs {
    background-color: #0f3460; color: #f7c59f;
    border: 1px solid #f7c59f; border-radius: 6px;
    padding: 7px 14px; font-size: 12px; font-weight: bold;
}
QPushButton#btn_dfs:hover { background-color: #1a4a7a; }

QPushButton#btn_connexite {
    background-color: #0f3460; color: #a8d8ea;
    border: 1px solid #a8d8ea; border-radius: 6px;
    padding: 7px 14px; font-size: 12px;
}
QPushButton#btn_connexite:hover { background-color: #1a4a7a; }

QPushButton#btn_reset {
    background-color: #2d2d4a; color: #ff6b6b;
    border: 1px solid #ff6b6b; border-radius: 6px;
    padding: 6px 12px; font-size: 11px;
}
QPushButton#btn_reset:hover { background-color: #3d2d4a; }

QPushButton#btn_carte {
    background-color: #0f3460; color: #64ffda;
    border: 1px solid #64ffda; border-radius: 6px;
    padding: 6px 12px; font-size: 11px;
}
QPushButton#btn_carte:hover { background-color: #1a4a7a; }

QTextEdit#zone_resultats {
    background-color: #0d1b2a; color: #ccd6f6; border: none;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 13px; padding: 12px;
}

QTabWidget::pane { border: 1px solid #0f3460; background-color: #0d1b2a; border-radius: 6px; }
QTabBar::tab {
    background-color: #16213e; color: #8892b0;
    padding: 8px 18px; border: 1px solid #0f3460;
    border-bottom: none; border-radius: 4px 4px 0 0; font-size: 12px;
}
QTabBar::tab:selected { background-color: #0d1b2a; color: #64ffda; font-weight: bold; }
QTabBar::tab:hover { color: #ccd6f6; }

QListWidget {
    background-color: #0d1b2a; color: #ccd6f6;
    border: 1px solid #0f3460; border-radius: 6px;
    font-size: 12px; outline: none;
}
QListWidget::item { padding: 4px 8px; border-bottom: 1px solid #16213e; }
QListWidget::item:selected { background-color: #0f3460; color: #64ffda; }

QScrollBar:vertical { background: #16213e; width: 8px; border-radius: 4px; }
QScrollBar::handle:vertical { background: #0f3460; border-radius: 4px; min-height: 20px; }
QScrollBar::handle:vertical:hover { background: #64ffda; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

QFrame#separateur { background-color: #0f3460; max-height: 1px; }

QLabel#station_badge {
    background-color: #0f3460; color: #64ffda;
    border: 1px solid #64ffda; border-radius: 6px;
    padding: 4px 10px; font-size: 12px; font-weight: bold;
}
"""

COULEURS_LIGNES = {
    "1": "#FFCD00", "2": "#003CA6", "3": "#6E6E00", "4": "#CF009E",
    "5": "#FF7E2E", "6": "#6ECA97", "7": "#F2A4B7", "8": "#CEADD2",
    "9": "#B6BD00", "10": "#C9910D", "11": "#8D5E2A", "12": "#007852",
    "13": "#6EC4E8", "14": "#62259D",
    "A": "#0072BC", "B": "#EF2E24", "C": "#00A650", "D": "#F5A623",
    "T1": "#00AEEF", "T2": "#E04403", "T3": "#8DC63F",
    "H": "#7B4F9E", "E": "#F47920",
}

COULEURS_FALLBACK = ["#e94560", "#64ffda", "#f7c59f", "#a8d8ea",
                     "#ff9ff3", "#ffeaa7", "#74b9ff", "#a29bfe"]


def couleur_ligne(ligne_id: str, lignes_data: dict) -> str:
    if ligne_id in COULEURS_LIGNES:
        return COULEURS_LIGNES[ligne_id]
    mapping = {
        "rouge": "#e94560", "bleu": "#003CA6", "vert": "#00A650",
        "orange": "#FF7E2E", "jaune": "#FFCD00", "violet": "#62259D",
        "rose": "#CF009E", "noir": "#333333", "marron": "#8D5E2A",
    }
    couleur_json = lignes_data.get(ligne_id, {}).get("couleur", "").lower()
    if couleur_json in mapping:
        return mapping[couleur_json]
    return COULEURS_FALLBACK[abs(hash(ligne_id)) % len(COULEURS_FALLBACK)]


# =============================================================================
#  BRIDGE Qt <-> JavaScript (WebChannel)
# =============================================================================

class MapBridge(QObject):
    """Pont de communication entre la carte Leaflet (JS) et PyQt6."""
    station_cliquee = pyqtSignal(str)

    @pyqtSlot(str)
    def on_station_click(self, nom_station: str):
        self.station_cliquee.emit(nom_station)


# =============================================================================
#  GÉNÉRATEUR DE CARTE LEAFLET (HTML embarqué)
# =============================================================================

def generer_html_carte(reseau: ReseauTransport,
                       depart: str = "",
                       arrivee: str = "",
                       chemin: list = None) -> str:
    """
    Génère un fichier HTML autonome avec une carte Leaflet interactive.
    Les stations sont affichées comme marqueurs cliquables.
    Le chemin Dijkstra (si fourni) est tracé en surbrillance.
    """
    # Coordonnées des stations depuis le JSON (si disponibles)
    stations_coords: dict = {}
    if hasattr(reseau, '_raw_data') and 'stations_coords' in reseau._raw_data:
        stations_coords = reseau._raw_data['stations_coords']

    # Centre de la carte
    if stations_coords:
        lats = [c[0] for c in stations_coords.values()]
        lons = [c[1] for c in stations_coords.values()]
        center_lat = sum(lats) / len(lats)
        center_lon = sum(lons) / len(lons)
    else:
        center_lat, center_lon = 44.836, -0.580  # Bordeaux par défaut

    # Construction JSON des stations pour JS
    stations_js = []
    for station in reseau.stations_physiques:
        lignes_s = reseau.trouver_ligne_station(station)
        if station in stations_coords:
            lat, lon = stations_coords[station]
        else:
            # Position aléatoire autour du centre si pas de coords
            import hashlib
            h = int(hashlib.md5(station.encode()).hexdigest(), 16)
            lat = center_lat + ((h % 200) - 100) * 0.001
            lon = center_lon + ((h % 300 - 150)) * 0.001

        couleurs_s = [couleur_ligne(l, reseau.lignes) for l in lignes_s]
        is_depart = station == depart
        is_arrivee = station == arrivee
        is_ferme = station in reseau.stations_fermees

        stations_js.append({
            "name": station,
            "lat": lat,
            "lon": lon,
            "lignes": lignes_s,
            "couleurs": couleurs_s,
            "is_depart": is_depart,
            "is_arrivee": is_arrivee,
            "is_ferme": is_ferme,
        })

    # Construction des arêtes du réseau pour les lignes
    aretes_js = []
    aretes_vues = set()
    for (s1, l1), voisins in reseau.adjacence.items():
        if s1 not in stations_coords:
            continue
        for (s2, l2, t) in voisins:
            if s2 not in stations_coords or l1 != l2:
                continue
            key = tuple(sorted([s1, s2]) + [l1])
            if key in aretes_vues:
                continue
            aretes_vues.add(key)
            aretes_js.append({
                "s1": s1, "s2": s2, "ligne": l1,
                "couleur": couleur_ligne(l1, reseau.lignes),
                "ferme": l1 in reseau.lignes_fermees,
            })

    # Chemin Dijkstra à surbrilligner
    chemin_coords = []
    if chemin:
        for (station, ligne) in chemin:
            if station in stations_coords:
                lat, lon = stations_coords[station]
                chemin_coords.append({
                    "lat": lat, "lon": lon,
                    "name": station, "ligne": ligne,
                    "couleur": couleur_ligne(ligne, reseau.lignes)
                })

    stations_json = json.dumps(stations_js, ensure_ascii=False)
    aretes_json = json.dumps(aretes_js, ensure_ascii=False)
    chemin_json = json.dumps(chemin_coords, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  html, body, #map {{ width: 100%; height: 100%; background: #0d1b2a; }}

  .leaflet-container {{ background: #1a1a2e !important; }}

  .station-marker {{
    cursor: pointer !important;
    transition: transform 0.15s ease;
  }}
  .station-marker:hover {{
    transform: scale(1.3);
  }}

  /* Popup custom */
  .leaflet-popup-content-wrapper {{
    background: #16213e;
    border: 1px solid #64ffda;
    border-radius: 8px;
    color: #ccd6f6;
    font-family: 'Consolas', monospace;
    font-size: 13px;
  }}
  .leaflet-popup-tip {{ background: #16213e; }}
  .popup-title {{ color: #64ffda; font-weight: bold; font-size: 14px; margin-bottom: 6px; }}
  .popup-ligne {{
    display: inline-block; border-radius: 10px;
    padding: 2px 8px; font-size: 11px; font-weight: bold;
    color: white; margin: 2px;
  }}
  .popup-btn {{
    display: block; width: 100%; margin-top: 8px; padding: 6px;
    border: none; border-radius: 5px; cursor: pointer;
    font-size: 12px; font-weight: bold;
  }}
  .btn-dep {{ background: #64ffda; color: #0d1b2a; }}
  .btn-arr {{ background: #e94560; color: white; }}
  .btn-dep:hover {{ background: #4edfbf; }}
  .btn-arr:hover {{ background: #c0392b; }}

  /* Légende */
  #legende {{
    position: absolute; bottom: 20px; right: 10px; z-index: 1000;
    background: rgba(22, 33, 62, 0.92);
    border: 1px solid #0f3460; border-radius: 8px;
    padding: 10px 14px; color: #ccd6f6;
    font-family: 'Consolas', monospace; font-size: 11px;
    min-width: 150px;
  }}
  #legende h4 {{ color: #64ffda; margin-bottom: 6px; font-size: 12px; }}
  .leg-item {{ display: flex; align-items: center; gap: 8px; margin: 3px 0; }}
  .leg-dot {{ width: 12px; height: 12px; border-radius: 50%; flex-shrink: 0; }}
  .leg-line {{ width: 20px; height: 3px; border-radius: 2px; flex-shrink: 0; }}

  /* Toast notification */
  #toast {{
    position: absolute; top: 12px; left: 50%; transform: translateX(-50%);
    z-index: 2000; background: #0f3460;
    border: 1px solid #64ffda; border-radius: 8px;
    color: #64ffda; font-family: 'Consolas', monospace; font-size: 12px;
    padding: 8px 18px; display: none;
    animation: fadeout 2s forwards;
  }}
  @keyframes fadeout {{ 0%{{opacity:1}} 70%{{opacity:1}} 100%{{opacity:0}} }}
</style>
<link rel="stylesheet"
  href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="qrc:///qtwebchannel/qwebchannel.js"></script>
</head>
<body>
<div id="map"></div>
<div id="legende">
  <h4>Lignes</h4>
  <div id="legende-content"></div>
  <div style="margin-top:8px; border-top:1px solid #0f3460; padding-top:6px;">
    <div class="leg-item"><div class="leg-dot" style="background:#64ffda; border:2px solid white;"></div> Départ</div>
    <div class="leg-item"><div class="leg-dot" style="background:#e94560; border:2px solid white;"></div> Arrivée</div>
    <div class="leg-item"><div class="leg-dot" style="background:#ff6b6b; border:2px dashed #ff6b6b; background:transparent;"></div> Fermée</div>
  </div>
</div>
<div id="toast"></div>

<script>
// ---- Données depuis Python ----
const STATIONS = {stations_json};
const ARETES   = {aretes_json};
const CHEMIN   = {chemin_json};

// ---- Initialisation WebChannel ----
let bridge = null;
new QWebChannel(qt.webChannelTransport, function(channel) {{
  bridge = channel.objects.bridge;
}});

function sendStation(name) {{
  if (bridge) bridge.on_station_click(name);
}}

// ---- Carte ----
const map = L.map('map', {{
  center: [{center_lat}, {center_lon}],
  zoom: 13,
  zoomControl: true,
  attributionControl: false,
}});

// Tuiles CartoDB Dark Matter (thème sombre)
L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
  attribution: '© OpenStreetMap © CARTO',
  subdomains: 'abcd',
  maxZoom: 19,
}}).addTo(map);

// ---- Dessin des arêtes (lignes de réseau) ----
ARETES.forEach(a => {{
  const s1 = STATIONS.find(s => s.name === a.s1);
  const s2 = STATIONS.find(s => s.name === a.s2);
  if (!s1 || !s2) return;
  const style = a.ferme
    ? {{ color: '#555', weight: 2, opacity: 0.4, dashArray: '5,5' }}
    : {{ color: a.couleur, weight: 4, opacity: 0.7 }};
  L.polyline([[s1.lat, s1.lon],[s2.lat, s2.lon]], style).addTo(map);
}});

// ---- Chemin Dijkstra en surbrillance ----
if (CHEMIN.length > 1) {{
  const coords = CHEMIN.map(p => [p.lat, p.lon]);
  L.polyline(coords, {{
    color: '#ffffff',
    weight: 7,
    opacity: 0.25,
    lineCap: 'round',
  }}).addTo(map);

  let prevLigne = null;
  for (let i = 0; i < CHEMIN.length - 1; i++) {{
    const p1 = CHEMIN[i], p2 = CHEMIN[i+1];
    L.polyline([[p1.lat, p1.lon],[p2.lat, p2.lon]], {{
      color: p1.couleur,
      weight: 6,
      opacity: 1,
      lineCap: 'round',
    }}).addTo(map);
  }}
}}

// ---- Marqueurs des stations ----
const lignesVues = {{}};

STATIONS.forEach(s => {{
  const mainCouleur = s.couleurs.length > 0 ? s.couleurs[0] : '#ccd6f6';
  const isOnChemin = CHEMIN.some(c => c.name === s.name);

  // Couleur du marqueur
  let fillColor = mainCouleur;
  let borderColor = '#ffffff';
  let radius = 7;

  if (s.is_depart) {{ fillColor = '#64ffda'; borderColor = '#fff'; radius = 11; }}
  else if (s.is_arrivee) {{ fillColor = '#e94560'; borderColor = '#fff'; radius = 11; }}
  else if (s.is_ferme) {{ fillColor = '#333'; borderColor = '#ff6b6b'; radius = 6; }}
  else if (isOnChemin) {{ radius = 9; borderColor = '#fff'; }}

  const marker = L.circleMarker([s.lat, s.lon], {{
    radius: radius,
    fillColor: fillColor,
    color: borderColor,
    weight: s.is_depart || s.is_arrivee ? 2.5 : 1.5,
    opacity: 1,
    fillOpacity: s.is_ferme ? 0.4 : 0.95,
    className: 'station-marker',
  }}).addTo(map);

  // Étiquette au survol
  marker.bindTooltip(s.name, {{
    direction: 'top',
    offset: [0, -8],
    className: 'station-tooltip',
    permanent: false,
  }});

  // Popup au clic
  const lignesBadges = s.lignes.map((l, i) =>
    `<span class="popup-ligne" style="background:${{s.couleurs[i] || '#555'}}">${{l}}</span>`
  ).join(' ');

  const fermeTag = s.is_ferme ? `<div style="color:#ff6b6b;font-size:11px;margin-top:4px;">⛔ Station fermée</div>` : '';
  const cheminTag = isOnChemin ? `<div style="color:#64ffda;font-size:11px;margin-top:4px;">✅ Sur l'itinéraire</div>` : '';

  const popupHtml = `
    <div class="popup-title">🚉 ${{s.name}}</div>
    <div>${{lignesBadges}}</div>
    ${{fermeTag}}${{cheminTag}}
    <button class="popup-btn btn-dep" onclick="setDepart('${{s.name.replace("'", "\\'")}}')">
      📍 Définir comme départ
    </button>
    <button class="popup-btn btn-arr" onclick="setArrivee('${{s.name.replace("'", "\\'")}}')">
      🏁 Définir comme arrivée
    </button>
  `;
  marker.bindPopup(popupHtml, {{ maxWidth: 220 }});

  // Collecter les lignes pour la légende
  s.lignes.forEach((l, i) => {{
    if (!lignesVues[l]) lignesVues[l] = s.couleurs[i] || '#ccc';
  }});
}});

// ---- Légende dynamique ----
const legendContent = document.getElementById('legende-content');
Object.entries(lignesVues).sort().forEach(([ligne, couleur]) => {{
  legendContent.innerHTML += `
    <div class="leg-item">
      <div class="leg-line" style="background:${{couleur}}"></div>
      <span>Ligne ${{ligne}}</span>
    </div>`;
}});

// ---- Fonctions appelées depuis les popups ----
function setDepart(name) {{
  showToast('📍 Départ : ' + name);
  sendStation('DEPART:' + name);
  map.closePopup();
}}

function setArrivee(name) {{
  showToast('🏁 Arrivée : ' + name);
  sendStation('ARRIVEE:' + name);
  map.closePopup();
}}

function showToast(msg) {{
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.style.display = 'block';
  t.style.animation = 'none';
  setTimeout(() => {{
    t.style.animation = 'fadeout 2s forwards';
    setTimeout(() => {{ t.style.display = 'none'; }}, 2000);
  }}, 50);
}}

// Zoom sur le chemin s'il existe
if (CHEMIN.length > 1) {{
  const bounds = CHEMIN.map(p => [p.lat, p.lon]);
  map.fitBounds(bounds, {{ padding: [40, 40] }});
}}
</script>
</body>
</html>"""
    return html


# =============================================================================
#  THREAD DE CALCUL
# =============================================================================

class ThreadCalcul(QThread):
    resultat_pret = pyqtSignal(object, int, str)
    erreur = pyqtSignal(str)

    def __init__(self, reseau, depart, arrivee, mode="dijkstra"):
        super().__init__()
        self.reseau = reseau
        self.depart = depart
        self.arrivee = arrivee
        self.mode = mode

    def run(self):
        try:
            if self.mode == "dijkstra":
                chemin, temps = dijkstra(self.reseau, self.depart, self.arrivee)
                self.resultat_pret.emit(chemin, temps, "dijkstra")
            elif self.mode == "bfs":
                chemin = bfs(self.reseau, self.depart, self.arrivee)
                self.resultat_pret.emit(chemin, 0, "bfs")
            elif self.mode == "dfs":
                chemin = dfs(self.reseau, self.depart, self.arrivee)
                self.resultat_pret.emit(chemin, 0, "dfs")
        except Exception as e:
            self.erreur.emit(str(e))


# =============================================================================
#  WIDGET RECHERCHE STATION
# =============================================================================

class StationSearch(QWidget):
    station_selectionnee = pyqtSignal(str)

    def __init__(self, placeholder: str, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.input = QLineEdit()
        self.input.setPlaceholderText(placeholder)
        self.completer = QCompleter()
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.completer.setMaxVisibleItems(10)
        self.input.setCompleter(self.completer)
        self.completer.popup().setStyleSheet("""
            QAbstractItemView {
                background-color: #0f3460; color: #ccd6f6;
                border: 1px solid #64ffda;
                selection-background-color: #e94560;
                font-size: 12px; padding: 2px;
            }
        """)
        layout.addWidget(self.input)
        self.input.textChanged.connect(self._on_text_changed)
        self.completer.activated.connect(self.station_selectionnee.emit)

    def mettre_a_jour_stations(self, stations: list):
        self.completer.setModel(QStringListModel(sorted(stations)))

    def _on_text_changed(self, texte: str):
        model = self.completer.model()
        if model:
            for i in range(model.rowCount()):
                if model.data(model.index(i, 0)).lower() == texte.lower():
                    self.station_selectionnee.emit(model.data(model.index(i, 0)))
                    break

    def valeur(self) -> str:
        return self.input.text().strip()

    def effacer(self):
        self.input.clear()


# =============================================================================
#  FENÊTRE PRINCIPALE
# =============================================================================

class FenetreCalculateur(QMainWindow):
    def __init__(self):
        super().__init__()
        self.reseau: ReseauTransport | None = None
        self.villes_disponibles: dict = {}
        self.thread_calcul: ThreadCalcul | None = None
        self._chemin_actuel: list = []
        self._temps_actuel: int = 0

        # WebChannel bridge
        self.bridge = MapBridge()
        self.bridge.station_cliquee.connect(self._on_station_carte_cliquee)

        self.setWindowTitle("Calculateur d'itinéraires — ESME AAP3")
        self.showFullScreen()
        self._appliquer_style()
        self._construire_ui()
        self._decouvrir_villes()

    def _appliquer_style(self):
        self.setStyleSheet(STYLE_GLOBAL)
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#1a1a2e"))
        self.setPalette(palette)

    def _construire_ui(self):
        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)

        layout_principal = QHBoxLayout(central)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        self.sidebar = self._creer_sidebar()
        layout_principal.addWidget(self.sidebar)

        zone_droite = self._creer_zone_droite()
        layout_principal.addWidget(zone_droite, stretch=1)

    # -------------------------------------------------------------------------
    def _creer_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 20, 16, 16)
        layout.setSpacing(10)

        titre = QLabel("🚇 Transit Planner")
        titre.setObjectName("titre_app")
        layout.addWidget(titre)

        sous_titre = QLabel("ESME Sudria — AAP3 2026")
        sous_titre.setObjectName("sous_titre")
        layout.addWidget(sous_titre)

        sep = QFrame()
        sep.setObjectName("separateur")
        sep.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep)

        # Sélection ville
        grp_ville = QGroupBox("Réseau")
        layout_ville = QVBoxLayout(grp_ville)
        layout_ville.setSpacing(6)
        layout_ville.addWidget(QLabel("Ville :"))
        self.combo_ville = QComboBox()
        self.combo_ville.addItem("— Choisir une ville —")
        self.combo_ville.currentIndexChanged.connect(self._on_ville_change)
        self.lbl_stats = QLabel("")
        self.lbl_stats.setStyleSheet("color: #64ffda; font-size: 11px;")
        self.lbl_stats.setWordWrap(True)
        layout_ville.addWidget(self.combo_ville)
        layout_ville.addWidget(self.lbl_stats)
        layout.addWidget(grp_ville)

        # Itinéraire
        grp_stations = QGroupBox("Itinéraire")
        layout_stations = QVBoxLayout(grp_stations)
        layout_stations.setSpacing(8)

        # Départ
        layout_stations.addWidget(QLabel("Station de départ :"))
        self.search_depart = StationSearch("Rechercher ou cliquer sur la carte...")
        layout_stations.addWidget(self.search_depart)
        self.lbl_depart_badge = QLabel("")
        self.lbl_depart_badge.setObjectName("station_badge")
        self.lbl_depart_badge.setWordWrap(True)
        self.lbl_depart_badge.hide()
        layout_stations.addWidget(self.lbl_depart_badge)

        # Arrivée
        layout_stations.addWidget(QLabel("Station d'arrivée :"))
        self.search_arrivee = StationSearch("Rechercher ou cliquer sur la carte...")
        layout_stations.addWidget(self.search_arrivee)
        self.lbl_arrivee_badge = QLabel("")
        self.lbl_arrivee_badge.setObjectName("station_badge")
        self.lbl_arrivee_badge.setWordWrap(True)
        self.lbl_arrivee_badge.hide()
        layout_stations.addWidget(self.lbl_arrivee_badge)

        # Astuce carte
        hint = QLabel("💡 Cliquez sur la carte pour sélectionner départ/arrivée")
        hint.setStyleSheet("color: #64ffda; font-size: 10px; font-style: italic;")
        hint.setWordWrap(True)
        layout_stations.addWidget(hint)

        # Swap
        btn_swap = QPushButton("⇅  Inverser")
        btn_swap.setStyleSheet("""
            QPushButton {
                background-color: #0f3460; color: #a8b2d8;
                border: 1px solid #1a4a7a; border-radius: 5px;
                padding: 5px; font-size: 11px;
            }
            QPushButton:hover { background-color: #1a4a7a; color: #ccd6f6; }
        """)
        btn_swap.clicked.connect(self._swap_stations)
        layout_stations.addWidget(btn_swap)
        layout.addWidget(grp_stations)

        # Bouton Calculer
        self.btn_calculer = QPushButton("🔍  Calculer l'itinéraire")
        self.btn_calculer.setObjectName("btn_calculer")
        self.btn_calculer.setEnabled(False)
        self.btn_calculer.clicked.connect(self._calculer_dijkstra)
        layout.addWidget(self.btn_calculer)

        # Parcours BFS/DFS
        grp_parcours = QGroupBox("Parcours de graphe")
        layout_parcours = QVBoxLayout(grp_parcours)
        layout_parcours.setSpacing(6)

        self.btn_bfs = QPushButton("🔎  BFS — Moins d'arrêts")
        self.btn_bfs.setObjectName("btn_bfs")
        self.btn_bfs.setEnabled(False)
        self.btn_bfs.clicked.connect(lambda: self._lancer_parcours("bfs"))

        self.btn_dfs = QPushButton("🔎  DFS — Exploration profondeur")
        self.btn_dfs.setObjectName("btn_dfs")
        self.btn_dfs.setEnabled(False)
        self.btn_dfs.clicked.connect(lambda: self._lancer_parcours("dfs"))

        self.btn_connexite = QPushButton("🔗  Vérifier connexité")
        self.btn_connexite.setObjectName("btn_connexite")
        self.btn_connexite.setEnabled(False)
        self.btn_connexite.clicked.connect(self._verifier_connexite)

        layout_parcours.addWidget(self.btn_bfs)
        layout_parcours.addWidget(self.btn_dfs)
        layout_parcours.addWidget(self.btn_connexite)
        layout.addWidget(grp_parcours)

        # Perturbations
        grp_perturb = QGroupBox("⚠️  Perturbations")
        layout_perturb = QVBoxLayout(grp_perturb)
        layout_perturb.setSpacing(6)

        layout_perturb.addWidget(QLabel("Station à fermer :"))
        self.search_fermer = StationSearch("Station fermée...")
        layout_perturb.addWidget(self.search_fermer)

        btn_fermer = QPushButton("Fermer cette station")
        btn_fermer.setStyleSheet("""
            QPushButton { background-color: #3d1515; color: #ff6b6b;
                border: 1px solid #ff6b6b; border-radius: 5px; padding: 6px; font-size: 11px; }
            QPushButton:hover { background-color: #5d2020; }
        """)
        btn_fermer.clicked.connect(self._fermer_station)
        layout_perturb.addWidget(btn_fermer)

        layout_perturb.addWidget(QLabel("Ligne à fermer :"))
        self.combo_ligne_fermer = QComboBox()
        layout_perturb.addWidget(self.combo_ligne_fermer)

        btn_fermer_ligne = QPushButton("Fermer cette ligne")
        btn_fermer_ligne.setStyleSheet("""
            QPushButton { background-color: #3d1515; color: #ff6b6b;
                border: 1px solid #ff6b6b; border-radius: 5px; padding: 6px; font-size: 11px; }
            QPushButton:hover { background-color: #5d2020; }
        """)
        btn_fermer_ligne.clicked.connect(self._fermer_ligne)
        layout_perturb.addWidget(btn_fermer_ligne)

        self.btn_reset = QPushButton("↺  Réinitialiser les perturbations")
        self.btn_reset.setObjectName("btn_reset")
        self.btn_reset.clicked.connect(self._reset_perturbations)
        layout_perturb.addWidget(self.btn_reset)
        layout.addWidget(grp_perturb)

        layout.addStretch()
        return sidebar

    # -------------------------------------------------------------------------
    def _creer_zone_droite(self) -> QWidget:
        widget = QWidget()
        widget.setStyleSheet("background-color: #1a1a2e;")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Barre de statut
        self.barre_statut = QLabel("  Choisissez une ville pour commencer.")
        self.barre_statut.setStyleSheet("""
            background-color: #0f3460; color: #64ffda;
            padding: 8px 16px; font-size: 12px;
            border-bottom: 1px solid #1a4a7a;
        """)
        layout.addWidget(self.barre_statut)

        # Splitter vertical : carte en haut, résultats en bas
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setStyleSheet("QSplitter::handle { background: #0f3460; height: 4px; }")
        layout.addWidget(splitter, stretch=1)

        # --- Carte Leaflet ---
        carte_widget = QWidget()
        carte_widget.setStyleSheet("background-color: #0d1b2a;")
        carte_layout = QVBoxLayout(carte_widget)
        carte_layout.setContentsMargins(0, 0, 0, 0)

        self.web_view = QWebEngineView()
        self.web_view.setMinimumHeight(350)

        # Configurer WebChannel
        self.channel = QWebChannel()
        self.channel.registerObject("bridge", self.bridge)
        self.web_view.page().setWebChannel(self.channel)

        carte_layout.addWidget(self.web_view)
        splitter.addWidget(carte_widget)

        # --- Tabs résultats / lignes / correspondances ---
        self.tabs = QTabWidget()
        self.tabs.setMinimumHeight(200)
        splitter.addWidget(self.tabs)
        splitter.setSizes([550, 300])

        # Tab résultats
        tab_resultats = QWidget()
        tab_resultats.setStyleSheet("background-color: #0d1b2a;")
        layout_res = QVBoxLayout(tab_resultats)
        layout_res.setContentsMargins(0, 0, 0, 0)
        self.zone_resultats = QTextEdit()
        self.zone_resultats.setObjectName("zone_resultats")
        self.zone_resultats.setReadOnly(True)
        layout_res.addWidget(self.zone_resultats)
        self.tabs.addTab(tab_resultats, "📋  Résultats")

        # Tab lignes
        tab_lignes = QWidget()
        tab_lignes.setStyleSheet("background-color: #0d1b2a;")
        layout_lignes = QVBoxLayout(tab_lignes)
        layout_lignes.setContentsMargins(12, 12, 12, 12)
        layout_lignes.setSpacing(8)
        lbl_l = QLabel("Lignes du réseau :")
        lbl_l.setStyleSheet("color: #64ffda; font-size: 13px; font-weight: bold;")
        layout_lignes.addWidget(lbl_l)
        scroll = QScrollArea()
        scroll.setStyleSheet("background-color: #0d1b2a; border: none;")
        scroll.setWidgetResizable(True)
        self.widget_lignes = QWidget()
        self.widget_lignes.setStyleSheet("background-color: #0d1b2a;")
        self.layout_lignes_inner = QVBoxLayout(self.widget_lignes)
        self.layout_lignes_inner.setSpacing(6)
        self.layout_lignes_inner.addStretch()
        scroll.setWidget(self.widget_lignes)
        layout_lignes.addWidget(scroll)
        self.tabs.addTab(tab_lignes, "🗺️  Lignes")

        # Tab correspondances
        tab_corres = QWidget()
        tab_corres.setStyleSheet("background-color: #0d1b2a;")
        layout_corres = QVBoxLayout(tab_corres)
        layout_corres.setContentsMargins(12, 12, 12, 12)
        lbl_c = QLabel("Stations de correspondance :")
        lbl_c.setStyleSheet("color: #64ffda; font-size: 13px; font-weight: bold;")
        layout_corres.addWidget(lbl_c)
        self.liste_corres = QListWidget()
        layout_corres.addWidget(self.liste_corres)
        self.tabs.addTab(tab_corres, "🔄  Correspondances")

        self._afficher_bienvenue()
        return widget

    # -------------------------------------------------------------------------
    #  CARTE — rafraîchissement
    # -------------------------------------------------------------------------
    def _rafraichir_carte(self, chemin: list = None):
        if not self.reseau:
            return
        depart = self.search_depart.valeur()
        arrivee = self.search_arrivee.valeur()
        html = generer_html_carte(
            self.reseau,
            depart=depart,
            arrivee=arrivee,
            chemin=chemin or []
        )
        self.web_view.setHtml(html, QUrl("about:blank"))

    def _on_station_carte_cliquee(self, payload: str):
        """Reçoit 'DEPART:NomStation' ou 'ARRIVEE:NomStation' depuis la carte JS."""
        if ":" not in payload:
            return
        role, nom_station = payload.split(":", 1)

        if role == "DEPART":
            self.search_depart.input.setText(nom_station)
            self.lbl_depart_badge.setText(f"📍 {nom_station}")
            self.lbl_depart_badge.show()
            self.barre_statut.setText(f"  📍 Départ sélectionné : {nom_station}")
        elif role == "ARRIVEE":
            self.search_arrivee.input.setText(nom_station)
            self.lbl_arrivee_badge.setText(f"🏁 {nom_station}")
            self.lbl_arrivee_badge.show()
            self.barre_statut.setText(f"  🏁 Arrivée sélectionnée : {nom_station}")

        # Rafraîchir la carte pour mettre en évidence la sélection
        self._rafraichir_carte()

    # -------------------------------------------------------------------------
    #  CHARGEMENT VILLE
    # -------------------------------------------------------------------------
    def _decouvrir_villes(self):
        dossiers = [".", os.path.dirname(os.path.abspath(__file__))]
        for d in dossiers:
            self.villes_disponibles.update(decouvrir_fichiers_json(d))
        if not self.villes_disponibles:
            self.barre_statut.setText("  ❌ Aucun fichier JSON trouvé.")
            return
        for nom in sorted(self.villes_disponibles.keys()):
            self.combo_ville.addItem(nom)

    def _on_ville_change(self, index: int):
        if index == 0:
            return
        nom_ville = self.combo_ville.currentText()
        chemin_fichier = self.villes_disponibles.get(nom_ville)
        if not chemin_fichier:
            return

        self.barre_statut.setText(f"  ⏳ Chargement de {nom_ville}...")
        QApplication.processEvents()

        self.reseau = ReseauTransport()
        try:
            # Charger le JSON brut pour récupérer les coords
            with open(chemin_fichier, encoding="utf-8") as f:
                raw = json.load(f)
            self.reseau._raw_data = raw
            self.reseau.charger_json(chemin_fichier)
        except Exception as e:
            self.barre_statut.setText(f"  ❌ Erreur : {e}")
            self.reseau = None
            return

        nb_stations = len(self.reseau.stations_physiques)
        nb_lignes = len(self.reseau.lignes)
        self.lbl_stats.setText(f"{nb_stations} stations · {nb_lignes} lignes")
        self.barre_statut.setText(
            f"  ✅ {nom_ville} chargé — {nb_stations} stations, {nb_lignes} lignes"
            " · Cliquez sur la carte pour sélectionner les stations"
        )

        stations = list(self.reseau.stations_physiques)
        self.search_depart.mettre_a_jour_stations(stations)
        self.search_arrivee.mettre_a_jour_stations(stations)
        self.search_fermer.mettre_a_jour_stations(stations)

        self.combo_ligne_fermer.clear()
        for lid in sorted(self.reseau.lignes.keys()):
            nom_l = self.reseau.lignes[lid].get("nom", f"Ligne {lid}")
            self.combo_ligne_fermer.addItem(f"{lid} — {nom_l}", lid)

        for btn in [self.btn_calculer, self.btn_bfs, self.btn_dfs, self.btn_connexite]:
            btn.setEnabled(True)

        self.lbl_depart_badge.hide()
        self.lbl_arrivee_badge.hide()
        self._chemin_actuel = []

        self._afficher_tab_lignes()
        self._afficher_tab_correspondances()
        self._afficher_bienvenue()
        self._rafraichir_carte()

    # -------------------------------------------------------------------------
    #  TABS LIGNES & CORRESPONDANCES
    # -------------------------------------------------------------------------
    def _afficher_bienvenue(self):
        ville = self.reseau.nom_ville if self.reseau else "votre ville"
        html = f"""
        <div style='font-family: Consolas, monospace; color: #ccd6f6; padding: 20px;'>
            <div style='color: #64ffda; font-size: 18px; font-weight: bold; margin-bottom: 8px;'>
                🚇 Bienvenue dans le calculateur d'itinéraires
            </div>
            <div style='color: #8892b0; font-size: 13px; margin-bottom: 20px;'>
                ESME Sudria — Module Algorithmique Avancée 3
            </div>
            {'<div style="color:#a8d8ea; font-size:13px;">Réseau chargé : <b style="color:#64ffda;">' + ville + '</b></div>' if self.reseau else ''}
            <br>
            <div style='color: #a8b2d8; font-size: 12px; line-height: 1.8;'>
                <b style='color:#ccd6f6;'>Comment utiliser :</b><br>
                1. Choisissez une ville dans le menu de gauche<br>
                2. <b style='color:#64ffda;'>Cliquez sur un station sur la carte</b> → choisir départ/arrivée<br>
                &nbsp;&nbsp;&nbsp;ou saisissez les noms dans les champs<br>
                3. Cliquez sur <b style='color:#e94560;'>Calculer l'itinéraire</b><br>
                4. Le trajet optimal s'affiche sur la carte et dans les résultats<br>
                <br>
                <b style='color:#ccd6f6;'>Algorithmes :</b><br>
                • <b style='color:#e94560;'>Dijkstra</b> — meilleur temps · tracé sur la carte<br>
                • <b style='color:#64ffda;'>BFS</b> — moins d'arrêts<br>
                • <b style='color:#f7c59f;'>DFS</b> — exploration profondeur<br>
            </div>
        </div>
        """
        self.zone_resultats.setHtml(html)

    def _afficher_tab_lignes(self):
        while self.layout_lignes_inner.count() > 1:
            item = self.layout_lignes_inner.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.reseau:
            return

        for lid, info in sorted(self.reseau.lignes.items()):
            nom = info.get("nom", f"Ligne {lid}")
            nb_s = len(info.get("stations", []))
            couleur = couleur_ligne(lid, self.reseau.lignes)

            frame = QFrame()
            frame.setStyleSheet(f"""
                QFrame {{ background-color: #16213e; border-left: 4px solid {couleur};
                         border-radius: 4px; padding: 4px; }}
            """)
            fl = QHBoxLayout(frame)
            fl.setContentsMargins(10, 6, 10, 6)

            badge = QLabel(lid)
            badge.setStyleSheet(f"""
                background-color: {couleur};
                color: {'black' if couleur in ('#FFCD00','#B6BD00','#6ECA97') else 'white'};
                border-radius: 10px; padding: 2px 8px;
                font-size: 11px; font-weight: bold;
                min-width: 28px; max-width: 60px;
            """)
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)

            lbl_nom = QLabel(nom)
            lbl_nom.setStyleSheet("color: #ccd6f6; font-size: 12px; font-weight: bold;")
            lbl_nb = QLabel(f"{nb_s} arrêts" if nb_s else "")
            lbl_nb.setStyleSheet("color: #8892b0; font-size: 11px;")
            lbl_nb.setAlignment(Qt.AlignmentFlag.AlignRight)

            fl.addWidget(badge)
            fl.addWidget(lbl_nom, stretch=1)
            fl.addWidget(lbl_nb)
            self.layout_lignes_inner.insertWidget(
                self.layout_lignes_inner.count() - 1, frame
            )

    def _afficher_tab_correspondances(self):
        self.liste_corres.clear()
        if not self.reseau:
            return
        corres = identifier_correspondances(self.reseau)
        for station, lignes in sorted(corres.items()):
            item = QListWidgetItem(f"  {station}  —  [{' / '.join(lignes)}]")
            item.setForeground(QColor("#ccd6f6"))
            self.liste_corres.addItem(item)

    # -------------------------------------------------------------------------
    #  CALCULS
    # -------------------------------------------------------------------------
    def _get_stations_saisies(self):
        depart = self.search_depart.valeur()
        arrivee = self.search_arrivee.valeur()
        if not depart or not arrivee:
            self._afficher_erreur("Veuillez saisir les deux stations.")
            return None

        for role, val, setter in [
            ("départ", depart, self.search_depart.input.setText),
            ("arrivée", arrivee, self.search_arrivee.input.setText),
        ]:
            if not self.reseau.station_existe(val):
                approx = [s for s in self.reseau.stations_physiques if val.lower() in s.lower()]
                if len(approx) == 1:
                    setter(approx[0])
                    if role == "départ":
                        depart = approx[0]
                    else:
                        arrivee = approx[0]
                else:
                    self._afficher_erreur(f"Station de {role} introuvable : '{val}'")
                    return None

        if depart == arrivee:
            self._afficher_erreur("La station de départ et d'arrivée sont identiques.")
            return None
        return depart, arrivee

    def _calculer_dijkstra(self):
        if not self.reseau:
            return
        paire = self._get_stations_saisies()
        if not paire:
            return
        self._lancer_calcul_thread(paire[0], paire[1], "dijkstra")

    def _lancer_parcours(self, mode: str):
        if not self.reseau:
            return
        paire = self._get_stations_saisies()
        if not paire:
            return
        self._lancer_calcul_thread(paire[0], paire[1], mode)

    def _lancer_calcul_thread(self, depart: str, arrivee: str, mode: str):
        self.btn_calculer.setEnabled(False)
        self.btn_bfs.setEnabled(False)
        self.btn_dfs.setEnabled(False)
        self.barre_statut.setText(f"  ⏳ Calcul en cours ({mode.upper()})...")

        self.thread_calcul = ThreadCalcul(self.reseau, depart, arrivee, mode)
        self.thread_calcul.resultat_pret.connect(self._on_resultat)
        self.thread_calcul.erreur.connect(self._on_erreur_calcul)
        self.thread_calcul.start()

    def _on_resultat(self, chemin, temps, mode: str):
        self.btn_calculer.setEnabled(True)
        self.btn_bfs.setEnabled(True)
        self.btn_dfs.setEnabled(True)

        depart = self.search_depart.valeur()
        arrivee = self.search_arrivee.valeur()

        if chemin is None:
            self.barre_statut.setText("  ❌ Aucun itinéraire trouvé.")
            self._afficher_erreur(
                f"Impossible de relier '{depart}' à '{arrivee}'.\n"
                "Vérifiez les perturbations actives ou les noms de stations."
            )
            return

        self.tabs.setCurrentIndex(0)

        if mode == "dijkstra":
            self._chemin_actuel = chemin
            self._temps_actuel = temps
            self.barre_statut.setText(
                f"  ✅ Dijkstra — {depart} → {arrivee} — {formater_temps(temps)}"
            )
            self._afficher_resultat_dijkstra(chemin, temps, depart, arrivee)
            # Mettre à jour la carte avec le tracé
            self._rafraichir_carte(chemin=chemin)

        elif mode == "bfs":
            self.barre_statut.setText(
                f"  ✅ BFS — {depart} → {arrivee} — {len(chemin)-1} arrêts"
            )
            self._afficher_resultat_parcours(chemin, "BFS", "🔎", "#64ffda")
            # BFS retourne des noms seuls, on ne trace pas sur la carte
            self._rafraichir_carte()

        elif mode == "dfs":
            self.barre_statut.setText(
                f"  ✅ DFS — {depart} → {arrivee} — {len(chemin)-1} arrêts"
            )
            self._afficher_resultat_parcours(chemin, "DFS", "🔎", "#f7c59f")
            self._rafraichir_carte()

    def _on_erreur_calcul(self, message: str):
        self.btn_calculer.setEnabled(True)
        self.btn_bfs.setEnabled(True)
        self.btn_dfs.setEnabled(True)
        self.barre_statut.setText(f"  ❌ Erreur : {message}")

    # -------------------------------------------------------------------------
    #  AFFICHAGE RÉSULTATS
    # -------------------------------------------------------------------------
    def _afficher_resultat_dijkstra(self, chemin: list, temps: int,
                                    depart: str, arrivee: str):
        html = f"""
        <div style='font-family: Consolas, monospace; padding: 16px; color: #ccd6f6;'>
            <div style='color: #e94560; font-size: 15px; font-weight: bold; margin-bottom: 4px;'>
                🗺️ Itinéraire Dijkstra (temps optimal)
            </div>
            <div style='color: #8892b0; font-size: 11px; margin-bottom: 16px;'>
                {depart}  →  {arrivee}
            </div>
            <div style='background-color: #16213e; border-radius: 8px; padding: 14px;
                        border-left: 3px solid #e94560;'>
        """

        i = 0
        while i < len(chemin):
            station, ligne = chemin[i]
            couleur = couleur_ligne(ligne, self.reseau.lignes)
            nom_ligne = self.reseau.lignes.get(ligne, {}).get("nom", f"Ligne {ligne}")

            html += f"""
                <div style='margin: 6px 0;'>
                    <span style='font-size: 16px; margin-right: 8px;'>🚉</span>
                    <span style='color: #64ffda; font-weight: bold;'>Monter</span>
                    <span style='color: #ccd6f6; margin: 0 6px;'>station</span>
                    <span style='color: white; font-weight: bold;'>{station}</span>
                    <span style='background-color: {couleur};
                                 color: {'#000' if couleur in ('#FFCD00','#B6BD00') else '#fff'};
                                 border-radius: 10px; padding: 1px 8px;
                                 font-size: 11px; font-weight: bold; margin-left: 8px;'>
                        {ligne}
                    </span>
                </div>
            """
            i += 1

            while i < len(chemin):
                s2, l2 = chemin[i]
                s_prev, l_prev = chemin[i - 1]
                couleur2 = couleur_ligne(l2, self.reseau.lignes)
                nom_ligne2 = self.reseau.lignes.get(l2, {}).get("nom", f"Ligne {l2}")

                if s2 == s_prev and l2 != l_prev:
                    html += f"""
                        <div style='margin: 6px 0 6px 28px; padding: 6px 10px;
                                    background-color: #1a1a3a;
                                    border-left: 3px solid {couleur2}; border-radius: 4px;'>
                            <span style='font-size: 14px; margin-right: 6px;'>🔄</span>
                            <span style='color: #f7c59f; font-weight: bold;'>Correspondance</span>
                            <span style='color: #a8b2d8;'> à </span>
                            <span style='color: white; font-weight: bold;'>{s2}</span>
                            <span style='color: #a8b2d8;'> → prendre </span>
                            <span style='background-color: {couleur2};
                                         color: {'#000' if couleur2 in ('#FFCD00','#B6BD00') else '#fff'};
                                         border-radius: 10px; padding: 1px 8px;
                                         font-size: 11px; font-weight: bold;'>
                                {l2} — {nom_ligne2}
                            </span>
                        </div>
                    """
                    ligne = l2
                    couleur = couleur2
                    i += 1
                    continue

                if l2 == ligne:
                    if i == len(chemin) - 1:
                        html += f"""
                            <div style='margin: 6px 0;'>
                                <span style='font-size: 16px; margin-right: 8px;'>🏁</span>
                                <span style='color: #e94560; font-weight: bold;'>Descendre</span>
                                <span style='color: #ccd6f6; margin: 0 6px;'>station</span>
                                <span style='color: white; font-weight: bold;'>{s2}</span>
                            </div>
                        """
                    else:
                        html += f"""
                            <div style='margin: 3px 0 3px 28px; color: #8892b0;'>
                                <span style='color: #1a4a7a;'>│</span> ➡️ &nbsp; {s2}
                            </div>
                        """
                    i += 1
                    continue
                break

        html += f"""
            </div>
            <br>
            <div style='background-color: #0f3460; border-radius: 8px; padding: 12px 16px;
                        text-align: center;'>
                <span style='font-size: 20px;'>⏱️</span>
                <span style='color: #64ffda; font-size: 16px; font-weight: bold; margin-left: 8px;'>
                    Temps total estimé : {formater_temps(temps)}
                </span>
            </div>
        </div>
        """
        self.zone_resultats.setHtml(html)
        self.zone_resultats.moveCursor(QTextCursor.MoveOperation.Start)

    def _afficher_resultat_parcours(self, chemin: list, mode: str, icone: str, couleur: str):
        html = f"""
        <div style='font-family: Consolas, monospace; padding: 16px; color: #ccd6f6;'>
            <div style='color: {couleur}; font-size: 15px; font-weight: bold; margin-bottom: 16px;'>
                {icone} Chemin {mode} — {len(chemin) - 1} arrêt(s)
            </div>
            <div style='background-color: #16213e; border-radius: 8px; padding: 14px;
                        border-left: 3px solid {couleur};'>
        """
        for i, station in enumerate(chemin):
            if i == 0:
                html += f"<div style='margin: 6px 0; color: #64ffda;'>🚉 <b>Départ :</b> <span style='color:white;'>{station}</span></div>"
            elif i == len(chemin) - 1:
                html += f"<div style='margin: 6px 0; color: #e94560;'>🏁 <b>Arrivée :</b> <span style='color:white;'>{station}</span></div>"
            else:
                html += f"<div style='margin: 3px 0 3px 24px; color: #8892b0;'><span style='color:#1a4a7a;'>│</span> &nbsp; {station}</div>"
        html += """
            </div>
            <br>
            <div style='color: #8892b0; font-size: 11px;'>
                ℹ️ BFS/DFS : nombre d'arrêts uniquement. Utilisez <b style='color:#e94560;'>Dijkstra</b> pour le temps optimal.
            </div>
        </div>"""
        self.zone_resultats.setHtml(html)
        self.zone_resultats.moveCursor(QTextCursor.MoveOperation.Start)

    def _afficher_erreur(self, message: str):
        html = f"""
        <div style='font-family: Consolas, monospace; padding: 20px; color: #ccd6f6;'>
            <div style='color: #ff6b6b; font-size: 15px; font-weight: bold; margin-bottom: 12px;'>❌ Erreur</div>
            <div style='background-color: #2d1515; border-left: 3px solid #ff6b6b;
                        border-radius: 6px; padding: 12px 16px; color: #ff9999;'>
                {message}
            </div>
        </div>"""
        self.zone_resultats.setHtml(html)

    # -------------------------------------------------------------------------
    #  ANALYSES
    # -------------------------------------------------------------------------
    def _verifier_connexite(self):
        if not self.reseau:
            return
        connexe = verifier_connexite(self.reseau)
        nb = len(self.reseau.stations_physiques)
        couleur_res = "#64ffda" if connexe else "#ff6b6b"
        icone = "✅" if connexe else "⚠️"
        texte = "CONNEXE" if connexe else "NON CONNEXE"
        desc = (f"Toutes les {nb} stations sont accessibles depuis n'importe quelle autre."
                if connexe else "Certaines stations ne sont pas accessibles depuis toutes les autres.")
        html = f"""
        <div style='font-family: Consolas, monospace; padding: 20px; color: #ccd6f6;'>
            <div style='color: #a8d8ea; font-size: 15px; font-weight: bold; margin-bottom: 16px;'>
                🔗 Connexité — {self.reseau.nom_ville}
            </div>
            <div style='background-color: #16213e; border-radius: 8px; padding: 20px;
                        border-left: 4px solid {couleur_res}; text-align: center;'>
                <div style='font-size: 40px;'>{icone}</div>
                <div style='color: {couleur_res}; font-size: 20px; font-weight: bold;'>
                    Le réseau est {texte}
                </div>
                <div style='color: #8892b0; font-size: 12px; margin-top: 8px;'>{desc}</div>
            </div>
        </div>"""
        self.zone_resultats.setHtml(html)
        self.tabs.setCurrentIndex(0)
        self.barre_statut.setText(f"  {icone} Connexité : {texte}")

    # -------------------------------------------------------------------------
    #  PERTURBATIONS
    # -------------------------------------------------------------------------
    def _fermer_station(self):
        if not self.reseau:
            return
        station = self.search_fermer.valeur()
        if not station or not self.reseau.station_existe(station):
            self._afficher_erreur(f"Station introuvable : '{station}'")
            return
        self.reseau.fermer_station(station)
        self.barre_statut.setText(f"  ⛔ Station '{station}' fermée.")
        self._rafraichir_carte(chemin=self._chemin_actuel or [])

    def _fermer_ligne(self):
        if not self.reseau:
            return
        idx = self.combo_ligne_fermer.currentIndex()
        if idx < 0:
            return
        ligne = self.combo_ligne_fermer.itemData(idx)
        self.reseau.fermer_ligne(ligne)
        self.barre_statut.setText(f"  ⛔ Ligne '{ligne}' fermée.")
        self._rafraichir_carte(chemin=self._chemin_actuel or [])

    def _reset_perturbations(self):
        if not self.reseau:
            return
        self.reseau.reinitialiser_perturbations()
        self._chemin_actuel = []
        self.barre_statut.setText("  ✅ Perturbations réinitialisées.")
        self._afficher_bienvenue()
        self._rafraichir_carte()

    # -------------------------------------------------------------------------
    #  UTILITAIRES
    # -------------------------------------------------------------------------
    def _swap_stations(self):
        dep = self.search_depart.valeur()
        arr = self.search_arrivee.valeur()
        self.search_depart.input.setText(arr)
        self.search_arrivee.input.setText(dep)
        self.lbl_depart_badge.setText(f"📍 {arr}" if arr else "")
        self.lbl_arrivee_badge.setText(f"🏁 {dep}" if dep else "")
        self.lbl_depart_badge.setVisible(bool(arr))
        self.lbl_arrivee_badge.setVisible(bool(dep))
        self._rafraichir_carte()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Escape:
            self.close()

# =============================================================================
#  POINT D'ENTRÉE
# =============================================================================

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Transit Planner — ESME AAP3")
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    fenetre = FenetreCalculateur()
    fenetre.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

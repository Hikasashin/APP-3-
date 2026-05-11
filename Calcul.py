"""
=============================================================================
  Calculateur d'itinéraires - Réseaux de transports en commun
  ESME Sudria - Module Algorithmique Avancée 3 (AAP3)
=============================================================================
  Auteurs  : [Votre équipe]
  Date     : 2026

  Fonctionnalités :
    1. Chargement de données depuis fichiers JSON (Paris, Lyon, Bordeaux, Lille)
    2. Construction d'un graphe pondéré (liste d'adjacence)
    3. Parcours BFS (moins d'arrêts) et DFS (exploration profondeur)
    4. Algorithme de Dijkstra (meilleur temps de parcours)
    5. Affichage lisible de l'itinéraire avec correspondances
    6. Interface console interactive avec gestion des erreurs
    7. Généricité totale : ajout d'une ville = ajout d'un fichier JSON
    8. [BONUS] Gestion des perturbations (stations/tronçons/lignes fermés)
=============================================================================
"""

import json
import os
import heapq
from collections import deque, defaultdict


# =============================================================================
#  SECTION 1 : CHARGEMENT DES DONNÉES ET CONSTRUCTION DU GRAPHE
# =============================================================================

class ReseauTransport:
    """
    Représente un réseau de transport sous forme de graphe pondéré.

    Structure de données choisie : liste d'adjacence (dictionnaire)
    Justification : le réseau est un graphe creux (sparse graph).
    Avec ~200-500 stations, une matrice d'adjacence serait de taille 500x500
    mais aurait très peu de valeurs non-nulles. La liste d'adjacence est
    bien plus efficace en mémoire et en temps de parcours pour ce cas.

    Chaque nœud est un tuple (station, ligne) pour distinguer le même
    arrêt physique sur des lignes différentes — ce qui permet de modéliser
    le coût de correspondance lors d'un changement de ligne.
    """

    def __init__(self):
        self.nom_ville = ""
        # Liste d'adjacence : {(station, ligne) -> [(voisin_station, voisin_ligne, temps), ...]}
        self.adjacence: dict[tuple, list] = defaultdict(list)
        # Infos sur les lignes {id_ligne -> {nom, couleur, stations}}
        self.lignes: dict = {}
        # Stations de correspondance {nom_station -> [liste de lignes]}
        self.correspondances: dict[str, list] = {}
        # Temps moyen entre stations (fallback si pas de connexions explicites)
        self.temps_moyen: int = 90
        # Ensemble de toutes les stations physiques (nom seul)
        self.stations_physiques: set = set()
        # Perturbations actives
        self.stations_fermees: set = set()
        self.troncons_fermes: set = set()   # {(station_a, station_b, ligne)}
        self.lignes_fermees: set = set()

    # -------------------------------------------------------------------------
    def charger_json(self, chemin_fichier: str) -> None:
        """Charge un réseau depuis un fichier JSON et construit le graphe."""
        with open(chemin_fichier, encoding="utf-8") as f:
            data = json.load(f)

        self.nom_ville = data.get("nom", os.path.basename(chemin_fichier))
        self.lignes = data.get("lignes", {})
        self.temps_moyen = data.get("temps_moyen", 90)

        # --- Correspondances ---
        for c in data.get("correspondances", []):
            station = c["station"]
            self.correspondances[station] = c["lignes"]

        # --- Connexions entre stations voisines ---
        # Les JSON fournis peuvent avoir les connexions vides ([])
        # Dans ce cas on les génère depuis l'ordre des stations de chaque ligne.
        connexions_explicites = data.get("connexions", [])

        if connexions_explicites:
            self._charger_connexions_explicites(connexions_explicites)
        else:
            self._generer_connexions_depuis_lignes()

        # --- Arêtes de correspondance (même station, ligne différente) ---
        self._ajouter_aretes_correspondance()

        # Construire l'ensemble des stations physiques
        for station, _ in self.adjacence.keys():
            self.stations_physiques.add(station)

    def _charger_connexions_explicites(self, connexions: list) -> None:
        """
        Ajoute les connexions définies explicitement dans le JSON.
        Gère les deux formats trouvés dans les fichiers :
          - {"depart": ..., "arrivee": ..., "temps": ..., "ligne": ...}
          - {"de": ..., "vers": ..., "temps": ..., "ligne": ...}
        """
        for c in connexions:
            depart = c.get("depart") or c.get("de")
            arrivee = c.get("arrivee") or c.get("vers")
            temps = c.get("temps", self.temps_moyen)
            ligne = c.get("ligne", "?")
            if depart and arrivee:
                self.adjacence[(depart, ligne)].append((arrivee, ligne, temps))
                # On référence aussi les stations dans chaque ligne
                self.stations_physiques.add(depart)
                self.stations_physiques.add(arrivee)

    def _generer_connexions_depuis_lignes(self) -> None:
        """
        Génère des connexions bidirectionnelles entre stations consécutives
        de chaque ligne (utilisé quand 'connexions' est vide dans le JSON).
        """
        for id_ligne, info_ligne in self.lignes.items():
            stations = info_ligne.get("stations", [])
            for i in range(len(stations) - 1):
                s1, s2 = stations[i], stations[i + 1]
                self.adjacence[(s1, id_ligne)].append((s2, id_ligne, self.temps_moyen))
                self.adjacence[(s2, id_ligne)].append((s1, id_ligne, self.temps_moyen))

    def _ajouter_aretes_correspondance(self) -> None:
        """
        Ajoute des arêtes de coût 120s entre les nœuds (station, ligneA)
        et (station, ligneB) pour chaque station de correspondance.
        """
        TEMPS_CORRESPONDANCE = 120
        for station, lignes_corres in self.correspondances.items():
            for i in range(len(lignes_corres)):
                for j in range(len(lignes_corres)):
                    if i != j:
                        la, lb = lignes_corres[i], lignes_corres[j]
                        self.adjacence[(station, la)].append(
                            (station, lb, TEMPS_CORRESPONDANCE)
                        )
        # Aussi : si une station apparaît dans plusieurs lignes sans être
        # déclarée dans "correspondances", on la gère ici
        station_lignes: dict[str, set] = defaultdict(set)
        for (station, ligne) in self.adjacence.keys():
            station_lignes[station].add(ligne)
        for station, lignes_set in station_lignes.items():
            if station not in self.correspondances and len(lignes_set) > 1:
                lignes_list = list(lignes_set)
                for i in range(len(lignes_list)):
                    for j in range(len(lignes_list)):
                        if i != j:
                            la, lb = lignes_list[i], lignes_list[j]
                            self.adjacence[(station, la)].append(
                                (station, lb, TEMPS_CORRESPONDANCE)
                            )

    # -------------------------------------------------------------------------
    def trouver_ligne_station(self, station: str) -> list[str]:
        """Retourne toutes les lignes qui desservent une station donnée."""
        return [ligne for (s, ligne) in self.adjacence.keys() if s == station]

    def station_existe(self, station: str) -> bool:
        return station in self.stations_physiques

    def get_noeuds_station(self, station: str) -> list[tuple]:
        """Retourne tous les nœuds (station, ligne) pour une station physique."""
        return [(s, l) for (s, l) in self.adjacence.keys() if s == station]

    # -------------------------------------------------------------------------
    # Gestion des perturbations
    # -------------------------------------------------------------------------
    def fermer_station(self, station: str) -> None:
        self.stations_fermees.add(station)

    def ouvrir_station(self, station: str) -> None:
        self.stations_fermees.discard(station)

    def fermer_troncon(self, s1: str, s2: str, ligne: str) -> None:
        self.troncons_fermes.add((s1, s2, ligne))
        self.troncons_fermes.add((s2, s1, ligne))

    def ouvrir_troncon(self, s1: str, s2: str, ligne: str) -> None:
        self.troncons_fermes.discard((s1, s2, ligne))
        self.troncons_fermes.discard((s2, s1, ligne))

    def fermer_ligne(self, ligne: str) -> None:
        self.lignes_fermees.add(ligne)

    def ouvrir_ligne(self, ligne: str) -> None:
        self.lignes_fermees.discard(ligne)

    def reinitialiser_perturbations(self) -> None:
        self.stations_fermees.clear()
        self.troncons_fermes.clear()
        self.lignes_fermees.clear()

    def _noeud_accessible(self, station: str, ligne: str) -> bool:
        """Vérifie si un nœud n'est pas bloqué par une perturbation."""
        if station in self.stations_fermees:
            return False
        if ligne in self.lignes_fermees:
            return False
        return True

    def _arete_accessible(self, s1: str, l1: str, s2: str, l2: str) -> bool:
        """Vérifie si une arête n'est pas bloquée."""
        if not self._noeud_accessible(s1, l1):
            return False
        if not self._noeud_accessible(s2, l2):
            return False
        # Tronçon fermé (même ligne = déplacement physique)
        if l1 == l2 and (s1, s2, l1) in self.troncons_fermes:
            return False
        return True

    def voisins_accessibles(self, station: str, ligne: str) -> list:
        """Retourne les voisins accessibles d'un nœud (perturbations comprises)."""
        resultat = []
        for (s2, l2, temps) in self.adjacence.get((station, ligne), []):
            if self._arete_accessible(station, ligne, s2, l2):
                resultat.append((s2, l2, temps))
        return resultat


# =============================================================================
#  SECTION 2 : ALGORITHMES DE PARCOURS DE GRAPHE
# =============================================================================

def bfs(reseau: ReseauTransport, depart: str, arrivee: str) -> list[str] | None:
    """
    Parcours en Largeur (BFS) — Breadth-First Search.
    Trouve le chemin avec le MOINS D'ARRÊTS (sans tenir compte des temps).
    Retourne la liste des stations physiques traversées, ou None si impossible.
    """
    # On part depuis n'importe quelle ligne desservant la station de départ
    noeuds_depart = reseau.get_noeuds_station(depart)
    if not noeuds_depart:
        return None

    # File FIFO : chaque élément est (station, ligne, chemin_stations)
    file = deque()
    visites = set()

    for (s, l) in noeuds_depart:
        if reseau._noeud_accessible(s, l):
            file.append((s, l, [s]))
            visites.add((s, l))

    while file:
        station, ligne, chemin = file.popleft()

        if station == arrivee:
            return chemin

        for (s2, l2, _) in reseau.voisins_accessibles(station, ligne):
            if (s2, l2) not in visites:
                visites.add((s2, l2))
                nouveau_chemin = chemin + ([s2] if s2 != chemin[-1] else [])
                file.append((s2, l2, nouveau_chemin))

    return None


def dfs(reseau: ReseauTransport, depart: str, arrivee: str) -> list[str] | None:
    """
    Parcours en Profondeur (DFS) — Depth-First Search.
    Explore le graphe en profondeur. Ne garantit PAS le chemin optimal.
    Retourne la liste des stations physiques traversées, ou None si impossible.
    """
    noeuds_depart = reseau.get_noeuds_station(depart)
    if not noeuds_depart:
        return None

    # Pile LIFO : (station, ligne, chemin)
    pile = []
    visites = set()

    for (s, l) in noeuds_depart:
        if reseau._noeud_accessible(s, l):
            pile.append((s, l, [s]))

    while pile:
        station, ligne, chemin = pile.pop()

        if (station, ligne) in visites:
            continue
        visites.add((station, ligne))

        if station == arrivee:
            return chemin

        for (s2, l2, _) in reseau.voisins_accessibles(station, ligne):
            if (s2, l2) not in visites:
                nouveau_chemin = chemin + ([s2] if s2 != chemin[-1] else [])
                pile.append((s2, l2, nouveau_chemin))

    return None


def verifier_connexite(reseau: ReseauTransport) -> bool:
    """
    Vérifie que toutes les stations sont accessibles depuis n'importe
    quelle autre station (graphe connexe) via un BFS global.
    Retourne True si le réseau est connexe, False sinon.
    """
    tous_noeuds = list(reseau.adjacence.keys())
    if not tous_noeuds:
        return True

    # Départ depuis le premier nœud accessible
    noeud_debut = None
    for n in tous_noeuds:
        if reseau._noeud_accessible(n[0], n[1]):
            noeud_debut = n
            break
    if noeud_debut is None:
        return False

    visites = set()
    file = deque([noeud_debut])
    visites.add(noeud_debut)

    while file:
        station, ligne = file.popleft()
        for (s2, l2, _) in reseau.voisins_accessibles(station, ligne):
            if (s2, l2) not in visites:
                visites.add((s2, l2))
                file.append((s2, l2))

    stations_visitees = {s for (s, _) in visites}
    return stations_visitees == reseau.stations_physiques


def identifier_correspondances(reseau: ReseauTransport) -> dict[str, list]:
    """
    Identifie toutes les stations de correspondance du réseau
    (stations desservies par au moins 2 lignes différentes).
    Retourne un dict {station -> [lignes]}.
    """
    station_lignes: dict[str, set] = defaultdict(set)
    for (station, ligne) in reseau.adjacence.keys():
        station_lignes[station].add(ligne)
    return {s: sorted(l) for s, l in station_lignes.items() if len(l) > 1}


# =============================================================================
#  SECTION 3 : ALGORITHME DE DIJKSTRA — MEILLEUR ITINÉRAIRE EN TEMPS
# =============================================================================

def dijkstra(reseau: ReseauTransport, depart: str, arrivee: str
             ) -> tuple[list | None, int]:
    """
    Algorithme de Dijkstra pour trouver le chemin le plus court en temps.

    Nœuds du graphe : (station, ligne) — permet de modéliser le coût de
    correspondance lors d'un changement de ligne à la même station.

    Retourne :
      - chemin : liste de tuples (station, ligne) de départ à arrivée
      - temps_total : temps en secondes (int)
    """
    noeuds_depart = [
        (s, l) for (s, l) in reseau.adjacence.keys()
        if s == depart and reseau._noeud_accessible(s, l)
    ]
    if not noeuds_depart:
        return None, 0

    # dist[(station, ligne)] = meilleur temps connu depuis départ
    dist: dict = {}
    # predecesseur[(station, ligne)] = (station_prec, ligne_prec)
    predecesseur: dict = {}

    # File de priorité min-heap : (temps, station, ligne)
    tas = []
    for (s, l) in noeuds_depart:
        dist[(s, l)] = 0
        predecesseur[(s, l)] = None
        heapq.heappush(tas, (0, s, l))

    while tas:
        temps_actuel, station, ligne = heapq.heappop(tas)

        # Si on a atteint l'arrivée, on reconstruit le chemin
        if station == arrivee:
            chemin = _reconstruire_chemin(predecesseur, (station, ligne))
            return chemin, temps_actuel

        # Ignorer si on a déjà trouvé un meilleur chemin
        if temps_actuel > dist.get((station, ligne), float("inf")):
            continue

        for (s2, l2, temps_arete) in reseau.voisins_accessibles(station, ligne):
            nouveau_temps = temps_actuel + temps_arete
            if nouveau_temps < dist.get((s2, l2), float("inf")):
                dist[(s2, l2)] = nouveau_temps
                predecesseur[(s2, l2)] = (station, ligne)
                heapq.heappush(tas, (nouveau_temps, s2, l2))

    return None, 0


def _reconstruire_chemin(predecesseur: dict, noeud_final: tuple) -> list:
    """Remonte le dictionnaire des prédécesseurs pour reconstruire le chemin."""
    chemin = []
    courant = noeud_final
    while courant is not None:
        chemin.append(courant)
        courant = predecesseur.get(courant)
    chemin.reverse()
    return chemin


# =============================================================================
#  SECTION 4 : AFFICHAGE DE L'ITINÉRAIRE
# =============================================================================

def formater_temps(secondes: int) -> str:
    """Convertit des secondes en chaîne lisible 'X minutes Y secondes'."""
    minutes = secondes // 60
    secs = secondes % 60
    if minutes == 0:
        return f"{secs} secondes"
    if secs == 0:
        return f"{minutes} minute{'s' if minutes > 1 else ''}"
    return f"{minutes} minute{'s' if minutes > 1 else ''} {secs} secondes"


def afficher_itineraire(chemin: list[tuple], temps_total: int,
                        reseau: ReseauTransport) -> None:
    """
    Affiche l'itinéraire de manière claire et formatée, comme demandé dans
    l'énoncé :
      - Station de montée et ligne
      - Stations traversées
      - Correspondances effectuées
      - Station de descente et ligne
      - Temps total
    """
    if not chemin:
        print("  Aucun itinéraire trouvé.")
        return

    print()
    print("=" * 60)
    print("  ITINÉRAIRE")
    print("=" * 60)

    i = 0
    while i < len(chemin):
        station, ligne = chemin[i]
        nom_ligne = reseau.lignes.get(ligne, {}).get("nom", f"Ligne {ligne}")

        # --- Montée ---
        print(f"  🚉 Monter station {station}, {nom_ligne}")
        i += 1

        # --- Parcours sur la même ligne ---
        while i < len(chemin):
            s_suiv, l_suiv = chemin[i]

            # Correspondance : même station, ligne différente
            if s_suiv == chemin[i - 1][0] and l_suiv != chemin[i - 1][1]:
                nom_ligne_suiv = reseau.lignes.get(l_suiv, {}).get(
                    "nom", f"Ligne {l_suiv}"
                )
                print(f"  🔄 Correspondance station {s_suiv}, "
                      f"prendre la {nom_ligne_suiv}")
                ligne = l_suiv
                nom_ligne = nom_ligne_suiv
                i += 1
                continue

            # Même ligne, on continue
            if l_suiv == ligne:
                # Descente si c'est le dernier nœud
                if i == len(chemin) - 1:
                    print(f"  🏁 Descendre station {s_suiv}, {nom_ligne}")
                    i += 1
                else:
                    # Vérifier si on change de ligne après
                    s_apres, l_apres = chemin[i + 1] if i + 1 < len(chemin) else (None, None)
                    if s_apres == s_suiv and l_apres != l_suiv:
                        # On descend ici pour correspondance
                        print(f"  ➡️  Continuer station {s_suiv}")
                    else:
                        print(f"  ➡️  Continuer station {s_suiv}")
                    i += 1
                continue

            # Changement de ligne vers une station différente : impossible
            # (cas non attendu dans un graphe bien construit)
            break

    print()
    print(f"  ⏱️  Temps total estimé : {formater_temps(temps_total)}")
    print("=" * 60)
    print()


def afficher_itineraire_bfs(chemin_stations: list[str]) -> None:
    """Affiche le résultat d'un parcours BFS (moins d'arrêts)."""
    if not chemin_stations:
        print("  Aucun chemin BFS trouvé.")
        return
    print()
    print("=" * 60)
    print("  CHEMIN BFS (moins d'arrêts — sans optimisation du temps)")
    print("=" * 60)
    for i, station in enumerate(chemin_stations):
        if i == 0:
            print(f"  🚉 Départ  : {station}")
        elif i == len(chemin_stations) - 1:
            print(f"  🏁 Arrivée : {station}")
        else:
            print(f"       ↓     {station}")
    print(f"  Nombre d'arrêts : {len(chemin_stations) - 1}")
    print("=" * 60)
    print()


# =============================================================================
#  SECTION 5 : GESTION DES PERTURBATIONS — AFFICHAGE ET COMPARAISON
# =============================================================================

def calculer_et_comparer_perturbation(
        reseau: ReseauTransport, depart: str, arrivee: str,
        temps_normal: int, chemin_normal: list | None) -> None:
    """
    Recalcule l'itinéraire avec les perturbations actives et compare
    avec le trajet normal.
    """
    chemin_perturbe, temps_perturbe = dijkstra(reseau, depart, arrivee)

    print()
    print("⚠️  IMPACT DES PERTURBATIONS")
    print("-" * 60)

    if chemin_normal:
        # Vérifier si le chemin normal passe par une perturbation
        chemin_impacte = False
        for (station, ligne) in chemin_normal:
            if not reseau._noeud_accessible(station, ligne):
                chemin_impacte = True
                break
        if chemin_impacte:
            print("  ⛔ L'itinéraire initial est impacté par une perturbation !")

    if chemin_perturbe is None:
        print("  ❌ Aucun itinéraire alternatif disponible.")
    else:
        diff = temps_perturbe - temps_normal
        print(f"  Temps normal     : {formater_temps(temps_normal)}")
        print(f"  Temps alternatif : {formater_temps(temps_perturbe)}")
        if diff > 0:
            print(f"  Impact           : +{formater_temps(diff)} de plus")
        else:
            print("  Impact           : aucun (même itinéraire possible)")
        afficher_itineraire(chemin_perturbe, temps_perturbe, reseau)


# =============================================================================
#  SECTION 6 : INTERFACE CONSOLE INTERACTIVE
# =============================================================================

def decouvrir_fichiers_json(dossier: str = ".") -> dict[str, str]:
    """
    Découvre automatiquement tous les fichiers JSON de réseaux dans un dossier.
    Retourne {nom_ville -> chemin_fichier}.
    Généricité : ajouter une ville = ajouter un fichier JSON dans le dossier.
    """
    villes = {}
    for fichier in sorted(os.listdir(dossier)):
        if fichier.endswith(".json"):
            chemin = os.path.join(dossier, fichier)
            try:
                with open(chemin, encoding="utf-8") as f:
                    data = json.load(f)
                nom = data.get("nom", fichier.replace(".json", "").capitalize())
                villes[nom] = chemin
            except Exception:
                pass  # Fichier JSON invalide, on l'ignore
    return villes


def saisir_station(reseau: ReseauTransport, role: str) -> str:
    """
    Demande à l'utilisateur de saisir une station avec autocomplétion partielle
    et gestion des erreurs de saisie.
    """
    while True:
        saisie = input(f"  Station de {role} : ").strip()
        if not saisie:
            print("  ⚠️  Veuillez saisir un nom de station.")
            continue

        # Recherche exacte (insensible à la casse)
        for station in reseau.stations_physiques:
            if station.lower() == saisie.lower():
                return station

        # Recherche partielle
        correspondances = [
            s for s in reseau.stations_physiques
            if saisie.lower() in s.lower()
        ]

        if len(correspondances) == 1:
            print(f"  ✅ Station trouvée : {correspondances[0]}")
            return correspondances[0]

        elif len(correspondances) > 1:
            print(f"  Plusieurs stations correspondent à '{saisie}' :")
            for i, s in enumerate(sorted(correspondances), 1):
                print(f"    {i}. {s}")
            choix = input("  Entrez le numéro ou affinez votre recherche : ").strip()
            if choix.isdigit():
                idx = int(choix) - 1
                triees = sorted(correspondances)
                if 0 <= idx < len(triees):
                    return triees[idx]
            print("  ⚠️  Choix invalide, recommencez.")
        else:
            print(f"  ❌ Station '{saisie}' introuvable. Vérifiez l'orthographe.")


def menu_perturbations(reseau: ReseauTransport) -> None:
    """Sous-menu pour gérer les perturbations."""
    while True:
        print()
        print("  --- GESTION DES PERTURBATIONS ---")
        print("  1. Fermer une station")
        print("  2. Fermer un tronçon (entre deux stations)")
        print("  3. Fermer une ligne entière")
        print("  4. Voir les perturbations actives")
        print("  5. Réinitialiser toutes les perturbations")
        print("  0. Retour")
        choix = input("  Choix : ").strip()

        if choix == "1":
            station = saisir_station(reseau, "fermeture")
            reseau.fermer_station(station)
            print(f"  ✅ Station '{station}' fermée.")

        elif choix == "2":
            print("  Station A :")
            s1 = saisir_station(reseau, "départ du tronçon")
            print("  Station B :")
            s2 = saisir_station(reseau, "arrivée du tronçon")
            lignes_s1 = reseau.trouver_ligne_station(s1)
            lignes_communes = [
                l for l in lignes_s1 if l in reseau.trouver_ligne_station(s2)
            ]
            if not lignes_communes:
                print("  ❌ Ces deux stations ne sont pas sur la même ligne.")
            else:
                print(f"  Lignes communes : {', '.join(lignes_communes)}")
                ligne = input("  Ligne à fermer : ").strip()
                if ligne in lignes_communes:
                    reseau.fermer_troncon(s1, s2, ligne)
                    print(f"  ✅ Tronçon {s1} ↔ {s2} (ligne {ligne}) fermé.")
                else:
                    print("  ❌ Ligne invalide.")

        elif choix == "3":
            print(f"  Lignes disponibles : {', '.join(sorted(reseau.lignes.keys()))}")
            ligne = input("  Ligne à fermer : ").strip()
            if ligne in reseau.lignes:
                reseau.fermer_ligne(ligne)
                print(f"  ✅ Ligne '{ligne}' fermée.")
            else:
                print("  ❌ Ligne introuvable.")

        elif choix == "4":
            print()
            print(f"  Stations fermées : {reseau.stations_fermees or 'aucune'}")
            print(f"  Tronçons fermés  : {reseau.troncons_fermes or 'aucun'}")
            print(f"  Lignes fermées   : {reseau.lignes_fermees or 'aucune'}")

        elif choix == "5":
            reseau.reinitialiser_perturbations()
            print("  ✅ Toutes les perturbations ont été réinitialisées.")

        elif choix == "0":
            break


def menu_analyses(reseau: ReseauTransport) -> None:
    """Sous-menu d'analyses du réseau."""
    while True:
        print()
        print("  --- ANALYSE DU RÉSEAU ---")
        print("  1. Vérifier la connexité du réseau")
        print("  2. Lister les stations de correspondance")
        print("  3. BFS (chemin avec le moins d'arrêts)")
        print("  4. DFS (exploration en profondeur)")
        print("  0. Retour")
        choix = input("  Choix : ").strip()

        if choix == "1":
            print()
            print("  Vérification en cours...")
            connexe = verifier_connexite(reseau)
            if connexe:
                print(f"  ✅ Le réseau de {reseau.nom_ville} est CONNEXE.")
                print(f"     Toutes les {len(reseau.stations_physiques)} stations "
                      f"sont accessibles.")
            else:
                print(f"  ⚠️  Le réseau de {reseau.nom_ville} n'est PAS entièrement "
                      f"connexe.")

        elif choix == "2":
            corres = identifier_correspondances(reseau)
            print()
            print(f"  Stations de correspondance ({len(corres)}) :")
            for station, lignes in sorted(corres.items()):
                print(f"    • {station} : lignes {', '.join(lignes)}")

        elif choix in ("3", "4"):
            depart = saisir_station(reseau, "départ")
            arrivee = saisir_station(reseau, "arrivée")
            if depart == arrivee:
                print("  ℹ️  Départ et arrivée identiques.")
                continue
            if choix == "3":
                chemin = bfs(reseau, depart, arrivee)
                afficher_itineraire_bfs(chemin)
            else:
                chemin = dfs(reseau, depart, arrivee)
                if chemin:
                    print()
                    print("  Chemin DFS trouvé :")
                    afficher_itineraire_bfs(chemin)
                else:
                    print("  ❌ Aucun chemin DFS trouvé.")

        elif choix == "0":
            break


def interface_principale() -> None:
    """
    Point d'entrée principal — menu interactif console.
    """
    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║     CALCULATEUR D'ITINÉRAIRES — TRANSPORTS EN COMMUN    ║")
    print("║                  ESME Sudria — AAP3 2026                ║")
    print("╚══════════════════════════════════════════════════════════╝")

    # Découverte automatique des fichiers JSON
    # On cherche dans le dossier courant ET dans le dossier du script
    dossiers_a_tester = [
        ".",
        os.path.dirname(os.path.abspath(__file__)),
    ]
    villes_disponibles = {}
    for dossier in dossiers_a_tester:
        villes_disponibles.update(decouvrir_fichiers_json(dossier))

    if not villes_disponibles:
        print()
        print("  ❌ Aucun fichier JSON de réseau trouvé dans le dossier courant.")
        print("     Placez les fichiers paris.json, lyon.json, etc. dans le même")
        print("     dossier que ce script.")
        return

    reseau: ReseauTransport | None = None
    ville_courante: str = ""

    while True:
        print()
        print("═" * 60)
        if ville_courante:
            print(f"  Réseau chargé : {ville_courante} "
                  f"({len(reseau.stations_physiques)} stations, "
                  f"{len(reseau.lignes)} lignes)")
        print()
        print("  MENU PRINCIPAL")
        print("  1. Choisir / changer de ville")
        print("  2. Calculer un itinéraire (Dijkstra — temps optimal)")
        print("  3. Analyses du réseau (BFS, DFS, connexité, correspondances)")
        print("  4. Gérer les perturbations")
        print("  0. Quitter")
        print()

        choix = input("  Votre choix : ").strip()

        # ----- Quitter -----
        if choix == "0":
            print()
            print("  À bientôt !")
            break

        # ----- Choisir une ville -----
        elif choix == "1":
            print()
            print("  Villes disponibles :")
            noms_tries = sorted(villes_disponibles.keys())
            for i, nom in enumerate(noms_tries, 1):
                print(f"    {i}. {nom}")
            print()
            saisie = input("  Entrez le numéro ou le nom de la ville : ").strip()

            ville_choisie = None
            if saisie.isdigit():
                idx = int(saisie) - 1
                if 0 <= idx < len(noms_tries):
                    ville_choisie = noms_tries[idx]
            else:
                for nom in noms_tries:
                    if saisie.lower() in nom.lower():
                        ville_choisie = nom
                        break

            if ville_choisie is None:
                print("  ❌ Ville non reconnue.")
                continue

            print(f"  Chargement de {ville_choisie}...")
            reseau = ReseauTransport()
            try:
                reseau.charger_json(villes_disponibles[ville_choisie])
                ville_courante = ville_choisie
                print(f"  ✅ {ville_courante} chargé : "
                      f"{len(reseau.stations_physiques)} stations, "
                      f"{len(reseau.lignes)} lignes.")
            except Exception as e:
                print(f"  ❌ Erreur lors du chargement : {e}")
                reseau = None
                ville_courante = ""

        # ----- Options nécessitant un réseau chargé -----
        elif choix in ("2", "3", "4"):
            if reseau is None:
                print("  ⚠️  Veuillez d'abord choisir une ville (option 1).")
                continue

            if choix == "2":
                # --- Calcul d'itinéraire Dijkstra ---
                print()
                depart = saisir_station(reseau, "départ")
                arrivee = saisir_station(reseau, "arrivée")

                if depart == arrivee:
                    print("  ℹ️  Vous êtes déjà à destination !")
                    continue

                print()
                print("  Calcul en cours...")

                # Calcul sans perturbations (pour comparaison)
                # On sauvegarde temporairement les perturbations
                stations_f = set(reseau.stations_fermees)
                troncons_f = set(reseau.troncons_fermes)
                lignes_f = set(reseau.lignes_fermees)

                reseau.reinitialiser_perturbations()
                chemin_normal, temps_normal = dijkstra(reseau, depart, arrivee)

                # Restaurer les perturbations
                reseau.stations_fermees = stations_f
                reseau.troncons_fermes = troncons_f
                reseau.lignes_fermees = lignes_f

                perturbations_actives = (
                    reseau.stations_fermees
                    or reseau.troncons_fermes
                    or reseau.lignes_fermees
                )

                if perturbations_actives:
                    # Afficher l'itinéraire avec perturbations
                    calculer_et_comparer_perturbation(
                        reseau, depart, arrivee, temps_normal, chemin_normal
                    )
                else:
                    if chemin_normal is None:
                        print(f"  ❌ Impossible de relier '{depart}' à '{arrivee}'.")
                    else:
                        afficher_itineraire(chemin_normal, temps_normal, reseau)

            elif choix == "3":
                menu_analyses(reseau)

            elif choix == "4":
                menu_perturbations(reseau)

        else:
            print("  ⚠️  Choix invalide, veuillez réessayer.")


# =============================================================================
#  POINT D'ENTRÉE
# =============================================================================

if __name__ == "__main__":
    interface_principale()

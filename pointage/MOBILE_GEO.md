# Pointage géolocalisé — Guide d'intégration mobile

Ce guide décrit ce que l'**application mobile** (agent de sécurité) doit changer pour
rester en phase avec le backend depuis l'ajout de la **géolocalisation du pointage**.

À lire en complément de [`API.md`](API.md), qui reste la référence complète de l'API.

> **En une phrase :** `check-in` et `check-out` exigent désormais `latitude` et
> `longitude` dans le corps de la requête. Sans elles → `400`. Aucune notion de zone
> autorisée : le backend se contente d'**enregistrer** la position (traçabilité).

---

## 1. Changement de contrat

Les endpoints **arrivée** (`POST /attendance/check-in/`) **et départ**
(`POST /attendance/check-out/`) reçoivent deux nouveaux champs **obligatoires**.

**Avant**

```json
{ "badge_token": "un5kZ_ikDy6nOC6bIpSH3w" }
```

**Maintenant** (les deux endpoints, même format)

```json
{
  "badge_token": "un5kZ_ikDy6nOC6bIpSH3w",
  "latitude": 9.535000,
  "longitude": -13.677300
}
```

### Règles de validation

| Champ | Contrainte |
|---|---|
| `latitude` | nombre, **obligatoire**, `-90 ≤ lat ≤ 90` |
| `longitude` | nombre, **obligatoire**, `-180 ≤ lng ≤ 180` |
| Précision | **6 décimales maximum** (≈ 0,11 m). Tronquer/arrondir avant l'envoi ; au-delà → `400`. |

- La réponse `Attendance` renvoie les coordonnées enregistrées sous forme de **chaînes**
  (`"9.535000"`), pas de nombres — c'est le format d'un décimal DRF. En lecture on trouve
  `check_in_latitude`, `check_in_longitude`, `check_out_latitude`, `check_out_longitude`
  (les `check_out_*` restent `null` tant que le départ n'est pas pointé).
- **Inchangés :** `POST /token/`, `GET /attendance/status/`, `GET /attendance/` (historique)
  et `GET /attendance/{id}/`. Aucune coordonnée à envoyer sur ces routes.

---

## 2. Étapes côté application

### 2.1 Permission de localisation

| Plateforme | À faire |
|---|---|
| **Android** | Déclarer `android.permission.ACCESS_FINE_LOCATION` dans le manifeste **et** en demander l'autorisation à l'exécution (runtime). |
| **iOS** | Ajouter la clé `NSLocationWhenInUseUsageDescription` à `Info.plist`, avec un texte FR clair (ex. « Utilisée pour attester le lieu de pointage »). |

Demander la permission **au bon moment** — au lancement de l'app ou avant le premier
scan — pas au milieu du flux de pointage.

### 2.2 Relever la position au moment du scan

- Récupérer la **position courante** (`FusedLocationProvider` / `CLLocationManager` /
  `getCurrentPosition`) au moment du scan, en **haute précision**.
- Utiliser un **timeout** raisonnable (≈ 5–10 s) et **ne pas réutiliser** une position
  ancienne : la coordonnée envoyée doit correspondre au lieu réel du pointage.
- **Formater à 6 décimales** avant l'envoi (troncature/arrondi).

### 2.3 Joindre les coordonnées aux deux requêtes

- Ajouter `latitude` / `longitude` au corps de **`check-in` ET `check-out`**.
- Le départ enregistre ses **propres** coordonnées (elles peuvent différer de l'arrivée).

---

## 3. Gestion des erreurs

Aux erreurs déjà documentées dans `API.md` s'ajoutent les cas liés aux coordonnées.

| Statut | Corps (exemple) | Cause | Réaction app |
|---|---|---|---|
| `400` | `{"latitude": ["This field is required."]}` | Coordonnée absente | Obtenir la position **puis** renvoyer ; ne jamais poster sans coords |
| `400` | `{"longitude": ["This field is required."]}` | Coordonnée absente | idem |
| `400` | `{"latitude": ["Ensure this value is less than or equal to 90."]}` | Hors bornes | Bug de formatage/relevé à corriger |
| `400` | `{"latitude": ["Ensure that there are no more than 6 decimal places."]}` | Trop de décimales | Tronquer à 6 décimales avant l'envoi |
| `401` | `{"detail": "Authentication credentials were not provided."}` | Jeton absent/invalide | Rediriger vers `/token/` |
| `409` | `{"detail": "Cet employé a déjà pointé son arrivée..."}` | Doublon arrivée/départ | Afficher `detail`, proposer la bonne action |
| `400` | `{"badge_token": ["Badge inconnu."]}` / `["Employé désactivé."]` | Badge invalide | Afficher le message, refuser |

---

## 4. Cas GPS indisponible ou refusé

Les coordonnées étant **obligatoires**, il est **impossible de pointer sans position**.
L'app doit gérer explicitement ces situations plutôt que d'envoyer une requête vouée au `400` :

- **Permission refusée** → bloquer le bouton de pointage, afficher un message
  (« Active la localisation pour pointer ») et proposer d'ouvrir les réglages.
- **GPS désactivé / mode avion** → inviter à réactiver la localisation.
- **Timeout / position indisponible** → message + **bouton Réessayer** (relance le relevé,
  pas l'envoi à vide).

> Décision produit : à ce stade le backend n'autorise **aucun** pointage sans coordonnées.
> Si un fonctionnement dégradé (pointage sans GPS) devient nécessaire, il faudra d'abord
> rendre les champs optionnels côté backend.

---

## 5. Points d'attention

- **Précision non contrôlée côté serveur.** Le backend n'impose aucun seuil de précision
  (`accuracy`) ni aucune zone. L'app peut afficher la précision à titre indicatif, mais
  n'est pas obligée de bloquer sur une position imprécise.
- **`accuracy` / altitude non stockés.** Le backend n'enregistre que `latitude`/`longitude`.
  Tout champ supplémentaire envoyé est ignoré. Pour conserver la précision ou l'altitude,
  il faudrait d'abord les ajouter au modèle et au serializer côté backend.
- **Déploiement synchronisé (⚠️ risque de rupture).** Le backend **rejette désormais**
  toute app qui pointe sans coordonnées. La mise à jour mobile doit être **déployée en même
  temps** que le backend, idéalement avec une **mise à jour forcée** pour éviter que des
  versions antérieures ne se retrouvent bloquées en `400`.

---

## 6. Checklist de test mobile

1. **Permission refusée** → tenter un pointage → l'app bloque proprement (aucune requête à
   vide, message clair).
2. **Permission accordée → arrivée** → `POST /check-in/` avec coords → `201`, la réponse
   contient `check_in_latitude` / `check_in_longitude` renseignés, `check_out_*` à `null`.
3. **Départ** → `POST /check-out/` avec coords (différentes) → `200`,
   `check_out_latitude` / `check_out_longitude` renseignés, les `check_in_*` **conservés**.
4. **GPS coupé pendant un scan** → message d'erreur + **Réessayer** fonctionnel.
5. **Coordonnée aberrante** (ex. `latitude = 200`) → `400` correctement affiché (test de
   robustesse du formatage).

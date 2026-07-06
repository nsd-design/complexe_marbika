# API Pointage — Documentation (app mobile)

API REST de pointage des employés du Complexe Marbika. Destinée à l'application
mobile utilisée par l'agent de sécurité : il scanne le **QR du badge** de l'employé
et envoie le jeton au backend pour enregistrer l'**arrivée** (check-in) ou le
**départ** (check-out).

---

## 1. Généralités

| | |
|---|---|
| **URL de base** | `https://<host>/attendance/api/v1/` |
| **Format** | JSON (`Content-Type: application/json`) en requête et réponse |
| **Encodage dates** | ISO 8601 en **UTC** (ex. `2026-07-06T15:57:18.215909Z`) — à convertir en heure locale côté mobile |
| **Slash final** | **Obligatoire** sur toutes les URL (ex. `/check-in/`, pas `/check-in`) |
| **Langue des messages** | Messages d'erreur métier en français |

> Toutes les routes ci-dessous sont préfixées par `/attendance/api/v1/attendance/`.

### Authentification (obligatoire)

**Toutes les opérations exigent une authentification par jeton.** Une requête sans
jeton valide est rejetée avec `401 Unauthorized`.

1. L'app obtient un jeton en échangeant les identifiants de l'agent de sécurité :

   ```
   POST /attendance/api/v1/token/
   Content-Type: application/json

   { "username": "<agent>", "password": "<mot_de_passe>" }
   ```
   → `200 OK` : `{ "token": "9944b09199c62bcf9418ad8bf3f04d7fb46e29ff" }`
   (identifiants invalides → `400`). Cet endpoint est le seul public.

2. L'app envoie ensuite ce jeton dans l'en-tête de **chaque** requête :

   ```
   Authorization: Token 9944b09199c62bcf9418ad8bf3f04d7fb46e29ff
   ```

L'agent ainsi authentifié est automatiquement tracé dans `created_by` (à l'arrivée)
et `updated_by` (au départ) du pointage.

> Le jeton n'expire pas ; en cas de compromission, il est révoqué côté serveur
> (l'agent doit alors en redemander un via `/token/`).

---

## 2. Concepts clés

- **`badge_token`** : chaîne opaque (~22 caractères, ex. `un5kZ_ikDy6nOC6bIpSH3w`)
  **encodée telle quelle dans le QR** du badge. C'est la seule donnée que l'app scanne
  et envoie. Le backend résout l'employé à partir de ce jeton.
- **Session de pointage** : un enregistrement `Attendance` = une arrivée + un départ.
  Le check-in crée la session (`check_out_time = null`, `is_open = true`), le check-out
  la clôture.
- **Contrainte anti-doublon (garantie backend)** :
  - impossible de pointer une **arrivée** si une session est déjà ouverte → `409`.
  - impossible de pointer un **départ** s'il n'y a aucune session ouverte → `409`.

  L'app mobile doit gérer ces `409` (voir §5).

---

## 3. Objets renvoyés

### Objet `Attendance`

```json
{
  "id": 8,
  "employee": { ... objet Employee ... },
  "check_in_time": "2026-07-06T15:57:18.215909Z",
  "check_out_time": null,
  "created_by": null,
  "updated_at": null,
  "updated_by": null,
  "is_open": true,
  "duration_seconds": null
}
```

| Champ | Type | Description |
|---|---|---|
| `id` | entier | Identifiant de la session de pointage |
| `employee` | objet `Employee` | Employé pointé |
| `check_in_time` | datetime | Horodatage de l'arrivée (auto) |
| `check_out_time` | datetime \| null | Horodatage du départ ; `null` si sur site |
| `created_by` | objet `Employee` \| null | Agent ayant enregistré l'**arrivée** (si authentifié) |
| `updated_at` | datetime \| null | Dernière modification (renseigné au départ) |
| `updated_by` | objet `Employee` \| null | Agent ayant enregistré le **départ** (si authentifié) |
| `is_open` | booléen | `true` = employé sur site (arrivée sans départ) |
| `duration_seconds` | entier \| null | Durée de la session en secondes ; `null` tant qu'ouverte |

### Objet `Employee`

```json
{
  "id": "7d2de01f-5470-4f53-b122-ce3a38a1e63d",
  "first_name": "Smoke",
  "last_name": "Test",
  "full_name": "Smoke Test",
  "telephone": "000",
  "email": "smoke@test.local"
}
```

| Champ | Type | Description |
|---|---|---|
| `id` | UUID (string) | Identifiant interne de l'employé |
| `first_name` / `last_name` | string | Prénom / nom |
| `full_name` | string | Nom complet (prérempli) |
| `telephone` | string | Téléphone |
| `email` | string | Email |

---

## 4. Endpoints

> **Toutes les routes ci-dessous exigent l'en-tête `Authorization: Token <jeton>`**
> (seul `POST /token/` en est dispensé). Sans jeton valide → `401 Unauthorized` :
> `{"detail": "Authentication credentials were not provided."}`.

### 4.0 Obtenir un jeton — `POST /attendance/api/v1/token/`

Endpoint **public**. Échange les identifiants de l'agent contre un jeton.

**Requête**

```json
{ "username": "agent_securite", "password": "••••••" }
```

**Réponse `200 OK`**

```json
{ "token": "9944b09199c62bcf9418ad8bf3f04d7fb46e29ff" }
```

**Erreur** — `400 Bad Request` si identifiants invalides :
`{"non_field_errors": ["Unable to log in with provided credentials."]}`.

```bash
curl -X POST https://<host>/attendance/api/v1/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "agent_securite", "password": "••••••"}'
```

---

### 4.1 Pointer une arrivée — `POST /attendance/check-in/`

Crée une nouvelle session de pointage pour l'employé associé au badge scanné.

**Requête**

```json
{ "badge_token": "un5kZ_ikDy6nOC6bIpSH3w" }
```

**Réponse `201 Created`** — l'objet `Attendance` créé :

```json
{
  "id": 8,
  "employee": {
    "id": "7d2de01f-5470-4f53-b122-ce3a38a1e63d",
    "first_name": "Smoke", "last_name": "Test", "full_name": "Smoke Test",
    "telephone": "000", "email": "smoke@test.local"
  },
  "check_in_time": "2026-07-06T15:57:18.215909Z",
  "check_out_time": null,
  "created_by": {
    "id": "b1a2...", "first_name": "Agent", "last_name": "Securite",
    "full_name": "Agent Securite", "telephone": "620000009", "email": "agent@marbika.local"
  },
  "updated_at": null,
  "updated_by": null,
  "is_open": true,
  "duration_seconds": null
}
```

> `created_by` = l'agent de sécurité authentifié qui a enregistré l'arrivée.

**Codes d'erreur**

| Statut | Corps | Cause |
|---|---|---|
| `401 Unauthorized` | `{"detail": "Authentication credentials were not provided."}` | Jeton absent/invalide |
| `409 Conflict` | `{"detail": "Cet employé a déjà pointé son arrivée. Il doit d'abord pointer son départ."}` | Une session est déjà ouverte |
| `400 Bad Request` | `{"badge_token": ["Badge inconnu."]}` | Jeton QR non reconnu |
| `400 Bad Request` | `{"badge_token": ["Employé désactivé."]}` | Compte employé inactif |
| `400 Bad Request` | `{"badge_token": ["..."]}` | `badge_token` manquant ou vide |

**Exemple**

```bash
curl -X POST https://<host>/attendance/api/v1/attendance/check-in/ \
  -H "Authorization: Token 9944b09199c62bcf9418ad8bf3f04d7fb46e29ff" \
  -H "Content-Type: application/json" \
  -d '{"badge_token": "un5kZ_ikDy6nOC6bIpSH3w"}'
```

---

### 4.2 Pointer un départ — `POST /attendance/check-out/`

Clôture la session ouverte de l'employé (renseigne `check_out_time`, `updated_at`,
`updated_by`).

**Requête**

```json
{ "badge_token": "un5kZ_ikDy6nOC6bIpSH3w" }
```

**Réponse `200 OK`** — l'objet `Attendance` clôturé :

```json
{
  "id": 8,
  "employee": {
    "id": "7d2de01f-5470-4f53-b122-ce3a38a1e63d",
    "first_name": "Smoke", "last_name": "Test", "full_name": "Smoke Test",
    "telephone": "000", "email": "smoke@test.local"
  },
  "check_in_time": "2026-07-06T15:57:18.215909Z",
  "check_out_time": "2026-07-06T18:30:02.360014Z",
  "created_by": { "full_name": "Agent Securite", "...": "..." },
  "updated_at": "2026-07-06T18:30:02.360014Z",
  "updated_by": { "full_name": "Agent Nuit", "...": "..." },
  "is_open": false,
  "duration_seconds": 9164
}
```

> `updated_by` = l'agent qui a enregistré le départ (peut différer de `created_by`,
> l'agent de l'arrivée). `duration_seconds` = durée de la session.

**Codes d'erreur**

| Statut | Corps | Cause |
|---|---|---|
| `401 Unauthorized` | `{"detail": "Authentication credentials were not provided."}` | Jeton absent/invalide |
| `409 Conflict` | `{"detail": "Aucun pointage d'arrivée en cours. L'employé doit d'abord pointer son arrivée."}` | Aucune session ouverte à clôturer |
| `400 Bad Request` | `{"badge_token": ["Badge inconnu."]}` | Jeton QR non reconnu |
| `400 Bad Request` | `{"badge_token": ["Employé désactivé."]}` | Compte employé inactif |

**Exemple**

```bash
curl -X POST https://<host>/attendance/api/v1/attendance/check-out/ \
  -H "Authorization: Token 9944b09199c62bcf9418ad8bf3f04d7fb46e29ff" \
  -H "Content-Type: application/json" \
  -d '{"badge_token": "un5kZ_ikDy6nOC6bIpSH3w"}'
```

---

### 4.3 État courant d'un employé — `GET /attendance/status/`

Indique si l'employé est actuellement **sur site** (session ouverte). Idéal juste
après le scan, pour afficher le bon bouton (Arrivée vs Départ).

**Paramètres de requête** (l'un des deux) :

| Paramètre | Description |
|---|---|
| `badge_token` | Jeton scanné (usage mobile) |
| `employee` | UUID de l'employé (usage interne / back-office) |

**Réponse `200 OK`**

```json
{
  "employee": "7d2de01f-5470-4f53-b122-ce3a38a1e63d",
  "on_site": true,
  "open_attendance": {
    "id": 8,
    "employee": { "id": "7d2de01f-...", "full_name": "Smoke Test", "...": "..." },
    "check_in_time": "2026-07-06T15:57:18.215909Z",
    "check_out_time": null,
    "is_open": true,
    "duration_seconds": null,
    "created_by": null, "updated_at": null, "updated_by": null
  }
}
```

- `on_site` : `true` si l'employé a une session ouverte, sinon `false`.
- `open_attendance` : l'objet `Attendance` ouvert, ou `null` si l'employé n'est pas sur site.

**Codes d'erreur**

| Statut | Corps | Cause |
|---|---|---|
| `404 Not Found` | `{"detail": "Badge inconnu."}` | `badge_token` non reconnu |
| `400 Bad Request` | `{"detail": "Fournir 'badge_token' (scan) ou 'employee'."}` | Aucun paramètre fourni |

**Exemple**

```bash
curl "https://<host>/attendance/api/v1/attendance/status/?badge_token=un5kZ_ikDy6nOC6bIpSH3w" \
  -H "Authorization: Token 9944b09199c62bcf9418ad8bf3f04d7fb46e29ff"
```

---

### 4.4 Historique — `GET /attendance/`

Liste des pointages, triés du plus récent au plus ancien (`check_in_time` décroissant).

**Filtres (query params, optionnels)**

| Paramètre | Description |
|---|---|
| `employee` | Filtre sur l'UUID d'un employé |
| `open` | `true` / `1` → seulement les sessions ouvertes (employés sur site) |

**Réponse `200 OK`** — tableau d'objets `Attendance` :

```json
[
  { "id": 8, "employee": { "...": "..." }, "check_in_time": "...", "is_open": false, "...": "..." },
  { "id": 7, "employee": { "...": "..." }, "check_in_time": "...", "is_open": true,  "...": "..." }
]
```

**Exemples**

```bash
# Tout l'historique d'un employé
curl "https://<host>/attendance/api/v1/attendance/?employee=7d2de01f-5470-4f53-b122-ce3a38a1e63d" \
  -H "Authorization: Token 9944b09199c62bcf9418ad8bf3f04d7fb46e29ff"

# Tous les employés actuellement sur site
curl "https://<host>/attendance/api/v1/attendance/?open=true" \
  -H "Authorization: Token 9944b09199c62bcf9418ad8bf3f04d7fb46e29ff"
```

---

### 4.5 Détail d'un pointage — `GET /attendance/{id}/`

**Réponse `200 OK`** : un objet `Attendance` (même structure que §3).
**`404 Not Found`** si l'`id` n'existe pas.

```bash
curl "https://<host>/attendance/api/v1/attendance/8/" \
  -H "Authorization: Token 9944b09199c62bcf9418ad8bf3f04d7fb46e29ff"
```

---

## 5. Flux mobile recommandé

1. **Connexion de l'agent** : `POST /token/` avec ses identifiants → stocker le jeton
   et l'envoyer dans l'en-tête `Authorization: Token <jeton>` de toutes les requêtes
   suivantes.
2. L'agent scanne le QR → on obtient le `badge_token`.
3. (Optionnel mais recommandé) `GET /status/?badge_token=<t>` :
   - `on_site = false` → afficher **« Pointer l'arrivée »** → `POST /check-in/`.
   - `on_site = true` → afficher **« Pointer le départ »** → `POST /check-out/`.
4. Toujours gérer les réponses :
   - `201` / `200` → succès, afficher l'employé (`employee.full_name`) et l'heure.
   - `401` → jeton absent/expiré/révoqué → rediriger vers la connexion (`/token/`).
   - `409` → l'action inverse a déjà été faite ; afficher le `detail` et proposer la bonne action.
   - `400` badge inconnu / désactivé → afficher le message, refuser le pointage.
   - `404` (status) → badge non reconnu.

> Il est possible d'appeler directement `check-in`/`check-out` sans passer par
> `status` : le backend garantit l'absence de doublon et renvoie un `409` explicite
> si l'action ne correspond pas à l'état courant.

---

## 6. Format des erreurs

Deux formes selon l'origine de l'erreur :

- **Validation de champ** (ex. badge) → clé = nom du champ :
  ```json
  { "badge_token": ["Badge inconnu."] }
  ```
- **Erreur métier / logique** → clé `detail` :
  ```json
  { "detail": "Cet employé a déjà pointé son arrivée. Il doit d'abord pointer son départ." }
  ```

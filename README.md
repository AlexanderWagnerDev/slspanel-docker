# SLSPanel 🎥

[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)](https://hub.docker.com/r/alexanderwagnerdev/slspanel)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

A modern web-based control panel for the IRL SLS live streaming server. Manage your streams, monitor players, and track statistics with an intuitive interface.

## ✨ Features

- 📺 **Stream Management** - View and control live streams and connected players
- 🔗 **Easy URL Access** - Publishing and playback URLs with one-click copy functionality
- 📊 **Real-Time Statistics** - Monitor bitrate, latency, and connection quality
- 🔐 **Optional Authentication** - Configurable admin login via environment variable
- ⚙️ **REST API Integration** - Seamless communication with SLS server
- 🐳 **Docker Ready** - Easy deployment with Docker Compose

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Running SLS (srt-live-server) instance
- SLS API key

### Installation with Docker Compose (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/AlexanderWagnerDev/slspanel-docker.git
cd slspanel-docker
```

2. Either copy `.env.example` to `.env` and edit it, or edit `docker-compose.yml` directly. The provided Compose file reads the variables from `.env` when present:
```yaml
environment:
  REQUIRE_LOGIN: "True"           # Enable/disable authentication
  USERNAME: "admin"               # Admin username
  PASSWORD: "supersecret"         # Admin password
  SLS_API_URL: "http://sls-api-url:8789"  # Hostname reachable from the container
  SLS_API_KEY: "your_api_key"     # Your SLS API key
  # ... more settings
```

When using `.env`, set `SLS_ADMIN_USERNAME` and `SLS_ADMIN_PASSWORD`; the Compose file maps them to the container's `USERNAME` and `PASSWORD`.

3. Start the container:
```bash
docker-compose up -d
```

4. Access the panel at `http://localhost:8000`

### Installation with Docker Run

For manual deployment:

```bash
docker run -d \
  --name slspanel \
  -e REQUIRE_LOGIN=True \
  -e USERNAME=admin \
  -e PASSWORD=supersecret \
  -e SLS_API_URL=http://sls-api-url:8789 \
  -e SLS_API_KEY=your_api_key \
  -e SLS_DOMAIN_IP=localhost \
  -e LANG=en \
  -e TZ=Europe/Vienna \
  -e SRT_PUBLISH_PORT=4001 \
  -e SRT_PLAYER_PORT=4000 \
  -e SRTLA_PUBLISH_PORT=5000 \
  -e SLS_STATS_PORT=8789 \
  -p 8000:8000/tcp \
  alexanderwagnerdev/slspanel:latest
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `REQUIRE_LOGIN` | Enable authentication (`True`/`False`) | `False` | No |
| `USERNAME` | Admin username | `admin` | If login enabled |
| `PASSWORD` | Admin password | - | If login enabled |
| `SLS_API_URL` | SLS server API endpoint | - | Yes |
| `SLS_API_KEY` | SLS API authentication key | - | Yes |
| `SLS_DOMAIN_IP` | Domain or IP for stream URLs | `localhost` | Yes |
| `LANG` | Interface language (`en`/`de`) | `en` | No |
| `TZ` | Timezone | `UTC` | No |
| `SRT_PUBLISH_PORT` | SRT publishing port | `4001` | Yes |
| `SRT_PLAYER_PORT` | SRT playback port | `4000` | Yes |
| `SRTLA_PUBLISH_PORT` | SRTLA publishing port | `5000` | Yes |
| `SLS_STATS_DOMAIN_IP` | Internal domain or IP used by the panel for statistics | `SLS_DOMAIN_IP` | No |
| `SLS_STATS_PUBLIC_DOMAIN_IP` | Public domain or IP used in copied statistics URLs | `SLS_STATS_DOMAIN_IP` | No |
| `SLS_STATS_SCHEME` | Scheme for statistics URLs (`http`/`https`) | `http` | No |
| `SLS_STATS_PORT` | SLS statistics port | `8789` | Yes |

When `REQUIRE_LOGIN=True`, `PASSWORD` must be non-empty and must not be the literal example password `password`. The container refuses to start otherwise. If an existing database still contains a superuser with the example password, startup also fails and asks the operator to change or deactivate that account; no account is modified automatically. Because the SQLite database is ephemeral, recreating the container also starts from a fresh database.

### Example Configuration

Minimal setup without authentication:
```yaml
environment:
  REQUIRE_LOGIN: "False"
  SLS_API_URL: "http://sls-server:8789"
  SLS_API_KEY: "myapikey123"
  SLS_DOMAIN_IP: "streaming.example.com"
```

## 🔧 Troubleshooting

### Cannot connect to SLS server
- Verify `SLS_API_URL` is correct and reachable from the container
- Use a hostname or IP reachable from the container; `localhost` inside the container is the panel container, not the Docker host
- Check if `SLS_API_KEY` matches your SLS configuration
- Ensure SLS server is running and API is enabled

### Login not working
- Verify `REQUIRE_LOGIN` is set to `True`
- Check `USERNAME` and `PASSWORD` are configured
- Clear browser cache and cookies

### View container logs
```bash
docker-compose logs -f slspanel
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Support

For questions, issues, or feature requests:
- Open an [issue on GitHub](https://github.com/AlexanderWagnerDev/slspanel-docker/issues)
- Check existing issues for solutions

## 🔗 Related Projects

- [SRTLA Server Docker](https://github.com/AlexanderWagnerDev/srtla-server-docker) - The streaming server this panel manages

---

# SLSPanel 🎥

*[Deutsche Version]*

[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)](https://hub.docker.com/r/alexanderwagnerdev/slspanel)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

Ein modernes webbasiertes Control Panel für den IRL SLS Live-Streaming-Server. Verwalte deine Streams, überwache Player und tracke Statistiken mit einer intuitiven Benutzeroberfläche.

## ✨ Features

- 📺 **Stream-Verwaltung** - Live-Streams und verbundene Player anzeigen und steuern
- 🔗 **Einfacher URL-Zugriff** - Publishing- und Playback-URLs mit Ein-Klick-Kopierfunktion
- 📊 **Echtzeit-Statistiken** - Bitrate, Latenz und Verbindungsqualität überwachen
- 🔐 **Optionale Authentifizierung** - Konfigurierbarer Admin-Login per Umgebungsvariable
- ⚙️ **REST-API-Integration** - Nahtlose Kommunikation mit dem SLS-Server
- 🐳 **Docker-Ready** - Einfaches Deployment mit Docker Compose

## 🚀 Schnellstart

### Voraussetzungen

- Docker und Docker Compose installiert
- Laufende SLS (srt-live-server) Instanz
- SLS API-Key

### Installation mit Docker Compose (Empfohlen)

1. Repository klonen:
```bash
git clone https://github.com/AlexanderWagnerDev/slspanel-docker.git
cd slspanel-docker
```

2. Entweder `.env.example` nach `.env` kopieren und bearbeiten oder `docker-compose.yml` direkt bearbeiten. Die mitgelieferte Compose-Datei liest die Variablen aus `.env`, falls vorhanden:
```yaml
environment:
  REQUIRE_LOGIN: "True"           # Authentifizierung aktivieren/deaktivieren
  USERNAME: "admin"               # Admin-Benutzername
  PASSWORD: "supersecret"         # Admin-Passwort
  SLS_API_URL: "http://sls-api-url:8789"  # Vom Container erreichbarer Hostname
  SLS_API_KEY: "your_api_key"     # Dein SLS API-Key
  # ... weitere Einstellungen
```

Bei Verwendung von `.env` `SLS_ADMIN_USERNAME` und `SLS_ADMIN_PASSWORD` setzen; die Compose-Datei überträgt sie auf `USERNAME` und `PASSWORD` des Containers.

3. Container starten:
```bash
docker-compose up -d
```

4. Panel unter `http://localhost:8000` aufrufen

### Installation mit Docker Run

Für manuelles Deployment:

```bash
docker run -d \
  --name slspanel \
  -e REQUIRE_LOGIN=True \
  -e USERNAME=admin \
  -e PASSWORD=supersecret \
  -e SLS_API_URL=http://sls-api-url:8789 \
  -e SLS_API_KEY=your_api_key \
  -e SLS_DOMAIN_IP=localhost \
  -e LANG=de \
  -e TZ=Europe/Vienna \
  -e SRT_PUBLISH_PORT=4001 \
  -e SRT_PLAYER_PORT=4000 \
  -e SRTLA_PUBLISH_PORT=5000 \
  -e SLS_STATS_PORT=8789 \
  -p 8000:8000/tcp \
  alexanderwagnerdev/slspanel:latest
```

## ⚙️ Konfiguration

### Umgebungsvariablen

| Variable | Beschreibung | Standard | Erforderlich |
|----------|--------------|----------|--------------|
| `REQUIRE_LOGIN` | Authentifizierung aktivieren (`True`/`False`) | `False` | Nein |
| `USERNAME` | Admin-Benutzername | `admin` | Bei Login |
| `PASSWORD` | Admin-Passwort | - | Bei Login |
| `SLS_API_URL` | SLS-Server API-Endpunkt | - | Ja |
| `SLS_API_KEY` | SLS API-Authentifizierungsschlüssel | - | Ja |
| `SLS_DOMAIN_IP` | Domain oder IP für Stream-URLs | `localhost` | Ja |
| `LANG` | Sprache der Oberfläche (`en`/`de`) | `en` | Nein |
| `TZ` | Zeitzone | `UTC` | Nein |
| `SRT_PUBLISH_PORT` | SRT Publishing-Port | `4001` | Ja |
| `SRT_PLAYER_PORT` | SRT Playback-Port | `4000` | Ja |
| `SRTLA_PUBLISH_PORT` | SRTLA Publishing-Port | `5000` | Ja |
| `SLS_STATS_DOMAIN_IP` | Interne Domain oder IP für Statistik-Aufrufe des Panels | `SLS_DOMAIN_IP` | Nein |
| `SLS_STATS_PUBLIC_DOMAIN_IP` | Öffentliche Domain oder IP in kopierten Statistik-URLs | `SLS_STATS_DOMAIN_IP` | Nein |
| `SLS_STATS_SCHEME` | Schema für Statistik-URLs (`http`/`https`) | `http` | Nein |
| `SLS_STATS_PORT` | SLS Statistik-Port | `8789` | Ja |

Wenn `REQUIRE_LOGIN=True` gesetzt ist, muss `PASSWORD` nicht leer und darf nicht das literale Beispielpasswort `password` sein. Der Container startet sonst nicht. Enthält eine bestehende Datenbank noch einen Superuser mit dem Beispielpasswort, schlägt der Start ebenfalls fehl und fordert den Betreiber auf, dieses Konto zu ändern oder zu deaktivieren; Konten werden nicht automatisch verändert. Da die SQLite-Datenbank ephemer ist, startet auch ein neu erstellter Container mit einer frischen Datenbank.

### Beispiel-Konfiguration

Minimale Einrichtung ohne Authentifizierung:
```yaml
environment:
  REQUIRE_LOGIN: "False"
  SLS_API_URL: "http://sls-server:8789"
  SLS_API_KEY: "myapikey123"
  SLS_DOMAIN_IP: "streaming.example.com"
```

## 🔧 Fehlerbehebung

### Verbindung zum SLS-Server nicht möglich
- Überprüfe, ob `SLS_API_URL` korrekt ist und vom Container aus erreichbar
- Prüfe, ob `SLS_API_KEY` mit deiner SLS-Konfiguration übereinstimmt
- Stelle sicher, dass der SLS-Server läuft und die API aktiviert ist

### Login funktioniert nicht
- Überprüfe, ob `REQUIRE_LOGIN` auf `True` gesetzt ist
- Prüfe, ob `USERNAME` und `PASSWORD` konfiguriert sind
- Lösche Browser-Cache und Cookies

### Container-Logs anzeigen
```bash
docker-compose logs -f slspanel
```

## 📝 Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert - siehe [LICENSE](LICENSE) Datei für Details.

## 🤝 Support

Für Fragen, Probleme oder Feature-Requests:
- Öffne ein [Issue auf GitHub](https://github.com/AlexanderWagnerDev/slspanel-docker/issues)
- Prüfe bestehende Issues für Lösungen

## 🔗 Verwandte Projekte

- [SRTLA Server Docker](https://github.com/AlexanderWagnerDev/srtla-server-docker) - Der Streaming-Server, den dieses Panel verwaltet
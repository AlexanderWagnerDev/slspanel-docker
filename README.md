# SLSPanel
SLSPanel is a web-based control panel for the IRL SLS live streaming server.
It allows managing streams, players, and statistics with optional admin login that can be enabled or disabled via environment variable.

## Features
• View and manage live streams and their players  
• Stream publishing and playback URLs with copy-to-clipboard functionality  
• Real-time streaming stats showing bitrate, latency, and connection quality  
• Optional admin login configurable via REQUIRE_LOGIN environment variable  
• Automated admin user creation via management command  
• REST API integration to communicate with the SLS server

## Installation with Docker
### Using docker-compose
The docker-compose.yml includes all environment variables for easy configuration. Change the values directly in docker-compose.yml before starting.  
```docker-compose up -d```    
The app will be accessible at http://localhost:8000.  

### Using docker run
You can also run the container manually with environment variables in the command:  
```
  docker run -d \
  -e REQUIRE_LOGIN=True \
  -e USERNAME=admin \
  -e PASSWORD=supersecret \
  -e SLS_API_URL=http://localhost:8789 \
  -e SLS_API_KEY=your_api_key \
  -e SLS_DOMAIN_IP=localhost \
  -e SLS_STATS_DOMAIN_IP=localhost \
  -e LANG=en \
  -e TZ=UTC \
  -e SRT_PUBLISH_PORT=4000 \
  -e SRT_PLAYER_PORT=4001 \
  -e SRTLA_PUBLISH_PORT=5000 \
  -e SLS_STATS_PORT=8789 \
  -p 8000:8000/tcp alexanderwagnerdev/slspanel:beta
```

## Configuration
• Control admin login behavior with the REQUIRE_LOGIN environment variable (True or False).  
• Set API URL, keys, stream server IP and Ports via environment variables.

## License
MIT License

## Support
For questions or issues, please open an issue on GitHub.

# Production deploy files
#
# Full new-user walkthrough: repository README.md → "Production deploy (Ubuntu VPS)".
#
#   deploy/nginx/gw.bobvolman.com.conf   TLS terminator → 127.0.0.1:8444 (API + /ws)
#   deploy/nginx/hud.example.conf        optional second vhost for the React HUD
#   deploy/fetch-models.sh               whisper.cpp small.en into the journal volume

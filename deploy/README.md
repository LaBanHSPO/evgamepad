# Production deploy files
#
# Full new-user walkthrough: repository README.md
#   - cTrader Open API registration
#   - Deploy the HUD on Vercel (free)
#   - Run the gateway with Docker (laptop or Ubuntu VPS)
#
#   deploy/nginx/gw.bobvolman.com.conf   TLS terminator → 127.0.0.1:8444 (API + /ws)
#   deploy/nginx/hud.example.conf        optional HUD vhost if you are not using Vercel
#   deploy/fetch-models.sh               whisper.cpp small.en into the journal volume

#для сброса всего и рестарта docker
docker compose down --remove-orphans
docker compose build --no-cache && docker compose run --rm strands-agent

#github commands
git status

git add .

git commit -m "feat: complete initial setup for Strands Agent and MCP integration"
git push origin main
docker rm -f $(docker ps -aq)
docker build --no-cache -t bench-metric .
docker run -d -p 8501:8501 bench-metric
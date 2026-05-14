import requests

tmdb_session = requests.Session()
tmdb_session.headers.update({
    "Accept": "application/json",
})
import json
import requests
from kafka import KafkaProducer

from dotenv import load_dotenv
import os

load_dotenv()

producer = KafkaProducer(bootstrap_servers=['localhost:9094'])


gh_headers = {"Accept":"application/vnd.github+json",
              "Authorization":"Bearer"+os.getenv("GITHUB_BEARER"),
              "X-GitHub-Api-Version":"2022-11-28",
              "per_page":"100"}

while True:
    page = 1
    response = requests.get(f"https://api.github.com/events?page={page}", headers=gh_headers)
    while 'next' in response.links.keys():
        print(page)
        page+=1
        events = response.json()
        for event in events:
            data = json.dumps(event, default=str).encode("utf-8")
            producer.send(topic="events", value=data)

        

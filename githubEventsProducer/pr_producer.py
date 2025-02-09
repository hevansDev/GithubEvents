#!/usr/bin/env python

import json

from random import choice
from confluent_kafka import Producer

from github import Github, Auth

from dotenv import load_dotenv
import os

load_dotenv()

bootstrap_servers = os.getenv("BOOTSTRAP_SERVERS")
sasl_username = os.getenv("SASL_USERNAME")
sasl_password = os.getenv("SASL_PASSWORD")
ssl_ca_location = os.getenv("SSL_CA_LOCATION")
client_id = os.getenv("CLIENT_ID")
github_auth = os.getenv("GITHUB_AUTH")

config = {
    # User-specific properties that you must set
    "bootstrap.servers": bootstrap_servers,
    "security.protocol": "SASL_SSL",
    "sasl.mechanisms": "PLAIN",
    "sasl.username": sasl_username,
    "sasl.password": sasl_password,
    "ssl.endpoint.identification.algorithm": "none",
    "ssl.ca.location": ssl_ca_location,

    # Best practice for higher availability in librdkafka clients prior to 1.7
    "session.timeout.ms": 45000,

    "client.id": client_id,

    # Fixed properties
    "acks": "all"
}

# Create Producer instance
producer = Producer(config)

# Optional per-message delivery callback (triggered by poll() or flush())
# when a message has been successfully delivered or permanently
# failed delivery (after retries).
def delivery_callback(err, msg):
    if err:
        print('ERROR: Message failed delivery: {}'.format(err))
    else:
        print("Produced event to topic {topic}: key = {key:12} value = {value:12}".format(
            topic=msg.topic(), key=msg.key().decode('utf-8'), value=msg.value().decode('utf-8')))

# Produce data by selecting random values from these lists.
topic = "github-repo-topic"

# using an access token
auth = Auth.Token(github_auth)

topic="github-pr-topic"

# Public Web Github
g = Github(auth=auth)

user = g.get_user("eleanorTurinTech")

for repo in user.get_repos():
    if repo.fork:
        # Get the parent (original) repository
        parent_repo = repo.parent
        print(f"\nRepository: {repo.name}")
        print(f"Original Repository: {parent_repo.full_name}")
        
        query = f"is:pr author:eleanorTurinTech repo:{parent_repo.full_name}"
        pulls = g.search_issues(query)

        for pull in pulls:
            print(f"PR #{pull.number}: {pull.title}")
            print(f"Status: {pull.state}")
            print(f"URL: {pull.html_url}")
            pr_json = {"name":repo.name, "pr_number":pull.number, "title":pull.title, "state":pull.state, "url":pull.html_url}
            try:
                # Add a key when producing the message
                producer.produce(
                    topic=topic,
                    key=str(pull.number),  # Add a key (converted to string)
                    value=json.dumps(pr_json).encode('utf-8'), 
                    callback=delivery_callback
                )
            except Exception as e:
                print(f"An error occurred: {e}")

# Block until the messages are sent.
producer.poll(10000)
producer.flush()
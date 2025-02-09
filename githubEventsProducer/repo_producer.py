#!/usr/bin/env python

import json
from confluent_kafka import Producer
from github import Github, Auth
from dotenv import load_dotenv
import os

load_dotenv()

# Environment variables setup
bootstrap_servers = os.getenv("BOOTSTRAP_SERVERS")
sasl_username = os.getenv("SASL_USERNAME")
sasl_password = os.getenv("SASL_PASSWORD")
ssl_ca_location = os.getenv("SSL_CA_LOCATION")
client_id = os.getenv("CLIENT_ID")
github_auth = os.getenv("GITHUB_AUTH")

# Kafka configuration
config = {
    "bootstrap.servers": bootstrap_servers,
    "security.protocol": "SASL_SSL",
    "sasl.mechanisms": "PLAIN",
    "sasl.username": sasl_username,
    "sasl.password": sasl_password,
    "ssl.endpoint.identification.algorithm": "none",
    "ssl.ca.location": ssl_ca_location,
    "session.timeout.ms": 45000,
    "client.id": client_id,
    "acks": "all"
}

producer = Producer(config)

def delivery_callback(err, msg):
    if err:
        print('ERROR: Message failed delivery: {}'.format(err))
    else:
        # Only decode the value since we're not sending a key
        print("Produced event to topic {topic}: value = {value}".format(
            topic=msg.topic(), 
            value=msg.value().decode('utf-8')))

topic = "github-repo-topic"

# Initialize Github client
g = Github(auth=Auth.Token(github_auth))

try:
    # Search for repositories, sorted by stars in descending order
    # This is more efficient than iterating through all users
    repos = g.search_repositories(query='stars:>1', sort='stars', order='desc')
    
    # Get the first 1000 repositories
    count = 0
    for repo in repos:
        if count >= 10000:
            break
            
        try:
            repo_json = repo.raw_data
            
            # Get open issues
            #issues = repo.get_issues(state='open')
            #issues_json = [issue.raw_data for issue in issues]
            #repo_json["issues"] = issues_json
            
            # Produce message to Kafka with a key
            producer.produce(
                topic, 
                key=str(repo.id).encode('utf-8'),  # Add a key
                value=json.dumps(repo_json).encode('utf-8'), 
                callback=delivery_callback
            )
            
            # Poll to handle delivery reports
            producer.poll(0)
            
            count += 1
            
            if count % 100 == 0:
                print(f"Processed {count} repositories")
                
        except Exception as e:
            print(f"Error processing repository {repo.full_name}: {e}")
            continue

except Exception as e:
    print(f"An error occurred: {e}")
finally:
    # Ensure all messages are delivered
    producer.flush()

print(f"Successfully processed {count} repositories")
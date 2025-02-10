#!/usr/bin/env python

import time
import uuid
from datetime import datetime, timezone
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

def produce_with_timestamp(producer, topic, key, value):
    # Get current timestamp in milliseconds
    timestamp_ms = int(time.time() * 1000)
    
    producer.produce(
        topic=topic,
        key=key.encode('utf-8'),
        value=value.encode('utf-8'),
        timestamp=timestamp_ms,  # Add explicit timestamp
        callback=delivery_callback
    )

try:
    # Search for repositories, sorted by stars in descending order
    repos = g.search_repositories(query='stars:>1', sort='stars', order='desc')
    
    # Get the first 1000 repositories
    count = 0
    for repo in repos:
        if count >= 10000:
            break
            
        try:
            repo_json = repo.raw_data
            
            # Add timestamp to the data itself
            current_time = datetime.now(timezone.utc)
            repo_json['producer_timestamp'] = datetime.now(timezone.utc).isoformat()

            # Create a unique key combining repo id and timestamp
            unique_key = "{}_{}_{}".format(
                repo.id,
                int(time.time() * 1000),
                str(uuid.uuid4())
            )
            
            producer.produce(
                topic=topic,
                key=unique_key.encode('utf-8'),  # Using unique key
                value=json.dumps(repo_json).encode('utf-8'), 
                timestamp=int(current_time.timestamp() * 1000),
                callback=delivery_callback
            )
            
            # Add a small delay between messages
            time.sleep(0.1)  # 100ms delay
            
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
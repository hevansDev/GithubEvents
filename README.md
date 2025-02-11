# GitHub Events

I built this project to assist me in my work as a Community Solution Engineer at [TurinTech](https://www.turintech.ai/) by making it easier to research popular repos on GitHub and to report on OKRs.

This project consists of dashboards for visualizing GitHub event data (popular repos, individual repo stats, and PRs from the [eleanorTurintech](https://github.com/eleanorTurintech)) and the associated infrastructure for collecting and serving this data.

## Setup

```bash
git clone https://github.com/hevansDev/GithubEvents.git
```

Run the docker compose to deploy Druid and Grafana.

```bash
docker compose up -d
```

Create a new virtual environment inside the `githubEventsProducer` directory and install Python dependencies.

```bash
cd githubEventsProducer
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install requirement.txt
```

Create a Kafka Broker with the following topics (for example via [Confluent Cloud](https://www.confluent.io/lp/confluent-cloud)): `github-pr-topic`, `github-repo-topic`.

Create a `.env` with the details of your Kafka broker and a [Github auth token] for accessing the GitHub API.

```bash
vi .env
```

```bash
BOOTSTRAP_SERVERS=""
SASL_USERNAME=""
SASL_PASSWORD=""
SSL_CA_LOCATION="/opt/homebrew/etc/openssl@3/cert.pem" #Update to match your OS
GITHUB_AUTH=""
CLIENT_ID=""
```

Create two new cron jobs to run both of the producers once an hour (or more frequently if you prefer).

```bash
sudo crontab -e
```

```bash
0 * * * * /path/to/github-events/githubEventsProducer/.venv/bin/python3 /path/to/github-events/githubEventsProducer/pr_producer.py
0 * * * * /path/to/github-events/githubEventsProducer/.venv/bin/python3 /path/to/github-events/githubEventsProducer/repo_producer.py
```

Add two new data sources to Druid, one for each topic with default settings. Set bootstrap server, topic name, and the following Kafka consumer config (with your own relevant details):

```bash
{
  "bootstrap.servers": "<bootstrap server>",
  "security.protocol": "SASL_SSL",
  "sasl.mechanism": "PLAIN",
  "sasl.jaas.config": "org.apache.kafka.common.security.plain.PlainLoginModule  required username=\"<username>\" password=\"<password>";"
}
```

## Usage

[View Dashboards](http://localhost:3000/) (password and username are both `druid`)

[View Druid Console](https://localhost:8888/)


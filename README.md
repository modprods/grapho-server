# grapho-server

Grapho server by Mod\
https://mod.studio

## Overview

This is a lightweight reference API server for the Grapho data science + storytelling toolkit
https://grapho.app

## Features

* REST API endpoints for graph database queries including
    * all - load editorially curated paths through Neo4j database
    * game - load complete graph perspective for offline use
    * neighbours - load nodes a set distance from given node
* OpenAPI compliant documentation
    * e.g. https://demo.grapho.app/docs

## Requirements

Neo4J 4.4 or above

python
    python 3.7 or above
    pipenv 

Tested on Debian 9.5, Debian 11.3

## Quickstart

```
    git clone <repos URL>
    cd grapho-server
    pipenv shell
    pipenv install
    cp env.sample .env
```
Edit .env to match your environment settings
```
    python api.py
```
Server will be available at http://0.0.0.0:5042

Once you have your graph database set up you can amend the test_api.py file with your own test coverage

```
    pytest
```

NOTE test suite uses the same server and database atm

## Environment settings
```
# Neo4J FQHN
NEO4J_HOST = "host.docker.internal"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "<INSERT PASSWORD>"
NEO4J_PORT_HTTP = 7474
NEO4J_PORT_BOLT = 7687
# uncomment next line to ignore dynamic db parameter and hardcode this
#NEO4J_DATABASE = "neo4j"
PUBLIC_URL = "http://<IP>:5042"
QUERY_LIMIT = 300
INCLUDE_FIXED_QUERIES = False
```
## Fixed Queries

Fixed Queries aka "API Handles" that do not require parameters can be hardcoded in the server as an array of dicts.

Grapho supports Handles stored in the grapho database, in the API (this), in the Grapho client (Unreal Engine) map, and in the overall (Unreal Engine) Project

NOTE Fixed Queries can reference server environment variables so make sure these are not commented out if needed

e.g. in the following fixed query, PUBLIC_URL and NEO4J_DATABASE are required

```
FIXED_QUERIES = [
    {
        "url": '{0}/asn_by_country/{1}/FJ'.format(
    PUBLIC_URL, NEO4J_DATABASE),
        "label": 'ASNs in Fiji',
        "slug": 'asn_fj'
    },
]
```
## Docker container

Use the provided Docker file to build and run your own containers

Run Docker Desktop (for your platform, tested on Docker Desktop for Windows)

```
git clone <repos URL>
cd grapho-server
docker build -t grapho-server .
docker run -p 5042:5042 -it grapho-server bash
```

Open a Terminal (the Exec fab in Docker Desktop)
Install your preferred text editor (or use vi)

```
vi .env
```

Edit your environment settings

```
pipenv run python api.py
```

In your host browser, go to URL specified as PUBLIC_URL

## Grapho XR notes

Add your server PUBLIC_URL to Settings | Base | API ROOT URL

Any databases your Neo4j account has access to should then be selectable under the drop-down menu

If your API uses the insecure defaults provided here (e.g. http not https), you may need to first approve links in on-device (e.g. Meta Quest Browser).

## Production notes

This is a reference implementation without enterprise security considerations.

It is expected that you would run this behind a firewall and web service (e.g. nginx) with your own certificate and authentication mechanism for greater security.

## Further documentation

See https://docs.grapho.app

Grapho licensees, see your Rack&Pin documentation for further detail

(C) 2025 Mod Productions Pty Ltd

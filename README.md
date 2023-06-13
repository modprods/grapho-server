# grapho-server

Grapho server by Mod\
https://mod.studio

## Overview

This is a lightweight reference API server for the Grapho spatial visualisation tool
https://grapho.app

## Features

* OpenAPI compliant documentation
* REST API endpoints for graph database queries

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
## Environment settings
```
NEO4J_HOST = "neo4j-server.domain"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "neo4j"
NEO4J_PORT_HTTP = 443
NEO4J_PORT_BOLT = 7687
NEO4J_DATABASE = "neo4j"
PUBLIC_URL = "https://api.grapho.app"
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

## Further documentation

Grapho licensees, see your Rack&Pin documentation for further detail


(C) 2023 Mod Productions Pty Ltd

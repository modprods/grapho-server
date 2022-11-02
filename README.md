# grapho-server

Grapho server by Mod\
https://mod.studio

## Overview

This is a lightweight reference API server for the Grapho XR mechanic for interacting with knowledge graphs.

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

    git clone <repos URL>
    cd grapho-server
    pipenv shell
    pipenv install
    cp env.sample .env

Edit .env to match your environment settings

    python api.py

Server will be available at http://0.0.0.0:5042

## Further documentation

See provided production documentation for further detail

e.g.

    http://<production>.rackandpin.com/wiki/OperationsGuide#APIserver

(C) 2022 Mod Productions Pty Ltd

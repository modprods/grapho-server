import json
import urllib.parse

import graphene
import requests
import responder
from dotenv import load_dotenv
from marshmallow import Schema, fields
from requests.auth import HTTPBasicAuth
from starlette.responses import PlainTextResponse, RedirectResponse
import httpx

load_dotenv(verbose=True,override=True)
import logging
import os
import time

#from py2neo import Graph
from query import GraphQuery
from tools import generate_grapho_id

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)

# create formatter - simple or more detail as required
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
formatter = logging.Formatter('%(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)
logger.propagate = False

from pathlib import Path

NEO4J_HOST = os.getenv('NEO4J_HOST')
NEO4J_USER = os.getenv('NEO4J_USER')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')
NEO4J_PORT_HTTP = os.getenv('NEO4J_PORT_HTTP')
NEO4J_PORT_BOLT = os.getenv('NEO4J_PORT_BOLT')
NEO4J_DATABASE = os.getenv('NEO4J_DATABASE')
logger.debug(f"NEO4J_DATABASE is {NEO4J_DATABASE}")
PUBLIC_URL = os.getenv('PUBLIC_URL')
QUERY_LIMIT = os.getenv('QUERY_LIMIT')
INCLUDE_FIXED_QUERIES = eval(os.getenv('INCLUDE_FIXED_QUERIES',"False"))

INCLUDE_ADDITIONAL_DIALOGUE = eval(os.getenv('INCLUDE_ADDITIONAL_DIALOGUE',"False"))

LOG_LEVEL = os.getenv('LOG_LEVEL')
if LOG_LEVEL == "DEBUG":
    logger.setLevel(logging.DEBUG)
    ch.setLevel(logging.DEBUG)

# Fixed Queries are hardcoded here - aka "API Handles" that do not require parameters
# Grapho supports Handles stored in DB, API, UE Map, and overall Project 

FIXED_QUERIES = [
    # {
    #     "url": '{0}/top_betweenness/10'.format(
    # PUBLIC_URL),
    #     "label": 'Top Betweenness',
    #     "slug": 'top_betweenness'
    # },
    {
        "url": '{0}/up_next'.format(
    PUBLIC_URL),
        "label": 'Up Next',
        "slug": 'Up Next'
    }

    # {
    #     "url": '{0}/top_node_similarity/10'.format(
    # PUBLIC_URL),
    #     "label": 'Top Similarity',
    #     "slug": 'top_similarity'
    # },
]

# logger.info(type(INCLUDE_FIXED_QUERIES))

API_TITLE = "Grapho API"
API_AUTHOR = "Michela Ledwidge"
API_PUBLISHER = "Mod Productions Pty Ltd."
API_COPYRIGHT = "All Rights Reserved"
API_VERSION = "1.5"

logger.info(f"{API_TITLE} v{API_VERSION} for Neo4j user {NEO4J_USER}")
logger.debug(f"INCLUDE_FIXED_QUERIES is {INCLUDE_FIXED_QUERIES}")

if int(NEO4J_PORT_HTTP) == 7474:
    NEO4J_API = f"neo4j://{NEO4J_HOST}:{NEO4J_PORT_BOLT}"
    logger.info(f"dev API instance\n{NEO4J_API}")
else:
    NEO4J_API = f"neo4j+s://{NEO4J_HOST}:{NEO4J_PORT_BOLT}"
    logger.info(f"live API instance\n{NEO4J_API}")

api = responder.API(title=API_TITLE, enable_hsts=False, version=API_VERSION, openapi="3.0.0", docs_route="/docs", cors=True, cors_params={"allow_origins":["*"]})


@api.schema("PageSchema")

class PageSchema(Schema):
    id = fields.Integer()
    label = fields.Str()
    source = fields.Str()
    source_url = fields.URL()
    image_url = fields.URL()
    video_url = fields.URL()
    archive_url = fields.URL()
    archive_date = fields.DateTime()

class Query(graphene.ObjectType):
    hello = graphene.String(name=graphene.String(default_value="stranger"))

    def resolve_hello(self, info, name):
        return f"Hello {name}"

schema = graphene.Schema(query=Query)
# view = GraphQLView(api=api, schema=schema)

# api.add_route("/graph", view)

pages = []

@api.route("/")
def hello_world(req, resp):
    resp.content = api.template('index.html', who="")

@api.route("/hello/{who}/html")
def hello_html(req, resp, *, who):
    resp.content = api.template('index.html', who=who)

@api.schema("HandleSchema")

class HandleSchema(Schema):
    id = fields.Integer()
    start_id = fields.Float()
    label = fields.Str()

async def fetch_url(client, url):
    logger.error(url)
    response = await client.get(url)
    return response.json()

async def fetch_all(urls):
    logger.error(urls)
    async with httpx.AsyncClient() as client:
        tasks = [fetch_url(client, url) for url in urls]
        results = await asyncio.gather(*tasks)
        return results

@api.route("/all/{db}")
async def api_all_database(req,resp,*,db):
    """All data for experience. Selection of database slug in API
    ---
    get:
        summary: All handles and fixed queries 
        description: Respond with all Handle nodes saved in database along with any fixed or parameterised queries hardcoded in API
        responses:
            200:
                description: Respond with all feed values required for experience
            503:
                description: Temporary service issue. Try again later
        parameters:
             - in: path
               name: db
               required: true
               schema:
                type: string
                minimum: 1
                default: neo4j
               description: The database name
    """
#    resp.status_code = api.status_codes.HTTP_302
#    resp.headers['Location'] = '/static/test.json'
    graphs = []
    DATABASE = db
    # LOD sets default number of neighbours to include in handles
    lod = 1 # default is 1
   # if DATABASE == 'groove':
   #     lod = 2
    handles_request = '{0}/handles/{1}'.format(PUBLIC_URL,DATABASE)
    logger.debug(f'Handles API request: {handles_request}')
    async with httpx.AsyncClient() as client:
        handles = await client.get(handles_request)
    # handle_requests = []
    try:
        for handle in handles.json()['results'][0]['data'][0]['graph']['nodes']:
            logger.debug(handle)
            try:
                label = handle['properties']['label']
            except KeyError as e:
                logger.error("TODO - fix dependency on label property")
                label = handle['properties']['name']
            try:
                handle_id = int(handle['id'])
                logger.warning(f"Neo4j integer id deprecated - need to change to string: {handle_id}")
                handle_request = '{0}/handle/{1}/{2}/{3}'.format(
            PUBLIC_URL, DATABASE,handle_id,lod)
                # r = requests.get(handle_request)
                # refactor for async
                # handle_requests.append(handle_request)
                async with httpx.AsyncClient() as client2:
                    r = await client2.get(handle_request)
            except ValueError as ex:
                handle_id = handle['id']
                template = "An exception of type {0} occurred. Arguments:\n{1!r}"
                message = template.format(type(ex).__name__, ex.args)
                logger.error(message)
                logger.error(f"Neo4j 5 new id detected: {handle_id} - not ready to support yet")
                handle_request = '{0}/handle'.format(
            PUBLIC_URL)
                logger.debug(f'Label: {label}')
                logger.debug(f'Id: {handle_id}')
                logger.debug(handle_request)
                r = requests.post(handle_request,json=handle_data)
            g = r.json()['results'][0]['data'][0]['graph']
            g['handle_id'] = handle_id
            graphs.append(g)
    except Exception as ex:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(ex).__name__, ex.args)
        logger.warning(message)
        resp.status_code = api.status_codes.HTTP_503
        data = dict(
            message="Invalid API request",
            error_code=503
        )
        resp.media = data
        return 
    handle_node_id = 100000 # HACK - instead of using DB generated id, create one for handles - DANGEROUS\
    handle_relationship_id = 200000  
    if INCLUDE_FIXED_QUERIES: # ??? WHY not just if INCLUDE_FIXED_QUERIES
        for f in FIXED_QUERIES:
            handle_node_id = handle_node_id + 1
            handle_relationship_id = handle_relationship_id + 1
            logger.debug(f['url'])
            r = requests.get(f["url"])
            g = {}
            nodes = []
            relationships = []
            try:
                for subgraph in r.json()['results'][0]['data']:
                    for n in subgraph['graph']['nodes']:
                        nodes.append(n)
                    for r in subgraph['graph']['relationships']:
                        relationships.append(r)
                handle_node = dict(
                        id=handle_node_id,
                        labels = ["Handle"],
                        properties= {
                            "label": f["label"],
                            "slug": f["slug"]
                        }
                )
                nodes.append(handle_node)
                g["nodes"] = nodes
                handle_relationship = dict(
                        id=handle_relationship_id,
                        type="NEXT",
                        startNode=handle_node_id,
                        endNode=nodes[0]['id'],
                        properties= {
                        }
                )
                relationships.append(handle_relationship)
                g["relationships"] = relationships
                g["handle_id"] = handle_node_id
                graphs.append(g)
            except TypeError:
                logger.warning(f"Fixed Query error for {f['url']} - no 'results'")
                try:
                    if 'node' in r.json()[0]:
                        logger.debug("Try to parse as GDS result")
                        for subgraph in r.json():
                            nodes.append(subgraph['node'])
                        # TODO fix break of DRY
                        handle_node = dict(
                                id=handle_node_id,
                                labels = ["Handle"],
                                properties= {
                                    "label": f["label"],
                                    "slug": f["slug"]
                                }
                        )
                        nodes.append(handle_node)
                        g["nodes"] = nodes
                        handle_relationship = dict(
                                id=handle_relationship_id,
                                type="NEXT",
                                startNode=str(handle_node_id),
                                endNode=str(nodes[0]['id']),
                                properties= {
                                }
                        )
                        relationships.append(handle_relationship)
                        g["relationships"] = relationships
                        g["handle_id"] = handle_node_id
                        graphs.append(g)
                except TypeError:
                    logger.warning(f"Fixed Query error for {f['url']} - no 'node' (GDS) format")

    if INCLUDE_ADDITIONAL_DIALOGUE:
        dialogue = requests.get('{0}/dialogue/{1}'.format(PUBLIC_URL,DATABASE))
        additional_dialogue=dialogue.json()['results'][0]['data'][0]['graph']['nodes']
    else:
        additional_dialogue = []
    data = dict(
        author=API_AUTHOR,
        database=DATABASE,
        url=PUBLIC_URL,
        publisher=API_PUBLISHER,
        copyright=API_COPYRIGHT,
        graphs=graphs,
        additional_dialogue=additional_dialogue
    )
    resp.media = data

@api.route("/node/schema/{db}")
def api_node_schema(req,resp,*, db):
    """Return schema for database nodes
    ---
    get:
        summary: Respond with schema for database nodes
        description: Respond with schema for database nodes
        parameters:
         - in: path
           name: db
           required: true
           schema:
            type: string
            minimum: 1
            default: apnic
           description: The database name                 
        responses:
            200:
                description: Respond with all feed values required for experience
            503:
                description: Temporary service issue. Try again later
    """
    DATABASE = db
    query = f"\
CALL apoc.meta.schema() yield value{chr(10)}\
UNWIND apoc.map.sortedProperties(value) as labelData{chr(10)}\
WITH labelData[0] as label, labelData[1] as data{chr(10)}\
WHERE data.type = 'node'{chr(10)}\
UNWIND apoc.map.sortedProperties(data.properties) as property{chr(10)}\
WITH label, property[0] as property, property[1] as propData{chr(10)}\
RETURN label,{chr(10)}\
property,{chr(10)}\
propData.type as type,{chr(10)}\
propData.indexed as isIndexed,{chr(10)}\
propData.unique as uniqueConstraint,{chr(10)}\
propData.existence as existenceConstraint"

    try:
        q = GraphQuery(NEO4J_API, NEO4J_USER, NEO4J_PASSWORD,req, db)
        graph = q.run(query,False)
        # logger.debug(graph)
        resp.media = json.loads(graph)
        resp.status_code = api.status_codes.HTTP_200 
    except:
        resp.status_code = api.status_codes.HTTP_503    

@api.route("/rel/schema/{db}")
def api_rel_schema(req,resp,*, db):
    """Return schema for database relationships
    ---
    get:
        summary: Respond with schema for database relationships
        description: Respond with schema for database relationships
        parameters:
         - in: path
           name: db
           required: true
           schema:
            type: string
            minimum: 1
            default: apnic
           description: The database name                 
        responses:
            200:
                description: Respond with all feed values required for experience
            503:
                description: Temporary service issue. Try again later
    """
    DATABASE = db
    endpoint = f'{NEO4J_API}/{DATABASE}/tx'
    query = f"\
CALL apoc.meta.schema() yield value{chr(10)}\
UNWIND apoc.map.sortedProperties(value) as labelData{chr(10)}\
WITH labelData[0] as label, labelData[1] as data{chr(10)}\
WHERE data.type = 'relationship'{chr(10)}\
UNWIND apoc.map.sortedProperties(data.properties) as property{chr(10)}\
WITH label, property[0] as property, property[1] as propData{chr(10)}\
RETURN label,{chr(10)}\
property,{chr(10)}\
propData.type as type,{chr(10)}\
propData.indexed as isIndexed,{chr(10)}\
propData.unique as uniqueConstraint,{chr(10)}\
propData.existence as existenceConstraint"
    try:
        q = GraphQuery(NEO4J_API, NEO4J_USER, NEO4J_PASSWORD,req, db)
        graph = q.run(query,False)
        # logger.debug(graph)
        resp.media = json.loads(graph)
        resp.status_code = api.status_codes.HTTP_200 
    except:
        resp.status_code = api.status_codes.HTTP_503 

@api.route("/neighbours/{db}/{node_id}/{distance}")
async def api_neighbours(req,resp,*, db, node_id, distance):
    """Subgraph comprising neighbours of specified node.
    ---
    get:
        summary: Node neighbours
        description: Respond with all feed values required for subgraph comprising neighbours of specified node.
        parameters:
         - in: path
           name: db
           required: true
           schema:
            type: string
            minimum: 1
            default: apnic
           description: The database name
         - in: path
           name: node_id
           required: true
           schema:
            type: integer
            minimum: 0
            default: 1000
           description: The node ID (e.g. 1000)
         - in: path
           name: distance
           required: true
           schema:
            type: integer
            minimum: 1
            default: 1
           description: Distance of neighbours to node_id                    
        responses:
            200:
                description: Respond with all feed values required for experience
            503:
                description: Temporary service issue. Try again later
    """
    DATABASE = db
    endpoint = f'{NEO4J_API}/{DATABASE}/tx'
    distance=int(distance)
    assert(1 <= distance <= 2)  
    query = f"\
MATCH (a)-[r*0..{distance}]-(neighbour){chr(10)}\
WHERE id(a) = {node_id} AND NOT neighbour:Handle{chr(10)}\
RETURN collect(distinct(neighbour)),r{chr(10)}\
LIMIT {QUERY_LIMIT}"
    logger.debug(query)
    try:
        q = GraphQuery(NEO4J_API, NEO4J_USER, NEO4J_PASSWORD,req, db)
        graph = q.run(query)
        # logger.debug(graph)
        resp.media = json.loads(graph)
        resp.status_code = api.status_codes.HTTP_200 
    except Exception as e:
        logger.error(e)
        resp.status_code = api.status_codes.HTTP_503
    q.close()

@api.route("/dialogue/{db}")
def api_dialogue(req,resp,*, db):
    """Subgraph comprising additional dialogue.
    ---
    get:
        summary: Dialogue nodes
        description: Dialogue specific nodes only.
        parameters:
         - in: path
           name: db
           required: true
           schema:
            type: string
            minimum: 1
            default: apnic
           description: The database name
        responses:
            200:
                description: Respond with all feed values required for experience
            503:
                description: Temporary service issue. Try again later
    """
    DATABASE = db
    endpoint = f'{NEO4J_API}/{DATABASE}/tx' 
    query = f"\
MATCH (a:Dialogue)\
RETURN a \
LIMIT {QUERY_LIMIT}"
    logger.debug(query)
    try:
        q = GraphQuery(NEO4J_API, NEO4J_USER, NEO4J_PASSWORD,req, db)
        graph = q.run(query)
        # logger.debug(graph)
        resp.media = json.loads(graph)
        resp.status_code = api.status_codes.HTTP_200 
    except Exception as e:
        logger.error(e)
        resp.status_code = api.status_codes.HTTP_503
    q.close()

@api.route("/game/{db}")
def api_game(req,resp,*, db):
    """Subgraph intended for use in game engine.
    ---
    get:
        summary: Game dataset
        description: Returns entire graph for offline use - USE WITH CARE!
        parameters:
         - in: path
           name: db
           required: true
           schema:
            type: string
            minimum: 1
            default: groove
           description: The database name
        responses:
            200:
                description: Respond with all feed values required for experience
            503:
                description: Temporary service issue. Try again later
    """
    DATABASE = db
    endpoint = f'{NEO4J_API}/{DATABASE}/tx' 
    query = f"""
MATCH (n)
WHERE NOT 'Term' IN labels(n) AND
NOT '_Bloom_Scene_' IN labels(n) AND
NOT '_Bloom_Perspective_' IN labels(n)
OPTIONAL MATCH (n)-[r]-(x)
RETURN n,r
"""
    logger.debug(query)
    try:
        q = GraphQuery(NEO4J_API, NEO4J_USER, NEO4J_PASSWORD,req, db)
        graph = q.run(query)
        # logger.debug(graph)
        resp.media = json.loads(graph)
        resp.status_code = api.status_codes.HTTP_200 
    except Exception as e:
        logger.error(e)
        resp.status_code = api.status_codes.HTTP_503
    q.close()

# @api.route("/ipv4/{db}/{addr}/{length}")
def api_ipv4(req,resp,*, db, addr,length):
    """Subgraph showing all about an IPv4 address.
    ---
    get:
        summary: All about IPv4
        description: Respond with all feed values required for subgraph showing all about an IPv4 address. given ID and LOD. LOD0 is curated path. LOD1 is path and all nodes within 1 node radius of path. LOD2 is path and all nodes within 2 node radius.
        parameters:
         - in: path
           name: db
           required: true
           schema:
            type: string
            minimum: 1
            default: neo4j
           description: The database name
         - in: path
           name: addr
           required: true
           schema:
            type: string
            minimum: 1
            default: 101.99.128.0
           description: The IPV4 starting address e.g. 17 in 101.99.128.0/17
         - in: path
           name: length
           required: true
           schema:
            type: integer
            minimum: 1
            default: 17
           description: The IPV4 address length e.g. 17 in 101.99.128.0/17
        responses:
            200:
                description: Respond with all feed values required for experience
            503:
                description: Temporary service issue. Try again later
    """
    DATABASE = db
    endpoint = f'{NEO4J_API}/{DATABASE}/tx' 
    query = f"\
MATCH (ip4:IPv4 {{inetnum: '{addr}/{length}'}}){chr(10)}\
WITH ip4{chr(10)}\
OPTIONAL MATCH (ip4)-[ro:DELEGATED_TO]-(org:Org){chr(10)}\
WITH ip4, collect(org) as org{chr(10)}\
OPTIONAL MATCH (ip4)-[ra:ORIGINATED_BY]-(asn:ASN){chr(10)}\
WITH ip4, org, collect(ra) AS ra, collect(asn) as asn{chr(10)}\
OPTIONAL MATCH (ip4)-[rc:MAINTAINED_BY|HAS_CONTACT]-(con:Contact){chr(10)}\
WITH ip4, org, ra, asn, collect(rc) AS rc, collect(con) as con{chr(10)}\
RETURN ip4,{chr(10)}\
    org     AS organisation,{chr(10)}\
    ra      AS asnEdges,{chr(10)}\
    asn     AS asn,{chr(10)}\
    rc      AS contactEdges,{chr(10)}\
    con     AS contacts{chr(10)}\
"
    logger.debug(query)
    # logger.debug(req.url.path)
    try:
        q = GraphQuery(NEO4J_API, NEO4J_USER, NEO4J_PASSWORD,req,db)
        graph = q.run(query)
        # logger.debug(graph)
        resp.media = json.loads(graph)
        resp.status_code = api.status_codes.HTTP_200 
    except Exception as e:
        logger.error(e)
        resp.status_code = api.status_codes.HTTP_503

# @api.route("/ipv6/{db}/{addr}/{length}")
def api_ipv6_roa(req,resp,*, db, addr,length):
    """Subgraph showing all about a ROA auth query for IPv6.
    ---
    get:
        summary: ROA auth for IPv6
        description: Respond with all feed values required for subgraph showing all about a ROA auth query for IPv6. given address
        parameters:
         - in: path
           name: db
           required: true
           schema:
            type: string
            minimum: 1
            default: apnic
           description: The database name
         - in: path
           name: addr
           required: true
           schema:
            type: string
            minimum: 1
            default: '2407:5600::'
           description: The IPv6 address e.g. '2407:5600::'
         - in: path
           name: length
           required: true
           schema:
            type: string
            minimum: 1
            default: '32'
           description: The IPv6 address length e.g. 32 in 2407:5600::/32
        responses:
            200:
                description: Respond with all feed values required for experience
            503:
                description: Temporary service issue. Try again later
    """
    DATABASE = db
    endpoint = f'{NEO4J_API}/{DATABASE}/tx' 
    query = f"\
MATCH (ip6:IPv6 {{inet6num: '{addr}/{length}'}}){chr(10)}\
WITH ip6{chr(10)}\
OPTIONAL MATCH (ip6)-[ORIGINATED_BY]-(asn:ASN){chr(10)}\
WITH ip6, collect(asn) as asnList, collect(asn.aut_num) AS aut_numList{chr(10)}\
OPTIONAL MATCH (roa:ROA){chr(10)}\
WHERE roa.asn IN aut_numList{chr(10)}\
  AND roa.lower <= ip6.lower{chr(10)}\
  AND roa.upper >= ip6.upper{chr(10)}\
  AND ip6.length <= roa.maxLength{chr(10)}\
RETURN ip6, asnList, collect(roa) AS roaList{chr(10)}\
"
    logger.debug(query)
    try:
        q = GraphQuery(NEO4J_API, NEO4J_USER, NEO4J_PASSWORD, req, db)
        graph = q.run(query)
        # logger.debug(graph)
        resp.media = json.loads(graph)
        resp.status_code = api.status_codes.HTTP_200 
    except Exception as e:
        logger.error(e)
        resp.status_code = api.status_codes.HTTP_503

# @api.route("/ipv4/paths/{db}/{addr1}/{length1}/{addr2}/{length2}")
def api_possible_paths(req,resp,*, db, addr1,length1,addr2,length2):
    """Subgraph showing possible paths between two IPv4 adddresses
    ---
    get:
        summary: Possible paths between two IPv4 adddresses
        description: Respond with all feed values required for subgraph showing all about possible paths between two given IPv4 adddresses
        parameters:
         - in: path
           name: db
           required: true
           schema:
            type: string
            minimum: 1
            default: apnic
           description: The database name
         - in: path
           name: addr1
           required: true
           schema:
            type: string
            minimum: 1
            default: 202.159.0.0
           description: The IPV4 starting address e.g. 202.159.0.0 in 202.159.0.0/24
         - in: path
           name: length1
           required: true
           schema:
            type: integer
            minimum: 1
            default: 24
           description: The IPV4 address length e.g. 24 in 202.159.0.0/24
         - in: path
           name: addr2
           required: true
           schema:
            type: string
            minimum: 1
            default: 104.28.92.0
           description: The IPV4 starting address e.g. 104.28.92.0 in 104.28.92.0/24
         - in: path
           name: length2
           required: true
           schema:
            type: integer
            minimum: 1
            default: 24
           description: The IPV4 address length e.g. 24 in 104.28.92.0/24
        responses:
            200:
                description: Respond with all feed values required for experience
            503:
                description: Temporary service issue. Try again later
    """
    DATABASE = db
    endpoint = f'{NEO4J_API}/{DATABASE}/tx' 
    query = f"\
MATCH{chr(10)}\
  (i:IPv4 {{inetnum: '{addr1}/{length1}'}}),{chr(10)}\
  (n:IPv4 {{inetnum: '{addr2}/{length2}'}}),{chr(10)}\
  p = allShortestPaths((i)-[*..5]-(n)){chr(10)}\
RETURN p{chr(10)}\
"
    logger.debug(query)
    try:
        q = GraphQuery(NEO4J_API, NEO4J_USER, NEO4J_PASSWORD, req, db)
        graph = q.run(query)
        # logger.debug(graph)
        resp.media = json.loads(graph)
        resp.status_code = api.status_codes.HTTP_200 
    except Exception as e:
        logger.error(e)
        resp.status_code = api.status_codes.HTTP_503

# @api.route("/asn/{db}/{asn}")
def api_asn(req,resp,*, db, asn):
    """Subgraph showing all about an ASN address.
    ---
    get:
        summary: All about ASN
        description: Respond with all feed values required for experience showing all about an ASN address. given ID and LOD. LOD0 is curated path. LOD1 is path and all nodes within 1 node radius of path. LOD2 is path and all nodes within 2 node radius.
        parameters:
         - in: path
           name: db
           required: true
           schema:
            type: string
            minimum: 1
            default: apnic
           description: The database name
         - in: path
           name: asn
           required: true
           schema:
            type: string
            minimum: 1
            default: AS3605
           description: The ASN id e.g. AS3605
        responses:
            200:
                description: Respond with all feed values required for experience
            503:
                description: Temporary service issue. Try again later
    """
    DATABASE = db
    endpoint = f'{NEO4J_API}/{DATABASE}/tx' 
    query = f"\
MATCH (asn:ASN {{aut_num: '{asn}'}}){chr(10)}\
WITH asn{chr(10)}\
OPTIONAL MATCH (asn)-[:DELEGATED_TO]-(org:Org){chr(10)}\
WITH asn, collect(org) as org{chr(10)}\
OPTIONAL MATCH (asn)-[]-(set:AS_set){chr(10)}\
WITH asn, org, collect(set) AS set{chr(10)}\
OPTIONAL MATCH (asn)-[r4:ORIGINATED_BY]-(ip4:IPv4){chr(10)}\
WITH asn, org, set, collect(r4) AS r4, collect(ip4) as ip4{chr(10)}\
OPTIONAL MATCH (asn)-[r6:ORIGINATED_BY]-(ip6:IPv6){chr(10)}\
WITH asn, org, set, r4, ip4, collect(r6) AS r6, collect(ip6) AS ip6{chr(10)}\
OPTIONAL MATCH (asn)-[rp:NEIGHBOUR_OF]-(peer:ASN){chr(10)}\
WITH asn, org, set, r4, ip4, r6, ip6, collect(rp) AS rp, collect(peer) AS peer{chr(10)}\
OPTIONAL MATCH (asn)-[rc:MAINTAINED_BY|HAS_CONTACT]-(con:Contact){chr(10)}\
WITH asn, org, set, r4, ip4, r6, ip6, rp, peer, collect(rc) AS rc, collect(con) AS con{chr(10)}\
RETURN asn,{chr(10)}\
    org     AS organisation,{chr(10)}\
    set     AS asnSets,{chr(10)}\
    con     AS contacts,{chr(10)}\
    rc      AS contactEdges,{chr(10)}\
    ip4     AS ip4Prefixes,{chr(10)}\
    r4      AS ip4Edges,{chr(10)}\
    ip6     AS ip6Prefixes,{chr(10)}\
    r6      AS ip6Edges,{chr(10)}\
    peer    AS asnPeers{chr(10)}\
"
    logger.debug(query)
    try:
        q = GraphQuery(NEO4J_API, NEO4J_USER, NEO4J_PASSWORD, req, db)
        graph = q.run(query)
        # logger.debug(graph)
        resp.media = json.loads(graph)
        resp.status_code = api.status_codes.HTTP_200 
    except Exception as e:
        logger.error(e)
        resp.status_code = api.status_codes.HTTP_503

@api.route("/search/{db}/{query}")
def api_default_freetext_search(req,resp,*, db, query):
    """Subgraph showing free text search results from default index 'defaultFulltextIndex'
    ---
    get:
        summary: Search results from defaultFulltextIndex
        description: Respond with all .
        parameters:
         - in: path
           name: db
           required: true
           schema:
            type: string
            minimum: 1
            default: apnic
           description: The database name
         - in: path
           name: query
           required: true
           schema:
            type: string
            minimum: 1
            default: ANZ*
           description: The search query e.g. ANZ*
        responses:
            200:
                description: Respond with all feed values required for experience
            503:
                description: Temporary service issue. Try again later
    """
    DATABASE = db
    endpoint = f'{NEO4J_API}/{DATABASE}/tx' 
    query = f'''
CALL db.index.fulltext.queryNodes("defaultFulltextIndex", "{query}") YIELD node
RETURN node 
'''
    logger.debug(query)
    try:
        q = GraphQuery(NEO4J_API, NEO4J_USER, NEO4J_PASSWORD, req, db)
        graph = q.run(query)
        # logger.debug(graph)
        resp.media = json.loads(graph)
        resp.status_code = api.status_codes.HTTP_200 
    except Exception as e:
        logger.error(e)
        resp.status_code = api.status_codes.HTTP_503

def neo4j_query(query):
    query = query
    data = {'statements': [ 
        {'statement': query, 
        'resultDataContents': ['graph']}]
    }
    print(data)
    r = requests.post(f'{NEO4J_API}/transaction/commit', \
        headers = {'Content-type': 'application/json'}, \
        json = data, \
        auth=HTTPBasicAuth(NEO4J_USER,NEO4J_PASSWORD) \
        )
    result = json.loads(r.text)
    return(json,r.status_code)

@api.route("/handles/{db}")
async def request_handles_database(req,resp,*,db):
    """All handles.
    ---
    get:
        summary: All handles
        description: Respond with all feed values required for experience showing all handles.
        responses:
            200:
                description: Respond with all feed values required for experience
            503:
                description: Temporary service issue. Try again later
        parameters:
             - in: path
               name: db
               required: true
               schema:
                type: string
                minimum: 1
                default: neo4j
               description: The database name
    post:
     summary: Post values
     description: 
     responses:
      200:
       description: A dictionary to be returned
     parameters:   
      - in: path
        name: db
        required: true
        schema:
         type: string
         minimum: 1
         default: neo4j
        description: The database name
    """
    query = '''
MATCH (n:Handle) WHERE n.visible IS NULL OR n.visible <> False RETURN n,ID(n)
'''
    logger.debug(query)
    try:
        q = GraphQuery(NEO4J_API, NEO4J_USER, NEO4J_PASSWORD,req, db)
        graph = q.run(query)
        logger.debug(graph)
        resp.media = json.loads(graph)
        resp.status_code = api.status_codes.HTTP_200 
    except Exception as e:
        logger.error(e)
        resp.status_code = api.status_codes.HTTP_503
    q.close() 

@api.route("/handle/{db}/{id}/{lod}")
async def request_handle_database(req,resp,*, db, id, lod):
    """Subgraph referenced by handle for Neo4j v4.4. Don't use for v5+
    ---
    get:
        summary: Handle lookup
        description: Respond with all feed values required for a handle given ID and LOD. LOD0 is curated path. LOD1 is path and all nodes within 1 node radius of path. LOD2 is path and all nodes within 2 node radius.
        parameters:
         - in: path
           name: id
           required: true
           schema:
            type: integer
            minimum: 1
           description: The handle ID
         - in: path
           name: lod
           required: false
           schema:
            type: integer
            minimum: 0
            default: 1
           description: The level of detail (LOD) to return
         - in: path
           name: db
           required: true
           schema:
            type: string
            minimum: 1
            default: apnic
           description: The database name                      
        responses:
            200:
                description: Respond with all feed values required for experience
            503:
                description: Temporary service issue. Try again later
    """
    query = f"\
        MATCH path = (a)-[:NEXT*]->(){chr(10)}\
        WHERE ID(a)={id}{chr(10)}\
        UNWIND (nodes(path)) as n{chr(10)}\
        WITH n LIMIT {QUERY_LIMIT} MATCH path2 = (n)-[*0..{lod}]-(b){chr(10)}\
        WHERE NOT (b:Handle AND NOT ID(b)={id}){chr(10)}\
        RETURN collect(nodes(path2)), collect(relationships(path2))"

    try:
        q = GraphQuery(NEO4J_API, NEO4J_USER, NEO4J_PASSWORD,req, db)
        logger.debug(query)
        graph = q.run(query)
        resp.media = json.loads(graph)
        resp.status_code = api.status_codes.HTTP_200 
    except Exception as e:
        logger.error(e)
        resp.status_code = api.status_codes.HTTP_503
    q.close()

@api.route("/handle")
async def request_handle_database_v5(req,resp):
    """Subgraph referenced by handle for Neo4j v4.4. Don't use for v5+
    ---
    post:
        summary: Handle lookup for Neo4j v5
        description: Respond with all feed values required for a handle given DATABASE, ID and LOD. LOD0 is curated path. LOD1 is path and all nodes within 1 node radius of path. LOD2 is path and all nodes within 2 node radius.
        parameters:
         - in: path
           name: elementid
           required: true
           schema:
            type: string
            default: 4:b1b34cd3-b9a1-456e-89ed-4359603f8be7:354
           description: The handle ID
         - in: path
           name: lod
           required: false
           schema:
            type: integer
            minimum: 0
            default: 1
           description: The level of detail (LOD) to return
         - in: path
           name: db
           required: true
           schema:
            type: string
            minimum: 1
            default: neo4j
           description: The database name                      
        responses:
            200:
                description: Respond with all feed values required for experience
            503:
                description: Temporary service issue. Try again later
    """
    logger.debug("request_handle_database_v5")
    data = await req.media()
    logger.debug(data)
    id = data['id']
    lod = data['lod']
    db = data['db']
    query = f"\
        MATCH path = (a)-[:NEXT*]->(){chr(10)}\
        WHERE elementid(a)='{id}'{chr(10)}\
        UNWIND (nodes(path)) as n{chr(10)}\
        WITH n LIMIT {QUERY_LIMIT} MATCH path2 = (n)-[*0..{lod}]-(b){chr(10)}\
        WHERE NOT (b:Handle AND NOT elementid(b)='{id}'){chr(10)}\
        RETURN collect(nodes(path2)), collect(relationships(path2))"

    try:
        q = GraphQuery(NEO4J_API, NEO4J_USER, NEO4J_PASSWORD,req, db)
        logger.debug(query)
        graph = q.run(query)
        resp.media = json.loads(graph)
        resp.status_code = api.status_codes.HTTP_200 
    except Exception as e:
        logger.error(e)
        resp.status_code = api.status_codes.HTTP_503

#@api.route("/connectednodes/{db}")
def connectednodes(req,resp,*,db):
    """Nodes that have at least one relationship
    ---
    get:
        summary: Respond with all feed values required for experience
        description: Respond with all feed values required for experience
        responses:
            200:
                description: Respond with all feed values required for experience
            503:
                description: Temporary service issue. Try again later
        parameters:
             - in: path
               name: db
               required: true
               schema:
                type: string
                minimum: 1
                default: apnic
               description: The database name
    """
    try:
        graph = Graph(f"neo4j+s://{NEO4J_HOST}:7687",name=db,auth=(NEO4J_USER,NEO4J_PASSWORD))
        resp.media=graph.run("MATCH (n) WHERE size((n)<-->()) > 0 RETURN count(n) as connected_nodes").data()
    except:
        resp.status_code = api.status_codes.HTTP_503    

#@api.route("/orphanednodes/{db}")
def orphanednodes(req,resp,*, db):
    """Nodes that have no relationships in graph.
    ---
    get:
        summary: Respond with all feed values required for experience
        description: Respond with all feed values required for experience
        responses:
            200:
                description: Respond with all feed values required for experience
            503:
                description: Temporary service issue. Try again later
        parameters:
             - in: path
               name: db
               required: true
               schema:
                type: string
                minimum: 1
                default: apnic
               description: The database name
    """
    try:
        graph = Graph(f"neo4j+s://{NEO4J_HOST}:7687",name=db,auth=(NEO4J_USER,NEO4J_PASSWORD))
        resp.media=graph.run("MATCH (n) WHERE size((n)<-->()) < 1 RETURN count(n) as orphaned_nodes").data()
    except:
        resp.status_code = api.status_codes.HTTP_503  

@api.route("/statistics/{db}")
async def statistics(req,resp,*,db):
    """Statistics for this database.
    ---
    get:
        summary: Counts nodes and relationships
        description: Respond with all feed values required for experience
        responses:
            200:
                description: Respond with all feed values required for experience
            503:
                description: Temporary service issue. Try again later
        parameters:
             - in: path
               name: db
               required: true
               schema:
                type: string
                minimum: 1
                default: neo4j
               description: The database name
    """
    query = "MATCH (n) WITH count(n) as nodes MATCH ()-[r]->() RETURN nodes, count(r) as relationships"
    try:
        q = GraphQuery(NEO4J_API, NEO4J_USER, NEO4J_PASSWORD,req, db)
        graph = q.run(query,False)
        # logger.debug(graph)
        resp.media = json.loads(graph)
        resp.status_code = api.status_codes.HTTP_200 
    except:
        resp.status_code = api.status_codes.HTTP_503    
    q.close()

@api.route("/databases")
async def databases(req,resp):
    """List databases available via this webservice.
    ---
    get:
        summary: List of databases
        description: Returns what databases accessible to this user
        responses:
            200:
                description: Respond with all feed values required for experience
            503:
                description: Temporary service issue. Try again later
    """

    query = "show databases where requestedStatus = 'online' and type = 'standard'"
    try:
        # NOTE - use Neo4j privileges to ensure NEO4J_USER can only see desired dbs 
        q = GraphQuery(NEO4J_API, NEO4J_USER, NEO4J_PASSWORD,req)
        graph = q.run(query,False)
        logger.debug(graph)
        resp.media = json.loads(graph)
        resp.status_code = api.status_codes.HTTP_200 
    except:
        resp.status_code = api.status_codes.HTTP_503  
    q.close()

# @api.route("/twitter")
async def twtter(req,resp):
    response = RedirectResponse(url='/all/twitter')



# @api.route("/neighbour_asn_diffcountry/{db}")
async def api_apnic_neighbour_asn_diffcountry(req,resp,*,db):
    """All data for experience. Selection of database slug in API
    ---
    get:
        summary: Neighbouring ASNs in different countries
        description: Respond with all feed values required for experience
        responses:
            200:
                description: Respond with all feed values required for experience
            503:
                description: Temporary service issue. Try again later
        parameters:
             - in: path
               name: db
               required: true
               schema:
                type: string
                minimum: 1
                default: apnic
               description: The database name
    """
    DATABASE = db
    endpoint = f'{NEO4J_API}/{DATABASE}/tx' 
    query = f"\
MATCH (as1:ASN)-[r1:NEIGHBOUR_OF]-(as2:ASN)-[r2:NEIGHBOUR_OF]-(as3:ASN){chr(10)}\
WHERE as1.country <> as2.country AND as2.country <> as3.country{chr(10)}\
RETURN as1, r1, as2, r2, as3 LIMIT 100{chr(10)}\
"
    logger.debug(query)
    try:
        q = GraphQuery(NEO4J_API, NEO4J_USER, NEO4J_PASSWORD, req, db)
        graph = q.run(query)
        # logger.debug(graph)
        resp.media = json.loads(graph)
        resp.status_code = api.status_codes.HTTP_200 
    except Exception as e:
        logger.error(e)
        resp.status_code = api.status_codes.HTTP_503

# @api.route("/asn_by_country/{db}/{country}")
async def api_apnic_asn_by_country(req,resp,*,db,country):
    """All data for experience. Selection of database slug in API
    ---
    get:
        summary: ASNs by country
        description: Respond with all feed values required for experience
        responses:
            200:
                description: Respond with all feed values required for experience
            503:
                description: Temporary service issue. Try again later
        parameters:
             - in: path
               name: db
               required: true
               schema:
                type: string
                minimum: 1
                default: apnic
             - in: path
               name: country
               required: true
               schema:
                type: string
                minimum: 1
                default: FJ
               description: The database name
    """
    DATABASE = db
    endpoint = f'{NEO4J_API}/{DATABASE}/tx' 
    query = f"\
MATCH (n:ASN) WHERE n.country = '{country}' RETURN n{chr(10)}\
"
    logger.debug(query)
    try:
        q = GraphQuery(NEO4J_API, NEO4J_USER, NEO4J_PASSWORD, req, db)
        graph = q.run(query)
        # logger.debug(graph)
        resp.media = json.loads(graph)
        resp.status_code = api.status_codes.HTTP_200 
    except Exception as e:
        logger.error(e)
        resp.status_code = api.status_codes.HTTP_503

# @api.route("/connected_contacts/{db}/{contact}")
async def api_apnic_connected_contacts(req,resp,*,db,contact):
    """All data for experience. Selection of database slug in API
    ---
    get:
        summary: Connected contacts
        description: Respond with all feed values required for experience
        responses:
            200:
                description: Respond with all feed values required for experience
            503:
                description: Temporary service issue. Try again later
        parameters:
             - in: path
               name: db
               required: true
               schema:
                type: string
                minimum: 1
                default: apnic
               description: The database name
             - in: path
               name: contact
               required: true
               schema:
                type: string
                minimum: 1
                default: SZ2-AP
               description: The contact name
    """
    DATABASE = db
    endpoint = f'{NEO4J_API}/{DATABASE}/tx' 
    query = f"\
MATCH (c:Contact {{contact: '{contact}'}}){chr(10)}\
CALL apoc.path.subgraphAll(c, {{{chr(10)}\
  labelFilter: 'Contact',{chr(10)}\
  relationshipFilter: 'HAS_CONTACT|MAINTAINED_BY',{chr(10)}\
  maxLevel:10,{chr(10)}\
  limit:200{chr(10)}\
}}) YIELD nodes, relationships{chr(10)}\
RETURN nodes, relationships LIMIT 200{chr(10)}\
"
    logger.debug(query)
    try:
        q = GraphQuery(NEO4J_API, NEO4J_USER, NEO4J_PASSWORD, req, db)
        graph = q.run(query)
        # logger.debug(graph)
        resp.media = json.loads(graph)
        resp.status_code = api.status_codes.HTTP_200 
    except Exception as e:
        logger.error(e)
        resp.status_code = api.status_codes.HTTP_503

# @api.route("/adjacent_asn_subgraph/{db}/{asn}")
async def api_apnic_adjacent_asn_subgraph(req,resp,*,db,asn):
    """All data for experience. Selection of database slug in API
    ---
    get:
        summary: Adjacent ASN
        description: Respond with all feed values required for experience
        responses:
            200:
                description: Respond with all feed values required for experience
            503:
                description: Temporary service issue. Try again later
        parameters:
             - in: path
               name: db
               required: true
               schema:
                type: string
                minimum: 1
                default: apnic
             - in: path
               name: asn
               required: true
               schema:
                type: string
                minimum: 1
                default: AS14051
               description: The database name
    """
    DATABASE = db
    endpoint = f'{NEO4J_API}/{DATABASE}/tx' 
    query = f"\
MATCH (as:ASN {{aut_num: '{asn}'}}){chr(10)}\
CALL apoc.path.subgraphAll(as, {{{chr(10)}\
  labelFilter: 'ASN|Contact',{chr(10)}\
  relationshipFilter: 'NEIGHBOUR_OF',{chr(10)}\
  maxLevel:1,{chr(10)}\
  limit:200{chr(10)}\
}}) YIELD nodes, relationships{chr(10)}\
RETURN nodes, relationships LIMIT 200{chr(10)}\
"
    logger.debug(query)
    try:
        q = GraphQuery(NEO4J_API, NEO4J_USER, NEO4J_PASSWORD, req, db)
        graph = q.run(query)
        # logger.debug(graph)
        resp.media = json.loads(graph)
        resp.status_code = api.status_codes.HTTP_200 
    except Exception as e:
        logger.error(e)
        resp.status_code = api.status_codes.HTTP_503


@api.route("/fixed_queries")
async def api_fixed_queries(req,resp):
    """All data for experience. Selection of database slug in API
    ---
    get:
        summary: Fixed queries
        description: Returns any hardcoded queries in API and returned by /all query alongside database stored Handles
        responses:
            200:
                description: Respond with all feed values required for experience
            503:
                description: Temporary service issue. Try again later
    """
    if INCLUDE_FIXED_QUERIES == True:
        resp.media=FIXED_QUERIES
    else:
        resp.media = {}
    resp.status_code = 200

@api.route("/top_betweenness/{limit}")
async def api_top_betweenness(req,resp,*,limit):
    """Return Neo4j gds.betweeness results on peopleGraph projection.
    ---
    get:
        summary: Top betweeness results
        description: Return Neo4j gds.betweeness results on peopleGraph projection.
        responses:
            200:
                description: Respond with all feed values required for experience
            503:
                description: Temporary service issue. Try again later
        parameters:
             - in: path
               name: limit
               required: true
               schema:
                type: integer
                minimum: 1
                default: 10
    """

    query = f"""
CALL gds.betweenness.stream(
"personGraph"
)
YIELD
  nodeId,
  score 
WITH gds.util.asNode(nodeId) AS node, score
RETURN {{
    id: id(node),
    labels: labels(node),
    properties: properties(node),
    score: score
}} AS node ORDER by score DESC LIMIT {limit}
"""
    try:
        # NOTE - use Neo4j privileges to ensure NEO4J_USER can only see desired dbs 
        q = GraphQuery(NEO4J_API, NEO4J_USER, NEO4J_PASSWORD,req)
        graph = q.run(query,False)
        logger.debug(graph)
        resp.media = json.loads(graph)
        resp.status_code = api.status_codes.HTTP_200 
    except:
        resp.status_code = api.status_codes.HTTP_503  

@api.route("/top_node_similarity/{limit}")
async def api_top_node_similarity(req,resp,*,limit):
    """Return Neo4j gds.nodeSimilarity results on peopleGraph projection.
    ---
    get:
        summary: Top node similarity results
        description: Return Neo4j gds.nodeSimilarity results on peopleGraph projection.
        responses:
            200:
                description: Respond with all feed values required for experience
            503:
                description: Temporary service issue. Try again later
        parameters:
             - in: path
               name: limit
               required: true
               schema:
                type: integer
                minimum: 1
                default: 10
    """

    query = f"""
CALL gds.nodeSimilarity.stream(
'personGraph'
) YIELD
  node1,
  node2,
  similarity
WITH node1, node2, similarity
MATCH (n),(o) WHERE ID(n)= node1 AND ID(o) = node2
RETURN n, o ORDER by similarity DESC LIMIT  {limit}
"""
    try:
        # NOTE - use Neo4j privileges to ensure NEO4J_USER can only see desired dbs 
        q = GraphQuery(NEO4J_API, NEO4J_USER, NEO4J_PASSWORD,req)
        graph = q.run(query,False)
        logger.debug(graph)
        resp.media = json.loads(graph)
        resp.status_code = api.status_codes.HTTP_200 
    except:
        resp.status_code = api.status_codes.HTTP_503  

@api.route("/up_next")
async def api_up_next(req,resp):
    """Return Neo4j Time label node based on current time
    ---
    get:
        summary: Top node similarity results
        description: Return Neo4j gds.nodeSimilarity results on peopleGraph projection.
        responses:
            200:
                description: Respond with all feed values required for experience
            503:
                description: Temporary service issue. Try again later
    """

    query = """
WITH datetime({timezone: 'Europe/London'}) AS currentDateTime
MATCH (startNode:Time)
WHERE startNode.datetime > currentDateTime
WITH startNode
ORDER BY startNode.datetime
LIMIT 1
MATCH path = (startNode)-[:NEXT*2]->(nextNode:Time)
UNWIND (nodes(path)) as n
WITH n MATCH path2 = (n)-[*0..1]-(b:Event|Time)
RETURN collect(nodes(path2)), collect(relationships(path2))
"""
    try:
        # NOTE - use Neo4j privileges to ensure NEO4J_USER can only see desired dbs 
        q = GraphQuery(NEO4J_API, NEO4J_USER, NEO4J_PASSWORD,req)
        # TODO document "True in run" below as WASTED HOURS with this off!!
        graph = q.run(query,True)
        # logger.debug(graph)
        resp.media = json.loads(graph)
        resp.status_code = api.status_codes.HTTP_200 
    except:
        resp.status_code = api.status_codes.HTTP_503  
    q.close()

if __name__ == "__main__":
    api.run(address="0.0.0.0")

import responder
import requests
from requests.auth import HTTPBasicAuth
from marshmallow import Schema, fields
import graphene
import json

#import squarify
import time
from py2neo import Graph

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)
# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)

from pathlib import Path

NEO4J_HOST = "neo4j-server"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "please"
#NEO4J_API = "http://grapho-neo4j.hq.modprods.com:7474/db/data"
DATABASE = "twitter"
NEO4J_API = f"http://neo4j-server:7474/db"

PUBLIC_URL = "https://api.grapho.app"

QUERY_LIMIT = 100

API_TITLE = "Grapho API"
API_AUTHOR = "Michela Ledwidge"
API_PUBLISHER = "Mod Productions Pty Ltd."
API_COPYRIGHT = "https://creativecommons.org/licenses/by/4.0/"
API_VERSION = "0.2"

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

@api.schema("ChartDataSchema")

class ChartDataSchema(Schema):
    label = fields.Str()
    value = fields.Float()
    rgb = fields.Str()
    rect = fields.Raw()

class Query(graphene.ObjectType):
    hello = graphene.String(name=graphene.String(default_value="stranger"))

    def resolve_hello(self, info, name):
        return f"Hello {name}"

schema = graphene.Schema(query=Query)
view = responder.ext.GraphQLView(api=api, schema=schema)

#{ hello(name: "michela") }

api.add_route("/graph", view)


@api.schema("StarChartSchema")

class StarChartSchema(Schema):
    name = fields.Str()
    id = fields.Integer()
    source = fields.Str()
    source_url = fields.URL()
    items = fields.List(fields.Nested(ChartDataSchema()))

@api.schema("PointChartSchema")

class PointChartSchema(Schema):
    name = fields.Str()
    id = fields.Integer()
    source = fields.Str()
    source_url = fields.URL()
    items = fields.List(fields.Nested(ChartDataSchema()))


# spawn point charts

pointcharts = []
starcharts = []
# DECISION on console or not??


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

@api.route("/all/{db}")
def api_all_database(req,resp,*,db):
    """All data for experience. Selection of database slug in API
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
               description: The database name
    """
#    resp.status_code = api.status_codes.HTTP_302
#    resp.headers['Location'] = '/static/test.json'
    graphs = []
    # sets default number of neighbours to include in handles
    lod = 1
    DATABASE = db
    handles = requests.get('{0}/handles/{1}'.format(PUBLIC_URL,DATABASE))
    #     for handle_id in [864,884,883,885,886]:
    for handle in handles.json()['results'][0]['data']:
      label = handle['graph']['nodes'][0]['properties']['label']
      handle_id = int(handle['graph']['nodes'][0]['id'])
      print(label)
      r = requests.get('{0}/handle/{1}/{2}/{3}'.format(
        PUBLIC_URL, DATABASE,handle_id,lod)
      )
      g = r.json()['results'][0]['data'][0]['graph']
      g['handle_id'] = handle_id
      graphs.append(g)
    data = dict(
        author=API_AUTHOR,
        database=DATABASE,
        url=PUBLIC_URL,
        publisher=API_PUBLISHER,
        copyright=API_COPYRIGHT,
 #       points = PointChartSchema().dump(pointcharts,many=True),
 #       pages=PageSchema().dump(pages,many=True),
        graphs=graphs
    )
    resp.media = data

# @api.route("/neighbours/{id}/{lod}")
def api_neighbours(req,resp,*, id, lod):
    """Subgraph comprising neighbours of specified node.
    ---
    get:
        summary: Respond with all feed values required for subgraph
        description: Respond with all feed values required for experience given ID and LOD. LOD0 is curated path. LOD1 is path and all nodes within 1 node radius of path. LOD2 is path and all nodes within 2 node radius.
        parameters:
         - in: path
           name: id
           required: true
           schema:
            type: integer
            minimum: 1
           description: The node ID
         - in: path
           name: lod
           required: true
           schema:
            type: integer
            minimum: 1
           description: Distance of neighbours (LOD) to return                      
        responses:
            200:
                description: Respond with all feed values required for experience
            503:
                description: Temporary service issue. Try again later
    """
    distance=int(lod)
    assert(1 <= distance <= 2)
    query = '''
MATCH (a)-[*0..{distance}]-(neighbour)
WHERE id(a) = {node_id}
RETURN collect(neighbour)
'''.format(node_id=id,distance=distance)
    data = {'statements': [ 
        {'statement': query, 
        'resultDataContents': ['graph']}]
    }
#   logger.debug(data)
    r = requests.post(f'{NEO4J_API}/transaction/commit', \
        headers = {'Content-type': 'application/json'}, \
        json = data, \
        auth=HTTPBasicAuth(NEO4J_USER,NEO4J_PASSWORD) \
        )
    resp.media=json.loads(r.text)
#    print(resp.media)
    resp.status_code = r.status_code

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
def request_handles_database(req,resp,*,db):
    """All handles.
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
               description: The database name
    post:
     summary: Post values
     description: 
     responses:
      200:
       description: A dictionary to be returned
    """
    query = 'MATCH (n:Handle) RETURN n LIMIT 25'
    data = {'statements': [ 
        {'statement': query, 
        'resultDataContents': ['graph']}]
    }
#    print(data)
    DATABASE = db
    # print(DATABASE)
    r = requests.post(f'{NEO4J_API}/{DATABASE}/tx', \
        headers = {'Content-type': 'application/json'}, \
        json = data, \
        auth=HTTPBasicAuth(NEO4J_USER,NEO4J_PASSWORD) \
        )
    resp.media=json.loads(r.text)
#    print(resp.media)
    resp.status_code = r.status_code

# @api.route("/handle/{id}/{lod}")
def request_handle(req,resp,*, id, lod):
    """Subgraph referenced by handle.
    ---
    get:
        summary: Respond with all feed values required for subgraph
        description: Respond with all feed values required for experience given ID and LOD. LOD0 is curated path. LOD1 is path and all nodes within 1 node radius of path. LOD2 is path and all nodes within 2 node radius.
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
           description: The level of detail (LOD) to return                      
        responses:
            200:
                description: Respond with all feed values required for experience
            503:
                description: Temporary service issue. Try again later
    """
    query = f"\
        MATCH path = (a)-[:NEXT*]-() \
        WHERE ID(a)={id} \
        UNWIND (nodes(path)) as n \
        WITH n LIMIT {QUERY_LIMIT} MATCH path2 = (n)-[*0..{lod}]-() \
        RETURN collect(nodes(path2)), collect(relationships(path2))"

#    print(f"id {id}\nlod {lod}\nquery {query}")
    data = {'statements': [ 
        {'statement': query, 
        'resultDataContents': ['graph']}]
    }
    endpoint = f'{NEO4J_API}/{DATABASE}/tx'
    print(endpoint)
    print(data)
    r = requests.post(endpoint, \
        headers = {'Content-type': 'application/json'}, \
        json = data, \
        auth=HTTPBasicAuth(NEO4J_USER,NEO4J_PASSWORD) \
        )
    resp.media=json.loads(r.text)
#    print(resp.media)
    resp.status_code = r.status_code

@api.route("/handle/{db}/{id}/{lod}")
def request_handle_database(req,resp,*, db, id, lod):
    """Subgraph referenced by handle.
    ---
    get:
        summary: Respond with all feed values required for subgraph
        description: Respond with all feed values required for experience given ID and LOD. LOD0 is curated path. LOD1 is path and all nodes within 1 node radius of path. LOD2 is path and all nodes within 2 node radius.
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
           description: The level of detail (LOD) to return
         - in: path
           name: db
           required: true
           schema:
            type: string
            minimum: 1
           description: The database name                      
        responses:
            200:
                description: Respond with all feed values required for experience
            503:
                description: Temporary service issue. Try again later
    """
    query = f"\
        MATCH path = (a)-[:NEXT*]-() \
        WHERE ID(a)={id} \
        UNWIND (nodes(path)) as n \
        WITH n LIMIT {QUERY_LIMIT} MATCH path2 = (n)-[*0..{lod}]-() \
        RETURN collect(nodes(path2)), collect(relationships(path2))"

#    print(f"id {id}\nlod {lod}\nquery {query}")
    data = {'statements': [ 
        {'statement': query, 
        'resultDataContents': ['graph']}]
    }
    DATABASE = db
    endpoint = f'{NEO4J_API}/{DATABASE}/tx'
    print(endpoint)
    print(data)
    r = requests.post(endpoint, \
        headers = {'Content-type': 'application/json'}, \
        json = data, \
        auth=HTTPBasicAuth(NEO4J_USER,NEO4J_PASSWORD) \
        )
    resp.media=json.loads(r.text)
#    print(resp.media)
    resp.status_code = r.status_code

# @api.route("/people")
def people(req,resp):
    """All people.
    ---
    get:
        summary: Respond with all feed values required for experience
        description: Respond with all feed values required for experience
        responses:
            200:
                description: Respond with all feed values required for experience
            503:
                description: Temporary service issue. Try again later
    """
    try:
        graph = Graph(f"bolt://{NEO4J_HOST}:7687",auth=(NEO4J_USER,NEO4J_PASSWORD))
        resp.media=graph.run("MATCH (n:Person) RETURN n LIMIT 25").data()
    except:
        resp.status_code = api.status_codes.HTTP_503

# @api.route("/organisations")
def organisations(req,resp):
    """All organisations.
    ---
    get:
        summary: Respond with all feed values required for experience
        description: Respond with all feed values required for experience
        responses:
            200:
                description: Respond with all feed values required for experience
            503:
                description: Temporary service issue. Try again later
    """
    try:
        graph = Graph(f"bolt://{NEO4J_HOST}:7687",auth=(NEO4J_USER,NEO4J_PASSWORD))
        resp.media=graph.run("MATCH (n:Organisation) RETURN n LIMIT 25").data()
    except:
        resp.status_code = api.status_codes.HTTP_503
    #print(graph.run("MATCH (n:Organisation) RETURN n LIMIT 25").to_data_frame())
    
# https://neo4j.com/docs/rest-docs/current/
#MATCH p=()-[r:DONATED_TO]->() RETURN p LIMIT 25

# @api.route("/donors")
def request_donors(req,resp):
    """All donors.
    ---
    get:
        summary: Respond with all feed values required for experience
        description: Respond with all feed values required for experience
        responses:
            200:
                description: Respond with all feed values required for experience
            503:
                description: Temporary service issue. Try again later
    """
    # try:
    graph = Graph(f"bolt://{NEO4J_HOST}:7687",auth=(NEO4J_USER,NEO4J_PASSWORD))
    query = "MATCH p=()-[r:DONATED_TO]->() RETURN p LIMIT 25"
    data = graph.run(cypher=query).data()
    donor_data = []
    print(data)
    for d in data:
        this_donor = dict(
        id = d['p'].start_node.identity,
        title = d['p'].start_node['title']
        )
        donor_data.append(this_donor)
    print(donor_data)
    data = dict(
        donors= donor_data
    )
    resp.media = data
#    except:
#        resp.status_code = api.status_codes.HTTP_503
    #print(graph.run("MATCH (n:Organisation) RETURN n LIMIT 25").to_data_frame())

@api.route("/connectednodes/{db}")
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
               description: The database name
    """
    try:
        graph = Graph(f"bolt://{NEO4J_HOST}:7687",name=db,auth=(NEO4J_USER,NEO4J_PASSWORD))
        resp.media=graph.run("MATCH (n) WHERE size((n)<-->()) > 0 RETURN count(n) as connected_nodes").data()
    except:
        resp.status_code = api.status_codes.HTTP_503    

@api.route("/orphanednodes/{db}")
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
               description: The database name
    """
    try:
        graph = Graph(f"bolt://{NEO4J_HOST}:7687",name=db, auth=(NEO4J_USER,NEO4J_PASSWORD))
        resp.media=graph.run("MATCH (n) WHERE size((n)<-->()) < 1 RETURN count(n) as orphaned_nodes").data()
    except:
        resp.status_code = api.status_codes.HTTP_503  

@api.route("/statistics/{db}")
def statistics(req,resp,*,db):
    """Statistics for this webservice.
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
               description: The database name
    """
    try:
        graph = Graph(f"bolt://{NEO4J_HOST}:7687",name=db,auth=(NEO4J_USER,NEO4J_PASSWORD))
        resp.media=graph.run("MATCH (n) RETURN count(n) as nodes").data()
    except:
        resp.status_code = api.status_codes.HTTP_503    

@api.route("/databases")
def databases(req,resp):
    """List databases available via this webservice.
    ---
    get:
        summary: Respond with all feed values required for experience
        description: Respond with all feed values required for experience
        responses:
            200:
                description: Respond with all feed values required for experience
            503:
                description: Temporary service issue. Try again later
    """
    try:
        graph = Graph(f"bolt://{NEO4J_HOST}:7687",name="system",auth=(NEO4J_USER,NEO4J_PASSWORD))
        resp.media=graph.run("SHOW DATABASES").data()
    except:
        resp.status_code = api.status_codes.HTTP_503  

if __name__ == "__main__":
    api.run(address="0.0.0.0")

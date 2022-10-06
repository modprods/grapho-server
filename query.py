from dotenv import load_dotenv
load_dotenv(verbose=True,override=True)
import os
import json

import logging
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

from pathlib import Path

NEO4J_HOST = os.getenv('NEO4J_HOST')
NEO4J_USER = os.getenv('NEO4J_USER')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')
NEO4J_PORT_HTTP = os.getenv('NEO4J_PORT_HTTP')
NEO4J_PORT_BOLT = os.getenv('NEO4J_PORT_BOLT')
DATABASE = os.getenv('DATABASE')
PUBLIC_URL = os.getenv('PUBLIC_URL')
QUERY_LIMIT = os.getenv('QUERY_LIMIT')
INCLUDE_FIXED_QUERIES = eval(os.getenv('INCLUDE_FIXED_QUERIES',"False"))

query = f"\
MATCH (as:ASN {{aut_num: 'AS14051'}}){chr(10)}\
CALL apoc.path.subgraphAll(as, {{{chr(10)}\
  labelFilter: 'ASN|Contact',{chr(10)}\
  relationshipFilter: 'NEIGHBOUR_OF',{chr(10)}\
  maxLevel:1,{chr(10)}\
  limit:200{chr(10)}\
}}) YIELD nodes, relationships{chr(10)}\
RETURN nodes, relationships LIMIT 200{chr(10)}\
"

query = "MATCH (n:Handle) RETURN n LIMIT 25"

from neo4j import GraphDatabase

class GraphQuery:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def run(self, query):
        with self.driver.session() as session:
            results = session.execute_read(self._read_query,query)
            return results

    @staticmethod
    def _read_query(tx, query):
        # logger.debug(query)
     #   query = query.replace("\n"," ")
        result = tx.run(query).graph()
        # logger.debug(result)
        graph = {}
        nodes = []
        relationships = []

        for i in result.nodes:
            n = dict(
                id = i.element_id,
                labels = list(i.labels),
                properties = dict(i.items())
            )
            nodes.append(n)
        for i in result.relationships:
            r = dict(
                id = i.element_id,
                type = i.type,
                startNode = i.nodes[0].element_id,
                endNode = i.nodes[1].element_id,
                properties = dict(i.items())
            )
            relationships.append(r)            

        graph = dict(
            results = [dict(
                columns = [],
                data = [
                    dict(
                        graph = dict(
                            nodes=nodes,
                            relationships=relationships
                        )
                    )
                ]
            )],
            errors = [],
            commit = "",
            transaction = {}
        )
        # logger.debug(type(graph))
        output = json.dumps(graph, default = str)
        # logger.debug(output)
        return output

if __name__ == "__main__":
    # logger.debug(NEO4J_API)
    # logger.debug(NEO4J_USER)
    # logger.debug(NEO4J_PASSWORD)

    if int(NEO4J_PORT_HTTP) == 7474:
        logger.info("dev API instance running")
        NEO4J_API = f"neo4j://{NEO4J_HOST}:{NEO4J_PORT_HTTP}"
    else:
        logger.info("live API instance running")
        NEO4J_API = f"neo4j+s://{NEO4J_HOST}"

    query = f"\
MATCH (n:Handle) RETURN n LIMIT 25\
"
#     query = f"\
# MATCH (as:ASN {{aut_num: 'AS14051'}}){chr(10)}\
# CALL apoc.path.subgraphAll(as, {{{chr(10)}\
#   labelFilter: 'ASN|Contact',{chr(10)}\
#   relationshipFilter: 'NEIGHBOUR_OF',{chr(10)}\
#   maxLevel:1,{chr(10)}\
#   limit:200{chr(10)}\
# }}) YIELD nodes, relationships{chr(10)}\
# RETURN nodes, relationships LIMIT 200{chr(10)}\
# "
    # logger.debug(query)
    q = GraphQuery(NEO4J_API, NEO4J_USER, NEO4J_PASSWORD)
    graph = q.run(query)
    logger.debug(graph)
    q.close()
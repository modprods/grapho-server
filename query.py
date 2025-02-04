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
NEO4J_DATABASE = os.getenv('NEO4J_DATABASE')
PUBLIC_URL = os.getenv('PUBLIC_URL')
QUERY_LIMIT = os.getenv('QUERY_LIMIT')
INCLUDE_FIXED_QUERIES = eval(os.getenv('INCLUDE_FIXED_QUERIES',"False"))

if int(NEO4J_PORT_HTTP) == 7474:
    logger.info("dev API instance running")
    NEO4J_API = f"neo4j://{NEO4J_HOST}:{NEO4J_PORT_BOLT}"
else:
    logger.info("live API instance running")
    NEO4J_API = f"neo4j+s://{NEO4J_HOST}:{NEO4J_PORT_BOLT}"

from neo4j import GraphDatabase, unit_of_work

class GraphQuery:
    def __init__(self, uri, user, password, req, database = None):
        self.driver = GraphDatabase.driver(
                uri,
                auth=(user, password),
                connection_timeout=60
        )
        self.path = req.url.path
        # rules for overriding database selection
        if NEO4J_DATABASE:  # override all queries based on environment
            self.database = NEO4J_DATABASE
        elif database:      # override based on query parameter
            self.database = database
        else:               # no override, use neo4j server default db
            self.database = None

    def close(self):
        self.driver.close()

    def run(self, query,graph=True):
        with self.driver.session(database=self.database) as session:
            results = session.execute_read(self._read_query,query,self.path,graph)
            return results

    @staticmethod
    @unit_of_work(timeout=30) # client timeout
    def _read_query(tx, query, path,graph):
        # logger.debug('_read_query')
        # logger.debug(query)
     #   query = query.replace("\n"," ")
        # for queries where not expecting a graph result, simpler result set
        if not graph:
            logger.debug("not a graph result")
            result = tx.run(query)
            data = [dict(record) for record in result]
            # logger.debug(data)
            output = json.dumps(data, default = str)
            return output
        result = tx.run(query).graph()
        graph = {}
        nodes = []
        relationships = []
        # raw
        # logger.debug("raw in query.py")
        # logger.debug(result)

        # for i in result:
        #     logger.debug(i)
        # logger.debug(f"{len(result.nodes)} nodes")
        for i in result.nodes:
            n = dict(
                id = i.id,
                labels = list(i.labels),
                properties = dict(i.items())
            )
            nodes.append(n)
        logger.debug(f"{len(result.relationships)} relationships")
        for i in result.relationships:
            r = dict(
                id = i.id,
                type = i.type,
                startNode = i.nodes[0].id, # this is deprecated (need to shift to element_id)
                endNode = i.nodes[1].id,
                properties = dict(i.items())
            )
            relationships.append(r)
        # # raw results            
        # for i in result:
        #     logger.debug(i)
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
            path = path,
            transaction = {}
        )
        # logger.debug(type(graph))
        output = json.dumps(graph, default = str)
        # logger.debug(output)
        return output

if __name__ == "__main__":
    logger.debug(NEO4J_API)
    logger.debug(NEO4J_USER)
    logger.debug(NEO4J_PASSWORD)
    logger.debug(f"NEO4J_DATABASE is {NEO4J_DATABASE}")

    query = f"\
MATCH{chr(10)}\
  (i:IPv4 {{inetnum: '202.159.0.0/24'}}),{chr(10)}\
  (n:IPv4 {{inetnum: '104.28.92.0/24'}}),{chr(10)}\
  p = allShortestPaths((i)-[*..5]-(n)){chr(10)}\
RETURN collect(nodes(p)), collect(relationships(p)){chr(10)}\
"

    # logger.debug(query)
    q = GraphQuery(NEO4J_API, NEO4J_USER, NEO4J_PASSWORD)
    # test query
    # graph = q.run(query)
    # logger.debug(graph)
    q.close()

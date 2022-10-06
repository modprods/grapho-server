from dotenv import load_dotenv
load_dotenv(verbose=True,override=True)
import os

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

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


if int(NEO4J_PORT_HTTP) == 7474:
    logger.info("dev API instance running")
    NEO4J_API = f"neo4j://{NEO4J_HOST}:{NEO4J_PORT_HTTP}"
else:
    logger.info("live API instance running")
    NEO4J_API = f"neo4j+s://{NEO4J_HOST}"

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

#query = "MATCH (n:Handle) RETURN n LIMIT 25"

from neo4j import GraphDatabase

class GraphQuery:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def run(self, query):
        with self.driver.session() as session:
            results = session.execute_read(self._read_query,query)

    @staticmethod
    def _read_query(tx, query):
        logger.debug(query)
     #   query = query.replace("\n"," ")
        result = tx.run(query)
        # logger.debug(result)
        for i,r in enumerate(result.single()):
            logger.debug(f"({i}) - loop ")
            for s in r:
                logger.debug(type(s).__name__)
                logger.debug(f"{s}\n\n")
        return None

class HelloWorldExample:

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def print_greeting(self, message):
        with self.driver.session() as session:
            results = session.execute_read(self._read_stats,message)
            # print(type(results[0]))
            # logger.debug(results)
            # for r in results:
            #     logger.debug(type(r))

    @staticmethod
    def _read_stats(tx, message):
        query
        query = query.replace("\n"," ")
        logger.debug(query)
        result = tx.run(query)
        # logger.debug(result)
        # logger.debug(result.single()[0])
        # r = result.data()
        for r in result.single():
            # logger.debug(r)
            for s in r:
                logger.debug(type(s))
                logger.debug("\n\n\n")
        return None


if __name__ == "__main__":
    logger.debug(NEO4J_API)
    logger.debug(NEO4J_USER)
    logger.debug(NEO4J_PASSWORD)
    # greeter = HelloWorldExample(NEO4J_API, NEO4J_USER, NEO4J_PASSWORD)
    # greeter.print_greeting("hello, world")
    # greeter.close()
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
    logger.debug(query)
    q = GraphQuery(NEO4J_API, NEO4J_USER, NEO4J_PASSWORD)
    q.run(query)
    q.close()
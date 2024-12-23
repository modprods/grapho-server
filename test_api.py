import pytest
import api as service
import sys
import json

#  pytest

import logging
from typing import Optional, Dict

from colorama import Fore, Back, Style

class ColoredFormatter(logging.Formatter):
    """Colored log formatter."""

    def __init__(self, *args, colors: Optional[Dict[str, str]]=None, **kwargs) -> None:
        """Initialize the formatter with specified format strings."""

        super().__init__(*args, **kwargs)

        self.colors = colors if colors else {}

    def format(self, record) -> str:
        """Format the specified record as text."""

        record.color = self.colors.get(record.levelname, '')
        record.reset = Style.RESET_ALL

        return super().format(record)


#     '{asctime} |{color} {levelname:8}  {reset} | {name} | {message}',

formatter = ColoredFormatter(
    '{color} {levelname:8}  {reset}| {message}',
    style='{', datefmt='%Y-%m-%d %H:%M:%S',
    colors={
        'DEBUG': Fore.BLACK,
        'INFO': Fore.GREEN,
        'WARNING': Fore.BLACK + Back.YELLOW,
        'ERROR': Fore.BLACK + Back.RED,
        'CRITICAL': Fore.BLACK + Back.RED + Style.BRIGHT,
    }
)

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.propagate = False
logger.handlers[:] = []
logger.addHandler(handler)

logger.setLevel(logging.DEBUG)

logger.debug("debug log test")
logger.info("info log test")
logger.warning("warn log test")
logger.error("error log test")

# update to run against different db
DATABASE = 'graphsummiteurope2024'

@pytest.fixture
def api():
    return service.api

def test_hello_world(api):
    r = api.requests.get("/")
    assert r.status_code == 200

def test_docs(api):
    r = api.requests.get("/docs")
    assert r.status_code == 200

def test_handles(api,caplog):
     caplog.set_level(logging.INFO)
     r = api.requests.get(f"/handles/{DATABASE}")
     assert r.status_code == 200
     # logger.info(r.text)
     data = json.loads(r.text)
     handle_list = [
          node["id"]
          for result in data.get("results", [])
          for record in result.get("data", [])
          for node in record.get("graph", {}).get("nodes", [])
     ]
     for id in handle_list:
          logger.info(f"Query handle id {id}")
          r = api.requests.get(f"/handle/{DATABASE}/{id}/1")
          assert r.status_code == 200

def test_all_method(api):
     r = api.requests.get(f"/all/{DATABASE}")
     assert r.status_code == 200

def test_neighbours(api):
     r = api.requests.get(f"/neighbours/{DATABASE}/0/1")
     assert r.status_code == 200

def test_statistics(api):
     r = api.requests.get(f"/statistics/{DATABASE}")
     assert r.status_code == 200

def test_databases(api):
     r = api.requests.get("/databases")
     assert r.status_code == 200
     
def test_fixed_queries(api):
     r = api.requests.get("/fixed_queries")
     assert r.status_code == 200

def test_dialogue(api):
     r = api.requests.get(f"/dialogue/{DATABASE}")
     assert r.status_code == 200

def test_up_next(api):
     r = api.requests.get("/up_next")
     assert r.status_code == 200

def test_game(api):
     r = api.requests.get(f"/game/{DATABASE}")
     assert r.status_code == 200

# def test_node_schema(api):
#      r = api.requests.get("/node/schema/apnic")
#      assert r.status_code == 200

# def test_rel_schema(api):
#      r = api.requests.get("/rel/schema/apnic")
#      assert r.status_code == 200



# def test_squarify(api):
#      r = api.requests.post("/squarify",json = {"x":0,"y":0,"width":700,"height":433,"values": [500, 433, 78, 25, 25, 7]} )
#      assert r.status_code == 200

# def test_people(api):
#      r = api.requests.get(PUBLIC_URL + "/people")
#      assert r.status_code == 200

# def test_organisations(api):
#      r = api.requests.get("/organisations")
#      assert r.status_code == 200

# def test_neighbours(api):
#      r = api.requests.get("/neighbours/apnic/1000/1")
#      assert r.status_code == 200

# def test_ipv4(api):
#      r = api.requests.get("/ipv4/apnic/101.99.128.0/17")
#      assert r.status_code == 200

# def test_ipv6(api):
#      r = api.requests.get("/ipv6/apnic/2407:5600::/32")
#      assert r.status_code == 200

# def test_asn(api):
#      r = api.requests.get("/asn/apnic/AS3605")
#      assert r.status_code == 200

# def test_handles(api):
#      r = api.requests.get("/handles/apnic")
#      assert r.status_code == 200

# def test_post_handles(api):
#      r = api.requests.post("/handles/apnic", json={})
#      assert r.status_code == 200

# def test_handle(api):
#      r = api.requests.get("/handle/apnic/4252153/1")
#      assert r.status_code == 200

# def test_connectednodes(api):
#      r = api.requests.get("/connectednodes/apnic")
#      assert r.status_code == 200

# def test_orphanednodes(api):
#      r = api.requests.get("/orphanednodes/apnic")
#      assert r.status_code == 200

# def test_neighbour_asn_diffcountry(api):
#      r = api.requests.get("/neighbour_asn_diffcountry/apnic")
#      assert r.status_code == 200

# def test_asn_by_country(api):
#      r = api.requests.get("/asn_by_country/apnic/FJ")
#      assert r.status_code == 200

# def test_connected_contact(api):
#      r = api.requests.get("/connected_contacts/apnic/SZ2-AP")
#      assert r.status_code == 200

# def test_adjacent_asn_subgraph(api):
#      r = api.requests.get("/adjacent_asn_subgraph/apnic/AS14051")
#      assert r.status_code == 200


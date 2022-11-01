import pytest
import api as service

#  pytest

@pytest.fixture
def api():
    return service.api

def test_hello_world(api):
    r = api.requests.get("/")
    assert r.status_code == 200

def test_all(api):
     r = api.requests.get("/all/apnic")
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

def test_neighbours(api):
     r = api.requests.get("/neighbours/apnic/1000/1")
     assert r.status_code == 200

def test_ipv4(api):
     r = api.requests.get("/ipv4/apnic/101.99.128.0/17")
     assert r.status_code == 200

def test_ipv6(api):
     r = api.requests.get("/ipv6/apnic/2407:5600::/32")
     assert r.status_code == 200

def test_asn(api):
     r = api.requests.get("/asn/apnic/AS3605")
     assert r.status_code == 200

def test_handles(api):
     r = api.requests.get("/handles/apnic")
     assert r.status_code == 200

def test_post_handles(api):
     r = api.requests.post("/handles/apnic", json={})
     assert r.status_code == 200

def test_handle(api):
     r = api.requests.get("/handle/apnic/4252153/1")
     assert r.status_code == 200

# def test_connectednodes(api):
#      r = api.requests.get("/connectednodes/apnic")
#      assert r.status_code == 200

# def test_orphanednodes(api):
#      r = api.requests.get("/orphanednodes/apnic")
#      assert r.status_code == 200

# def test_statistics(api):
#      r = api.requests.get("/statistics/apnic")
#      assert r.status_code == 200

def test_databases(api):
     r = api.requests.get("/databases")
     assert r.status_code == 200

def test_neighbour_asn_diffcountry(api):
     r = api.requests.get("/neighbour_asn_diffcountry/apnic")
     assert r.status_code == 200

def test_asn_by_country(api):
     r = api.requests.get("/asn_by_country/apnic/FJ")
     assert r.status_code == 200

def test_connected_contact(api):
     r = api.requests.get("/connected_contacts/apnic/SZ2-AP")
     assert r.status_code == 200

def test_adjacent_asn_subgraph(api):
     r = api.requests.get("/adjacent_asn_subgraph/apnic/AS14051")
     assert r.status_code == 200

def test_fixed_queries(api):
     r = api.requests.get("/fixed_queries")
     assert r.status_code == 200
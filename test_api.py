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
     r = api.requests.get("/all")
     assert r.status_code == 200

def test_squarify(api):
     r = api.requests.post("/squarify",json = {"x":0,"y":0,"width":700,"height":433,"values": [500, 433, 78, 25, 25, 7]} )
     assert r.status_code == 200

def test_people(api):
     r = api.requests.get("/people")
     assert r.status_code == 200

def test_organisations(api):
     r = api.requests.get("/organisations")
     assert r.status_code == 200

def test_neighbours(api):
     r = api.requests.get("/neighbours/811/1")
     assert r.status_code == 200

def test_handles(api):
     r = api.requests.get("/handles")
     assert r.status_code == 200

def test_connectednodes(api):
     r = api.requests.get("/connectednodes")
     assert r.status_code == 200

def test_orphanednodes(api):
     r = api.requests.get("/orphanednodes")
     assert r.status_code == 200

def test_statistics(api):
     r = api.requests.get("/statistics")
     assert r.status_code == 200
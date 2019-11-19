import tweepy
import json
# import jsons
# from bs4 import BeautifulSoup
import requests
from requests.auth import HTTPBasicAuth
import re
import sys
import asyncio
import websockets
# from models import BgpEvent

NEO4J_HOST = "grapho-dev"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "please"
NEO4J_API = "http://grapho-neo4j.hq.modprods.com:7474/db/data"

PUBLIC_URL = "https://api.grapho.app"

SEARCH_QUERY = "#SIGGRAPHAsia"
# See also "realtimelive -filter:retweets"
SEARCH_LIMIT = 100
TWEET_TRUNCATED = 120

# from MyStreamListener import MyStreamListener

# using DataFarms app Twitter credentials
auth = tweepy.OAuthHandler("W42qHPGPgCmClMPLqOo1KH4k3", "UZqQijR5k7yeHRfunVs9qdomPxpjxo4DY8K92gxhCgZBFSsOVn")
auth.set_access_token("792793-SqBcEVSNginYvvaq1Vyl5mIyDRB0rsSxLlwje9tFfJl", "Jb0lNzeJtGh5dxMVAF45HkMEi1V5HbNDKwXlrnpk65hSM")

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# create file handler
fh = logging.FileHandler('twitter-sniffer-debug.log')
fh.setLevel(logging.ERROR)
# create file handler
fh2 = logging.FileHandler('twitter-sniffer-info.log')
fh2.setLevel(logging.INFO)
# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger.addHandler(ch)
logger.addHandler(fh)
logger.addHandler(fh2)

AMQP_URI = "pyamqp://localhost"
WSS_URI = 'wss://api.rackandpin.com/ws/console?subscribe-broadcast&publish-broadcast&echo'

config = {
    'AMQP_URI': AMQP_URI  # e.g. "pyamqp://guest:guest@localhost"
}

class MyStreamListener(tweepy.StreamListener):

    def on_status(self, status):
        # logger.debug("MyStreamListener: {0}".format(status.text))
        save_tweet(status)
        update_handles()

    def on_error(self, status_code):
        logger.error("MyStreamListener on_error: {0}".format(status_code))
        if status_code == 420:
            logger.error("MyStreamListener on_error: disconnecting")
            #returning False in on_error disconnects the stream
            return False

def neo4j_query(query):
    query = query
    data = {'statements': [ 
        {'statement': query, 
        'resultDataContents': ['graph']}]
    }
    # print(data)
    r = requests.post(f'{NEO4J_API}/transaction/commit', \
        headers = {'Content-type': 'application/json'}, \
        json = data, \
        auth=HTTPBasicAuth(NEO4J_USER,NEO4J_PASSWORD) \
        )
    result = json.loads(r.text)
    return(result)

def save_tweet(t):
    q = """
MERGE (u:User {{name: '{0}', label: '{0} (@{1})', screen_name: '{1}', id: {2}, profile_image_url: '{3}', id_str: '{4}' }})
RETURN u.name
""".format(t.user.name,t.user.screen_name,t.user.id,t.user.profile_image_url,t.id_str)
    neo4j_query(q)
    if not (t.text[:4] == 'RT @' or t.retweeted):
        label = t.text[:TWEET_TRUNCATED] + '..' if len(t.text) > TWEET_TRUNCATED else t.text
        # image_url = "{0}/static/img/sample_tweet.png".format(PUBLIC_URL)
        q = """
MERGE (t:Tweet {{text: '{0}',label: '{1}', created_at: datetime('{2}'), id: {3}, source: '{4}', id_str: '{5}' }})
RETURN t.created_at
""".format(t.text, label, t.created_at.isoformat(),t.id,t.source,t.id_str)
        neo4j_query(q)
        q = """
MATCH  (p:User {{id: {0} }})
MATCH  (t:Tweet {{id: {1} }})
MERGE (p)-[r:POSTS]->(t)
RETURN p.name
""".format(t.user.id,t.id)
        neo4j_query(q)
        for h in t.entities['hashtags']:
            q = """
MERGE (h:Hashtag {{name: '{0}', label: '#{0}' }})
RETURN h.name
""".format(h['text'])
            neo4j_query(q)
            q = """
MATCH  (h:Hashtag {{name: '{0}' }})
MATCH  (t:Tweet {{id: {1} }})
MERGE (t)-[r:TAGS]->(h)
RETURN h.name
""".format(h['text'],t.id)
            neo4j_query(q)

        q = """
MERGE (s:Source {{name: '{0}', label: '{0}' }})
RETURN s.name
""".format(t.source)
        neo4j_query(q)
        q = """
MATCH  (s:Source {{name: '{0}' }})
MATCH  (t:Tweet {{id: {1} }})
MERGE (t)-[r:USING]->(s)
RETURN s.name
""".format(t.source,t.id)
        neo4j_query(q)
    else:
        logger.debug("retweet - don't count as Tweet")
        q = """
MATCH  (p:User {{id: {0} }})
MATCH  (t:Tweet {{id: {1} }})
MERGE (p)-[r:RETWEETS]->(t)
RETURN p.name
""".format(t.user.id,t.retweeted_status.id)
        logger.debug(q)
        neo4j_query(q)



def update_handles():
    # ensure Handle exists for each year and update curated NEXT path
    q = """
MATCH (a:Handle)-[r:NEXT]->(b)
DELETE r
RETURN a, b"""
    logger.debug(q)
    neo4j_query(q)
    q = """
MATCH (n:Tweet) WITH n.created_at as date 
MERGE (h:Handle {{label: toString(date.year) }})
RETURN h.label
""".format()
    logger.debug(q)
    neo4j_query(q)
    # get each handle 
    q = """
MATCH (h:Handle) RETURN h
""".format()
    logger.debug(q)
    result = neo4j_query(q)
    # for each Handle
    for n in result['results'][0]['data']:
        q = """
MATCH (n:Tweet) WITH n.created_at as date, n
WHERE date.year = {0}
RETURN n ORDER BY date DESC
""".format(int(n['graph']['nodes'][0]['properties']['label']))
        logger.debug(q)
        result = neo4j_query(q)
        logger.debug("year tweets : {0}".format(result['results']))
        #for each Tweet in year
        firstTweet = True
        for n2 in result['results'][0]['data']:
            if firstTweet:
                q = """
MATCH (h:Handle {{ label: '{0}' }})
MATCH (n:Tweet {{ id: {1} }})
MERGE (h)-[r:NEXT]->(n)
RETURN n
""".format(n['graph']['nodes'][0]['properties']['label'], n2['graph']['nodes'][0]['properties']['id'])
                logger.debug(q)
                neo4j_query(q)
                firstTweet = False
            else:
                q = """
MATCH (t1:Tweet {{ id: {0} }})
MATCH (t2:Tweet {{ id: {1} }})
MERGE (t1)-[r:NEXT]->(t2)
RETURN t1
""".format(previousTweetId, n2['graph']['nodes'][0]['properties']['id'])
                if previousTweetId != n2['graph']['nodes'][0]['properties']['id']:
                    logger.debug(q)
                    neo4j_query(q)
            previousTweetId = n2['graph']['nodes'][0]['properties']['id']               

def process_twitter_feed():
    api = tweepy.API(auth)
    # public_tweets = api.user_timeline("bgpstream",count=50)
    public_tweets = api.search(q=SEARCH_QUERY,count = SEARCH_LIMIT)
    for t in public_tweets:
        save_tweet(t)
    update_handles()
 
def listen_twitter_feed(follow=None, track=None):
    api = tweepy.API(auth)
    myStreamListener = MyStreamListener()   
    myStream = tweepy.Stream(auth = api.auth, listener=myStreamListener)
    if follow:
        myStream.filter(follow=[follow],is_async=True)
    elif track:
        myStream.filter(track=[track],is_async=True)
    else:
        logger.error("listen_twitter_feed: nothing configured to do")

# OFFLINE - cache tweets from feed
process_twitter_feed()

# DEFAULT - listen for new tweets
#listen_twitter_feed(follow="3237083798")
logger.info("listening for tweets containing '{0}'".format(SEARCH_QUERY))
listen_twitter_feed(track=SEARCH_QUERY)

# DEBUGGING
# api = "https://stat.ripe.net/data/bgplay/data.json?resource=140.99.96.0/21&starttime=2019-07-22T17:45:01&unix_timestamps=TRUE"
# event = BgpEvent()
# event.id = 213716
# event.url  = "https://bgpstream.com/event/213716"
# event.api = "https://portal.bgpmon.net/bgpplay_json_wrapper.php?&eventid=213716"
# process_bgp_api(event)

# https://portal.bgpmon.net/bgpplay_json_wrapper.php?&eventid=213716

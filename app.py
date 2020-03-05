import connexion
from connexion import NoContent

import yaml
import logging
import logging.config
import json
from apscheduler.schedulers.background import BackgroundScheduler
import datetime
from datetime import datetime
from datetime import date
import requests
import os
from threading import Thread

with open('app_conf.yaml', 'r') as f:
    app_config = yaml.safe_load(f.read())

with open ('log_conf.yaml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')


def get_ride_stats():

    logger.info("Start request")
    if os.path.exists(app_config['datastore']['filename']):
        with open(app_config['datastore']['filename']) as f:
            data = json.loads(f.read())

        logging.debug("Request data: {}".format(data))

        logging.info("Request complete")

        return data, 200
    else:
        logger.error("File doesn't exist")
        return 404

def populate_stats():
    """ Periodically update stats """
    logger.info("Start periodic testing")
    if os.path.exists(app_config['datastore']['filename']):
        with open(app_config['datastore']['filename']) as f:
            data = json.loads(f.read())
    else:
        currentTime = datetime.now()
        data = {"num_requests": 0,
            "num_reports": 0,
            "updated_timestamp": str(currentTime),
            "num_perfect_ratings": 0,
            "num_bad_ratings": 0}

    currentTime = datetime.now()

    parameters = {'startDate':data['updated_timestamp'], 'endDate': str(currentTime)}

    req = requests.get(app_config['eventstore']['url']+'/request',
                       params=parameters)
    rep = requests.get(app_config['eventstore']['url']+'/report',
                       params=parameters)

    reqStats = req.json()

    repStats = rep.json()

    if req.status_code != 200:
        logger.error("Error:  Did not receive 200 response code")
    else:
        logger.info("Number of Requests: " + str(len(reqStats)))

    if rep.status_code != 200:
        logger.error("Error:  Did not receive 200 response code")
    else:
        logger.info("Number of Reports: " + str(len(repStats)))

    num_of_5s = 0
    bad_ratings = 0
    k = 0
    while k < len(repStats):
        if repStats[k]['rating'] == '5/5':
            num_of_5s += 1
        elif repStats[k]['rating'] == '1/5' or repStats[k]['rating'] == '2/5':
            bad_ratings +=1
        k += 1

    if data.get('num_requests'):
        data['num_requests'] = data['num_requests'] + len(reqStats)
    else:
        data['num_requests'] = len(reqStats)

    if data.get('num_reports'):
        data['num_reports'] = data['num_reports'] + len(reqStats)
    else:
        data['num_reports'] = len(repStats)

    data['updated_timestamp'] = str(currentTime)

    if data.get('num_perfect_ratings'):
        data['num_perfect_ratings'] = data['num_perfect_ratings'] + num_of_5s
    else:
        data['num_perfect_ratings'] = num_of_5s

    if data.get('num_bad_ratings'):
        data['num_bad_ratings'] = data['num_bad_ratings'] + bad_ratings
    else:
        data['num_bad_ratings'] = bad_ratings

    with open(app_config['datastore']['filename'], "w") as f:
        f.write(json.dumps(data))

    logger.debug("Total number of requests: " + str(data['num_requests']) + ' ' +
                 "Total number of reports: " + str(data['num_reports']) + ' ' +
                 "Timestamp: " + str(data['updated_timestamp']) + ' ' +
                 "Total number of perfect ratings: " + str(data['num_perfect_ratings']) + ' ' +
                 "Total number of bad ratings: " + str(data['num_bad_ratings']))

    logger.info("Processing finished")

def init_scheduler():
    sched = BackgroundScheduler(daemon=True)
    sched.add_job(populate_stats,
                  'interval',
                  seconds=app_config['scheduler']['period_sec'])
    sched.start()


app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yaml")

if __name__ == "__main__":
    init_scheduler()

    app.run(port=8100, use_reloader=False)


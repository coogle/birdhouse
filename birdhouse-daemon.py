from BirdHouse import BirdHouse
import warnings
import json
import argparse

ap = argparse.ArgumentParser()

ap.add_argument("-c", "--config", required = True, help = "Path to the JSON configuration file")

args = vars(ap.parse_args())

warnings.filterwarnings("ignore")

birdhouse = BirdHouse(json.load(open(args["config"])))
birdhouse.run()

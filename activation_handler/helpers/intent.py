from snips_nlu import SnipsNLUEngine
import json
import io
DATASET="dataset.json"
snips = SnipsNLUEngine()
with io.open(DATASET) as f:
    dataset=json.load(f)
    snips.fit(dataset)



import json
import os

absolute_config_path = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(absolute_config_path, 'configs', 'templates.json'), 'r') as f:
    jsonConfig = json.load(f)

TEMPLATES = jsonConfig['templates']
REVIEWERS = jsonConfig['reviewers']
PRODUCTION_MAPPINGS = jsonConfig.get('productionMappings', {})

from pprint import pprint

import requests


payload = {'words': 'три;random;слова'}


res = requests.post("http://localhost:8082", data=payload)

data = res.json()

pprint(data)
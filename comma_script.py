import json

with open("train_expanded.json") as f:
    data = [json.loads(line) for line in f]

with open("FAQs.json", "w") as f:
    json.dump(data, f, indent=4)
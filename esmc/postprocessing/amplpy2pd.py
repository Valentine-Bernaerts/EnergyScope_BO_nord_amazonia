import json

def print_json(my_sets, file):  # printing the dictionary containing all the sets into directory/sets.json
        with open(file, 'w', encoding='utf-8') as fp:
            json.dump(my_sets, fp, indent=4, sort_keys=True)
        return

def read_json(file):
        # reading the saved dictionary containing all the sets from directory/sets.json
        with open(file, 'r', encoding='utf-8-sig') as fp:
            text = fp.read()
        if not text.strip():
            return {}
        return json.loads(text)


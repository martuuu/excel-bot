import json

cookies = []
with open('API-calls/cookies.txt', 'r') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        parts = line.split('\t')
        if len(parts) >= 3:
            name = parts[0]
            value = parts[1]
            domain = parts[2]
            cookies.append({"name": name, "value": value, "domain": domain})

with open('cookies.json', 'w') as f:
    json.dump(cookies, f, indent=4)

print("cookies.json created.")

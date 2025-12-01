# inference/commenter.py
import yaml

RULE_FILE = "comment_rules.yaml"

def load_rules():
    try:
        with open(RULE_FILE, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except:
        return {}

rules = load_rules()

def generate_comments(detections):
    if not rules:
        return ["⚠ No comment rules loaded."]

    results = []

    for det in detections:
        label = det.get("label", "").lower().strip()

        # Exact match
        if label in rules and isinstance(rules[label], str):
            results.append(rules[label])
            continue

        # Partial match with subrules
        for key, val in rules.items():
            if key in label and isinstance(val, dict):
                matched = False
                for skey, msg in val.items():
                    if skey in label:
                        results.append(msg)
                        matched = True
                        break
                if not matched:
                    results.append(list(val.values())[0])
                break

        else:
            if "default" in rules:
                results.append(rules["default"])

    # Remove duplicates
    return list(dict.fromkeys(results))

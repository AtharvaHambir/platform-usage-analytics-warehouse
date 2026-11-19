"""Generate deterministic November 2025 source deliveries and reference data."""
import csv
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
START = date(2025, 11, 1)
SOURCES = {"api": 4800, "usage": 2800, "billing": 800}
FIELDS = "delivery_id event_id event_day external_id kind amount_cents units status latency_ms feature_id client_id endpoint_id user_id session_id currency".split()


def write_csv(path, fields, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(fields)
        writer.writerows(rows)


def deliveries(source, per_day):
    for day in range(30):
        for pos in range(per_day):
            index = day * per_day + pos
            owner = pos % 200
            account = {"api": "A", "usage": "W", "billing": "B"}[source] + str(owner)
            kind = source
            amount = units = status = latency = feature = client = endpoint = user = session = currency = None
            if source == "api":
                status = 503 if index % 47 == 0 else 200
                latency, client, endpoint = 20 + index % 371, index % 3, index % 5
            elif source == "usage":
                if pos == 0:
                    account = "W-unmapped"
                units, feature = 1 + index % 7, index % 4
                user = owner + 200 * ((pos // 200) % 2)
                session = f"S{day}-{user}-{pos // 800}"
            else:
                kind = ("invoice", "payment", "credit")[(pos // 200 + day) % 3]
                amount = -250 if kind == "credit" else 1000 + owner
                currency = "USD" if owner % 2 else "EUR"
            event_id = f"{source}-{index}"
            row = [event_id, str(START + timedelta(days=day)), account, kind, amount, units,
                   status, latency, feature, client, endpoint, user, session, currency]
            yield [event_id + "-a", *row]
            if index % 1000 == 0:
                yield [event_id + "-b", *row]


def generate():
    for source, size in SOURCES.items():
        write_csv(ROOT / "data" / f"{source}.csv", FIELDS, deliveries(source, size))
    write_csv(ROOT / "seeds" / "identity_map.csv", ["source_name", "external_id", "customer_id"],
              ((s, prefix + str(n), n) for s, prefix in (("api", "A"), ("billing", "B"), ("usage", "W")) for n in range(200)))
    changes = [(n, "2025-11-01", "basic") for n in range(200)]
    changes += [(n, "2025-11-16", "pro") for n in range(0, 200, 2)]
    write_csv(ROOT / "seeds" / "plan_changes.csv", ["customer_id", "effective_day", "plan_id"], changes)


if __name__ == "__main__":
    generate()

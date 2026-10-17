
import csv
import datetime
import io
import json
import pathlib
import os
ROOT = pathlib.Path(__file__).resolve().parent
ADS = ROOT / "content" / "ads"

LIMITS = {
    "Premium-Startseite": 1,
    "Standard-Startseite": 3,
    "Rubrikensponsor": 1,
}

RESERVED_STATUSES = {"Reserviert", "Bestätigt"}


def load_bookings():
    bookings = []

    if not ADS.exists():
        return bookings

    for file in sorted(ADS.glob("*.json")):
        data = json.loads(file.read_text(encoding="utf-8"))
        status = data.get("booking_status", "")

        if status not in RESERVED_STATUSES:
            continue

        try:
            start = datetime.date.fromisoformat(
                str(data.get("start_date", ""))[:10]
            )
            end = datetime.date.fromisoformat(
                str(data.get("end_date", ""))[:10]
            )
        except (ValueError, TypeError):
            print("WARNUNG: Ungueltiges Datum:", file.name)
            continue

        if end < start:
            print("WARNUNG: Enddatum vor Startdatum:", file.name)
            continue

        placement = data.get("placement", "")
        if placement not in LIMITS:
            continue

        category = (
            data.get("category", "")
            if placement == "Rubrikensponsor"
            else ""
        )

        if placement == "Rubrikensponsor" and not category:
            print("WARNUNG: Rubrik fehlt:", file.name)
            continue

        bookings.append({
            "number": str(data.get("booking_number") or ""),
            "placement": placement,
            "category": category,
            "start": start,
            "end": end,
            "status": status,
        })

    return sorted(
        bookings,
        key=lambda b: (
            b["placement"],
            b["category"],
            b["start"],
            b["end"],
        ),
    )


def create_report(bookings):
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")

    writer.writerow([
        "Auftragsnummer",
        "Werbeplatz",
        "Rubrik",
        "Beginn",
        "Ende",
        "Buchungsstatus",
    ])

    for booking in bookings:
        writer.writerow([
            booking["number"],
            booking["placement"],
            booking["category"],
            booking["start"].isoformat(),
            booking["end"].isoformat(),
            booking["status"],
        ])

    return output.getvalue()


def check_conflicts(bookings):
    groups = {}

    for booking in bookings:
        key = (booking["placement"], booking["category"])
        groups.setdefault(key, []).append(booking)

    conflicts = []

    for key, entries in groups.items():
        events = []

        for booking in entries:
            events.append((booking["start"], 1))
            events.append((
                booking["end"] + datetime.timedelta(days=1), -1
            ))

        events.sort()

        count = 0
        limit = LIMITS[key[0]]
        conflict_start = None

        for date, change in events:
            previous = count
            count += change

            if previous <= limit and count > limit:
                conflict_start = date

            if previous > limit and count <= limit:
                conflicts.append((key, conflict_start, date))
                conflict_start = None

    return conflicts


def check_availability(bookings, placement, start, end, category=""):
    if placement not in LIMITS:
        raise ValueError("Unbekannter Werbeplatz")

    if end < start:
        raise ValueError("Enddatum liegt vor dem Startdatum")

    if placement == "Rubrikensponsor" and not category:
        raise ValueError("Bitte eine Rubrik angeben")

    limit = LIMITS[placement]
    events = []

    for booking in bookings:
        if booking["placement"] != placement:
            continue

        if placement == "Rubrikensponsor":
            if booking["category"] != category:
                continue

        overlap_start = max(start, booking["start"])
        overlap_end = min(end, booking["end"])

        if overlap_start > overlap_end:
            continue

        events.append((overlap_start, 1))
        events.append((
            overlap_end + datetime.timedelta(days=1), -1
        ))

    events.sort()

    occupied = 0
    max_occupied = 0

    for date, change in events:
        occupied += change
        max_occupied = max(max_occupied, occupied)

    return max(0, limit - max_occupied)

def main():
    bookings = load_bookings()
    request_start = os.environ.get("BOOKING_START", "")
    request_end = os.environ.get("BOOKING_END", "")

    if request_start and request_end:
        start = datetime.date.fromisoformat(request_start)
        end = datetime.date.fromisoformat(request_end)
        print("VERFUEGBARKEIT", start, "bis", end)

        for placement in ("Premium-Startseite", "Standard-Startseite"):
            free = check_availability(bookings, placement, start, end)
            print(placement + ":", free, "freie Plaetze")

        for category in (
            "Aktuelles", "Blaulicht", "Verkehr", "Politik",
            "Wirtschaft", "Veranstaltungen", "Sport", "Stadtgeschichte"
        ):
            free = check_availability(
                bookings, "Rubrikensponsor", start, end, category
            )
            print("Rubrikensponsor " + category + ":", free, "freie Plaetze")


    report = create_report(bookings)
    conflicts = check_conflicts(bookings)

    report_file = ROOT / "buchungsuebersicht.csv"
    report_file.write_text(
        "\ufeff" + report, encoding="utf-8"
    )

    print("Buchungen im Bericht:", len(bookings))
    print("Bericht erstellt: buchungsuebersicht.csv")

    if conflicts:
        for key, start, end_exclusive in conflicts:
            end = end_exclusive - datetime.timedelta(days=1)
            print(
                "UEBERBUCHUNG:",
                key[0],
                key[1],
                start.isoformat(),
                "bis",
                end.isoformat(),
            )
    else:
        print("Keine Ueberbuchungen festgestellt.")


if __name__ == "__main__":
    main()

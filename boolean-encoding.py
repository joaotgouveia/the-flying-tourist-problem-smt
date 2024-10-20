import datetime
from z3 import Optimize, Implies, Bool, Sum, Or, Not, sat


def parse():
    # Number of cities to visit
    n = int(input())

    # Dictionary of cities to visit, the key is the airport code.
    base = input().split()
    cities = {base[1]: {"name": base[0], "arrivals": [], "departures": []}}
    for _ in range(n - 1):
        city = input().split()
        cities[city[1]] = {
            "name": city[0],
            "kmin": int(city[2]),
            "kmax": int(city[3]),
            "arrivals": [],
            "departures": [],
        }

    # Number of flights available
    m = int(input())
    lastDate = ""
    currentDay = 0

    for i in range(m):
        line = input().split()

        date = line[0].split("/")
        date = datetime.date(2023, int(date[1]), int(date[0]))

        if i == 0:
            lastDate = date
        elif lastDate != date:
            currentDay += (date - lastDate).days
            lastDate = date

        flight = {
            "day": currentDay,
            "date": line[0],
            "departure": line[1],
            "arrival": line[2],
            "departureTime": line[3],
            "arrivalTime": line[4],
            "cost": int(line[5]),
            "id": i,
        }

        cities[line[1]]["departures"].append(flight)
        cities[line[2]]["arrivals"].append(flight)

    base = base[1]
    return m, base, cities


def printModel(model, cities):
    cost = 0
    takenFlights = []
    for airport in cities:
        for flight in cities[airport]["arrivals"]:
            if flight["id"] in model:
                cost += flight["cost"]
                takenFlights.append(flight)

    print(cost)
    takenFlights.sort(key=(lambda x: x["day"]))
    for flight in takenFlights:
        print(
            (
                f"{flight['date']} "
                f"{cities[flight['departure']]['name']} "
                f"{cities[flight['arrival']]['name']} "
                f"{flight['departureTime']} {flight['cost']}"
            )
        )


def solve(flightCount, base, cities):
    solver = Optimize()

    f = [None for i in range(flightCount)]
    for airport in cities:
        for flight in cities[airport]["arrivals"]:
            f[flight["id"]] = Bool("f_%i" % flight["id"])
            solver.add_soft(Not(f[flight["id"]]), flight["cost"])

    # We can't have a flight before our departure from the base.
    for departure in cities[base]["departures"]:
        for airport in cities:
            if airport != base:
                for flight in cities[airport]["departures"]:
                    if not flight["day"] > departure["day"]:
                        solver.add(Implies(f[departure["id"]], Not(f[flight["id"]])))

    # After arriving in a city, we must depart between kmin and kmax days later.
    for airport in cities:
        # We do not care about arrivals in the base
        if airport != base:
            for arrival in cities[airport]["arrivals"]:
                departures = []
                for departure in cities[airport]["departures"]:
                    if (
                        departure["day"] >= arrival["day"] + cities[airport]["kmin"]
                        and departure["day"] <= arrival["day"] + cities[airport]["kmax"]
                    ):
                        departures.append(departure["id"])

                departures = Or([f[i] for i in departures])
                solver.add(Implies(f[arrival["id"]], departures))

    # We must arrive at each city exactly once.
    for airport in cities:
        arrivals = [f[flight["id"]] for flight in cities[airport]["arrivals"]]
        solver.add(Sum(arrivals) == 1)

    # We must depart from the base exactly once.
    baseDepartures = [f[flight["id"]] for flight in cities[base]["departures"]]
    solver.add(Sum(baseDepartures) == 1)

    flightsTaken = []
    if solver.check() == sat:
        model = solver.model()
        for i in range(len(f)):
            if model[f[i]]:
                flightsTaken.append(i)

    return flightsTaken


if __name__ == "__main__":
    flightCount, base, cities = parse()
    model = solve(flightCount, base, cities)
    printModel(model, cities)

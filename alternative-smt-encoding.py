import datetime
from z3 import Optimize, Implies, Function, IntVector, IntSort, Sum, Or, And, unsat


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

    flightsToTake = len(cities.keys())
    solver = Optimize()

    # Id of every flight we'll take, in order
    f = IntVector("f", flightsToTake)

    # Cost function
    cost = Function("cost", IntSort(), IntSort())
    for airport in cities:
        for flight in cities[airport]["arrivals"]:
            solver.add(
                [
                    Implies(f[i] == flight["id"], cost(f[i]) == flight["cost"])
                    for i in range(flightsToTake)
                ]
            )

    # We must pick the ids from the available flights
    solver.add([And(f_i >= 0, f_i < flightCount) for f_i in f])

    # Our first flight must depart from the base
    baseDepartures = Or([f[0] == flight["id"] for flight in cities[base]["departures"]])
    solver.add(baseDepartures)

    # Our last flight must arrive at the base
    baseArrivals = Or([f[-1] == flight["id"] for flight in cities[base]["arrivals"]])
    solver.add(baseArrivals)

    # Each flight must arrive at a different city
    for i in range(flightsToTake):
        for airport in cities:
            fiArrivals = Or(
                [f[i] == flight["id"] for flight in cities[airport]["arrivals"]]
            )
            for j in range(i + 1, flightsToTake):
                fjArrivals = And(
                    [f[j] != flight["id"] for flight in cities[airport]["arrivals"]]
                )
                solver.add(Implies(fiArrivals, fjArrivals))

    # After arriving in a city, we must depart between kmin and kmax days later.
    for i in range(flightsToTake - 1):
        for airport in cities:
            # We do not care about arrivals in the base
            if airport != base:
                for arrival in cities[airport]["arrivals"]:
                    departures = []
                    for departure in cities[airport]["departures"]:
                        if (
                            departure["day"] >= arrival["day"] + cities[airport]["kmin"]
                            and departure["day"]
                            <= arrival["day"] + cities[airport]["kmax"]
                        ):
                            departures.append(departure["id"])

                    departures = Or([f[i + 1] == fID for fID in departures])
                    solver.add(Implies(f[i] == arrival["id"], departures))

    # We want to minimize the total cost of our trip
    solver.minimize(Sum([cost(f_i) for f_i in f]))

    if solver.check() == unsat:
        return 0, []

    model = solver.model()
    flightsTaken = [model[f_i].as_long() for f_i in f]

    return flightsTaken


if __name__ == "__main__":
    flightCount, base, cities = parse()
    model = solve(flightCount, base, cities)
    printModel(model, cities)

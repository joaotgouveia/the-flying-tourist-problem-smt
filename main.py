import datetime
from z3 import Optimize, And, Distinct, Implies, Sum, IntVector, unsat


def equal_flights(f1, f2):
    return (
        f1["day"] == f2["day"]
        and f1["arrival"] == f2["arrival"]
        and f1["departure"] == f2["departure"]
    )


def parse():
    # Number of cities to visit
    n = int(input())

    # Dictionary of cities to visit, the key is the airport code
    base = input().split()
    cities = {base[1]: {"name": base[0], "id": 0}}
    for i in range(n - 1):
        city = input().split()
        cities[city[1]] = {
            "name": city[0],
            "kmin": int(city[2]),
            "kmax": int(city[3]),
            "id": i + 1,
        }

    # Number of flights available
    m = int(input())
    lastDate = ""
    currentDay = 0

    # Array of flights available
    flights = []
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
        }

        duplicate = False
        for f in flights:
            if equal_flights(f, flight):
                duplicate = True
                if flight["cost"] < f["cost"]:
                    f["cost"] = flight["cost"]
                    f["departureTime"] = flight["departureTime"]
                    f["arrivalTime"] = flight["arrivalTime"]

        if not duplicate:
            flights.append(flight)

    return cities, flights


def printModel(model, cities, flights):
    for i in model:
        print(
            (
                f"{flights[i]['date']} "
                f"{cities[flights[i]['departure']]['name']} "
                f"{cities[flights[i]['arrival']]['name']} "
                f"{flights[i]['departureTime']} {flights[i]['cost']}"
            )
        )


def solve(cities, flights):
    flightsToTake = len(cities.keys())
    maxId = len(flights)
    solver = Optimize()

    # Id of every flight we'll take, in order
    f = IntVector("f", flightsToTake)

    # Cost of every flight we'll take, in order
    cost = IntVector("c", flightsToTake)

    # Day of every flight we'll take, in order
    date = IntVector("d", flightsToTake)

    # Arrival of every flight we'll take, in order
    arrival = IntVector("a", flightsToTake)

    # Departure of every flight we'll take, in order
    origin = IntVector("o", flightsToTake)

    for flightId in range(maxId):
        solver.add(
            [
                Implies(
                    f[i] == flightId,
                    And(
                        cost[i] == flights[flightId]["cost"],
                        date[i] == flights[flightId]["day"],
                        arrival[i] == cities[flights[flightId]["arrival"]]["id"],
                        origin[i] == cities[flights[flightId]["departure"]]["id"],
                    ),
                )
                for i in range(flightsToTake)
            ]
        )

    # We must pick the ids from the available flights
    solver.add([And(f_i >= 0, f_i < maxId) for f_i in f])

    # Our first flight must depart from the base
    solver.add(origin[0] == 0)

    # Our last flight must arrive at the base
    solver.add(arrival[-1] == 0)

    # Each flight must arrive at a different city
    solver.add(Distinct(arrival))

    for i in range(flightsToTake - 1):
        # We must depart from the city we previously arrived at
        solver.add(origin[i + 1] == arrival[i])

        # We must respects the provided stay times
        for airport in cities:
            if cities[airport]["id"] != 0:
                flightDate = And(
                    date[i + 1] - date[i] >= cities[airport]["kmin"],
                    date[i + 1] - date[i] <= cities[airport]["kmax"],
                )
                solver.add(Implies(arrival[i] == cities[airport]["id"], flightDate))

    # We want to minimize the total cost of our trip
    solver.minimize(Sum(cost))

    if solver.check() == unsat:
        return 0, []

    model = solver.model()
    cost = sum([model[c_i].as_long() for c_i in cost])
    flightsTaken = [model[f_i].as_long() for f_i in f]

    return cost, flightsTaken


if __name__ == "__main__":
    cities, flights = parse()
    cost, model = solve(cities, flights)
    print(cost)
    printModel(model, cities, flights)

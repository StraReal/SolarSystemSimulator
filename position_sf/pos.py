from skyfield.api import load, Topos
import skyfield.errors as SKErr
import datetime
import pathlib

max_date = datetime.datetime(year=2650, month=1, day=25)
min_date = datetime.datetime(year=1550, month=1, day=1)

def init():
    global planets
    _this_dir = pathlib.Path(__file__).parent
    _kernel_path = _this_dir / 'de440.bsp'
    planets = load(str(_kernel_path))


def get_position(planet:str='earth', date:datetime.datetime=datetime.datetime.now):
    # Load planetary ephemeris (DE440)

    sat   = planets[planet]
    sun     = planets['sun']

    date = max(min(max_date, date), min_date)

    # Skyfield expects a TimeScale object
    ts = load.timescale()
    t = ts.utc(date.year, date.month, date.day,
               date.hour, date.minute, date.second)

    # Get Earth’s position relative to the Sun
    vec = sat.at(t).observe(sun).position.km   # vector Sun->Earth in km
    x, y, z = vec
    return x, y, z, date


if __name__ == '__main__':
    init()
    x, y, z, date = get_position()
    print(f"Earth (Sun‑centered) today")
    print(f"  x = {x:,.0f} km")
    print(f"  y = {y:,.0f} km")
    print(f"  z = {z:,.0f} km")
-- ***Solar System Simulator*** --

What this project aims to do is simply simulate interactions between celestial bodies. There are some important things to note about it:

- The Space is relative to the Sun, and the Sun is not affected by gravitational forces, although it does exert its own on other planets.

- Unless Real-Size mode is used, Planets will be scaled to be 300 times their real size, and the sun to be 25 times its real size.

- Initial orbits are perfectly circular

- For some reason I still haven't figured out, although everything works perfectly, the velocities are much bigger than real ones.

- In the code, the variable FULL_SYSTEM is False, meaning that Mercury, Uranus and Neptune are removed, to achieve a better-looking system. They can be added back by making the variable True.

Starting the simulation for the first time will download real planet positions using the Skyfield module, which means it might take a moment to start-up the first time.

== **Controls** ==

C - Toggle between Heliocentric view and freecam

Space - Pause

Left Click (on space) - Keep holding to move in space

Left Click (on planet) - Goes into "Launching" mode; you can pull and, on release, the planet will be launched in the opposite direction

Right Click (on planet) - Follow planet, stop following by right-clicking anywhere else

Mouse Wheel - Zoom

S - Toggle Settings

Q - Create planet at current mouse position

R - Real-Time mode; time will pass at 1:1 to real life.

P - Real-Size mode; planets will scale to their actual size. More realistic, but space between planets are absolutely gargantuan compared to the planets.

D - Clear tails
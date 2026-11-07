jack-link-flex v0.1 for PCBWay's flex line (DRC clean).
STATUS: geometry per Hirose's recommended FPC; for the PCBWay pre-quote [Ed 7 Nov Q30 = A]: PCBWay hot-bar bonds the
main-board end onto the main board during the PCBA (to confirm); fallback: shipped loose, hand-soldered on the bench.

Outline 7.8 x 18.81 mm (Edge.Cuts), corners R0.15 at the FH26W end (R0.2 max [S]). Single-sided flex: polyimide 25 um base,
1/2 oz (18 um) rolled-annealed copper, polyimide coverlay 25 um + adhesive on the copper side with openings at both ends (F.Mask);
ENIG on the openings [A]. No holes, no vias. Min copper gap 0.1 (in the FH26W contact zone, Hirose's pattern), 0.15 elsewhere.
Stiffener (User.1): polyimide on the BACK (non-copper side) of the FH26W end, 4 mm from the end, 0.07 inside each edge,
thick enough for 0.20 +/- 0.03 mm total over the contacts [S Hirose: 0.2 +/- 0.03, stiffener 3.5 min].
FH26W end [S Hirose FH26 catalogue p. 8]: staggered contacts. Odd pins 0.3 wide from 0.3 to 1.0 from the end, 0.1 neck to 2.1;
even pins from a point at 1.0, 0.3 wide 1.1 to 2.1; both 0.2 from 2.25; coverlay opening to 2.5 (+/- 0.3). Width 7.8, span C 7.2, B 6.6.
(The tapers are staggered within Hirose's tolerances, odd 1.0-1.05 / even to 1.15 and even 2.1-2.2 / odd 2.2-2.3, so no gap is under 0.1.)
Bottom end: 25 solder fingers 0.15 wide, exposed 0.10-0.90 from the end, bonded face down onto the main board's pads (footprint
LinkFlex_MainBoard_Pads_25x0.3).
Installed bent twice (once): r 1.6 and r 1.03 inner radius (bend lines on User.2).

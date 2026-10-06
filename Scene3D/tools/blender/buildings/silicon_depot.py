"""SILICON_DEPOT: tall monolithic vault block with dark rack bays and violet accent strips
(concept style-library/styles/cqs-fleet/images/buildings/silicon_depot-concept.jpg).

Composed from fal components (assets/parts-colony: vaultBay x3, rackBay, entrancePorch; README-colony.md catalogue)
on the shared parametric kit (bkit: the core block and +X annex, roof crown and head houses, plinth, pipes, dressing,
lights). Built by colony_build.py:
    $PY tools/blender/buildings/colony_build.py silicon_depot <work> [--tex 4096]

Frame: metres, plinth top y = 0, +Z front, +X left. The concept camera looks from the front-left (az ~33, el ~24):
the long front with its four tall bays runs left on screen from the near corner, the +X side (annex, violet strip,
tall slot) recedes to the right.
Sizes (real-world, the concept's proportions against its double crew door and rack crates): vault block 50 x 26 m,
30 m to the bay hoods (four 11 m bays, doors 7.5 x 23 m), roof crown to 33 m, +X head tower to 38 m; annex 10 x 20 m,
26 m; slab 76 x 56 m.
"""
import bkit as K

SPEC = {
    'title': 'Silicon Depot', 'gameId': 'SILICON_DEPOT', 'group': 'storage',
    'footprint': [74, 48], 'height': 38.0,
    'camera': {'az': 26, 'el': 18},
    'about': 'monolithic vault block: four 30 m bays (three sealed vault doors, one open rack bay of crated silicon), violet accent strips, +X annex, entrance porch, roof crown and head tower',
}

X0, X1 = -25.0, 27.0       # core block x extent
Z0, Z1 = -14.0, 10.0       # core block z extent (front face z = Z1)
H = 30.0                   # core / hood height
BAYS = (-18.75, -6.25, 6.25, 18.75)   # bay centres (x): the 12.5 m fal bays side by side; the open rack bay is the +X one (nearest the camera)
BAY_Z = Z1 + 3.0           # bay component centre (z): 9 m deep, its back 1.5 m inside the core, piers proud of the face


def model(B):
    W, D = SPEC['footprint']
    CX, CZ = 5.0, 3.0
    FZ = CZ + D / 2
    K.plinth(B, W, D, h=1.4, chamfer=2.0, slab=7.0, lamp_pitch=16.0, centre=(CX, CZ),
             markings=[([(-31.0, FZ - 2.0), (41.0, FZ - 2.0)], 0.18, 'frame2'),
                       ([(40.0, FZ - 2.0), (40.0, -19.0)], 0.18, 'frame2'),
                       ([(10.0, 20.5), (10.0, FZ - 2.0)], 0.12, 'white'),
                       ([(14.0, 20.5), (14.0, FZ - 2.0)], 0.12, 'white'),
                       ([(19.0, 20.5), (19.0, FZ - 2.0)], 0.12, 'white')],
             grates=[(-12.0, FZ - 3.0, 2.2, 0.8), (30.0, FZ - 3.0, 2.2, 0.8), (39.5, -6.0, 0.8, 2.2)],
             steps=[(-26.0, FZ, '+z')])

    # --- the vault core (parametric): plain light walls behind the fal bays, dark base band, seamed back and -X sides
    K.block(B, ((X0 + X1) / 2, 0.0, (Z0 + Z1) / 2), (X1 - X0, H, Z1 - Z0),
            sides={'+z': {'bay': 12.5, 'storey': 7.5, 'base': 3.0, 'bands': False, 'seams': False},
                   '-z': {'bay': 6.0, 'storey': 7.5, 'base': 3.0, 'windows': [0], 'win': (1.2, 1.0)},
                   '-x': {'bay': 6.0, 'storey': 7.5, 'base': 3.0, 'louvres': [(12.0, 24.0, 3.0, 2.4)]},
                   '+x': {'skip_face': True}},
            roof={'parapet': 0.0, 'mat': 'panel2'}, post=1.2)
    # light parapet cap round the vault roof (the concept's roof edge reads pale, not as a dark outline)
    for (cx, cz, w, d) in (((X0 + X1) / 2, Z1 - 0.3, X1 - X0, 0.6), ((X0 + X1) / 2, Z0 + 0.3, X1 - X0, 0.6),
                           (X0 + 0.3, (Z0 + Z1) / 2, 0.6, Z1 - Z0)):
        B.box((w, 0.9, d), at=(cx, H + 0.45, cz), mat='panel2', bevel=0.08)
    # the four tall bays (fal components): three sealed vault doors, the open rack bay at the +X end
    for i, x in enumerate(BAYS):
        # the parts' front is their +X (Tripo H3.1 frame, catalogue note): heading -90 turns it to the building front
        K.component(B, 'rackBay' if i == 3 else 'vaultBay', (x, 0.0, BAY_Z), heading=-90.0)
    # rack bay interior glow (the crated racks lit from inside) and amber lamps at the hood lamp bars
    B.R.glowbox((BAYS[3], 13.0, BAY_Z - 2.5), (7.0, 20.0, 0.2), color='#ffb766', radiance=0.2)
    for x in BAYS:
        B.R.pin((x, H - 3.4, BAY_Z + 3.2))
        for y in (5.0, 11.0, 17.0):                          # small amber lamps up the door guide rail
            B.R.pin((x + 3.3, y, BAY_Z + 2.0))

    # --- +X annex (parametric): nearly full height, big plain light panels (the concept's side wall), the wide violet
    # band, a tall dark slot and a crew door; light frames so the side reads as one pale mass, not a dark grid
    AX0, AX1, AZ0, AZ1, AH = X1, 35.0, -14.0, 7.0, 28.0
    K.block(B, ((AX0 + AX1) / 2, 0.0, (AZ0 + AZ1) / 2), (AX1 - AX0, AH, AZ1 - AZ0),
            sides={'+x': {'bay': 10.5, 'storey': 9.0, 'base': 3.2, 'bands': False, 'doors': [17.5],
                          'louvres': [(3.0, 1.0, 2.4, 1.6)], 'slots': [(11.5, 10.0, 1.4, 15.0)]},
                   '+z': {'bay': 8.0, 'storey': 9.0, 'base': 3.2, 'bands': False, 'louvres': [(4.0, 22.0, 2.6, 2.4)]},
                   '-z': {'bay': 8.0, 'storey': 9.0, 'base': 3.2, 'bands': False}},
            roof={'parapet': 0.5, 'units': [('hvac', 0.0, -4.0, {'w': 3.4, 'd': 2.2}), ('vent', 2.0, 5.0, {})]}, post=0.8,
            frame='frame2')
    B.box((0.1, 19.0, 3.4), at=(AX1 + 0.4, 14.0, -7.5), mat='violet', bevel=0.0)          # wide violet band (+X face)
    B.box((0.1, 4.0, 1.4), at=(AX1 + 0.4, 3.2 + 2.0, -8.4), mat='violet', bevel=0.0)        # its foot (the concept's step)
    # tall front pier of the core where it meets the annex (the concept's light corner pier with the dark slot)
    B.box((4.0, H + 0.6, 4.0), at=(X1 - 1.0, (H + 0.6) / 2, Z1 + 1.0), mat='panel', bevel=0.12)
    B.box((4.2, 3.0, 4.2), at=(X1 - 1.0, 1.5, Z1 + 1.0), mat='frame', bevel=0.05)
    B.box((0.9, 14.0, 0.12), at=(X1 + 1.05, 18.0, Z1 + 1.0), mat='glassW', bevel=0.0)      # dark slot (+X face of the pier)
    B.box((1.2, 14.4, 0.2), at=(X1 + 1.0, 18.0, Z1 + 1.0), mat='frame', bevel=0.02)
    # down pipes on the annex front and +X face into ground cabinets
    K.pipe(B, [(AX1 - 1.2, AH - 1.0, AZ1 + 0.5), (AX1 - 1.2, 1.2, AZ1 + 0.5), (AX1 - 1.2, 1.2, AZ1 + 3.0)], r=0.25, rings=True)
    K.pipe(B, [(AX1 + 0.5, 22.0, -2.0), (AX1 + 0.5, 1.4, -2.0), (AX1 + 3.0, 1.4, -2.0)], r=0.3, rings=True)
    K.pipe(B, [(AX1 + 0.5, 22.0, -1.2), (AX1 + 0.5, 1.0, -1.2), (AX1 + 3.0, 1.0, -1.2)], r=0.2, rings=False)

    # --- roof: low crown strip with louvres just behind the bay hoods, a central head house with antennas, the +X head tower
    K.block(B, (-1.0, H, 1.0), (44.0, 2.4, 8.0),
            sides={'+z': {'bay': 5.0, 'base': 0.0, 'bands': False, 'seams': False,
                          'louvres': [(5.0, 0.6, 3.2, 1.6), (15.0, 0.6, 3.2, 1.6), (25.0, 0.6, 3.2, 1.6), (35.0, 0.6, 3.2, 1.6)]}},
            roof={'parapet': 0.0, 'mat': 'panel2', 'units': [('hvac', -12.0, 0.0, {'w': 3.6, 'd': 2.4}), ('hvac', 10.0, 0.0, {'w': 3.6, 'd': 2.4})]},
            post=0.5, y0=H, corner_lamps=False, frame='panel2')
    K.block(B, (-2.0, H + 2.4, 1.0), (8.0, 3.2, 6.0),
            sides={'+z': {'bay': 4.0, 'base': 0.0, 'windows': [0], 'win': (1.2, 0.9)}},
            roof={'parapet': 0.3, 'units': [('antenna', -2.0, 0.0, {'h': 5.0}), ('antenna', 2.0, 1.0, {'h': 7.0})]},
            post=0.4, frame='panel2')
    K.block(B, (30.0, 28.0, 1.0), (8.0, 10.0, 10.0),
            sides={'+z': {'bay': 4.5, 'storey': 4.0, 'base': 0.0, 'louvres': [(4.5, 4.0, 3.0, 2.4)], 'bands': False},
                   '+x': {'bay': 5.0, 'storey': 4.0, 'base': 0.0, 'windows': [1], 'win': (1.2, 1.0)}},
            roof={'parapet': 0.4, 'units': [('antenna', -2.5, -2.0, {'h': 6.0}), ('antenna', 2.5, 2.0, {'h': 8.0}),
                                            ('vent', 0.0, 2.0, {})]},
            post=0.6, frame='panel2')
    for (x, z) in ((-18.0, 2.0), (-10.0, 3.0), (8.0, 3.0), (14.0, 2.5)):
        K.vent_box(B, (x, H + 0.12, z), w=1.6, d=1.2, h=0.8)
    K.hvac(B, (31.0, AH + 0.12, 2.0), w=3.0, d=2.0)
    B.R.beacon((0.0, H + 5.6 + 7.4, 2.0))
    B.R.beacon((32.5, 38.4 + 8.4, 3.0))
    B.R.pin((34.3, 38.2, 6.3))
    B.R.pin((25.7, 38.2, 6.3))

    # --- the entrance porch (fal component) against the pier between the second and third bays, ramp to the front
    K.component(B, 'entrancePorch', (0.0, 0.0, BAY_Z + 8.4), heading=-90.0)
    # low loading plinths and clutter along the front (cabinets, AC units, crates, bollards)
    for (x, z, r) in ((-27.0, 9.0, 90.0), (-27.0, 11.0, 90.0), (37.5, 9.0, -90.0), (37.5, 11.0, -90.0)):
        K.cabinet(B, (x, 0.0, z), w=1.2, h=1.8, d=0.7, rot=r)
    for (x, z) in ((-21.0, 19.5), (11.0, 19.0), (38.5, -4.0)):
        K.hvac(B, (x, 0.0, z), w=2.4, d=1.6, h=1.6, fans=1)
    K.crate(B, (-24.0, 0.0, 20.0), (1.6, 1.4, 1.6))
    K.crate(B, (-24.0, 0.0, 22.0), (1.4, 1.1, 1.4), mat='violet')
    K.crate(B, (24.0, 0.0, 22.5), (1.8, 1.4, 1.8))
    K.crate(B, (26.2, 0.0, 22.5), (1.4, 1.0, 1.4))
    K.bollards(B, [(-6.5, 23.5), (6.5, 23.5), (-15.0, 24.5), (15.0, 24.5), (24.0, 25.0), (34.0, 25.0), (38.5, 12.0), (38.5, 2.0)])
    K.forklift(B, (20.0, 0.0, 24.0), heading=160)
    for (x, z, hd) in ((2.0, 25.0, 190), (-1.5, 26.0, 20), (16.0, 21.5, 250), (34.5, 6.0, 270)):
        K.worker(B, (x, 0.0, z), heading=hd)
    for (x, z, rot) in ((-30.5, 25.5, 135), (40.5, 25.5, -135), (40.5, -19.5, -45)):
        K.lamp_post(B, (x, 0.0, z), h=7.0, arm=1.0, rot=rot)
    # work floods on the annex, aimed away from the camera along the side apron
    K.flood_on_wall(B, (X0 - 0.05, 12.0, -10.0), (-1, 0, 0), (-30.0, 0.0, -20.0))

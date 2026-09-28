"""Writes tools/blender/specs/corvette-v3.json: the kit placements on the remodelled corvette hull.

    python3 tools/blender/hulls/corvette_spec.py

The mounting points repeat the hull dimensions of corvette.py (flank line, belt, bays, glazing
recess back wall, tower platform), so re-run this after changing those.
"""
import json, math, os
TAPER, TAPER0 = 0.2265, 19.0
def fX(z):
    if z >= TAPER0: return 16.15 - TAPER*(z-TAPER0)
    if z >= 0: return 16.15
    if z >= -30: return 16.15 - 0.3*(-z/30)
    return 15.85 - 0.35*((-30-z)/19)
def belt(z): return 0.22 if z <= 18.5 else (0.01 if z >= 21 else 0.22 + (0.01-0.22)*(z-18.5)/2.5)
def n_fl(z):
    if z >= TAPER0: n=(1,0,TAPER)
    elif z < -30: n=(1,0,-0.35/19)
    else: n=(1,0,0)
    L=math.sqrt(sum(c*c for c in n)); return [round(c/L,4) for c in n]
r=lambda v: [round(c,3) for c in v]
P=[]
# ---- drive: bells in the stern frame and the pods (exit plane centre, body toward +Z)
P += [
 {"id":"centre bell: bell-L x1.463 (r 5.12)","part":"bell-L","p":[0,-10.0,-52.6],"n":[0,0,1],"up":[0,1,0],"scale":1.4629,"snap":False,"seat":{"check":False}},
 {"id":"upper bells: bell-M x1.1136 (r 2.45)","part":"bell-M","p":[9.85,-5.44,-53.7],"n":[0,0,1],"up":[0,1,0],"scale":1.1136,"snap":False,"mirrorX":True,"seat":{"check":False}},
 {"id":"lower bells: bell-M x1.0636 (r 2.34)","part":"bell-M","p":[9.8,-14.08,-54.05],"n":[0,0,1],"up":[0,1,0],"scale":1.0636,"snap":False,"mirrorX":True,"seat":{"check":False}},
 {"id":"pod bells: bell-L (r 3.5)","part":"bell-L","p":[29.55,-14.95,-34.6],"n":[0,0,1],"up":[0,1,0],"snap":False,"mirrorX":True,"seat":{"check":False}},
]
# ---- turrets
P += [
 {"id":"fore turret: kit turret-M x1.15 on the roof (guns forward)","part":"turret-M","p":[0,3.45,3.5],"n":[0,1,0],"up":[0,0,1],"scale":1.15,"snap":False,"seat":{"check":False}},
 {"id":"aft turret (guns aft)","part":"turret-M","p":[0,3.45,-25.4],"n":[0,1,0],"up":[0,0,-1],"scale":1.15,"snap":False,"seat":{"check":False}},
]
# ---- torpedo doors in the recessed bow plate
P += [{"id":"torpedo doors x1.1 on the bow plate (z 52.75)","part":"torpedoDoor","p":[2.3,-9.6,52.75],"n":[0,0,1],"scale":1.1,"snap":False,"mirrorX":True,"seat":{"check":False}},
      {"part":"torpedoDoor","p":[2.3,-14.2,52.75],"n":[0,0,1],"scale":1.1,"snap":False,"mirrorX":True,"seat":{"check":False}}]
# ---- doors and airlocks in their bays (belt, y -13.6)
for z in (1.5, 9.9, -39.5):
    P.append({"id":f"crew door bay z {z}","part":"door","p":r([fX(z)+belt(z),-13.6,z]),"n":n_fl(z),"mirrorX":True})
    P.append({"part":"floodlight","p":r([fX(z),-10.9,z]),"n":n_fl(z),"rot":180,"mirrorX":True})
z=24.65
P.append({"id":"airlocks, bow flank","part":"airlock","p":r([fX(z)+belt(z),-13.45,z]),"n":n_fl(z),"mirrorX":True})
P.append({"part":"floodlight","p":r([fX(z),-10.6,z]),"n":n_fl(z),"rot":180,"mirrorX":True})
# ---- ports: two deck rows on the flank (3 m decks, 2.5 m pitch), fore and aft of the pylon
for y in (-6.8, -9.8):
    P.append({"id":f"ports, flank fore, y {y}","part":"port","row":{"from":[16.15,y,1.0],"to":[16.15,y,18.5],"pitch":2.5},"n":[1,0,0],"mirrorX":True})
    P.append({"id":f"ports, flank aft, y {y}","part":"port","row":{"from":[15.8,y,-27.5],"to":[15.8,y,-43.0],"pitch":2.5},"n":n_fl(-35),"mirrorX":True})
# deckhouse side row (sloped side, normal from the hit)
DHN=[0.8907,0.4546,0]
zs=[-29.0,-26.0,-15.5,-9.5,-3.5,3.5,6.5]
for z in zs:
    P.append({"part":"port","p":[9.5,0.9,z],"n":DHN,"mirrorX":True,"normal":"hit","id":"deckhouse side ports" if z==zs[0] else None})
# ---- bridge glazing panes on the recess back wall (y 1.35), bridge nose facets and sides
# back wall of the glazing recess: the band-top outline (y 2.05) offset 0.5 inward (as corvette.py)
def offset_open(pts, d, left):
    out=[]
    for i,p in enumerate(pts):
        ts=[]
        if i>0: ts.append(norm((pts[i][0]-pts[i-1][0], pts[i][1]-pts[i-1][1])))
        if i<len(pts)-1: ts.append(norm((pts[i+1][0]-pts[i][0], pts[i+1][1]-pts[i][1])))
        ns=[(-t[1],t[0]) if left else (t[1],-t[0]) for t in ts]
        if len(ns)==2:
            b_=norm((ns[0][0]+ns[1][0], ns[0][1]+ns[1][1])); k=d/max(b_[0]*ns[0][0]+b_[1]*ns[0][1],0.25)
            out.append((p[0]+b_[0]*k, p[1]+b_[1]*k))
        else: out.append((p[0]+ns[0][0]*d, p[1]+ns[0][1]*d))
    return out
def norm(v):
    L=math.hypot(*v); return (v[0]/L, v[1]/L)
half=[(8.61,11.0),(8.61,15.8),(7.62,20.06),(4.3,23.74),(0.0,24.85)]
line=half+[(-x,z) for x,z in reversed(half[:-1])]
inner=offset_open(line,0.9,True)
PANE=1.12
for i in range(len(inner)//2):          # port half; mirrorX gives starboard
    a_,b_=inner[i],inner[i+1]
    dx,dz=b_[0]-a_[0],b_[1]-a_[1]; L=math.hypot(dx,dz); ux,uz=dx/L,dz/L
    n=[round(uz,4),0,round(-ux,4)]
    m=PANE/2+0.06
    if L-2*m < 0: continue
    fa=[a_[0]+ux*m,1.35,a_[1]+uz*m]; fb=[b_[0]-ux*m,1.35,b_[1]-uz*m]
    k=int(math.floor((L-2*m)/PANE+1e-6))+1
    pitch=(L-2*m)/(k-1) if k>1 else PANE
    pitch=max(pitch,PANE)
    P.append({"id":"bridge glazing panes (recess back wall)" if i==0 else None,"part":"pane","row":{"from":r(fa),"to":r(fb),"pitch":PANE},"n":n,"mirrorX":True,"seat":{"check":False}})
# ---- tower bridge tier: leaning glazing (front, sides) and the vertical aft face
P.append({"id":"tower panes, front (leaning, faces forward and down)","part":"pane","row":{"from":[-4.6,11.52,-5.3],"to":[4.6,11.52,-5.3],"pitch":1.12},"n":[0,-0.603,0.798],"up":[0,0.798,0.603],"seat":{"check":False}})
P.append({"id":"tower panes, sides","part":"pane","row":{"from":[6.4,11.52,-6.9],"to":[6.4,11.52,-14.5],"pitch":1.12},"n":[0.798,-0.603,0],"up":[0.603,0.798,0],"mirrorX":True,"seat":{"check":False}})
# ---- rails: walkway deck edge (2 m bays), tower platform
P.append({"id":"walkway deck-edge rails (3 m bays)","part":"rail","row":{"from":[12.85,-1.46,-29.0],"to":[13.2,-1.46,17.0],"pitch":3.0},"n":[0,1,0],"mirrorX":True})
# tower platform (roof y 12.85): flat front edge x +-6.0 at z -4.14, sides x +-7.63 from z -5.77 to
# -14.72, 1.63 m corner chamfers, aft edge z -16.35; 3 m kit segments centred on the row points
P.append({"id":"tower platform rails, front","part":"rail","row":{"from":[-4.5,12.85,-4.55],"to":[4.5,12.85,-4.55],"pitch":3.0},"n":[0,1,0],"snap":False,"seat":{"check":False}})
P.append({"id":"tower platform rails, sides","part":"rail","row":{"from":[7.2,12.85,-7.27],"to":[7.2,12.85,-13.27],"pitch":3.0},"n":[0,1,0],"mirrorX":True,"snap":False,"seat":{"check":False}})
P.append({"id":"tower platform rails, aft","part":"rail","row":{"from":[-4.5,12.85,-15.95],"to":[4.5,12.85,-15.95],"pitch":3.0},"n":[0,1,0],"snap":False,"seat":{"check":False}})
for zc, az in ((-4.96 - 0.28, -1), (-15.53 + 0.28, 1)):
    P.append({"id":"tower platform rails, corners" if az < 0 else None,"part":"rail","p":[6.54,12.85,round(zc,3)],"n":[0,1,0],"along":[0.7071,0,round(az*0.7071,4)],"scale":[2.2,1,1],"mirrorX":True,"snap":False,"seat":{"check":False}})
# ---- ladders: walkway to deckhouse roof (two 3 m flights up the slope)
for z in (-21.5, 0.8):
    P.append({"id":"deckhouse ladders" if z<0 else None,"part":"ladder","p":[10.0,-0.25,z],"n":DHN,"up":[-0.4546,0.8907,0],"rows":{"count":2,"step":[-1.23,2.4,0]},"mirrorX":True})
# ---- RCS quads (8)
for z,x0 in ((46.2,None),(-47.3,None)):
    x=fX(z)+belt(z)
    for y in (-7.0,-14.0):
        P.append({"id":"rcs","part":"rcs","p":r([x,y,z]),"n":n_fl(z),"mirrorX":True,"normal":"hit"})
# ---- nav light housings (module lights at the lens, 0.23 m out)
P += [
 {"id":"nav lights: pod outboard sidelights","part":"navlight","p":[34.45,-14.95,-7.0],"n":[1,0,0],"mirrorX":True},
 {"part":"navlight","p":[0,-23.25,0.0],"n":[0,-1,0],"sink":0.15},
 {"part":"navlight","p":[0,23.07,-11.5],"n":[0,1,0]},
 {"part":"navlight","p":[0,-3.1,-49.25],"n":[0,0,-1]},
]
# ---- antennas, dome
P += [
 {"id":"yardarm whips","part":"antenna","p":[7.4,15.95,-13.0],"n":[0,1,0],"up":[0,0,1],"scale":0.5,"mirrorX":True},
 {"id":"deckhouse aft whips","part":"antenna","p":[4.0,3.45,-33.0],"n":[0,1,0],"up":[0,0,1],"scale":0.55,"mirrorX":True},
 {"id":"fal antenna on the director","part":"fal:antenna","p":[0.0,5.05,21.2],"n":[0,1,0],"up":[0,0,1],"scale":0.55},
 {"id":"radome on its plinth","part":"dome","p":[0,14.4,-7.3],"n":[0,1,0],"up":[0,0,1],"scale":1.1,"snap":False,"seat":{"check":False}},
]
P=[{k:v for k,v in q.items() if v is not None} for q in P]
spec={
 "about":"Warden-class corvette K-214, v3 REMODEL: the hull is clean hard-surface geometry built by tools/blender/hulls/corvette.py from measurements of the fal/Tripo v7 blueprint (ship frame, metres, bow +Z, dorsal +Y, port +X; not re-centred), textured by tools/blender/hulls/paint.py; this spec places the Blender parts kit (assets/parts-blender, +Z mounts) and one fal-kit antenna on it. Bells are kit bells scaled to the blueprint radii; the module's engines use the kit's documented depth / throat / wall times the same scale.",
 "hull":{"glb":"HULL_GLB_FROM_COMMAND_LINE","rotate":[0,0,0],"scale":1.0,"centre":False},
 "partsDir":"../../../assets/parts-blender",
 "kits":{"fal":"../../../assets/parts"},
 "partDefaults":{
  "door":{"sink":0.0},"airlock":{"sink":0.0},"port":{"sink":0.03,"normal":"hit"},"pane":{"sink":0.04},
  "rcs":{"sink":0.04},"floodlight":{"sink":0.02},"navlight":{"sink":0.0},
  "rail":{"sink":0.0,"xAlong":True,"scale":[3,1,1]},"ladder":{"sink":0.0,"lift":0.03},"antenna":{"sink":0.05},"fal:antenna":{"sink":0.05},"dome":{"sink":0.05}},
 "fixes":{"port":{"decimate":0.3},"pane":{"decimate":0.4},"door":{"decimate":0.35},"airlock":{"decimate":0.5},"rail":{"decimate":1.0},
          "rcs":{"decimate":0.5},"navlight":{"decimate":0.35},"floodlight":{"decimate":0.3},"ladder":{"decimate":0.45},
          "turret-M":{"decimate":0.5},"bell-M":{"decimate":0.3},"bell-L":{"decimate":0.3},"antenna":{"decimate":0.45},"dome":{"decimate":0.6},"torpedoDoor":{"decimate":0.25}},
 "seat":{"maxGap":0.15,"maxBury":0.4,"drop":True},
 "bake":{"ao":True,"res":2048,"distance":0.35,"samples":16,"aa":4,"strength":0.6},
 "placements":P,
}
json.dump(spec, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'specs', 'corvette-v3.json'), 'w'), indent=1)
print(len(P))

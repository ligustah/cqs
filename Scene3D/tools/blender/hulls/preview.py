"""Fast geometry previews of a hull object (Blender Workbench: studio light, cavity, shadow).

    import preview; preview.shots(obj, outdir, views=None, size=(1600, 1000))
    <blender-python> tools/blender/hulls/preview.py <file.blend|file.glb> <outdir> [view ...]

Views (ship frame, like the scene's ?az=&el=: az 0 = from ahead, 90 = from port, 180 = from
astern; el above the horizon), or close-ups given as cam=x,y,z:target=x,y,z:lens=mm.
"""
import math
import os
import sys

import bpy
from mathutils import Vector

C = lambda p: Vector((p[0], -p[2], p[1]))  # ship -> Blender
VIEWS = {
    'hero': dict(az=35, el=18), 'stern': dict(az=215, el=14), 'side': dict(az=90, el=4), 'top': dict(az=90, el=89.5),
    'bow': dict(az=0, el=6), 'belly': dict(az=60, el=-25), 'aft': dict(az=180, el=4),
    'bridge': dict(cam=(13, 5.5, 38), target=(1, 1.2, 19), lens=30), 'tower': dict(cam=(19, 17, 4), target=(0, 11.5, -12), lens=30),
    'ports': dict(cam=(27, -7, -4), target=(16, -8.8, 9), lens=30), 'door': dict(cam=(24, -10.5, 17.5), target=(16.2, -13.2, 8.5), lens=30),
    'walk': dict(cam=(17, 3.2, -34), target=(11.5, -1.2, -6), lens=30), 'sternc': dict(cam=(24, 6, -80), target=(0, -8, -44), lens=35),
}


def setup(size, samples=12):
    """Cycles CPU (Workbench/EEVEE need a GPU context): one hard sun + dim sky, clay material
    override, so facets, chamfers and recesses read clearly."""
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = samples
    sc.cycles.use_denoising = False
    sc.cycles.max_bounces = 2
    sc.render.resolution_x, sc.render.resolution_y = size
    sc.render.image_settings.file_format = 'JPEG'
    w = sc.world or bpy.data.worlds.new('w')
    sc.world = w
    w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.05, 0.055, 0.065, 1)
    w.node_tree.nodes['Background'].inputs['Strength'].default_value = 1.0
    if 'sun' not in bpy.data.objects:
        ld = bpy.data.lights.new('sun', 'SUN')
        ld.energy = 4.0
        ld.angle = 0.02
        sun = bpy.data.objects.new('sun', ld)
        sc.collection.objects.link(sun)
    m = bpy.data.materials.get('clay') or bpy.data.materials.new('clay')
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.5, 0.5, 0.49, 1)
    b.inputs['Roughness'].default_value = 0.45
    sc.view_layers[0].material_override = m
    return sc


def aim_sun(cam_dir, az_off=85, el=30):
    """Key light 85 degrees round from the camera azimuth and 30 degrees up (as the studio)."""
    sun = bpy.data.objects['sun']
    a = math.atan2(cam_dir.x, cam_dir.z) + math.radians(az_off)
    d = Vector((math.sin(a) * math.cos(math.radians(el)), math.sin(math.radians(el)), math.cos(a) * math.cos(math.radians(el))))
    sun.rotation_euler = (-C(d)).to_track_quat('-Z', 'Y').to_euler()


def camera(sc, v, R=80.0):
    cam = sc.camera
    if cam is None:
        cd = bpy.data.cameras.new('cam')
        cam = bpy.data.objects.new('cam', cd)
        sc.collection.objects.link(cam)
        sc.camera = cam
    cam.data.clip_start, cam.data.clip_end = 0.1, 2000
    if 'cam' in v:
        p, t = Vector(v['cam']), Vector(v['target'])
        cam.data.lens = v.get('lens', 35)
    else:
        az, el = math.radians(v['az']), math.radians(v['el'])
        t = Vector(v.get('target', (0, 0, 0)))
        d = Vector((math.sin(az) * math.cos(el), math.sin(el), math.cos(az) * math.cos(el)))
        p = t + d * v.get('dist', 190)
        cam.data.lens = v.get('lens', 50)
    cam.location = C(p)
    look = (C(t) - C(p)).normalized()
    cam.rotation_euler = look.to_track_quat('-Z', 'Y').to_euler()
    aim_sun(p - t)


def shots(obj, out, views=None, size=(1600, 1000)):
    os.makedirs(out, exist_ok=True)
    sc = setup(size)
    for name in views or ['hero', 'stern', 'side', 'bow', 'top', 'belly']:
        v = VIEWS.get(name) or parse(name)
        camera(sc, v)
        sc.render.filepath = os.path.join(out, f'{name.split(":")[0].replace("=", "-")}.jpg')
        bpy.ops.render.render(write_still=True)
        print('[preview]', sc.render.filepath, flush=True)


def parse(s):
    d = {}
    for part in s.split(':'):
        k, v = part.split('=')
        d[k] = tuple(float(x) for x in v.split(',')) if ',' in v else float(v)
    return d


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    src, out = argv[0], argv[1]
    if src.endswith('.blend'):
        bpy.ops.wm.open_mainfile(filepath=src)
    else:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.gltf(filepath=src)
    obj = next(o for o in bpy.data.objects if o.type == 'MESH')
    shots(obj, out, argv[2:] or None)

"""UV layout for the destroyer hull (tools/blender/hulls/destroyer.py).

common.unwrap projects the joined, bevelled hull: every 14 cm chamfer strip and every small box
face becomes its own island with its own margin, and on a 200 m hull with thousands of ports,
mullions and louvres that sea of islands left only ~17 % of the atlas painted. Here instead:
  1. pre_unwrap(ob) per volume BEFORE the bevel: smart projection (islands = face groups within
     50 degrees), rescaled so one UV unit = one metre (a uniform density across volumes); the
     bevel then interpolates the chamfer faces from their neighbours, so chamfers ride on the
     islands of the faces they join instead of forming islands of their own;
  2. small repeated detail (mullions, louvres, fins, coils, clamps, rails) is unwrapped at a
     fraction of the hull density (`detail`), it is one flat paint zone anyway;
  3. pack(ob): one uniform-scale pack of the joined hull, then the texel-density report.
"""
import math

import bpy
import bmesh
import numpy as np

import common as K


def _select_only(ob):
    vl = bpy.context.view_layer
    for o in vl.objects:
        o.select_set(False)
    ob.select_set(True)
    vl.objects.active = ob


def _areas(me):
    uv = me.uv_layers.active.data
    a3 = a2 = 0.0
    for p in me.polygons:
        a3 += p.area
        pts = [uv[i].uv for i in p.loop_indices]
        a2 += abs(sum(pts[i].x * pts[(i + 1) % len(pts)].y - pts[(i + 1) % len(pts)].x * pts[i].y for i in range(len(pts)))) / 2
    return a3, a2


def pre_unwrap(ob, density=1.0, angle=50.0):
    me = ob.data
    if not len(me.polygons):
        return
    if not me.uv_layers:
        me.uv_layers.new(name='UVMap')
    _select_only(ob)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=angle * K.DEG, island_margin=0.0, area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    a3, a2 = _areas(me)
    if a2 <= 0:
        return
    s = math.sqrt(a3 / a2) * density          # UV units -> metres (times the density factor)
    uv = me.uv_layers.active.data
    co = np.empty(len(uv) * 2, np.float32)
    uv.foreach_get('uv', co)
    uv.foreach_set('uv', co * s)


def pack(ob, margin=0.0006):
    _select_only(ob)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.pack_islands(rotate=True, scale=True, margin_method='SCALED', margin=margin, shape_method='CONCAVE')
    bpy.ops.object.mode_set(mode='OBJECT')
    a3, a2 = _areas(ob.data)
    return {'surface_m2': round(a3, 1), 'uv_fill': round(a2, 3), 'px_per_m_at_4096': round(4096 * math.sqrt(a2 / a3), 1)}


def unwrap(ob, angle=50.0, margin=0.0006):
    """Fallback (no pre-unwrap): common.unwrap."""
    return K.unwrap(ob, angle=angle, margin=margin)

"""GhostVan - original paranormal-investigation van for a Roblox ghost-hunter game.

  EGL_PLATFORM=surfaceless /opt/blender-venv/bin/python build_van.py [--preview] [--no-bake]

Original design (no real manufacturer, badge or livery): high-roof panel van, two-tone bone/charcoal with a
spectral-green stripe and an original ghost emblem, roof sensor gear, and a walk-in investigation HQ in the back
(desk with three camera-feed monitors, gear shelving, equipment locker, cab seats).

Sized for Roblox avatars: 20.4 x 8 x ~10.6 studs; cargo floor 1.95 studs up, ~6.8 studs interior headroom
(an R6 avatar is 5 studs tall), rear and side openings ~6.4 studs high.

Separate MeshParts (pivot = hinge / axle so doors and wheels can be scripted):
  Body, Interior, FrontDoorL, FrontDoorR, SlidingDoor, RearDoorL, RearDoorR, SteeringWheel,
  Wheel_FL/FR/RL/RR, Glass, HeadLights, TailLights, LightBar, CabinLights, Screen1-3
"""
import bpy  # noqa: F401
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import vankit as K  # noqa: E402
import bmesh  # noqa: E402
import geo  # noqa: E402
import optimize  # noqa: E402
import paint  # noqa: E402
import stage  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402
from shapely.geometry import Point, Polygon  # noqa: E402
from shapely.ops import unary_union  # noqa: E402

NAME = 'GhostVan'
OUT = os.path.join(os.path.dirname(HERE), 'Vehicles', NAME)
PREVIEW = '--preview' in sys.argv
NO_BAKE = '--no-bake' in sys.argv or PREVIEW

# ------------------------------------------------------------------ layout (studs). x: rear 0 -> front 20.2
HW = 4.0                     # half width
T = 0.25                     # wall thickness
FLOOR = 1.95                 # cargo floor top
ROOF = 9.1
AX_R, AX_F, WR, WY = 4.3, 17.3, 1.5, 3.38      # axles, wheel radius, wheel centre |y|
ARCH_R = 1.85
PROF = K.P([(0, 1.4), (19.95, 1.4), (20.2, 1.95), (20.2, 3.55), (19.95, 4.25), (17.95, 4.8), (15.65, 8.5),
            (15.0, 9.1), (0.4, 9.1), (0, 8.7)], r=0.18)
WS_A, WS_B = Vector((17.95, 0, 4.8)), Vector((15.65, 0, 8.5))           # windshield line (side view)
DOOR = K.P([(15.05, 1.62), (17.98, 1.62), (17.98, 4.72), (15.6, 8.4), (15.05, 8.4)])
SLIDE = K.rbox(10.2, FLOOR + 0.05, 14.55, 8.45, 0.08)
REAR = (2.1, 8.6, 3.45)      # rear opening z0, z1, half width
ARCHES = [Point(AX_R, WR).buffer(ARCH_R, 24), Point(AX_F, WR).buffer(ARCH_R, 24)]
FRONT_DOOR = DOOR.difference(ARCHES[1].buffer(0.06)).buffer(-0.05, join_style='mitre')


def materials():
    def mk(name, base, light, dark, rough, metal, relief='none', pl=0.35, **kw):
        return paint.painted(f'{NAME}_{name}', dict(base=base, light=light, dark=dark, rough=rough, metal=metal,
                                                    relief=relief, paint_light=pl, **kw),
                             height=20.0, bevel_radius=0.04, ao_dist=0.6, streak=0.25, seed=len(name) * 0.7,
                             flat_light=True)
    return {
        'paint': mk('Paint', '#D9D3C4', '#F4F0E6', '#8D877A', 0.38, 0.0),
        'skirt': mk('Skirt', '#2B2D31', '#4C4F55', '#141518', 0.55, 0.0),
        'stripe': mk('Stripe', '#3FCF8E', '#9CF5C6', '#167A4D', 0.35, 0.0),
        'trim': mk('Trim', '#26282C', '#4A4D53', '#111214', 0.7, 0.0, 'leather'),
        'chrome': mk('Chrome', '#A9ADB3', '#E6E9ED', '#4A4D52', 0.22, 1.0),
        'steel': mk('Steel', '#5D6168', '#9DA2A9', '#2A2C30', 0.4, 1.0),
        'cabin': mk('CabinPanel', '#C9C6BE', '#E6E3DC', '#7C7972', 0.6, 0.0, pl=0.25),
        'floor': mk('FloorMat', '#2A2B2E', '#45474C', '#151618', 0.85, 0.0, 'leather', pl=0.2),
        'desk': mk('Desk', '#6E5640', '#9C7E60', '#3A2B1E', 0.55, 0.0, 'weave', pl=0.25),
        'case': mk('Case', '#33373B', '#5C6167', '#17191B', 0.5, 0.0, 'leather', pl=0.3),
        'olive': mk('Olive', '#5E6448', '#8A9070', '#2E3222', 0.6, 0.0, 'leather', pl=0.3),
        'seat': mk('Seat', '#3A3632', '#5E5852', '#1C1A18', 0.8, 0.0, 'leather', pl=0.25),
        'tire': mk('Tire', '#232427', '#3E4044', '#0F1011', 0.85, 0.0, 'leather', pl=0.2),
        'rim': mk('Rim', '#B4B8BE', '#E9ECEF', '#55595E', 0.28, 1.0),
        'screen': paint.painted(f'{NAME}_ScreenMat', dict(base='#2DE08A', light='#B8FFDA', dark='#0E5A35', rough=0.1,
                                                          metal=0.0, relief='none', emit=2.0), height=2.0),
        'head': paint.painted(f'{NAME}_HeadMat', dict(base='#FFF4D6', light='#FFFFFF', dark='#C9B98E', rough=0.1,
                                                      metal=0.0, relief='none', emit=2.5), height=2.0),
        'tail': paint.painted(f'{NAME}_TailMat', dict(base='#E0262E', light='#FF7A7A', dark='#7A0E12', rough=0.1,
                                                      metal=0.0, relief='none', emit=2.0), height=2.0),
        'bar': paint.painted(f'{NAME}_BarMat', dict(base='#6CFFB0', light='#D8FFEA', dark='#1F8A55', rough=0.1,
                                                    metal=0.0, relief='none', emit=2.5), height=2.0),
        'cabinlight': paint.painted(f'{NAME}_CabinLightMat', dict(base='#9EF7FF', light='#FFFFFF', dark='#3C9AA6',
                                                                  rough=0.1, metal=0.0, relief='none', emit=2.0),
                                    height=2.0),
        'glass': _glass(),
    }


def _glass():
    m = bpy.data.materials.new(f'{NAME}_Glass')
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.05, 0.08, 0.09, 1)
    b.inputs['Roughness'].default_value = 0.05
    b.inputs['Alpha'].default_value = 0.45
    b.inputs['IOR'].default_value = 1.05
    m.blend_method = 'BLEND' if hasattr(m, 'blend_method') else None
    return m


def windshield_prism(col):
    d = WS_B - WS_A
    n = Vector((d.z, 0, -d.x)).normalized()
    if n.x < 0:
        n = -n
    pts = []
    for t, s in ((0.07, 1), (0.93, 1), (0.93, -1), (0.07, -1)):
        p = WS_A + d * t + n * 0.7 * s
        pts.append((p.x, p.z))
    return K.P(pts)


def build(col, M):
    parts = {}       # part name -> [objects]

    def add(part, o):
        parts.setdefault(part, []).append(o)
        return o

    # ------------------------------------------------------------ body shell (one solid, hollowed by booleans)
    body = K.side('BodyShell', PROF, 2 * HW, col, M['paint'], chamfer=0.38)
    cav = PROF.buffer(-T, join_style='mitre').intersection(K.rbox(T, FLOOR, 40, 40))
    cutters = [K.prism('cav', cav, -(HW - T), HW - T, col)]
    z0, z1, hy = REAR
    cutters.append(K.prism('rear', K.rbox(-1, z0, T + 0.3, z1, 0.1), -hy, hy, col))
    for s in (1, -1):
        cutters.append(K.prism('door', DOOR.difference(ARCHES[1]), s * (HW - T - 0.2), s * (HW + 0.6), col))
    cutters.append(K.prism('slide', SLIDE, -(HW + 0.6), -(HW - T - 0.2), col))
    cutters.append(K.prism('ws', windshield_prism(col), -(HW - 0.62), HW - 0.62, col))
    K.boolean(body, cutters, 'DIFFERENCE')
    # wheel-well housings inside the cargo floor, then the arches through skin + housing
    hous = []
    for ax in (AX_R, AX_F):
        for s in (1, -1):
            yy = s * (HW - T / 2 - 0.62)
            hous.append(K.block('hous', ax - 2.05, yy - 0.62, 1.4, ax + 2.05, yy + 0.62, 3.65, col, None, 0.02))
    K.boolean(body, hous, 'UNION')
    arch_cut = []
    for a in ARCHES:
        for s in (1, -1):
            arch_cut.append(K.prism('arch', a, s * 2.75, s * (HW + 0.6), col))
    K.boolean(body, arch_cut, 'DIFFERENCE')
    add('Body', body)

    # ------------------------------------------------------------ exterior trim on the body
    add('Body', K.block('FrontBumper', 19.55, -HW + 0.05, 1.45, 20.6, HW - 0.05, 2.35, col, M['trim'], 0.15))
    add('Body', K.block('RearBumper', -0.35, -HW + 0.05, 1.45, 0.6, HW - 0.05, 2.15, col, M['trim'], 0.12))
    add('Body', K.block('RearStep', -0.75, -1.6, 1.55, -0.2, 1.6, 1.8, col, M['steel'], 0.04))
    add('Body', K.front('GrilleFrame', K.rbox(-2.25, 2.45, 2.25, 3.85, 0.2), 20.12, 20.3, col, M['trim'], 0.05))
    for i in range(4):
        z = 2.65 + i * 0.3
        add('Body', K.front(f'GrilleSlat{i}', K.rbox(-2.0, z, 2.0, z + 0.12, 0.04), 20.25, 20.34, col, M['chrome'], 0.02))
    add('Body', K.front('PlateFront', K.rbox(-0.85, 1.6, 0.85, 2.15, 0.05), 20.58, 20.66, col, M['paint'], 0.02))
    add('Body', K.front('PlateRear', K.rbox(-0.85, 2.3, 0.85, 2.85, 0.05), -0.08, 0.0, col, M['paint'], 0.02))
    for s in (1, -1):
        # headlight + taillight housings
        add('Body', K.front(f'HeadBezel{s}', K.rbox(2.25 * 0 + 2.35, 2.55, 3.75, 3.75, 0.22) if s > 0 else
                            K.rbox(-3.75, 2.55, -2.35, 3.75, 0.22), 20.1, 20.26, col, M['trim'], 0.04))
        # mirrors on the A-pillar
        add('Body', K.rod(f'MirrorArm{s}', (17.75, s * 3.95, 4.95), (17.75, s * 4.55, 5.05), 0.06, col, M['trim']))
        add('Body', K.block(f'Mirror{s}', 17.55, s * 4.4 - 0.32, 4.8, 17.85, s * 4.4 + 0.32, 5.85, col, M['trim'], 0.08))
        # mud flaps
        for ax in (AX_R, AX_F):
            add('Body', K.block(f'Flap{s}{ax}', ax - ARCH_R - 0.12, s * WY - 0.55, 0.45, ax - ARCH_R + 0.0,
                                s * WY + 0.55, 1.45, col, M['trim'], 0.03))
        # roof rails
        for x in (1.2, 5.3, 9.4, 13.5):
            add('Body', K.block(f'RackFoot{s}{x}', x - 0.18, s * 3.35 - 0.15, ROOF - 0.05, x + 0.18, s * 3.35 + 0.15,
                                ROOF + 0.32, col, M['trim'], 0.04))
        add('Body', K.rod(f'RackRail{s}', (1.0, s * 3.35, ROOF + 0.4), (13.7, s * 3.35, ROOF + 0.4), 0.09, col,
                          M['steel']))
    for x in (2.5, 6.8, 11.0):
        add('Body', K.rod(f'RackBar{x}', (x, -3.35, ROOF + 0.4), (x, 3.35, ROOF + 0.4), 0.07, col, M['steel']))
    # wipers
    for y in (-1.6, 1.4):
        add('Body', K.rod(f'Wiper{y}', (17.75, y - 0.9, 5.05), (17.25, y + 0.6, 5.75), 0.035, col, M['trim'], 6))
    # side step under the sliding door, fuel cap, exhaust
    add('Body', K.block('SideStep', 10.4, -HW - 0.3, 1.15, 14.35, -HW + 0.4, 1.4, col, M['steel'], 0.04))
    add('Body', K.lathe_y('FuelCap', [(0, 0), (0.28, 0), (0.3, 0.03), (0.3, 0.06), (0, 0.06)], col, M['trim'],
                          (12.2, HW - 0.02, 4.0), 12))
    add('Body', K.lathe_x('Exhaust', [(0, 0), (0.16, 0), (0.16, 1.4), (0.2, 1.45), (0.2, 1.7), (0, 1.7)], col,
                          M['steel'], (0.2 - 1.7 + 0.2, -2.6, 1.25), 10))
    # ghost emblem (original): ring + ghost silhouette with eyes, both sides of the cargo box
    em_shape = emblem()
    for s in (1, -1):
        o = K.side(f'Emblem{s}', em_shape, 0.05, col, M['stripe'], 0.012, y=s * (HW + 0.015))
        add('Body', o)
    # roof gear: light bar, sensor dish, antennas, swivel spotlight
    add('Body', K.block('LightBarBase', 13.65, -2.7, ROOF + 0.45, 14.35, 2.7, ROOF + 0.62, col, M['trim'], 0.04))
    add('Body', K.lathe_z('DishMast', [(0, 0), (0.22, 0), (0.22, 0.12), (0.1, 0.18), (0.1, 1.05), (0, 1.05)], col,
                          M['steel'], (7.0, 0.0, ROOF + 0.4), 10))
    dish = K.lathe_z('Dish', [(0, 0.05), (0.35, 0.08), (0.85, 0.26), (1.25, 0.55), (1.3, 0.62), (1.2, 0.62),
                              (0.8, 0.38), (0.3, 0.2), (0, 0.17)], col, M['paint'], (7.0, 0.0, ROOF + 1.35), 20)
    dish.rotation_euler = (math.radians(0), math.radians(-28), 0)
    add('Body', dish)
    add('Body', K.rod('DishFeed', (7.0, 0, ROOF + 1.5), (7.55, 0, ROOF + 2.4), 0.04, col, M['steel'], 6))
    add('Body', K.lathe_z('DishLNB', [(0, 0), (0.12, 0), (0.12, 0.25), (0, 0.25)], col, M['trim'],
                          (7.55, 0, ROOF + 2.35), 8))
    for i, (x, y, h) in enumerate(((1.4, -2.8, 3.2), (2.2, -2.2, 2.4), (1.4, 2.8, 2.8))):
        add('Body', K.lathe_z(f'AntBase{i}', [(0, 0), (0.2, 0), (0.2, 0.12), (0.06, 0.2), (0, 0.2)], col, M['trim'],
                              (x, y, ROOF - 0.02), 8))
        add('Body', K.rod(f'Antenna{i}', (x, y, ROOF + 0.15), (x - 0.25, y, ROOF + h), 0.03, col, M['trim'], 5))
        add('Body', K.lathe_z(f'AntTip{i}', [(0, 0), (0.07, 0), (0.07, 0.12), (0, 0.12)], col, M['stripe'],
                              (x - 0.25, y, ROOF + h - 0.05), 6))
    add('Body', K.lathe_z('SpotBase', [(0, 0), (0.3, 0), (0.3, 0.12), (0.12, 0.2), (0.12, 0.45), (0, 0.45)], col,
                          M['trim'], (11.8, 2.3, ROOF - 0.02), 10))
    add('Body', K.lathe_x('SpotCan', [(0, 0), (0.22, 0), (0.3, 0.15), (0.3, 0.75), (0.32, 0.8), (0, 0.8)], col,
                          M['trim'], (11.45, 2.3, ROOF + 0.62), 12))

    # ------------------------------------------------------------ doors (pivot = hinge)
    win_door = FRONT_DOOR.buffer(-0.24, join_style='mitre').intersection(K.rbox(0, 5.0, 40, 40))
    for s, nm in ((1, 'FrontDoorL'), (-1, 'FrontDoorR')):
        add(nm, K.side(nm, FRONT_DOOR.difference(win_door), T, col, M['paint'], 0.05, y=s * (HW - T / 2)))
        add(nm, K.block(f'{nm}Handle', 15.3, s * (HW + 0.02) - 0.06, 4.25, 15.85, s * (HW + 0.02) + 0.06, 4.42, col,
                        M['trim'], 0.02))
        add(nm, K.side(f'{nm}Skirt', FRONT_DOOR.intersection(K.rbox(0, 0, 40, 2.6)), 0.04, col, M['skirt'], 0.01,
                       y=s * (HW + 0.005)))
        add(nm, K.side(f'{nm}Stripe', FRONT_DOOR.intersection(K.rbox(0, 2.85, 40, 3.2)), 0.04, col, M['stripe'],
                       0.01, y=s * (HW + 0.005)))
        add('Glass', K.side(f'{nm}Glass', win_door.buffer(0.03), 0.05, col, M['glass'], 0.01, y=s * (HW - T / 2)))
    slide = SLIDE.buffer(-0.05, join_style='mitre')
    add('SlidingDoor', K.side('SlidingDoor', slide, T, col, M['paint'], 0.05, y=-(HW - T / 2)))
    add('SlidingDoor', K.block('SlideHandle', 13.6, -HW - 0.08, 4.3, 14.2, -HW + 0.02, 4.45, col, M['trim'], 0.02))
    add('SlidingDoor', K.side('SlideSkirt', slide.intersection(K.rbox(0, 0, 40, 2.6)), 0.04, col, M['skirt'], 0.01,
                              y=-(HW + 0.005)))
    add('SlidingDoor', K.side('SlideStripe', slide.intersection(K.rbox(0, 2.85, 40, 3.2)), 0.04, col, M['stripe'],
                              0.01, y=-(HW + 0.005)))
    for s, nm in ((1, 'RearDoorL'), (-1, 'RearDoorR')):
        y0, y1 = (0.03, hy - 0.03) if s > 0 else (-hy + 0.03, -0.03)
        panel = K.rbox(y0, z0 + 0.03, y1, z1 - 0.03, 0.06)
        win = K.rbox(y0 + 0.4 if s > 0 else y0 + 0.5, 6.0, y1 - 0.5 if s > 0 else y1 - 0.4, 7.9, 0.2)
        add(nm, K.front(nm, panel.difference(win), 0.0, T, col, M['paint'], 0.05))
        add(nm, K.front(f'{nm}Skirt', panel.intersection(K.rbox(-9, 0, 9, 2.6)), -0.01, 0.0, col, M['skirt'], 0.004))
        add(nm, K.front(f'{nm}Stripe', panel.intersection(K.rbox(-9, 2.85, 9, 3.2)), -0.01, 0.0, col, M['stripe'],
                        0.004))
        add('Glass', K.front(f'{nm}Glass', win.buffer(0.03), 0.1, 0.15, col, M['glass'], 0.01))
        add(nm, K.block(f'{nm}Handle', -0.08, s * 0.3 - 0.25, 4.9, 0.0, s * 0.3 + 0.25, 5.05, col, M['trim'], 0.01))
        for zz in (2.9, 7.6):     # hinges
            add('Body', K.block(f'{nm}Hinge{zz}', -0.1, s * hy - 0.18, zz, 0.05, s * hy + 0.12, zz + 0.45, col,
                                M['steel'], 0.02))
    # roof ladder on the right rear door
    for yy in (-2.9, -1.7):
        add('RearDoorR', K.rod(f'LadRail{yy}', (-0.3, yy, 2.4), (-0.3, yy, 8.4), 0.06, col, M['steel']))
        for zz in (3.0, 8.0):
            add('RearDoorR', K.rod(f'LadStand{yy}{zz}', (-0.3, yy, zz), (0.0, yy, zz), 0.04, col, M['steel'], 6))
    for i in range(7):
        zz = 2.9 + i * 0.82
        add('RearDoorR', K.rod(f'LadRung{i}', (-0.3, -2.9, zz), (-0.3, -1.7, zz), 0.045, col, M['steel'], 6))

    # ------------------------------------------------------------ glass + lights
    d = WS_B - WS_A
    n = Vector((d.z, 0, -d.x)).normalized()
    n = n if n.x > 0 else -n
    ca, cb = WS_A + d * 0.05 - n * 0.1, WS_A + d * 0.95 - n * 0.1
    yy = HW - 0.55
    add('Glass', K.quad_panel('Windshield', [(ca.x, -yy, ca.z), (ca.x, yy, ca.z), (cb.x, yy, cb.z), (cb.x, -yy, cb.z)],
                              0.05, col, M['glass']))
    for s in (1, -1):
        add('HeadLights', K.front(f'Head{s}', K.rbox(2.5, 2.7, 3.6, 3.6, 0.15) if s > 0 else
                                  K.rbox(-3.6, 2.7, -2.5, 3.6, 0.15), 20.2, 20.32, col, M['head'], 0.03))
        add('TailLights', K.front(f'Tail{s}', K.rbox(3.55, 3.4, 3.92, 5.7, 0.08) if s > 0 else
                                  K.rbox(-3.92, 3.4, -3.55, 5.7, 0.08), -0.08, 0.02, col, M['tail'], 0.02))
    add('TailLights', K.front('BrakeLight', K.rbox(-0.7, 8.72, 0.7, 8.92, 0.05), -0.06, 0.02, col, M['tail'], 0.01))
    add('LightBar', K.block('LightBarLens', 13.72, -2.55, ROOF + 0.6, 14.28, 2.55, ROOF + 0.95, col, M['bar'], 0.08))
    for yy in (-1.6, 1.6):
        add('CabinLights', K.block(f'Strip{yy}', 1.0, yy - 0.12, ROOF - T - 0.07, 14.0, yy + 0.12, ROOF - T + 0.01,
                                   col, M['cabinlight'], 0.02))

    # ------------------------------------------------------------ interior (investigation HQ)
    I = 'Interior'
    add(I, K.block('FloorMat', T + 0.05, -(HW - T - 0.02), FLOOR - 0.02, 15.0, HW - T - 0.02, FLOOR + 0.05, col,
                   M['floor'], 0.02))
    wy = HW - T                                  # inner wall |y|
    # desk on the left wall
    add(I, K.block('DeskTop', 4.6, wy - 1.55, 4.2, 10.0, wy, 4.42, col, M['desk'], 0.05))
    add(I, K.block('DeskCab', 4.75, wy - 1.4, FLOOR, 6.25, wy, 4.2, col, M['case'], 0.04))
    for i, zz in enumerate((2.25, 3.0, 3.6)):
        add(I, K.block(f'Drawer{i}', 4.85, wy - 1.45, zz, 6.15, wy - 1.38, zz + 0.5, col, M['steel'], 0.02))
        add(I, K.block(f'DrawerPull{i}', 5.25, wy - 1.52, zz + 0.3, 5.75, wy - 1.44, zz + 0.37, col, M['chrome'], 0.01))
    add(I, K.block('DeskLeg', 9.75, wy - 1.45, FLOOR, 9.95, wy - 1.25, 4.2, col, M['steel'], 0.02))
    screens = []
    for i, x in enumerate((4.85, 6.6, 8.35)):
        add(I, K.block(f'MonArm{i}', x + 0.6, wy - 0.3, 5.45, x + 0.95, wy, 5.7, col, M['steel'], 0.03))
        add(I, K.block(f'Monitor{i}', x, wy - 0.42, 4.85, x + 1.55, wy - 0.22, 6.15, col, M['case'], 0.05))
        sc = K.block(f'Screen{i + 1}', x + 0.1, wy - 0.45, 4.95, x + 1.45, wy - 0.41, 6.05, col, M['screen'], 0.005)
        add(f'Screen{i + 1}', sc)
        screens.append(((x + 0.775, wy - 0.45, 5.5), (1.35, 1.1)))
    add(I, K.block('Keyboard', 6.4, wy - 1.35, 4.42, 7.9, wy - 0.85, 4.5, col, M['case'], 0.02))
    add(I, K.block('Mouse', 8.2, wy - 1.2, 4.42, 8.45, wy - 0.95, 4.52, col, M['case'], 0.03))
    add(I, K.block('Recorder', 8.9, wy - 1.2, 4.42, 9.8, wy - 0.5, 4.75, col, M['olive'], 0.04))
    for k in range(3):
        add(I, K.lathe_y(f'Knob{k}', [(0, 0), (0.07, 0), (0.07, 0.06), (0, 0.06)], col, M['chrome'],
                         (9.1 + k * 0.25, wy - 1.27, 4.6), 8))
    # shelf over the desk with gear
    add(I, K.block('DeskShelf', 4.6, wy - 0.75, 6.85, 10.0, wy, 6.97, col, M['desk'], 0.03))
    for i, (x0, x1, h, m) in enumerate(((4.8, 5.9, 0.75, 'olive'), (6.1, 6.9, 0.55, 'case'), (7.2, 8.6, 0.6, 'case'),
                                        (8.8, 9.8, 0.9, 'olive'))):
        add(I, K.block(f'ShelfGear{i}', x0, wy - 0.65, 6.97, x1, wy - 0.08, 6.97 + h, col, M[m], 0.05))
        add(I, K.block(f'ShelfGearFace{i}', x0 + 0.1, wy - 0.68, 7.05, x1 - 0.1, wy - 0.64, 6.97 + h - 0.1, col,
                       M['steel'], 0.01))
    # office stool
    add(I, K.lathe_z('StoolBase', [(0, 0), (0.7, 0), (0.7, 0.1), (0.12, 0.18), (0.12, 1.6), (0, 1.6)], col, M['steel'],
                     (7.3, 1.3, FLOOR), 10))
    add(I, K.lathe_z('StoolSeat', [(0, 0), (0.75, 0), (0.8, 0.12), (0.8, 0.3), (0.7, 0.38), (0, 0.38)], col, M['seat'],
                     (7.3, 1.3, FLOOR + 1.55), 14))
    # right wall: gear shelving behind the sliding door area
    for x in (0.5, 4.95, 9.4):
        add(I, K.block(f'RackPost{x}', x, -wy, FLOOR, x + 0.14, -wy + 1.3, 8.5, col, M['steel'], 0.02))
    for i, zz in enumerate((FLOOR + 0.25, 4.1, 6.0, 7.8)):
        add(I, K.block(f'RackShelf{i}', 0.5, -wy, zz, 9.54, -wy + 1.3, zz + 0.1, col, M['steel'], 0.02))
    cases = [(0.8, 2.6, FLOOR + 0.35, 1.0, 'case'), (2.9, 4.6, FLOOR + 0.35, 1.3, 'olive'),
             (5.3, 7.4, FLOOR + 0.35, 0.9, 'case'), (7.7, 9.2, FLOOR + 0.35, 1.2, 'olive'),
             (0.8, 2.0, 4.2, 0.8, 'olive'), (2.2, 4.4, 4.2, 0.6, 'case'), (5.3, 6.6, 4.2, 1.0, 'case'),
             (6.9, 9.1, 4.2, 0.7, 'olive'), (0.8, 3.2, 6.1, 0.9, 'case'), (5.4, 6.5, 6.1, 1.2, 'olive'),
             (6.8, 9.1, 6.1, 0.5, 'case')]
    for i, (x0, x1, zz, h, m) in enumerate(cases):
        add(I, K.block(f'Case{i}', x0, -wy + 0.1, zz, x1, -wy + 1.15, zz + h, col, M[m], 0.07))
        add(I, K.block(f'Latch{i}a', x0 + 0.2, -wy + 1.14, zz + h * 0.6, x0 + 0.42, -wy + 1.2, zz + h * 0.85, col,
                       M['stripe'], 0.01))
        add(I, K.block(f'Latch{i}b', x1 - 0.42, -wy + 1.14, zz + h * 0.6, x1 - 0.2, -wy + 1.2, zz + h * 0.85, col,
                       M['stripe'], 0.01))
    # tall equipment locker at the rear-left corner
    add(I, K.block('Locker', 0.4, wy - 1.2, FLOOR, 4.3, wy, 8.4, col, M['case'], 0.06))
    add(I, K.block('LockerSplit', 2.33, wy - 1.24, FLOOR + 0.2, 2.37, wy - 1.18, 8.2, col, M['trim'], 0.005))
    for x in (2.05, 2.65):
        add(I, K.block(f'LockerPull{x}', x - 0.04, wy - 1.3, 5.0, x + 0.04, wy - 1.2, 5.8, col, M['chrome'], 0.01))
    for i in range(4):
        add(I, K.block(f'LockerVent{i}', 0.7, wy - 1.22, 7.4 + i * 0.18, 2.1, wy - 1.19, 7.5 + i * 0.18, col,
                       M['trim'], 0.005))
    # cab: dash, seats, gear lever
    add(I, K.side('Dash', K.P([(16.55, 3.3), (17.95, 3.3), (17.95, 4.78), (17.25, 5.0), (16.55, 4.75)], r=0.12),
                  2 * (HW - T), col, M['trim'], 0.1))
    add(I, K.block('Firewall', 17.6, -(HW - T), FLOOR - 0.3, 20.0, HW - T, 4.6, col, M['trim'], 0.02))
    add(I, K.block('DashTop', 16.6, -(HW - T) + 0.2, 4.95, 17.4, -0.2, 5.05, col, M['case'], 0.03))
    add(I, K.block('Gauges', 16.5, 1.6, 4.4, 16.6, 3.0, 4.85, col, M['steel'], 0.02))
    for s in (1, -1):
        yc = s * 2.15
        seat = K.P([(15.15, 3.35), (16.6, 3.35), (16.7, 3.95), (15.6, 4.0), (15.45, 6.35), (15.1, 6.4),
                    (14.9, 6.1), (15.0, 3.9)], r=0.14)
        add(I, K.side(f'Seat{s}', seat, 1.9, col, M['seat'], 0.18, y=yc))
        add(I, K.block(f'SeatBase{s}', 15.25, yc - 0.8, FLOOR, 16.45, yc + 0.8, 3.38, col, M['case'], 0.05))
        add(I, K.side(f'Headrest{s}', K.P([(15.0, 6.45), (15.45, 6.45), (15.4, 7.2), (14.95, 7.2)], r=0.1), 1.1, col,
                      M['seat'], 0.1, y=yc))
    add(I, K.rod('GearStick', (16.4, 0.0, 3.4), (16.1, 0.0, 4.2), 0.05, col, M['steel'], 6))
    add(I, K.lathe_z('GearKnob', [(0, 0), (0.12, 0.02), (0.14, 0.12), (0.08, 0.22), (0, 0.22)], col, M['trim'],
                     (16.1, 0.0, 4.15), 8))
    # cab bulkhead pillars (leave the walk-through open)
    for s in (1, -1):
        ya, yb = (wy - 1.0, wy) if s > 0 else (-wy, -wy + 1.0)
        add(I, K.block(f'Bulkhead{s}', 14.55, ya, FLOOR, 14.75, yb, ROOF - T, col, M['cabin'], 0.03))
    # steering wheel (own part, pivot on its column)
    sw_c = Vector((16.15, 2.15, 5.35))
    wheel = geo.ring('SteeringWheel', 0.62, 0.075, sides=8, samples=24, col=col, material=M['trim'])
    wheel.rotation_euler = (0, math.radians(-90 + 35), math.radians(90))
    wheel.location = sw_c
    add('SteeringWheel', wheel)
    for a in (0, 120, 240):
        r = math.radians(a)
        tip = Vector((0, math.cos(r) * 0.6, math.sin(r) * 0.6))
        tip = Matrix.Rotation(math.radians(35), 3, 'Y') @ tip
        add('SteeringWheel', K.rod(f'Spoke{a}', sw_c, sw_c + tip, 0.04, col, M['trim'], 6))
    add('SteeringWheel', K.lathe_x('Hub', [(0, 0), (0.17, 0), (0.17, 0.12), (0, 0.12)], col, M['stripe'],
                                   (sw_c.x - 0.06, sw_c.y, sw_c.z), 10))
    add(I, K.rod('Column', sw_c + Vector((0.08, 0, -0.05)), (17.0, 2.15, 4.4), 0.09, col, M['trim'], 8))

    # ------------------------------------------------------------ wheels (pivot = axle centre)
    for nm, x, s in (('Wheel_FL', AX_F, 1), ('Wheel_FR', AX_F, -1), ('Wheel_RL', AX_R, 1), ('Wheel_RR', AX_R, -1)):
        tread = [(0.9, -0.26), (0.97, -0.48), (1.32, -0.52), (1.44, -0.44), (1.5, -0.3), (1.5, -0.14), (1.45, -0.12), (1.45, 0.12),
                 (1.5, 0.14), (1.5, 0.3), (1.44, 0.44), (1.32, 0.52), (0.97, 0.48), (0.9, 0.26)]
        rim = [(0, -0.3), (0.96, -0.3), (0.96, 0.32), (0.92, 0.44), (0.8, 0.3), (0.34, 0.36), (0.3, 0.44), (0, 0.46)]
        if s < 0:
            tread = [(r, -y) for r, y in reversed(tread)]
            rim = [(r, -y) for r, y in reversed(rim)]
        tire = K.lathe_y(f'{nm}Tire', tread, col, M['tire'], (x, s * WY, WR), 20)
        rimo = K.lathe_y(f'{nm}Rim', rim, col, M['rim'], (x, s * WY, WR), 20)
        add(nm, tire)
        add(nm, rimo)
        for k in range(5):
            a = 2 * math.pi * k / 5
            add(nm, K.lathe_y(f'{nm}Lug{k}', [(0, 0), (0.06, 0), (0.06, 0.08), (0, 0.08)] if s > 0 else
                              [(0, -0.08), (0.06, -0.08), (0.06, 0), (0, 0)], col, M['chrome'],
                              (x + 0.5 * math.cos(a), s * (WY + 0.36), WR + 0.5 * math.sin(a)), 6))
    return parts, screens


def emblem():
    ring = Point(0, 0).buffer(1.55, 32).difference(Point(0, 0).buffer(1.35, 32))
    head = Point(0, 0.28).buffer(0.82, 24)
    body = K.rbox(-0.82, -0.75, 0.82, 0.28)
    ghost = head.union(body)
    for i in range(3):
        ghost = ghost.difference(Point(-0.55 + i * 0.55, -0.82).buffer(0.26, 12))
    for ex in (-0.3, 0.3):
        ghost = ghost.difference(K.rbox(ex - 0.12, 0.2, ex + 0.12, 0.6, 0.11))
    g = ring.union(ghost).buffer(0)
    from shapely import affinity
    g = affinity.scale(g, 1.0, 1.0)
    return affinity.translate(g, 7.6, 6.0)


def tag_and_join(objs, name):
    K.apply(objs)
    o = paint.join(objs, name)
    return o


def main():
    stage.reset_scene()
    col = stage.collection(NAME)
    M = materials()
    parts, screens = build(col, M)
    K.apply([o for ps in parts.values() for o in ps])
    joined = {p: paint.join(objs, p) if len(objs) > 1 else objs[0] for p, objs in parts.items()}
    for p, o in joined.items():
        o.name = p
        o.data.name = p
    # two-tone + stripe on the body skin
    body = joined['Body']
    for i, m in enumerate(body.data.materials):
        if m is None:
            body.data.materials[i] = M['paint']
    K.split_at_z(body, (2.6, 2.85, 3.2))

    def exterior(c, n):
        return abs(c.y) > HW - 0.12 or c.x < 0.12 or c.x > 18.5 or c.z < 1.5
    K.assign(body, M['skirt'], lambda c, n: c.z < 2.6 and exterior(c, n))
    K.assign(body, M['stripe'], lambda c, n: 2.85 < c.z < 3.2 and (abs(c.y) > HW - 0.05 or c.x < 0.02) and abs(n.z) < 0.5)
    K.assign(body, M['cabin'], lambda c, n: abs(c.y) < HW - T + 0.01 and FLOOR - 0.01 < c.z < ROOF - T + 0.01 and
             T - 0.01 < c.x < 17.2 and not (abs(n.y) < 0.2 and n.z < -0.9))
    return col, M, joined, screens


# ------------------------------------------------------------------ finishing
ORIGIN_X = (AX_R + AX_F) / 2          # model origin: ground point between the axles
# Blender +Y exports as Roblox -Z (verified by parsing the FBX), so the front (+X authoring) goes to Blender +Y
TO_GAME = Matrix.Rotation(math.radians(90), 4, 'Z') @ Matrix.Translation((-ORIGIN_X, 0, 0))
BAKE_GROUPS = {   # one texture set per group, shared by its MeshParts
    'Exterior': (['Body', 'FrontDoorL', 'FrontDoorR', 'SlidingDoor', 'RearDoorL', 'RearDoorR'], 2048),
    'Interior': (['Interior', 'SteeringWheel'], 2048),
    'Wheels': (['Wheel_FL', 'Wheel_FR', 'Wheel_RL', 'Wheel_RR'], 1024),
}
FLAT = {'Glass': 'glass', 'HeadLights': 'head', 'TailLights': 'tail', 'LightBar': 'bar', 'CabinLights': 'cabinlight',
        'Screen1': 'screen', 'Screen2': 'screen', 'Screen3': 'screen'}
FRONT_HINGE_X = 17.98


def pivots(screens):
    hy = REAR[2]
    pv = {'FrontDoorL': (FRONT_HINGE_X, HW - 0.05, 5.0), 'FrontDoorR': (FRONT_HINGE_X, -(HW - 0.05), 5.0),
          'RearDoorL': (0.0, hy, 5.3), 'RearDoorR': (0.0, -hy, 5.3), 'SlidingDoor': (12.375, -HW, 5.2),
          'SteeringWheel': (16.15, 2.15, 5.35),
          'Wheel_FL': (AX_F, WY, WR), 'Wheel_FR': (AX_F, -WY, WR), 'Wheel_RL': (AX_R, WY, WR),
          'Wheel_RR': (AX_R, -WY, WR)}
    for i, (c, _) in enumerate(screens):
        pv[f'Screen{i + 1}'] = c
    return pv


def game_pos(p):
    """authoring point -> Roblox model space (studs, +Y up, front = -Z, right = +X)."""
    b = TO_GAME @ Vector(p)                     # Blender coords after the export rotation
    return [round(b.x, 3), round(b.z, 3), round(-b.y, 3)]


def bake_group(name, objs, size, samples):
    for o in objs:
        vg = o.vertex_groups.new(name=o.name)
        vg.add(list(range(len(o.data.vertices))), 1.0, 'REPLACE')
    names = [o.name for o in objs]
    tmp = paint.join(list(objs), f'_bake_{name}')
    paint.unwrap(tmp, margin=0.003, angle=55)
    maps = paint.bake_maps(tmp, os.path.join(OUT, 'Textures'), f'{NAME}_{name}', size=size, samples=samples)
    tmp.data.materials.clear()
    tmp.data.materials.append(paint.baked_material(f'{NAME}_{name}_Baked', maps))
    out = {}
    for nm in names:
        o = tmp.copy()
        o.data = tmp.data.copy()
        bpy.context.collection.objects.link(o) if o.name not in bpy.context.collection.objects else None
        for c in tmp.users_collection:
            if o.name not in c.objects:
                c.objects.link(o)
        bm = bmesh.new()
        bm.from_mesh(o.data)
        dl = bm.verts.layers.deform.active
        gi = o.vertex_groups[nm].index
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if gi not in v[dl]], context='VERTS')
        bm.to_mesh(o.data)
        bm.free()
        o.vertex_groups.clear()
        o.name = nm
        o.data.name = nm
        out[nm] = o
    bpy.data.objects.remove(tmp, do_unlink=True)
    return out, maps


DOORS = {   # Roblox model space: front = -Z, right = +X. Angle = rotation about +Y at the hinge.
    'FrontDoorL': {'Kind': 'Hinge', 'Angle': -72}, 'FrontDoorR': {'Kind': 'Hinge', 'Angle': 72},
    'RearDoorL': {'Kind': 'Hinge', 'Angle': -100}, 'RearDoorR': {'Kind': 'Hinge', 'Angle': 100},
    'SlidingDoor': {'Kind': 'Slide', 'Out': 0.42, 'Back': 4.4},
}


def lua(v, ind=1):
    pad = '\t' * ind
    if isinstance(v, dict):
        items = []
        for k, x in v.items():
            key = k if str(k).isidentifier() else f'["{k}"]'
            items.append(f'{pad}{key} = {lua(x, ind + 1)},')
        return '{\n' + '\n'.join(items) + '\n' + '\t' * (ind - 1) + '}'
    if isinstance(v, (list, tuple)):
        if len(v) == 3 and all(isinstance(x, (int, float)) for x in v):
            return f'Vector3.new({v[0]}, {v[1]}, {v[2]})'
        return '{ ' + ', '.join(lua(x, ind + 1) for x in v) + ' }'
    if isinstance(v, bool):
        return 'true' if v else 'false'
    if isinstance(v, str):
        return f'"{v}"'
    return str(v)


def write_config(stats):
    P = stats['parts']
    cfg = {
        'Name': NAME,
        'BodyPart': 'Body',
        'BodyBoxCentre': P['Body']['box_centre'],   # model origin (ground, between axles) = Body box centre - this
        'Doors': {},
        'Points': stats['points'],
        'Screens': {k: {'Face': 'Right'} for k in stats['screens']},
        'TextureSets': {g: {'Parts': ns, 'ColorMap': 'rbxassetid://0', 'NormalMap': 'rbxassetid://0',
                            'RoughnessMap': 'rbxassetid://0', 'MetalnessMap': 'rbxassetid://0'}
                        for g, (ns, _) in BAKE_GROUPS.items()},
        'Neon': {'HeadLights': [255, 244, 214], 'TailLights': [224, 38, 46], 'LightBar': [108, 255, 176],
                 'CabinLights': [158, 247, 255], 'Screen1': [45, 224, 138], 'Screen2': [45, 224, 138],
                 'Screen3': [45, 224, 138]},
        'Glass': {'Part': 'Glass', 'Color': [14, 22, 24], 'Transparency': 0.55},
        'NoCollide': ['HeadLights', 'TailLights', 'LightBar', 'CabinLights', 'Screen1', 'Screen2', 'Screen3',
                      'SteeringWheel'],
    }
    for n, d in DOORS.items():
        e = dict(d)
        hinge = Vector(game_pos(pivots([])[n]))
        e['HingeOffset'] = [round(x, 3) for x in (hinge - Vector(P[n]['box_centre']))]   # from the part's centre
        cfg['Doors'][n] = e
    path = os.path.join(OUT, 'Roblox', 'GhostVanConfig.luau')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as fh:
        fh.write('--!strict\n-- GENERATED by blender/build_van.py - model-space numbers for the GhostVan MeshParts.\n')
        fh.write('-- Model space: +Y up, front = -Z (LookVector), right = +X. Units: studs.\n')
        fh.write('return ' + lua(cfg) + '\n')


def set_pivot(o, p):
    p = Vector(p)
    o.data.transform(Matrix.Translation(-p))
    o.location = p


def finish(col, M, J, screens):
    stats = {'name': NAME, 'units': 'studs', 'parts': {}}
    t0 = sum(geo.tri_count([o]) for o in J.values())
    removed = optimize.remove_hidden_faces(J['Body'], occluders=[J['Interior']], rays=20)
    removed += optimize.remove_hidden_faces(J['Interior'], occluders=[J['Body']], rays=20)
    stats['hidden_faces_removed'] = removed
    stats['triangles_before_optimise'] = t0
    for o in J.values():
        geo.shade_by_angle(o, 32)
    final, tex = {}, {}
    samples = 1 if NO_BAKE else 16
    for g, (names, size) in BAKE_GROUPS.items():
        if NO_BAKE:
            for n in names:
                final[n] = J[n]
            continue
        parts, maps = bake_group(g, [J[n] for n in names], size, samples)
        final.update(parts)
        tex[g] = {k: os.path.relpath(v, OUT) for k, v in maps.items()}
    for n, key in FLAT.items():
        o = J[n]
        o.data.materials.clear()
        o.data.materials.append(M[key])
        final[n] = o
    pv = pivots(screens)
    for n, o in final.items():
        piv = pv.get(n, (ORIGIN_X, 0, 0))
        set_pivot(o, piv)
        o.matrix_world = TO_GAME @ Matrix.Translation(Vector(piv))
        bpy.ops.object.select_all(action='DESELECT')
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        geo.shade_by_angle(o, 32)
    meshes = list(final.values())
    for n, o in final.items():
        stats['parts'][n] = {'triangles': geo.tri_count([o]), 'pivot': game_pos(pv.get(n, (ORIGIN_X, 0, 0))),
                             'texture_set': next((g for g, (ns, _) in BAKE_GROUPS.items() if n in ns), None),
                             'health': geo.mesh_health(o)}
    stats['triangles_total'] = geo.tri_count(meshes)
    lo, hi = stage.bounds(meshes)
    stats['bounds_roblox'] = {'size_x_width': round(hi.x - lo.x, 2), 'size_y_height': round(hi.z - lo.z, 2),
                              'size_z_length': round(hi.y - lo.y, 2)}
    stats['textures'] = tex
    stats['points'] = {k: game_pos(v) for k, v in {
        'DriverSeat': (15.85, 2.15, 3.7), 'PassengerSeat': (15.85, -2.15, 3.7), 'Stool': (7.3, 1.3, FLOOR + 1.7),
        'CabinLight': (7.5, 0, ROOF - 0.6), 'HeadLightL': (20.3, 3.05, 3.15), 'HeadLightR': (20.3, -3.05, 3.15),
        'LightBar': (14.0, 0, ROOF + 0.8), 'RearEntry': (-1.5, 0, 0.0), 'SideEntry': (12.4, -HW - 1.5, 0.0),
        'Spotlight': (11.45, 2.3, ROOF + 0.62)}.items()}
    stats['screens'] = {f'Screen{i + 1}': {'centre': game_pos(c), 'size': list(sz), 'faces': 'Right (+X, into the cabin)'}
                        for i, (c, sz) in enumerate(screens)}
    # MeshParts are re-centred on their bounding box by Roblox: store each part's box centre in model space
    for n, o in final.items():
        vs = [o.matrix_world @ v.co for v in o.data.vertices]
        lo_, hi_ = [min(v[i] for v in vs) for i in range(3)], [max(v[i] for v in vs) for i in range(3)]
        c = [(a + b) / 2 for a, b in zip(lo_, hi_)]
        stats['parts'][n]['box_centre'] = [round(c[0], 3), round(c[2], 3), round(-c[1], 3)]
        stats['parts'][n]['box_size'] = [round(hi_[0] - lo_[0], 3), round(hi_[2] - lo_[2], 3), round(hi_[1] - lo_[1], 3)]
    write_config(stats)
    os.makedirs(os.path.join(OUT, 'Exports'), exist_ok=True)
    stage.export_fbx(os.path.join(OUT, 'Exports', f'{NAME}.fbx'), meshes)
    with open(os.path.join(OUT, f'{NAME}_stats.json'), 'w') as fh:
        json.dump(stats, fh, indent=1)
    src = os.path.join(OUT, 'Source')
    os.makedirs(src, exist_ok=True)
    if not NO_BAKE:
        bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(src, f'{NAME}.blend'))
    print('STATS', json.dumps({'tris': stats['triangles_total'], 'removed': removed, 'bounds': stats['bounds_roblox']}))
    return final, stats


if __name__ == '__main__':
    col, M, J, screens = main()
    os.makedirs(OUT, exist_ok=True)
    for p, o in J.items():
        print(p, len(o.data.polygons), geo.tri_count([o]))
    print('TOTAL_TRIS', geo.tri_count(list(J.values())))
    if PREVIEW:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, '_preview.blend'))
    else:
        finish(col, M, J, screens)

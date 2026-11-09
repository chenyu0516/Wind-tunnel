FeatureScript 3112;
import(path : "onshape/std/common.fs", version : "3112.0");

// Mini wind tunnel (1:43, Arduino Uno) — 3D layout model from build_plan_mini.md.
// Units mm. Frame from spec/mini.json: x downstream, y left, z up;
// x = 0 at contraction exit, z = 0 on the test-section floor inner surface, duct axis z = 63.

const ZC = 63;      // duct axis height
const T = 3;        // panel thickness
const DESK = -150;  // desk top (assumed)

function mmv(x is number, y is number, z is number) returns Vector
{
    return vector(x, y, z) * millimeter;
}

function bodies(id is Id) returns Query
{
    return qCreatedBy(id, EntityType.BODY);
}

function blk(context is Context, id is Id, a is array, b is array)
{
    fCuboid(context, id, { "corner1" : mmv(a[0], a[1], a[2]), "corner2" : mmv(b[0], b[1], b[2]) });
}

function cyl(context is Context, id is Id, a is array, b is array, d is number)
{
    fCylinder(context, id, { "bottomCenter" : mmv(a[0], a[1], a[2]), "topCenter" : mmv(b[0], b[1], b[2]), "radius" : d / 2 * millimeter });
}

function cut(context is Context, id is Id, targets is Query, tools is Query, keep is boolean)
{
    opBoolean(context, id, { "tools" : tools, "targets" : targets, "operationType" : BooleanOperationType.SUBTRACTION, "keepTools" : keep });
}

function fuse(context is Context, id is Id, q is Query)
{
    opBoolean(context, id, { "tools" : q, "operationType" : BooleanOperationType.UNION });
}

function tagQ(context is Context, q is Query, name is string, c is Color)
{
    setProperty(context, { "entities" : q, "propertyType" : PropertyType.NAME, "value" : name });
    setProperty(context, { "entities" : q, "propertyType" : PropertyType.APPEARANCE, "value" : c });
}

function tag(context is Context, id is Id, name is string, c is Color)
{
    tagQ(context, bodies(id), name, c);
}

function shellBox(context is Context, id is Id, a is array, b is array, ia is array, ib is array)
{
    blk(context, id + "o", a, b);
    blk(context, id + "i", ia, ib);
    cut(context, id + "s", bodies(id + "o"), bodies(id + "i"), false);
}

function pipe(context is Context, id is Id, a is array, b is array, od is number, bore is number)
{
    cyl(context, id + "o", a, b, od);
    cyl(context, id + "i", a, b, bore);
    cut(context, id + "s", bodies(id + "o"), bodies(id + "i"), false);
}

// Straight rectangular duct along x, open ends, inner w x h centred on the duct axis.
function rectDuct(context is Context, id is Id, x0 is number, x1 is number, w is number, h is number)
{
    shellBox(context, id, [x0, -w / 2 - T, ZC - h / 2 - T], [x1, w / 2 + T, ZC + h / 2 + T],
            [x0 - 1, -w / 2, ZC - h / 2], [x1 + 1, w / 2, ZC + h / 2]);
}

// Rectangle w x h in the y-z plane at station x (sketch x = world y, sketch y = world z).
function rectSection(context is Context, id is Id, x is number, w is number, h is number) returns Query
{
    const sk = newSketchOnPlane(context, id, { "sketchPlane" : plane(mmv(x, 0, 0), vector(1, 0, 0), vector(0, 1, 0)) });
    skRectangle(sk, "r", { "firstCorner" : vector(-w / 2, ZC - h / 2) * millimeter, "secondCorner" : vector(w / 2, ZC + h / 2) * millimeter });
    skSolve(sk);
    return qSketchRegion(id);
}

// Hollow lofted duct through rectangular stations (inner sizes), wall thickness t.
function loftDuct(context is Context, id is Id, xs is array, ws is array, hs is array, t is number)
{
    var outer = [];
    var inner = [];
    var sketches = [];
    for (var i = 0; i < size(xs); i += 1)
    {
        outer = append(outer, rectSection(context, id + ("o" ~ i), xs[i], ws[i] + 2 * t, hs[i] + 2 * t));
        inner = append(inner, rectSection(context, id + ("i" ~ i), xs[i], ws[i], hs[i]));
        sketches = append(sketches, bodies(id + ("o" ~ i)));
        sketches = append(sketches, bodies(id + ("i" ~ i)));
    }
    opLoft(context, id + "lo", { "profileSubqueries" : outer, "bodyType" : ToolBodyType.SOLID });
    opLoft(context, id + "li", { "profileSubqueries" : inner, "bodyType" : ToolBodyType.SOLID });
    cut(context, id + "s", bodies(id + "lo"), bodies(id + "li"), false);
    opDeleteBodies(context, id + "d", { "entities" : qUnion(sketches) });
}

// Side profile (points [x, z]) extruded across y0..y1.
function sideExtrude(context is Context, id is Id, pts is array, y0 is number, y1 is number)
{
    const sk = newSketchOnPlane(context, id + "sk", { "sketchPlane" : plane(mmv(0, y1, 0), vector(0, -1, 0), vector(1, 0, 0)) });
    var p = [];
    for (var q in pts)
    {
        p = append(p, vector(q[0], q[1]) * millimeter);
    }
    p = append(p, p[0]);
    skPolyline(sk, "p", { "points" : p });
    skSolve(sk);
    opExtrude(context, id + "ex", { "entities" : qSketchRegion(id + "sk"), "direction" : vector(0, -1, 0),
                "endBound" : BoundingType.BLIND, "endDepth" : (y1 - y0) * millimeter });
    opDeleteBodies(context, id + "del", { "entities" : bodies(id + "sk") });
}

// Tube of diameter d along a polyline of [x, y, z] points, fused into one body.
// Each segment runs d/2 past both ends so neighbouring segments overlap at the bends.
function tubePath(context is Context, id is Id, pts is array, d is number)
{
    var q = [];
    for (var i = 1; i < size(pts); i += 1)
    {
        const a = vector(pts[i - 1][0], pts[i - 1][1], pts[i - 1][2]);
        const b = vector(pts[i][0], pts[i][1], pts[i][2]);
        const u = normalize(b - a) * (d / 2);
        fCylinder(context, id + ("c" ~ i), { "bottomCenter" : (a - u) * millimeter, "topCenter" : (b + u) * millimeter, "radius" : d / 2 * millimeter });
        q = append(q, bodies(id + ("c" ~ i)));
    }
    fuse(context, id + "u", qUnion(q));
}

// Flat board whose inner edge is a smooth curve (2D points [u, v] in plane pl, u increasing)
// and whose outer edge is the straight line v = vOuter; extruded along the plane normal.
function curveBoard(context is Context, id is Id, pl is Plane, pts is array, vOuter is number, depth is number)
{
    const sk = newSketchOnPlane(context, id + "sk", { "sketchPlane" : pl });
    var p = [];
    for (var q in pts)
    {
        p = append(p, vector(q[0], q[1]) * millimeter);
    }
    const n = size(pts);
    const a = vector(pts[n - 1][0], vOuter) * millimeter;
    const b = vector(pts[0][0], vOuter) * millimeter;
    skFitSpline(sk, "c", { "points" : p });
    skLineSegment(sk, "l1", { "start" : p[n - 1], "end" : a });
    skLineSegment(sk, "l2", { "start" : a, "end" : b });
    skLineSegment(sk, "l3", { "start" : b, "end" : p[0] });
    skSolve(sk);
    opExtrude(context, id + "ex", { "entities" : qSketchRegion(id + "sk"), "direction" : pl.normal,
                "endBound" : BoundingType.BLIND, "endDepth" : depth * millimeter });
    opDeleteBodies(context, id + "del", { "entities" : bodies(id + "sk") });
}

// M6 levelling foot: rubber pad on the desk plus bolt up into the part above (top z).
function levelFoot(context is Context, id is Id, x is number, y is number, zTop is number)
{
    cyl(context, id + "pad", [x, y, DESK], [x, y, DESK + 4], 18);
    cyl(context, id + "bolt", [x, y, DESK + 4], [x, y, zTop], 6);
    fuse(context, id + "u", bodies(id));
}

// One 120 x 120 x 38 fan centred at (yc, zc).
function fan(context is Context, id is Id, x0 is number, yc is number, zc is number, n is string, frameColor is Color, rotorColor is Color)
{
    const x1 = x0 + 38;
    blk(context, id + "fr", [x0, yc - 60, zc - 60], [x1, yc + 60, zc + 60]);
    cyl(context, id + "vh", [x0 - 1, yc, zc], [x1 + 1, yc, zc], 116);
    cut(context, id + "vc", bodies(id + "fr"), bodies(id + "vh"), false);
    blk(context, id + "s0", [x1 - 4, yc + 18, zc - 2], [x1, yc + 59, zc + 2]);
    blk(context, id + "s1", [x1 - 4, yc - 59, zc - 2], [x1, yc - 18, zc + 2]);
    blk(context, id + "s2", [x1 - 4, yc - 2, zc + 18], [x1, yc + 2, zc + 59]);
    blk(context, id + "s3", [x1 - 4, yc - 2, zc - 59], [x1, yc + 2, zc - 18]);
    const frame = qUnion([bodies(id + "fr"), bodies(id + "s0"), bodies(id + "s1"), bodies(id + "s2"), bodies(id + "s3")]);
    fuse(context, id + "fu", frame);
    tagQ(context, frame, "A5 12038 fan frame " ~ n, frameColor);

    cyl(context, id + "hub", [x0 + 2, yc, zc], [x1 - 4, yc, zc], 40);
    var rotor = [bodies(id + "hub")];
    for (var k = 0; k < 7; k += 1)
    {
        const bid = id + ("b" ~ k);
        blk(context, bid, [-1, -12, 18], [1, 12, 56]);
        const tr = transform(mmv((x0 + x1) / 2 - 1, yc, zc)) *
            rotationAround(line(mmv(0, 0, 0), vector(1, 0, 0)), k * 360 / 7 * degree) *
            rotationAround(line(mmv(0, 0, 0), vector(0, 0, 1)), 35 * degree);
        opTransform(context, bid + "t", { "bodies" : bodies(bid), "transform" : tr });
        rotor = append(rotor, bodies(bid));
    }
    fuse(context, id + "ru", qUnion(rotor));
    tagQ(context, qUnion(rotor), "A5 Fan rotor " ~ n, rotorColor);
}

annotation { "Feature Type Name" : "MiniWindTunnel" }
export const miniWindTunnel = defineFeature(function(context is Context, id is Id, definition is map)
    precondition
    {
    }
    {
        const WOOD = color(0.80, 0.68, 0.50);
        const PET = color(0.92, 0.90, 0.82, 0.6);
        const PC = color(0.62, 0.80, 1.0, 0.28);
        const STEEL = color(0.45, 0.47, 0.50);
        const ALU = color(0.78, 0.80, 0.84);
        const BLACK = color(0.12, 0.12, 0.14);
        const DARK = color(0.25, 0.25, 0.28);
        const CELLC = color(0.70, 0.72, 0.60);
        const PRINT = color(0.95, 0.55, 0.15);
        const RED = color(0.80, 0.08, 0.08);
        const WHITE = color(0.95, 0.95, 0.95);
        const BRASS = color(0.80, 0.62, 0.25);
        const SILICONE = color(0.92, 0.92, 0.88, 0.7);
        const DESKC = color(0.72, 0.58, 0.40);
        const BRICK = color(0.65, 0.25, 0.18);
        const SPINE = color(0.62, 0.45, 0.28);
        const HIGHP = color(0.90, 0.30, 0.30, 0.85);
        const LOWP = color(0.30, 0.50, 0.90, 0.85);

        // ---------- A1 inlet bell (lip radius 42) ----------
        var bx = [];
        var bw = [];
        var bh = [];
        for (var k = 0; k <= 5; k += 1)
        {
            const u = k / 5;
            const d = 42 * (1 - sqrt(1 - (1 - u) * (1 - u)));
            bx = append(bx, -696 + 63 * u);
            bw = append(bw, 412 + 2 * d);
            bh = append(bh, 309 + 2 * d);
        }
        loftDuct(context, id + "bell", bx, bw, bh, T);
        tag(context, id + "bell", "A1 Inlet bell", PET);

        // ---------- A1 settling chamber, honeycomb, screens ----------
        rectDuct(context, id + "set", -633, -378, 412, 309);
        tag(context, id + "set", "A1 Settling chamber 412x309", WOOD);
        blk(context, id + "hc", [-616, -206, ZC - 154.5], [-576, 206, ZC + 154.5]);
        tag(context, id + "hc", "A1 Honeycomb (6 mm straws, 40 deep)", color(0.95, 0.93, 0.75, 0.55));
        blk(context, id + "sc1", [-513.5, -206, ZC - 154.5], [-512.5, 206, ZC + 154.5]);
        tag(context, id + "sc1", "A1 Screen 1", color(0.3, 0.3, 0.32, 0.35));
        blk(context, id + "sc2", [-450.5, -206, ZC - 154.5], [-449.5, 206, ZC + 154.5]);
        tag(context, id + "sc2", "A1 Screen 2", color(0.3, 0.3, 0.32, 0.35));

        // ---------- A2 contraction 6:1, 5th-order profile ----------
        var cx = [];
        var cw = [];
        var ch = [];
        for (var k = 0; k <= 10; k += 1)
        {
            const t = k / 10;
            const f = 6 * t ^ 5 - 15 * t ^ 4 + 10 * t ^ 3;
            cx = append(cx, -378 + 378 * t);
            cw = append(cw, 412 - 244 * f);
            ch = append(ch, 309 - 183 * f);
        }
        loftDuct(context, id + "con", cx, cw, ch, 1);
        tag(context, id + "con", "A2 Contraction 6:1 (PET sheet)", PET);
        const ribS = [0, 76, 151, 189, 227, 302, 378];
        var ribs = [];
        var ribSlots = [];
        var spineSlots = [];
        for (var k = 0; k < size(ribS); k += 1)
        {
            const s = ribS[k];
            const t = s / 378;
            const f = 6 * t ^ 5 - 15 * t ^ 4 + 10 * t ^ 3;
            const w = 412 - 244 * f + 2;
            const h = 309 - 183 * f + 2;
            const xa = min(max(-378 + s - 3, -378), -6);
            const rid = id + ("rib" ~ k);
            shellBox(context, rid, [xa, -w / 2 - 25, ZC - h / 2 - 25], [xa + 6, w / 2 + 25, ZC + h / 2 + 25],
                    [xa - 1, -w / 2, ZC - h / 2], [xa + 7, w / 2, ZC + h / 2]);
            ribs = append(ribs, bodies(rid));
            // half-lap slots: rib is notched from its outer edge (12.5 deep) at the middle of each side,
            // spine is notched from its curved inner edge (12.5 deep) at each rib station
            const sid = id + ("rs" ~ k);
            blk(context, sid + "t", [xa - 1, -3, ZC + h / 2 + 12.5], [xa + 7, 3, ZC + h / 2 + 26]);
            blk(context, sid + "b", [xa - 1, -3, ZC - h / 2 - 26], [xa + 7, 3, ZC - h / 2 - 12.5]);
            blk(context, sid + "l", [xa - 1, w / 2 + 12.5, ZC - 3], [xa + 7, w / 2 + 26, ZC + 3]);
            blk(context, sid + "r", [xa - 1, -w / 2 - 26, ZC - 3], [xa + 7, -w / 2 - 12.5, ZC + 3]);
            ribSlots = append(ribSlots, bodies(sid));
            const pid = id + ("ps" ~ k);
            blk(context, pid + "t", [xa, -4, ZC + h / 2 - 4], [xa + 6, 4, ZC + h / 2 + 12.5]);
            blk(context, pid + "b", [xa, -4, ZC - h / 2 - 12.5], [xa + 6, 4, ZC - h / 2 + 4]);
            blk(context, pid + "l", [xa, w / 2 - 4, ZC - 4], [xa + 6, w / 2 + 12.5, ZC + 4]);
            blk(context, pid + "r", [xa, -w / 2 - 12.5, ZC - 4], [xa + 6, -w / 2 + 4, ZC + 4]);
            spineSlots = append(spineSlots, bodies(pid));
        }

        // Four spines (6 mm plywood): inner edge = sheet outer surface curve, outer edge straight,
        // so the ribs drop into the slots already spaced and squared.
        var vTop = [];
        var vBot = [];
        var vL = [];
        var vR = [];
        for (var k = 0; k <= 20; k += 1)
        {
            const t = k / 20;
            const f = 6 * t ^ 5 - 15 * t ^ 4 + 10 * t ^ 3;
            const x = -378 + 378 * t;
            const h = 309 - 183 * f + 2;
            const w = 412 - 244 * f + 2;
            vTop = append(vTop, [x, ZC + h / 2]);
            vBot = append(vBot, [x, ZC - h / 2]);
            vL = append(vL, [x, w / 2]);
            vR = append(vR, [x, -w / 2]);
        }
        const xzPlane = plane(mmv(0, 3, 0), vector(0, -1, 0), vector(1, 0, 0));
        const xyPlane = plane(mmv(0, 0, ZC - 3), vector(0, 0, 1), vector(1, 0, 0));
        curveBoard(context, id + "spT", xzPlane, vTop, ZC + 155.5 + 25, 6);
        curveBoard(context, id + "spB", xzPlane, vBot, ZC - 155.5 - 25, 6);
        curveBoard(context, id + "spL", xyPlane, vL, 207 + 25, 6);
        curveBoard(context, id + "spR", xyPlane, vR, -207 - 25, 6);
        // spine extensions past both end ribs so the end ribs sit in closed slots;
        // inlet end steps out over the settling-chamber wall, exit end over sleeve 1
        blk(context, id + "xspT1", [-393, -3, ZC + 157.5], [-378, 3, ZC + 180.5]);
        blk(context, id + "xspT2", [0, -3, ZC + 69.3], [8, 3, ZC + 180.5]);
        blk(context, id + "xspB1", [-393, -3, ZC - 180.5], [-378, 3, ZC - 157.5]);
        blk(context, id + "xspB2", [0, -3, ZC - 180.5], [8, 3, ZC - 69.3]);
        blk(context, id + "xspL1", [-393, 209, ZC - 3], [-378, 232, ZC + 3]);
        blk(context, id + "xspL2", [0, 90.3, ZC - 3], [8, 232, ZC + 3]);
        blk(context, id + "xspR1", [-393, -232, ZC - 3], [-378, -209, ZC + 3]);
        blk(context, id + "xspR2", [0, -232, ZC - 3], [8, -90.3, ZC + 3]);
        const spineNames = ["spT", "spB", "spL", "spR"];
        const spineLabels = ["A2 Spine top (6 mm plywood, half-lapped with ribs)", "A2 Spine bottom (straight edge = datum)", "A2 Spine left", "A2 Spine right"];
        var spineQ = [];
        for (var k = 0; k < 4; k += 1)
        {
            const nm = spineNames[k];
            spineQ = append(spineQ, qUnion([bodies(id + nm), bodies(id + ("x" ~ nm ~ "1")), bodies(id + ("x" ~ nm ~ "2"))]));
            fuse(context, id + ("spfu" ~ k), spineQ[k]);
        }
        cut(context, id + "ribcut", qUnion(ribs), qUnion(ribSlots), false);
        cut(context, id + "spcut", qUnion(spineQ), qUnion(spineSlots), false);
        for (var k = 0; k < size(ribS); k += 1)
        {
            tag(context, id + ("rib" ~ k), "A2 Contraction rib s=" ~ ribS[k] ~ " (half-lap slots)", WOOD);
        }
        for (var k = 0; k < 4; k += 1)
        {
            tagQ(context, spineQ[k], spineLabels[k], SPINE);
        }
        // ---------- A3 test section 168 x 126 x 336, clear PC ----------
        rectDuct(context, id + "ts", 0, 336, 168, 126);

        // ---------- slip-joint sleeves (3 mm, 0.3 mm clearance; tape the seam after assembly) ----------
        shellBox(context, id + "sl1", [0, -90.3, ZC - 69.3], [20, 90.3, ZC + 69.3], [-1, -87.3, ZC - 66.3], [21, 87.3, ZC + 66.3]);
        tag(context, id + "sl1", "H1 Sleeve 1 (glued to last contraction rib; test section slides in 20 mm; tape seam)", WOOD);
        shellBox(context, id + "sl2", [316, -90.3, ZC - 69.3], [344, 90.3, ZC + 69.3], [315, -87.3, ZC - 66.3], [345, 87.3, ZC + 66.3]);
        tag(context, id + "sl2", "H1 Sleeve 2 (glued to diffuser inlet; over test-section outlet 20 mm; tape seam)", WOOD);

        // ---------- B ground plate, wheel wells, saddles ----------
        sideExtrude(context, id + "gp", [[42, 22.5], [48, 21], [294, 21], [294, 24], [48, 24]], -83, 83);
        sideExtrude(context, id + "flap", [[294.5, 21], [310, 19.5], [310, 21], [294.5, 24]], -83, 83);
        tag(context, id + "flap", "B Ground plate trailing-edge flap", WHITE);
        const WH = [[147, -19], [147, 19], [210, -19], [210, 19]];
        const TR = 8;
        const ANG = 20.9 * degree;
        const TZ = 31.2;
        const cxo = TR * sin(ANG);
        const czo = TZ - TR * cos(ANG);
        const sl = tan(ANG);
        const HW = 4.5;
        var openings = [];
        var holes = [];
        var wells = [bodies(id + "ts")];
        for (var i = 0; i < 4; i += 1)
        {
            const x = WH[i][0];
            const y = WH[i][1];
            const n = i + 1;
            blk(context, id + ("op" ~ i), [x - 10, y - 5, 20], [x + 10, y + 5, 25]);
            openings = append(openings, bodies(id + ("op" ~ i)));

            shellBox(context, id + ("well" ~ i), [x - 13, y - 7, 9], [x + 13, y + 7, 21], [x - 10, y - 5, 12], [x + 10, y + 5, 22]);
            wells = append(wells, bodies(id + ("well" ~ i)));

            sideExtrude(context, id + ("sad" ~ i), [[x - HW, 13], [x + HW, 13], [x + HW, czo + (HW - cxo) * sl],
                        [x, czo - cxo * sl], [x - HW, czo + (HW - cxo) * sl]], y - 4, y + 4);
            tag(context, id + ("sad" ~ i), "B V-saddle " ~ n, PRINT);

            cyl(context, id + ("tyre" ~ i), [x, y - 3, TZ], [x, y + 3, TZ], 16);
            tag(context, id + ("tyre" ~ i), "Car tyre " ~ n, BLACK);

            blk(context, id + ("post" ~ i), [x - 1.5, y - 1.5, -35], [x + 1.5, y + 1.5, 13]);
            tag(context, id + ("post" ~ i), "C Saddle post " ~ n, STEEL);

            pipe(context, id + ("shr" ~ i), [x, y, 0], [x, y, 9], 5.5, 4.5);
            tag(context, id + ("shr" ~ i), "B Post shroud " ~ n, ALU);

            cyl(context, id + ("hole" ~ i), [x, y, -4], [x, y, 12.5], 4.6);
            holes = append(holes, bodies(id + ("hole" ~ i)));
        }
        cut(context, id + "gpc", bodies(id + "gp"), qUnion(openings), false);
        tag(context, id + "gp", "B Ground plate (3 mm, 4:1 elliptic leading edge)", WHITE);
        cut(context, id + "hcut", qUnion(wells), qUnion(holes), false);
        for (var i = 0; i < 4; i += 1)
        {
            tag(context, id + ("well" ~ i), "B Wheel well (closed) " ~ (i + 1), DARK);
        }
        const legs = [[60, -70], [60, 70], [280, -70], [280, 70]];
        for (var i = 0; i < 4; i += 1)
        {
            cyl(context, id + ("gpl" ~ i), [legs[i][0], legs[i][1], 0], [legs[i][0], legs[i][1], 21], 6);
            tag(context, id + ("gpl" ~ i), "B Ground plate standoff " ~ (i + 1), ALU);
        }

        // ---------- 1:43 car (planning shape) ----------
        sideExtrude(context, id + "car", [[126, 27], [126, 37], [129, 41], [152, 44], [170, 57], [218, 58], [229, 52], [231, 44], [231, 27]], -19, 19);
        try silent(opFillet(context, id + "car" + "fil", { "entities" : qCreatedBy(id + "car" + "ex", EntityType.EDGE), "radius" : 1.5 * millimeter }));
        tag(context, id + "car", "1:43 car (planning shape)", RED);

        // ---------- probes and taps ----------
        cyl(context, id + "pit1", [55, 55, 87], [85, 55, 87], 4);
        cyl(context, id + "pit2", [85, 55, 85], [85, 55, 150], 4);
        cut(context, id + "pitc", bodies(id + "ts"), bodies(id + "pit2"), true);
        const pitot = qUnion([bodies(id + "pit1"), bodies(id + "pit2")]);
        fuse(context, id + "pitf", pitot);
        tagQ(context, pitot, "D Pitot tube D4", BRASS);
        tag(context, id + "ts", "A3 Test section (3 mm clear PC)", PC);

        const taps = [
                [[-420, 209, ZC], [-420, 215, ZC]], [[-420, -209, ZC], [-420, -215, ZC]],
                [[-420, 0, ZC + 157.5], [-420, 0, ZC + 163.5]], [[-420, 0, ZC - 157.5], [-420, 0, ZC - 163.5]],
                [[30, 87, ZC], [30, 93, ZC]], [[30, -87, ZC], [30, -93, ZC]],
                [[30, 0, ZC + 66], [30, 0, ZC + 72]], [[30, 0, ZC - 66], [30, 0, ZC - 72]],
                [[42, -87, 75], [42, -93, 75]], [[126, -87, 75], [126, -93, 75]],
                [[210, -87, 75], [210, -93, 75]], [[294, -87, 75], [294, -93, 75]]
            ];
        var tapQ = [];
        for (var i = 0; i < size(taps); i += 1)
        {
            cyl(context, id + ("tap" ~ i), taps[i][0], taps[i][1], 2.5);
            tapQ = append(tapQ, bodies(id + ("tap" ~ i)));
        }
        tagQ(context, qUnion(tapQ), "D Wall static tap fittings", BRASS);

        // ---------- C plenum, balance, pedestal ----------
        shellBox(context, id + "pl", [87, -83, -136], [273, 83, -3], [90, -80, -133], [270, 80, -2]);
        blk(context, id + "plh", [150, -30, -137], [210, 30, -132]);
        cut(context, id + "plc", bodies(id + "pl"), bodies(id + "plh"), false);
        tag(context, id + "pl", "C Sealed plenum (PC)", PC);
        shellBox(context, id + "skirt", [145, -35, -138], [215, 35, -136.2], [162, -18, -139], [198, 18, -135]);
        tag(context, id + "skirt", "C Rubber skirt", DARK);

        blk(context, id + "frm", [140, -26, -40], [217, 26, -35]);
        blk(context, id + "tab", [217, 13, -50], [222, 23, -35]);
        const frame = qUnion([bodies(id + "frm"), bodies(id + "tab")]);
        fuse(context, id + "frmf", frame);
        tagQ(context, frame, "C Common frame (with drag push tab - bolt to cell)", ALU);

        const bl = [[152, -20], [152, 20], [205, -20], [205, 20]];
        for (var i = 0; i < 4; i += 1)
        {
            blk(context, id + ("blade" ~ i), [bl[i][0] - 0.05, bl[i][1] - 5, -60], [bl[i][0] + 0.05, bl[i][1] + 5, -40]);
            tag(context, id + ("blade" ~ i), "C Feeler-gauge blade 0.1x10x20 " ~ (i + 1), STEEL);
        }
        blk(context, id + "plat", [130, -30, -65], [230, 30, -60]);
        tag(context, id + "plat", "C Drag stage", ALU);
        blk(context, id + "dcp", [222, -23.5, -60], [228, -13.5, -55]);
        tag(context, id + "dcp", "C Drag load cell mount", ALU);
        blk(context, id + "dcell", [222, -23.5, -55], [228, 23.5, -43]);
        tag(context, id + "dcell", "C 100 g drag load cell", CELLC);

        blk(context, id + "vcell", [140, -6.35, -80], [220, 6.35, -67.3]);
        tag(context, id + "vcell", "C 1 kg vertical load cell", CELLC);
        blk(context, id + "vsp1", [140, -6.35, -67.3], [158, 6.35, -65]);
        tag(context, id + "vsp1", "C Load cell upper spacer", ALU);
        blk(context, id + "vsp2", [202, -6.35, -83], [220, 6.35, -80]);
        tag(context, id + "vsp2", "C Load cell lower spacer", ALU);
        blk(context, id + "bbase", [120, -40, -93], [240, 40, -83]);
        tag(context, id + "bbase", "C Balance base plate", ALU);
        blk(context, id + "col", [162, -18, DESK + 10], [198, 18, -93]);
        tag(context, id + "col", "C Pedestal column (through plenum floor; bolts to balance base; stays in classroom)", STEEL);
        blk(context, id + "ped", [105, -165, DESK], [255, 165, DESK + 10]);
        tag(context, id + "ped", "C Pedestal plate (on desk)", STEEL);
        blk(context, id + "brk1", [105, 100, DESK + 10], [255, 160, -60]);
        tag(context, id + "brk1", "C Ballast 1", BRICK);
        blk(context, id + "brk2", [105, -160, DESK + 10], [255, -100, -60]);
        tag(context, id + "brk2", "C Ballast 2", BRICK);

        cyl(context, id + "vent1", [178, -87, 75], [178, -99, 75], 4);
        cyl(context, id + "vent2", [178, -97, 77], [178, -97, -42], 4);
        cyl(context, id + "vent3", [178, -99, -40], [178, -83, -40], 4);
        const vent = qUnion([bodies(id + "vent1"), bodies(id + "vent2"), bodies(id + "vent3")]);
        fuse(context, id + "ventf", vent);
        tagQ(context, vent, "C Plenum vent tube (to mid-car side-wall tap)", SILICONE);

        // transport lock: thumb screws through both plenum walls clamp the common frame and the balance base
        var lockQ = [];
        var shaftQ = [];
        const sides = [1, -1];
        const lockRows = [[-37.5, 26], [-88, 40]];
        for (var i = 0; i < 2; i += 1)
        {
            for (var j = 0; j < 2; j += 1)
            {
                const s = sides[i];
                const z = lockRows[j][0];
                const lockId = id + ("lock" ~ i ~ j);
                cyl(context, lockId + "k", [200, s * 83, z], [200, s * 91, z], 14);
                cyl(context, lockId + "s", [200, s * 87, z], [200, s * lockRows[j][1], z], 4);
                shaftQ = append(shaftQ, bodies(lockId + "s"));
                lockQ = append(lockQ, bodies(lockId));
            }
        }
        cut(context, id + "lockc", bodies(id + "pl"), qUnion(shaftQ), true);
        for (var i = 0; i < 2; i += 1)
        {
            for (var j = 0; j < 2; j += 1)
            {
                fuse(context, id + ("locku" ~ i ~ j), bodies(id + ("lock" ~ i ~ j)));
            }
        }
        tagQ(context, qUnion(lockQ), "H3 Transport lock screws (shown locked; back out before measuring)", BRASS);

        // module 2 feet under the plenum corners (pedestal stays separate)
        var feet2 = [];
        const pf = [[93, -75], [93, 75], [267, -75], [267, 75]];
        for (var i = 0; i < 4; i += 1)
        {
            levelFoot(context, id + ("pft" ~ i), pf[i][0], pf[i][1], -133);
            feet2 = append(feet2, bodies(id + ("pft" ~ i)));
        }
        tagQ(context, qUnion(feet2), "H2 Module 2 levelling feet M6 x4", DARK);

        // ---------- A4 diffuser, safety mesh ----------
        loftDuct(context, id + "dif", [336, 986], [168, 240], [126, 240], T);
        tag(context, id + "dif", "A4 Diffuser 168x126 to 240x240", WOOD);

        var mesh = [];
        shellBox(context, id + "mfr", [985.5, -123, ZC - 123], [988, 123, ZC + 123], [985, -120, ZC - 120], [989, 120, ZC + 120]);
        mesh = append(mesh, bodies(id + "mfr"));
        for (var j = 0; j <= 30; j += 1)
        {
            const v = -120 + 8 * j;
            blk(context, id + ("mh" ~ j), [986.4, -120, ZC + v - 0.4], [987.2, 120, ZC + v + 0.4]);
            blk(context, id + ("mv" ~ j), [986.4, v - 0.4, ZC - 120], [987.2, v + 0.4, ZC + 120]);
            mesh = append(mesh, bodies(id + ("mh" ~ j)));
            mesh = append(mesh, bodies(id + ("mv" ~ j)));
        }
        fuse(context, id + "meshf", qUnion(mesh));
        tagQ(context, qUnion(mesh), "A4 Safety mesh (7 mm opening)", STEEL);

        // ---------- A5 fan box: two 2 x 2 layers stacked (x 998-1036 and 1036-1074) ----------
        rectDuct(context, id + "fm", 988, 1086, 240, 240);
        tag(context, id + "fm", "A5 Fan box 240x240 (two stacked 2x2 layers)", WOOD);
        const fp = [[-60, ZC - 60], [60, ZC - 60], [-60, ZC + 60], [60, ZC + 60]];
        for (var i = 0; i < 4; i += 1)
        {
            fan(context, id + ("fan" ~ i), 998, fp[i][0], fp[i][1], "layer 1 #" ~ (i + 1), BLACK, DARK);
            fan(context, id + ("fanB" ~ i), 1036, fp[i][0], fp[i][1], "layer 2 #" ~ (i + 1), BLACK, DARK);
        }

        // ---------- supports and desks ----------
        // module 1 (inlet: bell + settling + contraction) and module 3 (diffuser + fans) cradles on M6 levelling feet
        blk(context, id + "sup1", [-600, -180, DESK + 15], [-570, 180, ZC - 157.5]);
        blk(context, id + "sup2", [-480, -180, DESK + 15], [-450, 180, ZC - 157.5]);
        tagQ(context, qUnion([bodies(id + "sup1"), bodies(id + "sup2")]), "H2 Module 1 cradles", WOOD);
        blk(context, id + "sup3", [992, -126, DESK + 15], [1082, 126, ZC - 123]);
        sideExtrude(context, id + "sup5", [[600, DESK + 15], [630, DESK + 15], [630, -28.8], [600, -26.15]], -100, 100);
        tagQ(context, qUnion([bodies(id + "sup3"), bodies(id + "sup5")]), "H2 Module 3 cradles", WOOD);
        var feet1 = [];
        var feet3 = [];
        const feet1Pos = [[-585, -165], [-585, 165], [-465, -165], [-465, 165]];
        const feet3Pos = [[615, -85], [615, 85], [1037, -110], [1037, 110]];
        for (var i = 0; i < 4; i += 1)
        {
            levelFoot(context, id + ("f1t" ~ i), feet1Pos[i][0], feet1Pos[i][1], DESK + 25);
            feet1 = append(feet1, bodies(id + ("f1t" ~ i)));
            levelFoot(context, id + ("f3t" ~ i), feet3Pos[i][0], feet3Pos[i][1], DESK + 25);
            feet3 = append(feet3, bodies(id + ("f3t" ~ i)));
        }
        tagQ(context, qUnion(feet1), "H2 Module 1 levelling feet M6 x4", DARK);
        tagQ(context, qUnion(feet3), "H2 Module 3 levelling feet M6 x4", DARK);

        const desks = [[-715, 185], [185, 1085]];
        for (var i = 0; i < 2; i += 1)
        {
            const dx0 = desks[i][0];
            const dx1 = desks[i][1];
            const did = id + ("desk" ~ i);
            blk(context, did + "top", [dx0, -300, DESK - 20], [dx1, 300, DESK]);
            blk(context, did + "l0", [dx0 + 20, -280, -900], [dx0 + 60, -240, DESK - 20]);
            blk(context, did + "l1", [dx0 + 20, 240, -900], [dx0 + 60, 280, DESK - 20]);
            blk(context, did + "l2", [dx1 - 60, -280, -900], [dx1 - 20, -240, DESK - 20]);
            blk(context, did + "l3", [dx1 - 60, 240, -900], [dx1 - 20, 280, DESK - 20]);
            tag(context, did, "Desk " ~ (i + 1), DESKC);
        }

        // ---------- D electronics and speed sensors (on desk 2) ----------
        // electronics board: everything that plugs together lives on one plywood board, carried as one piece
        const BZ = DESK + 6;
        blk(context, id + "eboard", [190, -295, DESK], [390, -155, BZ]);
        tag(context, id + "eboard", "H5 Electronics board (Uno, 3 HX711, sensor B, tees, connectors)", WOOD);
        blk(context, id + "uno", [215, -209, BZ + 6], [283.6, -155.6, BZ + 7.6]);
        tag(context, id + "uno", "D Arduino Uno", color(0.0, 0.45, 0.65));
        var standoffs = [];
        const sop = [[218, -206], [280.6, -206], [218, -158.6], [280.6, -158.6]];
        for (var i = 0; i < 4; i += 1)
        {
            cyl(context, id + ("so" ~ i), [sop[i][0], sop[i][1], BZ], [sop[i][0], sop[i][1], BZ + 6], 4);
            standoffs = append(standoffs, bodies(id + ("so" ~ i)));
        }
        tagQ(context, qUnion(standoffs), "H5 Uno standoffs", BRASS);
        for (var i = 0; i < 3; i += 1)
        {
            blk(context, id + ("hx" ~ i), [200 + 24 * i, -292, BZ], [221 + 24 * i, -258, BZ + 3]);
            tag(context, id + ("hx" ~ i), "D HX711 #" ~ (i + 1), color(0.1, 0.5, 0.2));
        }
        blk(context, id + "conn", [350, -172, BZ], [388, -160, BZ + 10]);
        tag(context, id + "conn", "H5 Connector strip (3 load cells, fan PWM/tach, hatch switch, USB)", BLACK);
        cyl(context, id + "qcH", [192, -215, BZ + 3], [206, -215, BZ + 3], 7);
        cyl(context, id + "qcL", [192, -245, BZ + 3], [206, -245, BZ + 3], 7);
        tagQ(context, qUnion([bodies(id + "qcH"), bodies(id + "qcL")]), "H5 Pressure quick-connects (unplug to carry)", BRASS);
        blk(context, id + "psu", [700, 170, DESK], [850, 290, DESK + 86]);
        tag(context, id + "psu", "G 12 V 20 A+ power supply (old ATX)", DARK);

        shellBox(context, id + "sabox", [400, -295, DESK], [600, -165, DESK + 150], [402, -293, DESK + 2], [598, -167, DESK + 148]);
        tag(context, id + "sabox", "D2 Speed sensor A airtight box", color(0.9, 0.95, 1.0, 0.22));
        pipe(context, id + "dish", [510, -230, DESK + 2], [510, -230, DESK + 52], 106, 100);
        cyl(context, id + "dishf", [510, -230, DESK + 2], [510, -230, DESK + 5], 106);
        const dish = qUnion([bodies(id + "dish"), bodies(id + "dishf")]);
        fuse(context, id + "dishu", dish);
        tagQ(context, dish, "D2 A Oil dish ID 100", WHITE);
        cyl(context, id + "oil", [510, -230, DESK + 5], [510, -230, DESK + 50], 100);
        cyl(context, id + "bellA", [510, -230, DESK + 15], [510, -230, DESK + 95], 62.4);
        cyl(context, id + "bellB", [510, -230, DESK + 14], [510, -230, DESK + 93.8], 60);
        cut(context, id + "bellc", bodies(id + "bellA"), bodies(id + "bellB"), false);
        cut(context, id + "oilc", bodies(id + "oil"), bodies(id + "bellA"), true);
        tag(context, id + "oil", "D2 A Baby oil 45 deep", color(1.0, 0.85, 0.35, 0.5));
        tag(context, id + "bellA", "D2 A Bell ID 60 (PETG)", PRINT);
        cyl(context, id + "thread", [510, -230, DESK + 95], [510, -230, DESK + 120], 1);
        tag(context, id + "thread", "D2 A Thread", WHITE);
        blk(context, id + "sacell", [466, -236, DESK + 120], [513, -224, DESK + 126]);
        tag(context, id + "sacell", "D2 A 100 g load cell", CELLC);
        blk(context, id + "saarm", [405, -238, DESK + 126], [470, -222, DESK + 136]);
        blk(context, id + "sapil", [405, -240, DESK + 2], [425, -220, DESK + 126]);
        const bracket = qUnion([bodies(id + "saarm"), bodies(id + "sapil")]);
        fuse(context, id + "sabr", bracket);
        tagQ(context, bracket, "D2 A Rigid bracket (glued to box floor)", ALU);
        // ports on the tunnel-side wall of the box (x = 400)
        cyl(context, id + "portH", [392, -190, DESK + 60], [402, -190, DESK + 60], 4);
        tag(context, id + "portH", "D2 A High port (box air only)", BRASS);
        // low side: brass U-snorkel from the port, over the dish rim, down, under the bell rim, up inside the bell
        tubePath(context, id + "snork", [[392, -270, DESK + 60], [510, -270, DESK + 60], [510, -270, DESK + 10],
                    [510, -245, DESK + 10], [510, -245, DESK + 85]], 4);
        cut(context, id + "snorkc", bodies(id + "oil"), bodies(id + "snork"), true);
        tag(context, id + "snork", "D2 A Low port + brass U-tube (tip 35 above oil)", BRASS);

        // speed sensor B: two film canisters taped together, one barb each on top
        cyl(context, id + "bmp1", [330, -207, BZ], [330, -207, BZ + 50], 35);
        cyl(context, id + "bmp2", [330, -243, BZ], [330, -243, BZ + 50], 35);
        tag(context, id + "bmp1", "D2 B High canister BMP280 0x77", BLACK);
        tag(context, id + "bmp2", "D2 B Low canister BMP280 0x76", BLACK);
        cyl(context, id + "bnub1", [330, -207, BZ + 50], [330, -207, BZ + 56], 4);
        cyl(context, id + "bnub2", [330, -243, BZ + 50], [330, -243, BZ + 56], 4);
        tagQ(context, qUnion([bodies(id + "bnub1"), bodies(id + "bnub2")]), "D2 B Barbs", BRASS);

        // ---------- D pressure lines: wall static rings -> tees -> sensors A and B ----------
        // high side: settling-chamber ring (4 taps at x = -420, joined by a loop)
        tubePath(context, id + "H" + "ring", [[-420, 215, ZC], [-420, 215, ZC + 163.5], [-420, -215, ZC + 163.5],
                    [-420, -215, ZC - 163.5], [-420, 215, ZC - 163.5], [-420, 215, ZC]], 4);
        tubePath(context, id + "H" + "lead", [[-420, -215, ZC - 163.5], [-420, -215, DESK + 3], [186, -215, DESK + 3], [186, -215, BZ + 3], [300, -215, BZ + 3]], 4);
        tubePath(context, id + "H" + "toA", [[300, -215, BZ + 3], [300, -190, BZ + 3], [300, -190, DESK + 60], [392, -190, DESK + 60]], 4);
        tubePath(context, id + "H" + "toB", [[300, -215, BZ + 3], [300, -215, DESK + 70], [330, -207, DESK + 70], [330, -207, BZ + 56]], 4);
        fuse(context, id + "Hu", bodies(id + "H"));
        tag(context, id + "H", "D High-side line (red): settling ring > tee > A box air, B high", HIGHP);
        // low side: test-section entrance ring (4 taps at x = 30, clear of sleeve 1)
        tubePath(context, id + "L" + "ring", [[30, 93, ZC], [30, 93, ZC + 72], [30, -93, ZC + 72],
                    [30, -93, ZC - 72], [30, 93, ZC - 72], [30, 93, ZC]], 4);
        tubePath(context, id + "L" + "lead", [[30, -93, ZC - 72], [30, -245, ZC - 72], [30, -245, DESK + 3], [186, -245, DESK + 3], [186, -245, BZ + 3], [300, -245, BZ + 3]], 4);
        tubePath(context, id + "L" + "toA", [[300, -245, BZ + 3], [300, -270, BZ + 3], [300, -270, DESK + 60], [392, -270, DESK + 60]], 4);
        tubePath(context, id + "L" + "toB", [[300, -245, BZ + 3], [300, -245, DESK + 75], [330, -243, DESK + 75], [330, -243, BZ + 56]], 4);
        fuse(context, id + "Lu", bodies(id + "L"));
        tag(context, id + "L", "D Low-side line (blue): entrance ring > tee > inside A bell, B low", LOWP);
        blk(context, id + "teeH", [296, -219, BZ], [304, -211, BZ + 7]);
        blk(context, id + "teeL", [296, -249, BZ], [304, -241, BZ + 7]);
        tagQ(context, qUnion([bodies(id + "teeH"), bodies(id + "teeL")]), "D Tees", BRASS);

        // ---------- E smoke: removable wand through a roof grommet, jar source sucked by the tunnel ----------
        tubePath(context, id + "wand", [[100, 0, 215], [100, 0, 47], [114, 0, 47]], 4);
        cut(context, id + "wandc", bodies(id + "ts"), bodies(id + "wand"), true);
        tag(context, id + "wand", "E Smoke wand D4 (tip downstream ahead of car; remove for force runs)", BRASS);
        pipe(context, id + "grom", [100, 0, 129], [100, 0, 133], 12, 4);
        tag(context, id + "grom", "E Wand grommet (roof x = 100)", DARK);
        pipe(context, id + "jar", [40, 210, DESK], [40, 210, DESK + 130], 90, 86);
        cyl(context, id + "jarb", [40, 210, DESK], [40, 210, DESK + 2], 90);
        const jar = qUnion([bodies(id + "jar"), bodies(id + "jarb")]);
        fuse(context, id + "jaru", jar);
        tagQ(context, jar, "E Smoke source jar", color(0.85, 0.95, 0.9, 0.3));
        cyl(context, id + "lid", [40, 210, DESK + 130], [40, 210, DESK + 136], 92);
        tag(context, id + "lid", "E Jar lid (smoke barb + small air inlet)", ALU);
        cyl(context, id + "incense", [40, 210, DESK + 2], [40, 210, DESK + 95], 2);
        tag(context, id + "incense", "E Incense stick (or ultrasonic mister)", color(0.45, 0.28, 0.15));
        tubePath(context, id + "hose", [[40, 210, DESK + 136], [40, 210, 215], [100, 0, 215]], 6);
        tag(context, id + "hose", "E Smoke hose (fed by tunnel suction, no blower)", SILICONE);
        blk(context, id + "clamp", [34, 204, 60], [46, 216, 72]);
        tag(context, id + "clamp", "E Pinch clamp (sets smoke flow)", BLACK);
    }, {});

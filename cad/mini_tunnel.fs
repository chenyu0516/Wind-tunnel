FeatureScript 3112;
import(path : "onshape/std/common.fs", version : "3112.0");

// Mini wind tunnel (1:43, Arduino Uno): the model the laser cutter and 3D printer work from (build_plan_mini.md).
// Units mm. Frame from spec/mini.json: x downstream, y left, z up;
// x = 0 at contraction exit, z = 0 on the test-section floor inner surface, duct axis z = 63.
//
// Every part name starts with how the part is made:
//   LC3-PLY  laser-cut 3 mm plywood          LC3-ACR  laser-cut 3 mm clear acrylic
//   PET      cut from 1 mm PET sheet (its flat pattern is in the laser view)
//   3DP      3D-printed PETG                 BUY      bought part, shown for reference
//   REF      not part of the tunnel (desks)
// The laser cutter takes 3 mm at most, so thicker parts are two 3 mm layers glued together ("layer 1/2").
// View "Laser sheets" lays every LC3 and PET part flat at z = 0, packed onto beds of the given size.
// Export each bed's top faces as DXF. Parts bigger than the bed are set aside to the right and turned red.

export enum TunnelView
{
    annotation { "Name" : "Assembled" }
    ASSEMBLED,
    annotation { "Name" : "Laser sheets (flat)" }
    LASER
}

const BED_X_BOUNDS = { (millimeter) : [100, 600, 3000] } as LengthBoundSpec;
const BED_Y_BOUNDS = { (millimeter) : [100, 400, 3000] } as LengthBoundSpec;

const ZC = 63;      // duct axis height
const T = 3;        // laser-cut sheet thickness
const SH = 1;       // PET sheet thickness (bell and contraction)
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

// Block split into two 3 mm layers along axis ax (0 = x, 1 = y, 2 = z): id + "a" (lower), id + "b" (upper).
function lam(context is Context, id is Id, a is array, b is array, ax is number)
{
    const m = (a[ax] + b[ax]) / 2;
    var b1 = b;
    b1[ax] = m;
    var a2 = a;
    a2[ax] = m;
    blk(context, id + "a", a, b1);
    blk(context, id + "b", a2, b);
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

// Name a laser-cut (mat "PLY" / "ACR") or PET part and return its entry for the laser view.
// Each entry must be exactly one body.
function lc(context is Context, q is Query, mat is string, name is string, c is Color) returns map
{
    const full = (mat == "PET" ? "PET" : "LC3-" ~ mat) ~ " | " ~ name;
    tagQ(context, q, full, c);
    return { "q" : q, "m" : mat, "nm" : full };
}

// Same, for a part with openings that smaller parts can be nested in on the laser bed.
// holes: [[cornerA, cornerB], ...], world points [x, y, z] on opposite corners of each rectangular opening.
function lch(context is Context, q is Query, mat is string, name is string, c is Color, holes is array) returns map
{
    var e = lc(context, q, mat, name, c);
    e.holes = holes;
    return e;
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

// Half-width and half-height of a contraction rib opening at station x: outside of the 1 mm sheet + 0.2 mm.
function ribHole(x is number) returns array
{
    const t = min(max((x + 378) / 378, 0), 1);
    const f = 6 * t ^ 5 - 15 * t ^ 4 + 10 * t ^ 3;
    return [(412 - 244 * f) / 2 + SH + 0.2, (309 - 183 * f) / 2 + SH + 0.2];
}

// Rectangular duct along x from four 3 mm panels with finger-jointed corners; inner w x h centred on (y 0, z zc).
// Bodies id + "t", "b", "l", "r". Top and bottom own the end fingers. Fingers are about 20 mm long, and short
// frames (collar, sleeves) still get at least 3 per corner so every corner interlocks.
function boxPanels(context is Context, id is Id, x0 is number, x1 is number, w is number, h is number, zc is number)
{
    const W = w / 2;
    const H = h / 2;
    blk(context, id + "t", [x0, -W - T, zc + H], [x1, W + T, zc + H + T]);
    blk(context, id + "b", [x0, -W - T, zc - H - T], [x1, W + T, zc - H]);
    blk(context, id + "l", [x0, W, zc - H - T], [x1, W + T, zc + H + T]);
    blk(context, id + "r", [x0, -W - T, zc - H - T], [x1, -W, zc + H + T]);
    var n = max(round((x1 - x0) / 20), 3);
    if (n % 2 == 0)
    {
        n += 1;
    }
    const L = (x1 - x0) / n;
    const corners = [[1, 1], [-1, 1], [1, -1], [-1, -1]];
    for (var c = 0; c < 4; c += 1)
    {
        const sy = corners[c][0];
        const sz = corners[c][1];
        const ya = sy > 0 ? W : -W - T - 0.5;
        const za = sz > 0 ? zc + H : zc - H - T - 0.5;
        var toSide = [];
        var toTop = [];
        for (var k = 0; k < n; k += 1)
        {
            const gid = id + ("g" ~ c) + ("k" ~ k);
            const xa = k == 0 ? x0 - 0.5 : x0 + k * L;
            const xb = k == n - 1 ? x1 + 0.5 : x0 + (k + 1) * L;
            blk(context, gid, [xa, ya, za], [xb, ya + T + 0.5, za + T + 0.5]);
            if (k % 2 == 0)
            {
                toSide = append(toSide, bodies(gid));
            }
            else
            {
                toTop = append(toTop, bodies(gid));
            }
        }
        const sidePanel = bodies(id + (sy > 0 ? "l" : "r"));
        const capPanel = bodies(id + (sz > 0 ? "t" : "b"));
        cut(context, id + ("c" ~ c) + "s", sidePanel, qUnion(toSide), false);
        cut(context, id + ("c" ~ c) + "t", capPanel, qUnion(toTop), false);
    }
}

// Rectangle r = [y0, y1, z0, z1] in the y-z plane at station x (sketch x = world y, sketch y = world z).
function rectSection(context is Context, id is Id, x is number, r is array) returns Query
{
    const sk = newSketchOnPlane(context, id, { "sketchPlane" : plane(mmv(x, 0, 0), vector(1, 0, 0), vector(0, 1, 0)) });
    skRectangle(sk, "r", { "firstCorner" : vector(r[0], r[2]) * millimeter, "secondCorner" : vector(r[1], r[3]) * millimeter });
    skSolve(sk);
    return qSketchRegion(id);
}

// One duct wall lofted through rectangular sections secs[i] at stations xs[i].
function loftWall(context is Context, id is Id, xs is array, secs is array)
{
    var profiles = [];
    var sketches = [];
    for (var i = 0; i < size(xs); i += 1)
    {
        profiles = append(profiles, rectSection(context, id + ("s" ~ i), xs[i], secs[i]));
        sketches = append(sketches, bodies(id + ("s" ~ i)));
    }
    opLoft(context, id + "lo", { "profileSubqueries" : profiles, "bodyType" : ToolBodyType.SOLID });
    opDeleteBodies(context, id + "d", { "entities" : qUnion(sketches) });
}

// Four separate duct walls of thickness t through stations xs with inner sizes ws x hs (centred on the duct axis).
// Top and bottom fit between the sides; the sides are 2 t taller and cover their edges.
// Bodies id + "t", "b", "l", "r". Each wall bends one way only, so it can be cut from a flat sheet.
function ductWalls(context is Context, id is Id, xs is array, ws is array, hs is array, t is number)
{
    const names = ["t", "b", "l", "r"];
    for (var j = 0; j < 4; j += 1)
    {
        var secs = [];
        for (var i = 0; i < size(xs); i += 1)
        {
            const W = ws[i] / 2;
            const H = hs[i] / 2;
            var r = [-W - t, -W, ZC - H - t, ZC + H + t];
            if (j == 0)
            {
                r = [-W + 0.05, W - 0.05, ZC + H, ZC + H + t];
            }
            else if (j == 1)
            {
                r = [-W + 0.05, W - 0.05, ZC - H - t, ZC - H];
            }
            else if (j == 2)
            {
                r = [W, W + t, ZC - H - t, ZC + H + t];
            }
            secs = append(secs, r);
        }
        loftWall(context, id + names[j], xs, secs);
    }
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

// Flat pattern of a sheet bent one way: stations xs, distance of the sheet from the duct axis rs (the bend curve),
// half-width across the bend hw. Returns outline points [s, v] with s = distance along the sheet.
function unroll(xs is array, rs is array, hw is array) returns array
{
    var s = 0;
    var up = [];
    var dn = [];
    for (var i = 0; i < size(xs); i += 1)
    {
        if (i > 0)
        {
            s += sqrt((xs[i] - xs[i - 1]) ^ 2 + (rs[i] - rs[i - 1]) ^ 2);
        }
        up = append(up, [s, hw[i]]);
        dn = append(dn, [s, -hw[i]]);
    }
    for (var i = size(dn) - 1; i >= 0; i -= 1)
    {
        up = append(up, dn[i]);
    }
    return up;
}

// Closed outline (points [x, y]) on the XY plane, extruded t upwards.
function flatPoly(context is Context, id is Id, pts is array, t is number)
{
    const sk = newSketchOnPlane(context, id + "sk", { "sketchPlane" : XY_PLANE });
    var p = [];
    for (var q in pts)
    {
        p = append(p, vector(q[0], q[1]) * millimeter);
    }
    p = append(p, p[0]);
    skPolyline(sk, "p", { "points" : p });
    skSolve(sk);
    opExtrude(context, id + "ex", { "entities" : qSketchRegion(id + "sk"), "direction" : vector(0, 0, 1),
                "endBound" : BoundingType.BLIND, "endDepth" : t * millimeter });
    opDeleteBodies(context, id + "del", { "entities" : bodies(id + "sk") });
}

// How to lay one part flat: largest planar face down, longest straight edge of that face along x.
// Returns its flat footprint w x h and the nesting openings in footprint coordinates.
function flatInfo(context is Context, e is map) returns map
{
    const q = e.q;
    const faces = evaluateQuery(context, qGeometry(qOwnedByBody(q, EntityType.FACE), GeometryType.PLANE));
    var best = faces[0];
    var bestA = 0 * meter * meter;
    for (var f in faces)
    {
        const a = evArea(context, { "entities" : f });
        if (a > bestA)
        {
            bestA = a;
            best = f;
        }
    }
    const pl = evPlane(context, { "face" : best });
    var dir = pl.x;
    var bestL = 0 * meter;
    for (var ed in evaluateQuery(context, qGeometry(qAdjacent(best, AdjacencyType.EDGE, EntityType.EDGE), GeometryType.LINE)))
    {
        const len = evLength(context, { "entities" : ed });
        if (len > bestL)
        {
            bestL = len;
            dir = evLine(context, { "edge" : ed }).direction;
        }
    }
    const zAx = -pl.normal;
    dir = normalize(dir - dot(dir, zAx) * zAx);
    const cs = coordSystem(pl.origin, dir, zAx);
    const T0 = fromWorld(cs);
    const bx = evBox3d(context, { "topology" : q, "cSys" : cs, "tight" : true });
    const mn = bx.minCorner / millimeter;
    const mx = bx.maxCorner / millimeter;
    var holes = [];
    if (e.holes != undefined)
    {
        for (var hp in e.holes)
        {
            const a = (T0 * mmv(hp[0][0], hp[0][1], hp[0][2])) / millimeter;
            const b = (T0 * mmv(hp[1][0], hp[1][1], hp[1][2])) / millimeter;
            holes = append(holes, [min(a[0], b[0]) - mn[0], min(a[1], b[1]) - mn[1], max(a[0], b[0]) - mn[0], max(a[1], b[1]) - mn[1]]);
        }
    }
    return { "q" : q, "T0" : T0, "mn" : mn, "mx" : mx, "w" : mx[0] - mn[0], "h" : mx[1] - mn[1], "holes" : holes, "nm" : e.nm };
}

// Move a part (flatInfo p) so its flat footprint starts at (px, py) on z = 0, turned 90 degrees if rot.
function placeFlat(context is Context, id is Id, p is map, px is number, py is number, rot is boolean)
{
    var R = identityTransform();
    var x0 = p.mn[0];
    var y0 = p.mn[1];
    if (rot)
    {
        R = rotationAround(line(mmv(0, 0, 0), vector(0, 0, 1)), 90 * degree);
        x0 = -p.mx[1];
        y0 = p.mn[0];
    }
    const tr = transform(mmv(px - x0, py - y0, -p.mn[2])) * R * p.T0;
    opTransform(context, id, { "bodies" : p.q, "transform" : tr });
}

function bedOutline(context is Context, id is Id, x0 is number, y0 is number, bedX is number, bedY is number)
{
    const sk = newSketchOnPlane(context, id, { "sketchPlane" : XY_PLANE });
    skRectangle(sk, "r", { "firstCorner" : vector(x0, y0) * millimeter, "secondCorner" : vector(x0 + bedX, y0 + bedY) * millimeter });
    skSolve(sk);
}

function without(arr is array, k is number) returns array
{
    var out = [];
    for (var i = 0; i < size(arr); i += 1)
    {
        if (i != k)
        {
            out = append(out, arr[i]);
        }
    }
    return out;
}

// Pack all laser and PET parts onto beds: one row of beds per material (acrylic, plywood, PET),
// each bed outlined by a sketch rectangle. Largest parts first; each part goes into the free rectangle
// it fills best on any bed (either way round), and the openings of ring-shaped parts (ribs, frames,
// the hatch opening) become free space for smaller parts. Parts that fit no bed go to the right of
// the row, in red. Returns a one-line summary (shown as the feature's info message).
function layFlat(context is Context, id is Id, items is array, bedX is number, bedY is number) returns string
{
    var report = "";
    const GAP = 6;
    const SG = 60;
    const mats = ["ACR", "PLY", "PET"];
    var n = 0;
    var Y0 = 0;
    for (var g = 0; g < size(mats); g += 1)
    {
        var parts = [];
        for (var it in items)
        {
            if (it.m == mats[g])
            {
                parts = append(parts, flatInfo(context, it));
            }
        }
        if (size(parts) == 0)
        {
            continue;
        }
        parts = sort(parts, function(a, b)
            {
                return b.w * b.h - a.w * a.h;
            });
        var beds = [];   // per bed: free rectangles [x, y, w, h]; a part needs (w + GAP) x (h + GAP)
        var big = [];
        for (var p in parts)
        {
            const fitsN = p.w + 2 * GAP <= bedX && p.h + 2 * GAP <= bedY;
            const fitsR = p.h + 2 * GAP <= bedX && p.w + 2 * GAP <= bedY;
            if (!fitsN && !fitsR)
            {
                big = append(big, p);
                continue;
            }
            var bs = -1;
            var bi = -1;
            var br = false;
            var bestScore = inf;
            for (var s = 0; s < size(beds); s += 1)
            {
                for (var i = 0; i < size(beds[s]); i += 1)
                {
                    const cand = beds[s][i];
                    for (var r in [false, true])
                    {
                        const cw = r ? p.h : p.w;
                        const chh = r ? p.w : p.h;
                        if (cw + GAP <= cand[2] + 1e-6 && chh + GAP <= cand[3] + 1e-6)
                        {
                            const score = cand[2] * cand[3] - (cw + GAP) * (chh + GAP);
                            if (score < bestScore)
                            {
                                bestScore = score;
                                bs = s;
                                bi = i;
                                br = r;
                            }
                        }
                    }
                }
            }
            if (bs < 0)
            {
                beds = append(beds, [[GAP, GAP, bedX - GAP, bedY - GAP]]);
                bs = size(beds) - 1;
                bi = 0;
                br = !fitsN || (fitsR && p.h > p.w);
            }
            const fr = beds[bs][bi];
            const w = br ? p.h : p.w;
            const h = br ? p.w : p.h;
            const W = w + GAP;
            const H = h + GAP;
            var free = without(beds[bs], bi);
            const rw = fr[2] - W;
            const th = fr[3] - H;
            var pieces = rw < th ? [[fr[0] + W, fr[1], rw, H], [fr[0], fr[1] + H, fr[2], th]] : [[fr[0] + W, fr[1], rw, fr[3]], [fr[0], fr[1] + H, W, th]];
            for (var hl in p.holes)
            {
                // opening in bed coordinates (footprint coordinates, turned if the part is turned)
                var hr = [fr[0] + hl[0], fr[1] + hl[1], fr[0] + hl[2], fr[1] + hl[3]];
                if (br)
                {
                    hr = [fr[0] + h - hl[3], fr[1] + hl[0], fr[0] + h - hl[1], fr[1] + hl[2]];
                }
                pieces = append(pieces, [hr[0] + GAP, hr[1] + GAP, hr[2] - hr[0] - GAP, hr[3] - hr[1] - GAP]);
            }
            for (var pc in pieces)
            {
                if (pc[2] > 10 && pc[3] > 10)
                {
                    free = append(free, pc);
                }
            }
            beds[bs] = free;
            placeFlat(context, id + ("t" ~ n), p, bs * (bedX + SG) + fr[0], Y0 + fr[1], br);
            n += 1;
        }
        for (var s = 0; s < size(beds); s += 1)
        {
            bedOutline(context, id + ("bed" ~ g ~ "s" ~ s), s * (bedX + SG), Y0, bedX, bedY);
        }
        var bx = size(beds) * (bedX + SG);
        var bigH = 0;
        for (var p in big)
        {
            const rot = p.h > p.w;
            placeFlat(context, id + ("t" ~ n), p, bx, Y0 + GAP, rot);
            n += 1;
            tagQ(context, p.q, p.nm ~ " [BIGGER THAN BED: split or cut elsewhere]", color(0.9, 0.1, 0.1));
            bx += (rot ? p.h : p.w) + GAP;
            bigH = max(bigH, rot ? p.w : p.h);
        }
        report = report ~ mats[g] ~ ": " ~ size(parts) ~ " parts on " ~ size(beds) ~ " beds" ~ (size(big) > 0 ? ", " ~ size(big) ~ " too big" : "") ~ ". ";
        Y0 -= max(bedY, bigH + GAP) + 150;
    }
    return report;
}

// M6 T-nut pressed in from below: its 8 mm barrel cuts the hole through the plywood layers above it
// (laser-cut hole), the 19 mm flange sits under the bottom face. Returns the T-nut body.
function tNut(context is Context, id is Id, x is number, y is number, zBot is number, ply is Query) returns Query
{
    cyl(context, id + "b", [x, y, zBot - 1.5], [x, y, zBot + 8], 8);
    cut(context, id + "c", ply, bodies(id + "b"), true);
    cyl(context, id + "f", [x, y, zBot - 1.5], [x, y, zBot], 19);
    const q = qUnion([bodies(id + "b"), bodies(id + "f")]);
    fuse(context, id + "u", q);
    return q;
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
    tagQ(context, frame, "BUY | A5 Fan QFR1212GHE frame " ~ n, frameColor);

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
    tagQ(context, qUnion(rotor), "BUY | A5 Fan rotor " ~ n, rotorColor);
}

annotation { "Feature Type Name" : "MiniWindTunnel" }
export const miniWindTunnel = defineFeature(function(context is Context, id is Id, definition is map)
    precondition
    {
        annotation { "Name" : "View" }
        definition.view is TunnelView;
        annotation { "Name" : "Laser bed length" }
        isLength(definition.bedX, BED_X_BOUNDS);
        annotation { "Name" : "Laser bed width" }
        isLength(definition.bedY, BED_Y_BOUNDS);
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
        const SPINE = color(0.62, 0.45, 0.28);
        const HIGHP = color(0.90, 0.30, 0.30, 0.85);
        const LOWP = color(0.30, 0.50, 0.90, 0.85);
        const wallNames = ["t", "b", "l", "r"];
        const wallLabels = ["top", "bottom", "left", "right"];
        var L = [];   // laser-cut and PET parts, one body per entry (for the laser view)

        // ---------- A1 inlet bell: 4 PET sheets bent over 8 plywood gussets, 4 plywood lip strips in front ----------
        // Elliptic lip, 63 long x 42 radial. Each sheet bends one way only, so it is cut flat (pattern in the laser view).
        var bx = [];
        var bw = [];
        var bh = [];
        for (var k = 0; k <= 8; k += 1)
        {
            const phi = (90 - 11.25 * k) * degree;
            const d = 42 * (1 - cos(phi));
            bx = append(bx, -633 - 63 * sin(phi));
            bw = append(bw, 412 + 2 * d);
            bh = append(bh, 309 + 2 * d);
        }
        ductWalls(context, id + "bell", bx, bw, bh, SH);
        for (var j = 0; j < 4; j += 1)
        {
            tag(context, id + "bell" + wallNames[j], "PET | A1 Inlet bell sheet " ~ wallLabels[j] ~ " (cut from its flat pattern)", PET);
        }
        const HO = 205.5;   // lip strips and gussets: outer half-height
        const WO = 257;     // outer half-width
        blk(context, id + "lipt", [-699, -WO, ZC + 196.5], [-696, WO, ZC + HO]);
        blk(context, id + "lipb", [-699, -WO, ZC - HO], [-696, WO, ZC - 196.5]);
        blk(context, id + "lipl", [-699, 248, ZC - 196.5], [-696, WO, ZC + 196.5]);
        blk(context, id + "lipr", [-699, -WO, ZC - 196.5], [-696, -248, ZC + 196.5]);
        for (var j = 0; j < 4; j += 1)
        {
            L = append(L, lc(context, bodies(id + ("lip" ~ wallNames[j])), "PLY", "A1 Bell lip strip " ~ wallLabels[j], WOOD));
        }
        // gussets: inner edge follows the outside of the sheet, outer edge straight; tail glued onto the settling chamber
        var gTop = [];
        var gBot = [];
        var gL = [];
        var gR = [];
        for (var k = 0; k <= 8; k += 1)
        {
            gTop = append(gTop, [bx[k], ZC + bh[k] / 2 + SH + 0.3]);
            gBot = append(gBot, [bx[k], ZC - bh[k] / 2 - SH - 0.3]);
            gL = append(gL, [bx[k], bw[k] / 2 + SH + 0.3]);
            gR = append(gR, [bx[k], -bw[k] / 2 - SH - 0.3]);
        }
        for (var i = 0; i < 8; i += 1)
        {
            const gid = id + ("bg" ~ i);
            const s = i % 2 == 0 ? 1 : -1;
            if (i < 4)
            {
                // top (i 0, 1) and bottom (i 2, 3) gussets in planes y = +-130
                const c = s * 130;
                const up = i < 2;
                curveBoard(context, gid + "c", plane(mmv(0, c + 1.5, 0), vector(0, -1, 0), vector(1, 0, 0)), up ? gTop : gBot, up ? ZC + HO : ZC - HO, 3);
                blk(context, gid + "e", [-633, c - 1.5, up ? ZC + 157.5 : ZC - HO], [-603, c + 1.5, up ? ZC + HO : ZC - 157.5]);
            }
            else
            {
                // left (i 4, 5) and right (i 6, 7) gussets in planes z = axis +-90
                const c = ZC + s * 90;
                const lft = i < 6;
                curveBoard(context, gid + "c", plane(mmv(0, 0, c - 1.5), vector(0, 0, 1), vector(1, 0, 0)), lft ? gL : gR, lft ? WO : -WO, 3);
                blk(context, gid + "e", [-633, lft ? 209 : -WO, c - 1.5], [-603, lft ? WO : -209, c + 1.5]);
            }
            fuse(context, gid + "u", bodies(gid));
            L = append(L, lc(context, bodies(gid), "PLY", "A1 Bell gusset " ~ (i + 1), SPINE));
        }

        // ---------- A1 settling chamber (finger-jointed plywood), honeycomb, screens in pull-out frames ----------
        boxPanels(context, id + "set", -633, -378, 412, 309, ZC);
        const scrX = [-513, -450];
        var slotQ = [];
        for (var i = 0; i < 2; i += 1)
        {
            blk(context, id + ("slot" ~ i), [scrX[i] - 3.6, -196.3, ZC + 153], [scrX[i] + 3.6, 196.3, ZC + 159]);
            slotQ = append(slotQ, bodies(id + ("slot" ~ i)));
        }
        // 1 mm static-tap holes at x = -420 (fittings glued on outside)
        cyl(context, id + "sth0", [-420, 0, ZC + 153], [-420, 0, ZC + 159], 1);
        cyl(context, id + "sth1", [-420, 0, ZC - 159], [-420, 0, ZC - 153], 1);
        cyl(context, id + "sth2", [-420, 205, ZC], [-420, 210, ZC], 1);
        cyl(context, id + "sth3", [-420, -210, ZC], [-420, -205, ZC], 1);
        cut(context, id + "setc", bodies(id + "set"), qUnion(append(slotQ, qUnion([bodies(id + "sth0"), bodies(id + "sth1"), bodies(id + "sth2"), bodies(id + "sth3")]))), false);
        for (var j = 0; j < 4; j += 1)
        {
            L = append(L, lc(context, bodies(id + "set" + wallNames[j]), "PLY", "A1 Settling chamber panel " ~ wallLabels[j] ~ (j == 0 ? " (2 screen slots)" : ""), WOOD));
        }
        blk(context, id + "hc", [-616, -206, ZC - 154.5], [-576, 206, ZC + 154.5]);
        tag(context, id + "hc", "3DP | A1 Honeycomb (printed hex tiles, or 6 mm straws; 40 deep)", color(0.95, 0.93, 0.75, 0.55));
        for (var i = 0; i < 2; i += 1)
        {
            const xs = scrX[i];
            const sid = id + ("scr" ~ i);
            // frame fills the chamber; a narrower tab (y +-196) passes through the roof slot as a grip
            const fx = [[xs - 3.5, xs - 0.5], [xs + 0.5, xs + 3.5]];
            for (var m = 0; m < 2; m += 1)
            {
                const fid = sid + ("f" ~ (m + 1));
                shellBox(context, fid + "s", [fx[m][0], -206, ZC - 154.5], [fx[m][1], 206, ZC + 154.5], [fx[m][0] - 1, -191, ZC - 139.5], [fx[m][1] + 1, 191, ZC + 139.5]);
                blk(context, fid + "t", [fx[m][0], -196, ZC + 154.5], [fx[m][1], 196, ZC + 165.5]);
                fuse(context, fid + "u", bodies(fid));
                L = append(L, lch(context, bodies(fid), "PLY", "A1 Screen " ~ (i + 1) ~ " frame " ~ (m == 0 ? "front (pulls out through roof slot)" : "back"), WOOD,
                            [[[fx[m][0], -191, ZC - 139.5], [fx[m][0], 191, ZC + 139.5]]]));
            }
            blk(context, sid + "m", [xs - 0.5, -198, ZC - 148], [xs + 0.5, 198, ZC + 148]);
            tag(context, sid + "m", "BUY | A1 Screen " ~ (i + 1) ~ " mesh (voile or stainless, 60-70 % open), glued between frames", color(0.3, 0.3, 0.32, 0.35));
        }

        // ---------- A2 contraction 6:1, 5th-order profile: 4 PET sheets ----------
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
        ductWalls(context, id + "con", cx, cw, ch, SH);
        for (var j = 0; j < 4; j += 1)
        {
            tag(context, id + "con" + wallNames[j], "PET | A2 Contraction sheet " ~ wallLabels[j] ~ " (cut from its flat pattern)", PET);
        }
        // ribs: each is two 3 mm plywood layers glued (6 mm), half-lapped with the spines
        const ribS = [0, 76, 151, 189, 227, 302, 378];
        var ribs = [];
        var ribSlots = [];
        var spineSlots = [];
        for (var k = 0; k < size(ribS); k += 1)
        {
            const s = ribS[k];
            const t = s / 378;
            const f = 6 * t ^ 5 - 15 * t ^ 4 + 10 * t ^ 3;
            const w = 412 - 244 * f + 2 * SH + 0.4;   // 0.2 mm clearance around the sheets
            const h = 309 - 183 * f + 2 * SH + 0.4;
            const xa = min(max(-378 + s - 3, -378), -6);
            const rid = id + ("rib" ~ k);
            // each 3 mm layer gets its own opening, sized at its upstream face, so the narrowing sheet
            // rests on the layer edges and never cuts into the rib
            const ho = ribHole(xa);
            const hi = ribHole(xa + 3);
            shellBox(context, rid + "a", [xa, -w / 2 - 25, ZC - h / 2 - 25], [xa + 3, w / 2 + 25, ZC + h / 2 + 25],
                    [xa - 1, -ho[0], ZC - ho[1]], [xa + 4, ho[0], ZC + ho[1]]);
            shellBox(context, rid + "b", [xa + 3, -w / 2 - 25, ZC - h / 2 - 25], [xa + 6, w / 2 + 25, ZC + h / 2 + 25],
                    [xa + 2, -hi[0], ZC - hi[1]], [xa + 7, hi[0], ZC + hi[1]]);
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

        // Four spines, each two 3 mm plywood layers: inner edge = sheet outer surface curve, outer edge straight,
        // so the ribs drop into the slots already spaced and squared. They run 30 mm past the inlet rib
        // (stepping out over the settling chamber, into a notch in the joint collar) and 8 mm past the exit rib (over sleeve 1).
        var vTop = [];
        var vBot = [];
        var vL = [];
        var vR = [];
        for (var k = 0; k <= 20; k += 1)
        {
            const t = k / 20;
            const f = 6 * t ^ 5 - 15 * t ^ 4 + 10 * t ^ 3;
            const x = -378 + 378 * t;
            const h = 309 - 183 * f + 2 * SH + 0.4;
            const w = 412 - 244 * f + 2 * SH + 0.4;
            vTop = append(vTop, [x, ZC + h / 2]);
            vBot = append(vBot, [x, ZC - h / 2]);
            vL = append(vL, [x, w / 2]);
            vR = append(vR, [x, -w / 2]);
        }
        const spines = [
                { "nm" : "spT", "pts" : vTop, "vo" : ZC + 180.5, "ax" : 1, "label" : "A2 Spine top",
                    "e" : [[[-408, -3, ZC + 157.5], [-378, 3, ZC + 180.5]], [[0, -3, ZC + 69.3], [8, 3, ZC + 180.5]]] },
                { "nm" : "spB", "pts" : vBot, "vo" : ZC - 180.5, "ax" : 1, "label" : "A2 Spine bottom (straight edge = assembly datum)",
                    "e" : [[[-408, -3, ZC - 180.5], [-378, 3, ZC - 157.5]], [[0, -3, ZC - 180.5], [8, 3, ZC - 69.3]]] },
                { "nm" : "spL", "pts" : vL, "vo" : 232, "ax" : 2, "label" : "A2 Spine left",
                    "e" : [[[-408, 209, ZC - 3], [-378, 232, ZC + 3]], [[0, 90.3, ZC - 3], [8, 232, ZC + 3]]] },
                { "nm" : "spR", "pts" : vR, "vo" : -232, "ax" : 2, "label" : "A2 Spine right",
                    "e" : [[[-408, -232, ZC - 3], [-378, -209, ZC + 3]], [[0, -232, ZC - 3], [8, -90.3, ZC + 3]]] }
            ];
        var spineQ = [];
        var spineEntries = [];
        for (var j = 0; j < 4; j += 1)
        {
            const sp = spines[j];
            for (var ly = 0; ly < 2; ly += 1)
            {
                const sid = id + sp.nm + (ly == 0 ? "a" : "b");
                var pl = plane(mmv(0, ly == 0 ? 3 : 0, 0), vector(0, -1, 0), vector(1, 0, 0));
                if (sp.ax == 2)
                {
                    pl = plane(mmv(0, 0, ly == 0 ? ZC : ZC - 3), vector(0, 0, 1), vector(1, 0, 0));
                }
                curveBoard(context, sid + "c", pl, sp.pts, sp.vo, 3);
                for (var m = 0; m < 2; m += 1)
                {
                    var a = sp.e[m][0];
                    var b = sp.e[m][1];
                    const mid = (a[sp.ax] + b[sp.ax]) / 2;
                    if (ly == 0)
                    {
                        a[sp.ax] = mid;
                    }
                    else
                    {
                        b[sp.ax] = mid;
                    }
                    blk(context, sid + ("e" ~ m), a, b);
                }
                fuse(context, sid + "u", bodies(sid));
                spineQ = append(spineQ, bodies(sid));
                spineEntries = append(spineEntries, { "q" : bodies(sid), "label" : sp.label ~ " layer " ~ (ly + 1) ~ " of 2" });
            }
        }
        cut(context, id + "ribcut", qUnion(ribs), qUnion(ribSlots), false);
        cut(context, id + "spcut", qUnion(spineQ), qUnion(spineSlots), false);
        for (var k = 0; k < size(ribS); k += 1)
        {
            const xa = min(max(-378 + ribS[k] - 3, -378), -6);
            const ho = ribHole(xa);
            const hi = ribHole(xa + 3);
            L = append(L, lch(context, bodies(id + ("rib" ~ k) + "a"), "PLY", "A2 Contraction rib s=" ~ ribS[k] ~ " layer 1 of 2", WOOD,
                        [[[xa, -ho[0], ZC - ho[1]], [xa, ho[0], ZC + ho[1]]]]));
            L = append(L, lch(context, bodies(id + ("rib" ~ k) + "b"), "PLY", "A2 Contraction rib s=" ~ ribS[k] ~ " layer 2 of 2", WOOD,
                        [[[xa + 3, -hi[0], ZC - hi[1]], [xa + 3, hi[0], ZC + hi[1]]]]));
        }
        for (var e in spineEntries)
        {
            L = append(L, lc(context, e.q, "PLY", e.label, SPINE));
        }
        // Joint collar: rib 0 only covers 1.8 mm of the chamber panels' end grain, so a frame of four 3 mm plywood strips
        // with finger-jointed corners (3 fingers each) is glued around the outside of the chamber's outlet end, butting
        // rib 0's upstream face. Each strip has a closed notch the spine tab sits in (glued on three sides).
        // The collar stops at x = -414, clear of the static-tap ring at x = -420.
        boxPanels(context, id + "col", -414, -378, 418, 315, ZC);
        cut(context, id + "colc", bodies(id + "col"), qUnion(spineQ), true);
        for (var j = 0; j < 4; j += 1)
        {
            L = append(L, lc(context, bodies(id + "col" + wallNames[j]), "PLY", "A2 Joint collar strip " ~ wallLabels[j] ~ " (chamber to rib 0, notched for spine)", WOOD));
        }

        // ---------- A3 test section 168 x 126 x 336: flat 3 mm clear acrylic panels (laser-cut, solvent-glued) ----------
        // The side panels run down past the floor at x 87..273 and form the side walls of the balance box (C),
        // so the test section and the balance are one module with no separate plenum.
        // Floor and walls are finger-jointed along both bottom corners (17 fingers of ~20 mm; the walls own the end ones),
        // so the panels square themselves while the capillary solvent cement is run in. Where a wall continues down into
        // the balance box, the floor's fingers pass through slots in the wall.
        blk(context, id + "tsF", [0, -87, -3], [336, 87, 0]);
        const sideProfile = [[0, -3], [87, -3], [87, -86], [273, -86], [273, -3], [336, -3], [336, 126], [0, 126]];
        sideExtrude(context, id + "tsL", sideProfile, 84, 87);
        sideExtrude(context, id + "tsR", sideProfile, -87, -84);
        const nTs = 17;
        for (var sd = 0; sd < 2; sd += 1)
        {
            const y0 = sd == 0 ? 84 : -87;
            var toFloor = [];
            var toWall = [];
            for (var k = 0; k < nTs; k += 1)
            {
                const xa = k == 0 ? -0.5 : 336 * k / nTs;
                const xb = k == nTs - 1 ? 336.5 : 336 * (k + 1) / nTs;
                const jid = id + ("tsJ" ~ sd) + ("k" ~ k);
                if (k % 2 == 0)
                {
                    // wall finger: notch the floor
                    blk(context, jid, [xa, sd == 0 ? y0 : y0 - 0.5, -3.5], [xb, sd == 0 ? y0 + 3.5 : y0 + 3, 0.5]);
                    toWall = append(toWall, bodies(jid));
                }
                else
                {
                    // floor finger: slot or notch in the wall
                    blk(context, jid, [xa, sd == 0 ? y0 - 0.5 : y0, -3], [xb, sd == 0 ? y0 + 3 : y0 + 3.5, 0]);
                    toFloor = append(toFloor, bodies(jid));
                }
            }
            cut(context, id + ("tsJf" ~ sd), bodies(id + "tsF"), qUnion(toWall), false);
            cut(context, id + ("tsJw" ~ sd), bodies(id + (sd == 0 ? "tsL" : "tsR")), qUnion(toFloor), false);
        }
        // Roof: rests ON the wall tops (wider than the passage) so it can be hinged at the inlet with tape and shimmed
        // up 0-6 mm at the outlet without opening side slots; tape seals the top edges. Four acrylic locators glued to the
        // outside of the walls keep it central (the outlet pair stands 6 mm higher to keep locating it when shimmed).
        // Car hatch opening (x 120..300, y -75..75) and four magnet holes.
        blk(context, id + "tsT", [0, -87, 126], [336, 87, 129]);
        const locs = [[40, 70, 129], [280, 310, 135]];
        for (var i = 0; i < 2; i += 1)
        {
            for (var sd = 0; sd < 2; sd += 1)
            {
                const lid = id + ("tsLoc" ~ i ~ sd);
                blk(context, lid, [locs[i][0], sd == 0 ? 87 : -90, 106], [locs[i][1], sd == 0 ? 90 : -87, locs[i][2]]);
                L = append(L, lc(context, bodies(lid), "ACR", "A3 Roof locator " ~ (i == 0 ? "inlet " : "outlet ") ~ (sd == 0 ? "left" : "right") ~ " (glued to the wall outside)", PC));
            }
        }
        blk(context, id + "tsTo", [120, -75, 125], [300, 75, 130]);
        const magPos = [[112, 80], [112, -80], [308, 80], [308, -80]];
        var magHoles = [bodies(id + "tsTo")];
        for (var i = 0; i < 4; i += 1)
        {
            cyl(context, id + ("tsTm" ~ i), [magPos[i][0], magPos[i][1], 125], [magPos[i][0], magPos[i][1], 130], 6);
            magHoles = append(magHoles, bodies(id + ("tsTm" ~ i)));
        }
        cut(context, id + "tsTc", bodies(id + "tsT"), qUnion(magHoles), false);

        // ---------- A3 car hatch: plug fills the opening (0.5 mm recess), cover rests on a foam gasket ----------
        // Suction pulls the hatch inwards, so the magnets only locate it. Plug and cover are glued together.
        blk(context, id + "hPlug", [120.3, -74.7, 126.5], [299.7, 74.7, 129.5]);
        L = append(L, lc(context, bodies(id + "hPlug"), "ACR", "A3 Car hatch plug (glued under the cover)", PC));
        blk(context, id + "hCov", [108, -86, 129.5], [312, 86, 132.5]);
        blk(context, id + "hTab", [200, 86, 129.5], [214, 93, 132.5]);
        fuse(context, id + "hFu", qUnion([bodies(id + "hCov"), bodies(id + "hTab")]));
        L = append(L, lc(context, qUnion([bodies(id + "hCov"), bodies(id + "hTab")]), "ACR", "A3 Car hatch cover with switch tab", PC));
        shellBox(context, id + "hGsk", [116, -79, 129], [304, 79, 129.5], [120, -75, 128.9], [300, 75, 129.6]);
        tag(context, id + "hGsk", "BUY | A3 Hatch gasket (2 mm foam tape, compressed)", DARK);
        cyl(context, id + "hKnob", [210, 0, 132.5], [210, 0, 145], 20);
        tag(context, id + "hKnob", "3DP | A3 Hatch knob", PRINT);
        var mags = [];
        for (var i = 0; i < 4; i += 1)
        {
            cyl(context, id + ("hMag" ~ i), [magPos[i][0], magPos[i][1], 126], [magPos[i][0], magPos[i][1], 129], 6);
            mags = append(mags, bodies(id + ("hMag" ~ i)));
        }
        tagQ(context, qUnion(mags), "BUY | A3 Hatch magnets 6x3 in roof (steel washers under cover)", STEEL);
        blk(context, id + "hSw", [200, 87, 112], [214, 93, 128]);
        blk(context, id + "hSwL", [205, 89, 128], [209, 91, 129.5]);
        fuse(context, id + "hSwF", qUnion([bodies(id + "hSw"), bodies(id + "hSwL")]));
        tagQ(context, qUnion([bodies(id + "hSw"), bodies(id + "hSwL")]), "BUY | D Hatch microswitch (cover tab presses lever; fans off when lifted)", BLACK);

        // ---------- H1 slip-joint sleeves: four 3 mm plywood strips each, finger-jointed corners (0.3 mm clearance; tape the seam) ----------
        const sleeves = [[0, 20, "H1 Sleeve 1 (glued to last contraction rib)"], [316, 336, "H1 Sleeve 2 (glued to the diffuser flange)"]];
        for (var i = 0; i < 2; i += 1)
        {
            const x0 = sleeves[i][0];
            const x1 = sleeves[i][1];
            const sid = id + ("sl" ~ (i + 1));
            boxPanels(context, sid, x0, x1, 174.6, 132.6, ZC);
            for (var j = 0; j < 4; j += 1)
            {
                L = append(L, lc(context, bodies(sid + wallNames[j]), "PLY", sleeves[i][2] ~ " strip " ~ wallLabels[j], WOOD));
            }
        }

        // ---------- B ground plate, wheel wells, saddles ----------
        sideExtrude(context, id + "gp", [[42, 22.5], [48, 21], [294, 21], [294, 24], [48, 24]], -83, 83);
        sideExtrude(context, id + "flap", [[294.5, 21], [310, 19.5], [310, 21], [294.5, 24]], -83, 83);
        L = append(L, lc(context, bodies(id + "flap"), "ACR", "B Ground plate trailing-edge flap (sand the taper)", WHITE));
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
        var wells = [bodies(id + "tsF")];
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
            tag(context, id + ("sad" ~ i), "3DP | B V-saddle " ~ n, PRINT);

            cyl(context, id + ("tyre" ~ i), [x, y - 3, TZ], [x, y + 3, TZ], 16);
            tag(context, id + ("tyre" ~ i), "BUY | Car tyre " ~ n, BLACK);

            blk(context, id + ("post" ~ i), [x - 1.5, y - 1.5, -8], [x + 1.5, y + 1.5, 13]);
            tag(context, id + ("post" ~ i), "BUY | C Saddle post " ~ n ~ " (3 mm steel rod, screws into the frame)", STEEL);

            pipe(context, id + ("shr" ~ i), [x, y, 0], [x, y, 9], 5.5, 4.5);
            tag(context, id + ("shr" ~ i), "BUY | B Post shroud " ~ n ~ " (aluminium tube)", ALU);

            cyl(context, id + ("hole" ~ i), [x, y, -4], [x, y, 12.5], 4.6);
            holes = append(holes, bodies(id + ("hole" ~ i)));
        }
        cut(context, id + "gpc", bodies(id + "gp"), qUnion(openings), false);
        L = append(L, lc(context, bodies(id + "gp"), "ACR", "B Ground plate (sand the 4:1 elliptic leading edge)", WHITE));
        cut(context, id + "hcut", qUnion(wells), qUnion(holes), false);
        for (var i = 0; i < 4; i += 1)
        {
            tag(context, id + ("well" ~ i), "3DP | B Wheel well (closed) " ~ (i + 1), DARK);
        }
        const legs = [[60, -70], [60, 70], [280, -70], [280, 70]];
        for (var i = 0; i < 4; i += 1)
        {
            cyl(context, id + ("gpl" ~ i), [legs[i][0], legs[i][1], 0], [legs[i][0], legs[i][1], 21], 6);
            tag(context, id + ("gpl" ~ i), "BUY | B Ground plate standoff M3 x 21 " ~ (i + 1), ALU);
        }

        // ---------- 1:43 car (planning shape) ----------
        sideExtrude(context, id + "car", [[126, 27], [126, 37], [129, 41], [152, 44], [170, 57], [218, 58], [229, 52], [231, 44], [231, 27]], -19, 19);
        try silent(opFillet(context, id + "car" + "fil", { "entities" : qCreatedBy(id + "car" + "ex", EntityType.EDGE), "radius" : 1.5 * millimeter }));
        tag(context, id + "car", "BUY | 1:43 diecast car (planning shape)", RED);

        // ---------- probes and taps ----------
        cyl(context, id + "pit1", [55, 55, 87], [85, 55, 87], 4);
        cyl(context, id + "pit2", [85, 55, 85], [85, 55, 150], 4);
        cut(context, id + "pitc", bodies(id + "tsT"), bodies(id + "pit2"), true);
        const pitot = qUnion([bodies(id + "pit1"), bodies(id + "pit2")]);
        fuse(context, id + "pitf", pitot);
        tagQ(context, pitot, "BUY | D Pitot tube D4 (brass)", BRASS);

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
        tagQ(context, qUnion(tapQ), "BUY | D Wall static tap fittings", BRASS);
        // 1 mm tap holes in the test-section panels (laser-cut, square to the wall)
        const tapHoles = [[[30, 83, ZC], [30, 88, ZC]], [[30, -88, ZC], [30, -83, ZC]], [[30, 0, 125], [30, 0, 130]], [[30, 0, -4], [30, 0, 1]],
                [[42, -88, 75], [42, -83, 75]], [[126, -88, 75], [126, -83, 75]], [[210, -88, 75], [210, -83, 75]], [[294, -88, 75], [294, -83, 75]]];
        var thQ = [];
        for (var i = 0; i < size(tapHoles); i += 1)
        {
            cyl(context, id + ("tth" ~ i), tapHoles[i][0], tapHoles[i][1], 1);
            thQ = append(thQ, bodies(id + ("tth" ~ i)));
        }
        cut(context, id + "tthc", qUnion([bodies(id + "tsF"), bodies(id + "tsL"), bodies(id + "tsR"), bodies(id + "tsT")]), qUnion(thQ), false);

        // ---------- C balance box: part of module 2, directly under the test-section floor ----------
        // Walls: the two side panels (tsL/tsR) plus two end walls; floor = removable tray that carries the balance.
        // The box is sealed except through the wheel wells, so its pressure matches the air at the car.
        lam(context, id + "bxF", [87, -87, -92], [273, 87, -86], 2);
        blk(context, id + "bxE1", [87, -84, -86], [90, 84, -3]);
        blk(context, id + "bxE2", [270, -84, -86], [273, 84, -3]);

        // Balance with NO slide, laid out like the UPenn build guide (Weakly et al., ASEE 2024):
        // the drag cell STANDS UP from the base, a corner bracket on its top end joins it to the
        // vertical (lift) cell, which lies flat and carries the frame on its free end.
        // Load path: car -> saddles -> posts -> frame -> 1 kg vertical cell -> corner bracket -> 100 g drag cell -> foot -> base.
        // The weight runs along the drag cell's length, so it does not bend the drag cell sideways.
        lam(context, id + "frm", [140, -37, -14], [217, 37, -8], 2);
        blk(context, id + "flug", [160, 22, -26], [165, 30, -14]);
        tag(context, id + "flug", "3DP | C Frame stop lug", PRINT);
        blk(context, id + "vsp1", [154.7, -6.35, -16.3], [172.7, 6.35, -14]);
        tag(context, id + "vsp1", "3DP | C Spacer: vertical cell free end to frame", PRINT);
        blk(context, id + "vcell", [154.7, -6.35, -29], [234.7, 6.35, -16.3]);
        tag(context, id + "vcell", "BUY | C 1 kg vertical load cell (lies flat; free end carries the frame)", CELLC);
        blk(context, id + "brkH", [214, -10, -32], [240, 10, -29]);
        blk(context, id + "brkV", [234.7, -10, -46], [240, 10, -32]);
        fuse(context, id + "brkF", qUnion([bodies(id + "brkH"), bodies(id + "brkV")]));
        tagQ(context, qUnion([bodies(id + "brkH"), bodies(id + "brkV")]), "3DP | C Corner bracket joining the two load cells", PRINT);
        blk(context, id + "dcell", [222, -6.35, -79], [234.7, 6.35, -32]);
        tag(context, id + "dcell", "BUY | C 100 g drag load cell (stands up; senses fore-aft; top end in corner bracket)", CELLC);
        blk(context, id + "dfoot", [209.3, -10, -80], [222, 10, -66]);
        tag(context, id + "dfoot", "3DP | C Drag cell foot (bolted to base plate)", PRINT);
        lam(context, id + "bbase", [120, -45, -86], [245, 45, -80], 2);

        // Overload stops, adjustable so the 0.3 mm gaps can be set on the bench (tray out):
        // down-stop = M4 pan-head screw, head up, in a printed pillar under the frame;
        // fore-aft = printed fork around the frame lug with an M3 screw from each side.
        blk(context, id + "zpil", [139, -6, -80], [151, 6, -20.5]);
        cyl(context, id + "zpH1", [145, 0, -30.5], [145, 0, -20], 5.6);
        cyl(context, id + "zpH2", [145, 0, -45], [145, 0, -30], 4.2);
        cut(context, id + "zpc", bodies(id + "zpil"), qUnion([bodies(id + "zpH1"), bodies(id + "zpH2")]), false);
        tag(context, id + "zpil", "3DP | C Down-stop pillar (M4 heat-set insert on top)", PRINT);
        cyl(context, id + "zscH", [145, 0, -17.3], [145, 0, -14.3], 8);
        cyl(context, id + "zscN", [145, 0, -20.5], [145, 0, -17.3], 7.5);
        cyl(context, id + "zscS", [145, 0, -40], [145, 0, -17.3], 4);
        fuse(context, id + "zscU", qUnion([bodies(id + "zscH"), bodies(id + "zscN"), bodies(id + "zscS")]));
        tagQ(context, qUnion([bodies(id + "zscH"), bodies(id + "zscN"), bodies(id + "zscS")]),
                "BUY | C Down-stop M4 x 25 pan-head screw + lock nut (head 0.3 mm under the frame)", STEEL);
        blk(context, id + "fkA", [151, 20, -80], [157, 32, -19]);
        blk(context, id + "fkB", [168, 20, -80], [174, 32, -19]);
        blk(context, id + "fkC", [151, 20, -80], [174, 32, -74]);
        fuse(context, id + "fkU", qUnion([bodies(id + "fkA"), bodies(id + "fkB"), bodies(id + "fkC")]));
        cyl(context, id + "fkH1", [150, 26, -22], [158, 26, -22], 2.5);
        cyl(context, id + "fkH2", [167, 26, -22], [175, 26, -22], 2.5);
        cut(context, id + "fkc", qUnion([bodies(id + "fkA"), bodies(id + "fkB"), bodies(id + "fkC")]), qUnion([bodies(id + "fkH1"), bodies(id + "fkH2")]), false);
        tagQ(context, qUnion([bodies(id + "fkA"), bodies(id + "fkB"), bodies(id + "fkC")]), "3DP | C Stop fork around the frame lug (M3 tapped holes)", PRINT);
        const fs = [[145.6, 148.6, 151, 159.7], [179.4, 176.4, 174, 165.3]];   // head end, head/nut, nut/arm, tip
        for (var i = 0; i < 2; i += 1)
        {
            const sid = id + ("fks" ~ i);
            cyl(context, sid + "h", [fs[i][0], 26, -22], [fs[i][1], 26, -22], 5.5);
            cyl(context, sid + "n", [fs[i][1], 26, -22], [fs[i][2], 26, -22], 6.2);
            cyl(context, sid + "s", [fs[i][0], 26, -22], [fs[i][3], 26, -22], 3);
            fuse(context, sid + "u", bodies(sid));
            tag(context, sid, "BUY | C Fore-aft stop M3 x 16 screw + lock nut (tip 0.3 mm from the lug)", STEEL);
        }

        // transport lock: one thumb screw per side through the box wall, clamping the frame plate
        const sides = [1, -1];
        var lockQ = [];
        var shaftQ = [];
        for (var i = 0; i < 2; i += 1)
        {
            const s = sides[i];
            const lockId = id + ("lock" ~ i);
            cyl(context, lockId + "k", [200, s * 87, -11], [200, s * 95, -11], 14);
            cyl(context, lockId + "s", [200, s * 91, -11], [200, s * 37, -11], 4);
            shaftQ = append(shaftQ, bodies(lockId + "s"));
            lockQ = append(lockQ, bodies(lockId));
        }
        cut(context, id + "lockc", qUnion([bodies(id + "tsL"), bodies(id + "tsR")]), qUnion(shaftQ), true);
        for (var i = 0; i < 2; i += 1)
        {
            fuse(context, id + ("locku" ~ i), bodies(id + ("lock" ~ i)));
        }
        tagQ(context, qUnion(lockQ), "BUY | H3 Transport lock M4 thumb screws (shown locked; back out before measuring)", BRASS);

        // module 2 feet under the tray corners (no pedestal, no ballast); T-nuts pressed in from below,
        // barrel tops sealed inside the box with a dab of hot glue (the box must stay airtight)
        var tnQ = [];
        var feet2 = [];
        const pf = [[95, -79], [95, 79], [265, -79], [265, 79]];
        for (var i = 0; i < 4; i += 1)
        {
            levelFoot(context, id + ("pft" ~ i), pf[i][0], pf[i][1], -86);
            feet2 = append(feet2, bodies(id + ("pft" ~ i)));
            tnQ = append(tnQ, tNut(context, id + ("tn2" ~ i), pf[i][0], pf[i][1], -92, bodies(id + "bxF")));
        }
        tagQ(context, qUnion(feet2), "BUY | H2 Module 2 levelling feet M6 x4 (T-nuts in the tray)", DARK);

        // module 2 laser parts
        L = append(L, lc(context, bodies(id + "tsF"), "ACR", "A3 Test-section floor (post and tap holes)", PC));
        L = append(L, lch(context, bodies(id + "tsL"), "ACR", "A3 Test-section side left + balance box wall (one piece)", PC,
                    [[[0, 87, -86], [87, 87, -3]], [[273, 87, -86], [336, 87, -3]]]));
        L = append(L, lch(context, bodies(id + "tsR"), "ACR", "A3 Test-section side right + balance box wall (one piece, side taps)", PC,
                    [[[0, -87, -86], [87, -87, -3]], [[273, -87, -86], [336, -87, -3]]]));
        L = append(L, lch(context, bodies(id + "tsT"), "ACR", "A3 Test-section roof with hatch opening", PC, [[[120, -75, 126], [300, 75, 126]]]));
        L = append(L, lc(context, bodies(id + "bxE1"), "ACR", "C Balance box end wall upstream", PC));
        L = append(L, lc(context, bodies(id + "bxE2"), "ACR", "C Balance box end wall downstream", PC));
        L = append(L, lc(context, bodies(id + "bxF" + "a"), "PLY", "C Balance tray / box floor layer 1 of 2 (T-nuts for feet)", WOOD));
        L = append(L, lc(context, bodies(id + "bxF" + "b"), "PLY", "C Balance tray / box floor layer 2 of 2", WOOD));
        L = append(L, lc(context, bodies(id + "frm" + "a"), "PLY", "C Common frame plate layer 1 of 2 (posts screw in)", WOOD));
        L = append(L, lc(context, bodies(id + "frm" + "b"), "PLY", "C Common frame plate layer 2 of 2", WOOD));
        L = append(L, lc(context, bodies(id + "bbase" + "a"), "PLY", "C Balance base plate layer 1 of 2 (bolted to tray)", WOOD));
        L = append(L, lc(context, bodies(id + "bbase" + "b"), "PLY", "C Balance base plate layer 2 of 2", WOOD));

        // ---------- A4 diffuser: four flat plywood panels; safety mesh on a plywood frame ----------
        ductWalls(context, id + "dif", [336, 986], [168, 240], [126, 240], T);
        for (var j = 0; j < 4; j += 1)
        {
            L = append(L, lc(context, bodies(id + "dif" + wallNames[j]), "PLY", "A4 Diffuser panel " ~ wallLabels[j] ~ " (168x126 to 240x240)", WOOD));
        }
        // inlet flange: sleeve 2 butts against it and is glued to it; the diffuser panels pass through it
        shellBox(context, id + "dfl", [336, -90.3, ZC - 69.3], [339, 90.3, ZC + 69.3], [335, -87.2, ZC - 66.3], [340, 87.2, ZC + 66.3]);
        L = append(L, lch(context, bodies(id + "dfl"), "PLY", "A4 Diffuser inlet flange (sleeve 2 glued to it)", WOOD, [[[336, -87.2, ZC - 66.3], [336, 87.2, ZC + 66.3]]]));
        shellBox(context, id + "mfr", [986, -123, ZC - 123], [989, 123, ZC + 123], [985, -120, ZC - 120], [990, 120, ZC + 120]);
        L = append(L, lch(context, bodies(id + "mfr"), "PLY", "A4 Safety mesh frame", WOOD, [[[986, -120, ZC - 120], [986, 120, ZC + 120]]]));
        var mesh = [];
        for (var j = 0; j < 30; j += 1)
        {
            const v = -116 + 8 * j;
            blk(context, id + ("mh" ~ j), [989.1, -119.5, ZC + v - 0.4], [989.9, 119.5, ZC + v + 0.4]);
            blk(context, id + ("mv" ~ j), [989.1, v - 0.4, ZC - 119.5], [989.9, v + 0.4, ZC + 119.5]);
            mesh = append(mesh, bodies(id + ("mh" ~ j)));
            mesh = append(mesh, bodies(id + ("mv" ~ j)));
        }
        fuse(context, id + "meshf", qUnion(mesh));
        tagQ(context, qUnion(mesh), "BUY | A4 Safety mesh (7 mm opening)", STEEL);

        // ---------- A5 fan box (finger-jointed plywood): one 2 x 2 layer of fans (x 998-1036) ----------
        boxPanels(context, id + "fm", 989, 1048, 240, 240, ZC);
        for (var j = 0; j < 4; j += 1)
        {
            L = append(L, lc(context, bodies(id + "fm" + wallNames[j]), "PLY", "A5 Fan box panel " ~ wallLabels[j], WOOD));
        }
        const fp = [[-60, ZC - 60], [60, ZC - 60], [-60, ZC + 60], [60, ZC + 60]];
        for (var i = 0; i < 4; i += 1)
        {
            fan(context, id + ("fan" ~ i), 998, fp[i][0], fp[i][1], "#" ~ (i + 1), BLACK, DARK);
        }

        // ---------- H2 cradles: base plate + upright web, each two 3 mm plywood layers; M6 levelling feet ----------
        // [base corner a, base corner b, [web x0 ...], top z of webs, label, web half-width]
        const cradles = [
                [[-600, -180], [-562, 180], [-588], ZC - 157.5, "H2 Module 1 cradle (settling chamber, inlet end)", 180],
                [[-486, -180], [-450, 180], [-468], ZC - 157.5, "H2 Module 1 cradle (settling chamber, outlet end)", 180],
                [[594, -100], [630, 100], [612], -28, "H2 Module 3 cradle under the diffuser (fill the 0.3-0.8 mm slope with glue)", 95],
                [[992, -126], [1045, 126], [995, 1036], ZC - 123, "H2 Module 3 cradle under the fan box", 126]
            ];
        for (var i = 0; i < size(cradles); i += 1)
        {
            const cr = cradles[i];
            const cid = id + ("cr" ~ i);
            lam(context, cid + "base", [cr[0][0], cr[0][1], DESK + 15], [cr[1][0], cr[1][1], DESK + 21], 2);
            for (var m = 0; m < size(cr[2]); m += 1)
            {
                lam(context, cid + ("web" ~ m), [cr[2][m], -cr[5], DESK + 21], [cr[2][m] + 6, cr[5], cr[3]], 0);
            }
            L = append(L, lc(context, bodies(cid + "base" + "a"), "PLY", cr[4] ~ " base layer 1 of 2 (T-nuts for feet)", WOOD));
            L = append(L, lc(context, bodies(cid + "base" + "b"), "PLY", cr[4] ~ " base layer 2 of 2", WOOD));
            for (var m = 0; m < size(cr[2]); m += 1)
            {
                L = append(L, lc(context, bodies(cid + ("web" ~ m) + "a"), "PLY", cr[4] ~ " web " ~ (m + 1) ~ " layer 1 of 2", WOOD));
                L = append(L, lc(context, bodies(cid + ("web" ~ m) + "b"), "PLY", cr[4] ~ " web " ~ (m + 1) ~ " layer 2 of 2", WOOD));
            }
        }
        var feet1 = [];
        var feet3 = [];
        // feet sit beside the webs (not under them) so each T-nut barrel clears the web above
        const feet1Pos = [[-573, -165], [-573, 165], [-477, -165], [-477, 165]];
        const feet3Pos = [[603, -85], [603, 85], [1018, -110], [1018, 110]];
        const feet1Cr = [0, 0, 1, 1];
        const feet3Cr = [2, 2, 3, 3];
        for (var i = 0; i < 4; i += 1)
        {
            levelFoot(context, id + ("f1t" ~ i), feet1Pos[i][0], feet1Pos[i][1], DESK + 21);
            feet1 = append(feet1, bodies(id + ("f1t" ~ i)));
            levelFoot(context, id + ("f3t" ~ i), feet3Pos[i][0], feet3Pos[i][1], DESK + 21);
            feet3 = append(feet3, bodies(id + ("f3t" ~ i)));
            tnQ = append(tnQ, tNut(context, id + ("tn1" ~ i), feet1Pos[i][0], feet1Pos[i][1], DESK + 15, bodies(id + ("cr" ~ feet1Cr[i]) + "base")));
            tnQ = append(tnQ, tNut(context, id + ("tn3" ~ i), feet3Pos[i][0], feet3Pos[i][1], DESK + 15, bodies(id + ("cr" ~ feet3Cr[i]) + "base")));
        }
        tagQ(context, qUnion(feet1), "BUY | H2 Module 1 levelling feet M6 x4", DARK);
        // Contraction prop: both module 1 cradles are under the settling chamber, so without this the contraction and
        // sleeve 1 hang off the chamber joint. Pad (two layers, T-nut in layer 1) with two cheeks glued to the sides of
        // the bottom spine; its M6 foot is screwed down to just touch the desk after module 1 is levelled on its 4 feet.
        // The cheeks are glued to the spine AND bolted through it (M3), so the prop does not rely on glue alone.
        // The foot sits 12 mm off the spine so the T-nut barrel clears the spine edge.
        lam(context, id + "prop" + "pad", [-60, -24, ZC - 186.5], [-30, 24, ZC - 180.5], 2);
        blk(context, id + "prop" + "cl", [-60, 3, ZC - 180.5], [-30, 6, ZC - 160.5]);
        blk(context, id + "prop" + "cr", [-60, -6, ZC - 180.5], [-30, -3, ZC - 160.5]);
        cyl(context, id + "propH", [-45, -7, ZC - 170.5], [-45, 7, ZC - 170.5], 3.2);
        cut(context, id + "propHc", qUnion([bodies(id + "prop" + "cl"), bodies(id + "prop" + "cr"), bodies(id + "spB")]), bodies(id + "propH"), false);
        cyl(context, id + "propS" + "s", [-45, -9, ZC - 170.5], [-45, 8.5, ZC - 170.5], 3);
        cyl(context, id + "propS" + "h", [-45, 6, ZC - 170.5], [-45, 8.5, ZC - 170.5], 5.5);
        cyl(context, id + "propS" + "n", [-45, -8.4, ZC - 170.5], [-45, -6, ZC - 170.5], 6.2);
        fuse(context, id + "propSu", bodies(id + "propS"));
        tag(context, id + "propS", "BUY | H2 Prop bolt M3 x 20 + nut (through both cheeks and the bottom spine)", STEEL);
        L = append(L, lc(context, bodies(id + "prop" + "pad" + "a"), "PLY", "H2 Module 1 contraction prop pad layer 1 of 2 (T-nut for foot)", WOOD));
        L = append(L, lc(context, bodies(id + "prop" + "pad" + "b"), "PLY", "H2 Module 1 contraction prop pad layer 2 of 2", WOOD));
        L = append(L, lc(context, bodies(id + "prop" + "cl"), "PLY", "H2 Module 1 contraction prop cheek left (glued to bottom spine)", WOOD));
        L = append(L, lc(context, bodies(id + "prop" + "cr"), "PLY", "H2 Module 1 contraction prop cheek right (glued to bottom spine)", WOOD));
        levelFoot(context, id + "f1p", -45, 12, ZC - 180.5);
        tag(context, id + "f1p", "BUY | H2 Module 1 prop foot M6 (set after levelling)", DARK);
        tnQ = append(tnQ, tNut(context, id + "tnP", -45, 12, ZC - 186.5, bodies(id + "prop" + "pad")));
        tagQ(context, qUnion(tnQ), "BUY | H2 M6 T-nuts for the levelling feet (pressed in from below)", STEEL);
        tagQ(context, qUnion(feet3), "BUY | H2 Module 3 levelling feet M6 x4", DARK);

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
            tag(context, did, "REF | Desk " ~ (i + 1), DESKC);
        }

        // ---------- D electronics and speed sensor (two barometers, on desk 2) ----------
        // electronics board: everything that plugs together lives on one plywood board, carried as one piece
        const BZ = DESK + 3;
        blk(context, id + "eboard", [190, -295, DESK], [390, -155, BZ]);
        L = append(L, lc(context, bodies(id + "eboard"), "PLY", "H5 Electronics board (Uno, 2 HX711, barometer pair, connectors)", WOOD));
        blk(context, id + "uno", [215, -209, BZ + 6], [283.6, -155.6, BZ + 7.6]);
        tag(context, id + "uno", "BUY | D Arduino Uno", color(0.0, 0.45, 0.65));
        var standoffs = [];
        const sop = [[218, -206], [280.6, -206], [218, -158.6], [280.6, -158.6]];
        for (var i = 0; i < 4; i += 1)
        {
            cyl(context, id + ("so" ~ i), [sop[i][0], sop[i][1], BZ], [sop[i][0], sop[i][1], BZ + 6], 4);
            standoffs = append(standoffs, bodies(id + ("so" ~ i)));
        }
        tagQ(context, qUnion(standoffs), "BUY | H5 Uno standoffs", BRASS);
        for (var i = 0; i < 2; i += 1)
        {
            blk(context, id + ("hx" ~ i), [200 + 24 * i, -292, BZ], [221 + 24 * i, -258, BZ + 3]);
            tag(context, id + ("hx" ~ i), "BUY | D HX711 #" ~ (i + 1), color(0.1, 0.5, 0.2));
        }
        blk(context, id + "conn", [350, -172, BZ], [388, -160, BZ + 10]);
        tag(context, id + "conn", "BUY | H5 Connector strip (2 load cells, fan PWM, hatch switch, USB)", BLACK);
        cyl(context, id + "qcH", [192, -215, BZ + 3.5], [206, -215, BZ + 3.5], 7);
        cyl(context, id + "qcL", [192, -245, BZ + 3.5], [206, -245, BZ + 3.5], 7);
        tagQ(context, qUnion([bodies(id + "qcH"), bodies(id + "qcL")]), "BUY | H5 Pressure quick-connects (unplug to carry)", BRASS);
        blk(context, id + "psu", [700, 170, DESK], [850, 290, DESK + 86]);
        tag(context, id + "psu", "BUY | G 12 V 10 A+ power supply (old ATX)", DARK);

        // speed sensor: two BMP280s, each sealed in a film canister with one barb on top; the canisters touch and are
        // wrapped together in foam so they stay at the same temperature. Red line -> high (0x77), blue -> low (0x76).
        cyl(context, id + "bmp1", [330, -207, BZ], [330, -207, BZ + 50], 35);
        cyl(context, id + "bmp2", [330, -243, BZ], [330, -243, BZ + 50], 35);
        tag(context, id + "bmp1", "BUY | D2 High-side canister, BMP280 0x77 (red line)", BLACK);
        tag(context, id + "bmp2", "BUY | D2 Low-side canister, BMP280 0x76 (blue line)", BLACK);
        cyl(context, id + "bnub1", [330, -207, BZ + 50], [330, -207, BZ + 56], 4);
        cyl(context, id + "bnub2", [330, -243, BZ + 50], [330, -243, BZ + 56], 4);
        tagQ(context, qUnion([bodies(id + "bnub1"), bodies(id + "bnub2")]), "BUY | D2 Canister barbs", BRASS);
        shellBox(context, id + "bfoam", [302, -271, BZ], [358, -179, BZ + 46], [312, -261, BZ - 1], [348, -189, BZ + 47]);
        tag(context, id + "bfoam", "BUY | D2 Foam wrap around both canisters (same temperature)", color(0.85, 0.85, 0.6, 0.5));

        // ---------- D pressure lines: wall static rings -> quick-connects -> barometer canisters (no tees) ----------
        // high side: settling-chamber ring (4 taps at x = -420, joined by a loop)
        tubePath(context, id + "H" + "ring", [[-420, 215, ZC], [-420, 215, ZC + 163.5], [-420, -215, ZC + 163.5],
                    [-420, -215, ZC - 163.5], [-420, 215, ZC - 163.5], [-420, 215, ZC]], 4);
        tubePath(context, id + "H" + "lead", [[-420, -215, ZC - 163.5], [-420, -215, DESK + 3], [186, -215, DESK + 3], [186, -215, BZ + 3], [300, -215, BZ + 3]], 4);
        tubePath(context, id + "H" + "toB", [[300, -215, BZ + 3], [300, -215, DESK + 70], [330, -207, DESK + 70], [330, -207, BZ + 56]], 4);
        fuse(context, id + "Hu", bodies(id + "H"));
        tag(context, id + "H", "BUY | D High-side line (red): settling ring > high canister", HIGHP);
        // low side: test-section entrance ring (4 taps at x = 30, clear of sleeve 1)
        tubePath(context, id + "L" + "ring", [[30, 93, ZC], [30, 93, ZC + 72], [30, -93, ZC + 72],
                    [30, -93, ZC - 72], [30, 93, ZC - 72], [30, 93, ZC]], 4);
        tubePath(context, id + "L" + "lead", [[30, -93, ZC - 72], [30, -245, ZC - 72], [30, -245, DESK + 3], [186, -245, DESK + 3], [186, -245, BZ + 3], [300, -245, BZ + 3]], 4);
        tubePath(context, id + "L" + "toB", [[300, -245, BZ + 3], [300, -245, DESK + 75], [330, -243, DESK + 75], [330, -243, BZ + 56]], 4);
        fuse(context, id + "Lu", bodies(id + "L"));
        tag(context, id + "L", "BUY | D Low-side line (blue): entrance ring > low canister", LOWP);

        // ---------- E smoke: removable wand through a roof grommet, jar source sucked by the tunnel ----------
        tubePath(context, id + "wand", [[100, 0, 215], [100, 0, 47], [114, 0, 47]], 4);
        cut(context, id + "wandc", bodies(id + "tsT"), bodies(id + "wand"), true);
        tag(context, id + "wand", "BUY | E Smoke wand D4 brass (tip downstream ahead of car; remove for force runs)", BRASS);
        pipe(context, id + "grom", [100, 0, 129], [100, 0, 133], 12, 4);
        tag(context, id + "grom", "BUY | E Wand grommet (roof x = 100)", DARK);
        pipe(context, id + "jar", [40, 210, DESK], [40, 210, DESK + 130], 90, 86);
        cyl(context, id + "jarb", [40, 210, DESK], [40, 210, DESK + 2], 90);
        const jar = qUnion([bodies(id + "jar"), bodies(id + "jarb")]);
        fuse(context, id + "jaru", jar);
        tagQ(context, jar, "BUY | E Smoke source jar", color(0.85, 0.95, 0.9, 0.3));
        cyl(context, id + "lid", [40, 210, DESK + 130], [40, 210, DESK + 136], 92);
        tag(context, id + "lid", "BUY | E Jar lid (smoke barb + small air inlet)", ALU);
        cyl(context, id + "incense", [40, 210, DESK + 2], [40, 210, DESK + 95], 2);
        tag(context, id + "incense", "BUY | E Incense stick (or ultrasonic mister)", color(0.45, 0.28, 0.15));
        tubePath(context, id + "hose", [[40, 210, DESK + 136], [40, 210, 215], [100, 0, 215]], 6);
        tag(context, id + "hose", "BUY | E Smoke hose (fed by tunnel suction, no blower)", SILICONE);
        blk(context, id + "clamp", [34, 204, 60], [46, 216, 72]);
        tag(context, id + "clamp", "BUY | E Pinch clamp (sets smoke flow)", BLACK);

        // ---------- Laser view: flat patterns of the PET sheets, then every laser part laid flat on beds ----------
        if (definition.view == TunnelView.LASER)
        {
            const fid = id + "flat";
            var px = [];
            var pr = [];
            var pq = [];
            for (var k = 0; k <= 40; k += 1)
            {
                const t = k / 40;
                const f = 6 * t ^ 5 - 15 * t ^ 4 + 10 * t ^ 3;
                px = append(px, -378 + 378 * t);
                pr = append(pr, (309 - 183 * f) / 2);   // half-height: bend curve of top/bottom, half-width of sides (- SH)
                pq = append(pq, (412 - 244 * f) / 2);   // half-width: half-width of top/bottom, bend curve of sides
            }
            var qx = [];
            var qr = [];
            var qq = [];
            for (var k = 0; k <= 30; k += 1)
            {
                const phi = (90 - 3 * k) * degree;
                const d = 42 * (1 - cos(phi));
                qx = append(qx, -633 - 63 * sin(phi));
                qr = append(qr, 309 / 2 + d);
                qq = append(qq, 412 / 2 + d);
            }
            var prS = [];
            var qrS = [];
            for (var k = 0; k < size(pr); k += 1)
            {
                prS = append(prS, pr[k] + SH);
            }
            for (var k = 0; k < size(qr); k += 1)
            {
                qrS = append(qrS, qr[k] + SH);
            }
            const pats = [
                    [unroll(px, pr, pq), "A2 Contraction sheet top (flat pattern)"],
                    [unroll(px, pr, pq), "A2 Contraction sheet bottom (flat pattern)"],
                    [unroll(px, pq, prS), "A2 Contraction sheet left (flat pattern)"],
                    [unroll(px, pq, prS), "A2 Contraction sheet right (flat pattern)"],
                    [unroll(qx, qr, qq), "A1 Bell sheet top (flat pattern)"],
                    [unroll(qx, qr, qq), "A1 Bell sheet bottom (flat pattern)"],
                    [unroll(qx, qq, qrS), "A1 Bell sheet left (flat pattern)"],
                    [unroll(qx, qq, qrS), "A1 Bell sheet right (flat pattern)"]
                ];
            for (var i = 0; i < size(pats); i += 1)
            {
                flatPoly(context, fid + ("p" ~ i), pats[i][0], SH);
                L = append(L, lc(context, bodies(fid + ("p" ~ i)), "PET", pats[i][1], PET));
            }
            var keep = [];
            for (var e in L)
            {
                keep = append(keep, e.q);
            }
            opDeleteBodies(context, fid + "del", { "entities" : qSubtraction(qCreatedBy(id, EntityType.BODY), qUnion(keep)) });
            reportFeatureInfo(context, id, layFlat(context, fid + "lay", L, definition.bedX / millimeter, definition.bedY / millimeter));
        }
    }, { "view" : TunnelView.ASSEMBLED, "bedX" : 600 * millimeter, "bedY" : 400 * millimeter });

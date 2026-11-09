FeatureScript 3112;
import(path : "onshape/std/common.fs", version : "3112.0");

// Mini wind tunnel (1:43, Arduino Uno) — 3D layout model from build_plan_mini.zh-TW.md.
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

// One 120 x 120 x 38 fan centred at (yc, zc).
function fan(context is Context, id is Id, yc is number, zc is number, n is number, frameColor is Color, rotorColor is Color)
{
    const x0 = 998;
    const x1 = 1036;
    blk(context, id + "fr", [x0, yc - 60, zc - 60], [x1, yc + 60, zc + 60]);
    cyl(context, id + "vh", [x0 - 1, yc, zc], [x1 + 1, yc, zc], 116);
    cut(context, id + "vc", bodies(id + "fr"), bodies(id + "vh"), false);
    blk(context, id + "s0", [x1 - 4, yc + 18, zc - 2], [x1, yc + 59, zc + 2]);
    blk(context, id + "s1", [x1 - 4, yc - 59, zc - 2], [x1, yc - 18, zc + 2]);
    blk(context, id + "s2", [x1 - 4, yc - 2, zc + 18], [x1, yc + 2, zc + 59]);
    blk(context, id + "s3", [x1 - 4, yc - 2, zc - 59], [x1, yc + 2, zc - 18]);
    const frame = qUnion([bodies(id + "fr"), bodies(id + "s0"), bodies(id + "s1"), bodies(id + "s2"), bodies(id + "s3")]);
    fuse(context, id + "fu", frame);
    tagQ(context, frame, "A5 12038 風扇框 " ~ n, frameColor);

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
    tagQ(context, qUnion(rotor), "A5 風扇轉子 " ~ n, rotorColor);
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
        tag(context, id + "bell", "A1 進氣喇叭口", PET);

        // ---------- A1 settling chamber, honeycomb, screens ----------
        rectDuct(context, id + "set", -633, -378, 412, 309);
        tag(context, id + "set", "A1 穩定段 412×309", WOOD);
        blk(context, id + "hc", [-616, -206, ZC - 154.5], [-576, 206, ZC + 154.5]);
        tag(context, id + "hc", "A1 蜂巢（6 mm 吸管，深 40）", color(0.95, 0.93, 0.75, 0.55));
        blk(context, id + "sc1", [-513.5, -206, ZC - 154.5], [-512.5, 206, ZC + 154.5]);
        tag(context, id + "sc1", "A1 整流網 1", color(0.3, 0.3, 0.32, 0.35));
        blk(context, id + "sc2", [-450.5, -206, ZC - 154.5], [-449.5, 206, ZC + 154.5]);
        tag(context, id + "sc2", "A1 整流網 2", color(0.3, 0.3, 0.32, 0.35));

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
        tag(context, id + "con", "A2 收縮段 6:1（PET 薄板）", PET);
        const ribS = [0, 76, 151, 189, 227, 302, 378];
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
            tag(context, rid, "A2 收縮段肋板 s=" ~ s, WOOD);
        }

        // ---------- A3 test section 168 x 126 x 336, clear PC ----------
        rectDuct(context, id + "ts", 0, 336, 168, 126);

        // ---------- B ground plate, wheel wells, saddles ----------
        sideExtrude(context, id + "gp", [[42, 22.5], [48, 21], [294, 21], [294, 24], [48, 24]], -83, 83);
        sideExtrude(context, id + "flap", [[294.5, 21], [310, 19.5], [310, 21], [294.5, 24]], -83, 83);
        tag(context, id + "flap", "B 地面板後緣襟翼", WHITE);
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
            tag(context, id + ("sad" ~ i), "B V 形托座 " ~ n, PRINT);

            cyl(context, id + ("tyre" ~ i), [x, y - 3, TZ], [x, y + 3, TZ], 16);
            tag(context, id + ("tyre" ~ i), "車模輪胎 " ~ n, BLACK);

            blk(context, id + ("post" ~ i), [x - 1.5, y - 1.5, -35], [x + 1.5, y + 1.5, 13]);
            tag(context, id + ("post" ~ i), "C 托座支柱 " ~ n, STEEL);

            pipe(context, id + ("shr" ~ i), [x, y, 0], [x, y, 9], 5.5, 4.5);
            tag(context, id + ("shr" ~ i), "B 支柱護套 " ~ n, ALU);

            cyl(context, id + ("hole" ~ i), [x, y, -4], [x, y, 12.5], 4.6);
            holes = append(holes, bodies(id + ("hole" ~ i)));
        }
        cut(context, id + "gpc", bodies(id + "gp"), qUnion(openings), false);
        tag(context, id + "gp", "B 地面板（3 mm，前緣 4:1 橢圓）", WHITE);
        cut(context, id + "hcut", qUnion(wells), qUnion(holes), false);
        for (var i = 0; i < 4; i += 1)
        {
            tag(context, id + ("well" ~ i), "B 輪井（封底）" ~ (i + 1), DARK);
        }
        const legs = [[60, -70], [60, 70], [280, -70], [280, 70]];
        for (var i = 0; i < 4; i += 1)
        {
            cyl(context, id + ("gpl" ~ i), [legs[i][0], legs[i][1], 0], [legs[i][0], legs[i][1], 21], 6);
            tag(context, id + ("gpl" ~ i), "B 地面板支腳 " ~ (i + 1), ALU);
        }

        // ---------- 1:43 car (planning shape) ----------
        sideExtrude(context, id + "car", [[126, 27], [126, 37], [129, 41], [152, 44], [170, 57], [218, 58], [229, 52], [231, 44], [231, 27]], -19, 19);
        try silent(opFillet(context, id + "car" + "fil", { "entities" : qCreatedBy(id + "car" + "ex", EntityType.EDGE), "radius" : 1.5 * millimeter }));
        tag(context, id + "car", "1:43 車模（估計外形）", RED);

        // ---------- probes and taps ----------
        cyl(context, id + "pit1", [55, 55, 87], [85, 55, 87], 4);
        cyl(context, id + "pit2", [85, 55, 85], [85, 55, 150], 4);
        cut(context, id + "pitc", bodies(id + "ts"), bodies(id + "pit2"), true);
        const pitot = qUnion([bodies(id + "pit1"), bodies(id + "pit2")]);
        fuse(context, id + "pitf", pitot);
        tagQ(context, pitot, "D 皮托管 ø4", BRASS);
        tag(context, id + "ts", "A3 測試段（3 mm 透明 PC）", PC);

        const taps = [
                [[-420, 209, ZC], [-420, 215, ZC]], [[-420, -209, ZC], [-420, -215, ZC]],
                [[-420, 0, ZC + 157.5], [-420, 0, ZC + 163.5]], [[-420, 0, ZC - 157.5], [-420, 0, ZC - 163.5]],
                [[13, 87, ZC], [13, 93, ZC]], [[13, -87, ZC], [13, -93, ZC]],
                [[13, 0, ZC + 66], [13, 0, ZC + 72]], [[13, 0, ZC - 66], [13, 0, ZC - 72]],
                [[42, -87, 75], [42, -93, 75]], [[126, -87, 75], [126, -93, 75]],
                [[210, -87, 75], [210, -93, 75]], [[294, -87, 75], [294, -93, 75]]
            ];
        var tapQ = [];
        for (var i = 0; i < size(taps); i += 1)
        {
            cyl(context, id + ("tap" ~ i), taps[i][0], taps[i][1], 2.5);
            tapQ = append(tapQ, bodies(id + ("tap" ~ i)));
        }
        tagQ(context, qUnion(tapQ), "D 壁面靜壓孔接頭", BRASS);

        // ---------- C plenum, balance, pedestal ----------
        shellBox(context, id + "pl", [87, -83, -136], [273, 83, -3], [90, -80, -133], [270, 80, -2]);
        blk(context, id + "plh", [150, -30, -137], [210, 30, -132]);
        cut(context, id + "plc", bodies(id + "pl"), bodies(id + "plh"), false);
        tag(context, id + "pl", "C 密封靜壓箱（PC）", PC);
        shellBox(context, id + "skirt", [145, -35, -138], [215, 35, -136.2], [162, -18, -139], [198, 18, -135]);
        tag(context, id + "skirt", "C 橡膠裙", DARK);

        blk(context, id + "frm", [140, -26, -40], [217, 26, -35]);
        blk(context, id + "tab", [217, 13, -50], [222, 23, -35]);
        const frame = qUnion([bodies(id + "frm"), bodies(id + "tab")]);
        fuse(context, id + "frmf", frame);
        tagQ(context, frame, "C 共用框架（含阻力推片）", ALU);

        const bl = [[152, -20], [152, 20], [205, -20], [205, 20]];
        for (var i = 0; i < 4; i += 1)
        {
            blk(context, id + ("blade" ~ i), [bl[i][0] - 0.05, bl[i][1] - 5, -60], [bl[i][0] + 0.05, bl[i][1] + 5, -40]);
            tag(context, id + ("blade" ~ i), "C 厚薄規鋼片 0.1×10×20 " ~ (i + 1), STEEL);
        }
        blk(context, id + "plat", [130, -30, -65], [230, 30, -60]);
        tag(context, id + "plat", "C 阻力平台", ALU);
        blk(context, id + "dcp", [222, -23.5, -60], [228, -13.5, -55]);
        tag(context, id + "dcp", "C 阻力荷重元座", ALU);
        blk(context, id + "dcell", [222, -23.5, -55], [228, 23.5, -43]);
        tag(context, id + "dcell", "C 100 g 阻力荷重元", CELLC);

        blk(context, id + "vcell", [140, -6.35, -80], [220, 6.35, -67.3]);
        tag(context, id + "vcell", "C 1 kg 垂直荷重元", CELLC);
        blk(context, id + "vsp1", [140, -6.35, -67.3], [158, 6.35, -65]);
        tag(context, id + "vsp1", "C 荷重元上墊塊", ALU);
        blk(context, id + "vsp2", [202, -6.35, -83], [220, 6.35, -80]);
        tag(context, id + "vsp2", "C 荷重元下墊塊", ALU);
        blk(context, id + "bbase", [120, -40, -93], [240, 40, -83]);
        tag(context, id + "bbase", "C 天平底板", ALU);
        blk(context, id + "col", [162, -18, DESK + 10], [198, 18, -93]);
        tag(context, id + "col", "C 底座柱（穿過靜壓箱底）", STEEL);
        blk(context, id + "ped", [100, -165, DESK], [260, 165, DESK + 10]);
        tag(context, id + "ped", "C 底座板（放桌面）", STEEL);
        blk(context, id + "brk1", [105, 100, DESK + 10], [255, 160, -60]);
        tag(context, id + "brk1", "C 配重 1", BRICK);
        blk(context, id + "brk2", [105, -160, DESK + 10], [255, -100, -60]);
        tag(context, id + "brk2", "C 配重 2", BRICK);

        cyl(context, id + "vent1", [178, -87, 75], [178, -99, 75], 4);
        cyl(context, id + "vent2", [178, -97, 77], [178, -97, -42], 4);
        cyl(context, id + "vent3", [178, -99, -40], [178, -83, -40], 4);
        const vent = qUnion([bodies(id + "vent1"), bodies(id + "vent2"), bodies(id + "vent3")]);
        fuse(context, id + "ventf", vent);
        tagQ(context, vent, "C 靜壓箱通氣管（接車身中段側壁孔）", SILICONE);

        // ---------- A4 diffuser, safety mesh ----------
        loftDuct(context, id + "dif", [336, 986], [168, 240], [126, 240], T);
        tag(context, id + "dif", "A4 擴散段 168×126→240×240", WOOD);

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
        tagQ(context, qUnion(mesh), "A4 安全網（網目 7 mm）", STEEL);

        // ---------- A5 fan box and 2 x 2 fans ----------
        rectDuct(context, id + "fm", 988, 1047, 240, 240);
        tag(context, id + "fm", "A5 風扇座 240×240", WOOD);
        const fp = [[-60, ZC - 60], [60, ZC - 60], [-60, ZC + 60], [60, ZC + 60]];
        for (var i = 0; i < 4; i += 1)
        {
            fan(context, id + ("fan" ~ i), fp[i][0], fp[i][1], i + 1, BLACK, DARK);
        }

        // ---------- supports and desks ----------
        blk(context, id + "sup1", [-600, -180, DESK], [-570, 180, ZC - 157.5]);
        blk(context, id + "sup2", [-440, -180, DESK], [-410, 180, ZC - 157.5]);
        blk(context, id + "sup3", [992, -126, DESK], [1043, 126, ZC - 123]);
        tagQ(context, qUnion([bodies(id + "sup1"), bodies(id + "sup2"), bodies(id + "sup3")]), "墊塊", WOOD);

        const desks = [[-740, 160], [160, 1060]];
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
            tag(context, did, "課桌 " ~ (i + 1), DESKC);
        }

        // ---------- D electronics and speed sensors (on desk 2) ----------
        blk(context, id + "uno", [300, 180, DESK + 6], [368.6, 233.4, DESK + 7.6]);
        tag(context, id + "uno", "D Arduino Uno", color(0.0, 0.45, 0.65));
        blk(context, id + "psu", [700, 170, DESK], [850, 290, DESK + 86]);
        tag(context, id + "psu", "G 12 V ≥20 A 電源（舊 ATX）", DARK);

        shellBox(context, id + "sabox", [400, -295, DESK], [600, -165, DESK + 150], [402, -293, DESK + 2], [598, -167, DESK + 148]);
        tag(context, id + "sabox", "D2 風速感測器 A：密封保鮮盒", color(0.9, 0.95, 1.0, 0.22));
        pipe(context, id + "dish", [510, -230, DESK + 2], [510, -230, DESK + 52], 106, 100);
        cyl(context, id + "dishf", [510, -230, DESK + 2], [510, -230, DESK + 5], 106);
        const dish = qUnion([bodies(id + "dish"), bodies(id + "dishf")]);
        fuse(context, id + "dishu", dish);
        tagQ(context, dish, "D2 A 油碗 內徑 100", WHITE);
        cyl(context, id + "oil", [510, -230, DESK + 5], [510, -230, DESK + 50], 100);
        cyl(context, id + "bellA", [510, -230, DESK + 15], [510, -230, DESK + 95], 62.4);
        cyl(context, id + "bellB", [510, -230, DESK + 14], [510, -230, DESK + 93.8], 60);
        cut(context, id + "bellc", bodies(id + "bellA"), bodies(id + "bellB"), false);
        cut(context, id + "oilc", bodies(id + "oil"), bodies(id + "bellA"), true);
        tag(context, id + "oil", "D2 A 嬰兒油 深 45", color(1.0, 0.85, 0.35, 0.5));
        tag(context, id + "bellA", "D2 A 鐘罩 內徑 60（PETG）", PRINT);
        cyl(context, id + "thread", [510, -230, DESK + 95], [510, -230, DESK + 120], 1);
        tag(context, id + "thread", "D2 A 吊線", WHITE);
        blk(context, id + "sacell", [466, -236, DESK + 120], [513, -224, DESK + 126]);
        tag(context, id + "sacell", "D2 A 100 g 荷重元", CELLC);
        blk(context, id + "saarm", [405, -238, DESK + 126], [470, -222, DESK + 136]);
        blk(context, id + "sapil", [405, -240, DESK + 2], [425, -220, DESK + 126]);
        const bracket = qUnion([bodies(id + "saarm"), bodies(id + "sapil")]);
        fuse(context, id + "sabr", bracket);
        tagQ(context, bracket, "D2 A 硬支架（黏盒底）", ALU);
        cyl(context, id + "port1", [600, -250, DESK + 90], [608, -250, DESK + 90], 4);
        cyl(context, id + "port2", [600, -210, DESK + 90], [608, -210, DESK + 90], 4);
        tagQ(context, qUnion([bodies(id + "port1"), bodies(id + "port2")]), "D2 A 高／低壓口", BRASS);
        cyl(context, id + "bmp1", [632, -205, DESK], [632, -205, DESK + 50], 35);
        cyl(context, id + "bmp2", [632, -245, DESK], [632, -245, DESK + 50], 35);
        tagQ(context, qUnion([bodies(id + "bmp1"), bodies(id + "bmp2")]), "D2 風速感測器 B：BMP280 底片盒", BLACK);
    }, {});

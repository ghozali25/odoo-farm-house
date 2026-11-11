# -*- coding: utf-8 -*-
"""
3D airspace geometry for farm locations.

Porting note (19.0 -> 18.0): the original implementation ran its 3D
intersection test inside PostgreSQL via PostGIS (``CREATE EXTENSION postgis``
+ ``ST_3DIntersects(ST_GeomFromText(...))``). PostGIS is NOT available on the
Odoo 18 test bed (and is not a dependency of this module), so the test is now
done in pure Python on the stored WKT text:

* the airspace boundary is a ``POLYGON Z`` (a flat or sloped 3D polygon);
* the UAV trajectory is a ``LINESTRING Z`` (or plain 2D ``LINESTRING``);
* intersection = the trajectory's 2D projection crosses the polygon
  footprint (or passes through it) while its Z range overlaps the polygon's
  Z range. A vertical flight straight through a horizontal polygon (e.g. a
  climb from below the ceiling to above it) is detected via the
  point-in-polygon test on the footprint.

The stored field stays a plain ``Char`` holding WKT text, so no database
extension, column type or migration is needed. Geometry is approximate
(planar, lon/lat treated as local coordinates) which matches how the
original PostGIS call was used (SRID 4326 with no geodesic handling).
"""
from odoo import fields, models
import logging
import math

_logger = logging.getLogger(__name__)


def _parse_wkt_points(wkt):
    """Parse the coordinate list out of a ``POLYGON Z (...)`` /
    ``LINESTRING Z (...)`` / ``LINESTRING (...)`` WKT string.

    Returns a list of ``(x, y, z)`` tuples (``z`` is ``None`` when the WKT
    carries no Z coordinate), or an empty list when the text cannot be parsed.
    """
    if not wkt or not isinstance(wkt, str):
        return []
    text = wkt.strip()
    start = text.find('((')
    if start != -1:
        inner = text[start + 2:text.rfind('))')]
    else:
        start = text.find('(')
        if start == -1:
            return []
        inner = text[start + 1:text.rfind(')')]
    points = []
    for part in inner.split(','):
        coords = part.strip().split()
        if len(coords) < 2:
            continue
        try:
            x, y = float(coords[0]), float(coords[1])
            z = float(coords[2]) if len(coords) > 2 else None
        except ValueError:
            _logger.warning("Unparseable WKT coordinate: %r in %r", part, wkt)
            return []
        points.append((x, y, z))
    return points


def _point_in_polygon_2d(x, y, polygon):
    """Ray-casting point-in-polygon test (boundary counts as inside)."""
    inside = False
    n = len(polygon)
    if n < 3:
        return False
    p1x, p1y = polygon[0]
    for i in range(n + 1):
        p2x, p2y = polygon[i % n]
        if min(p1y, p2y) <= y <= max(p1y, p2y) and y != p2y:
            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
            if x <= xinters:
                inside = not inside
        elif y == p1y == p2y and min(p1x, p2x) <= x <= max(p1x, p2x):
            return True  # point lies on a horizontal edge
        p1x, p1y = p2x, p2y
    return inside


def _segments_intersect_2d(p1, p2, p3, p4):
    """Return the ``t`` parameter (0..1 along p1->p2) where the 2D segments
    intersect, or ``None`` when they do not intersect. Collinear overlapping
    segments report ``t = 0``."""
    d1x, d1y = p2[0] - p1[0], p2[1] - p1[1]
    d2x, d2y = p4[0] - p3[0], p4[1] - p3[1]
    denom = d1x * d2y - d1y * d2x
    if abs(denom) < 1e-12:
        return None
    t = ((p3[0] - p1[0]) * d2y - (p3[1] - p1[1]) * d2x) / denom
    u = ((p3[0] - p1[0]) * d1y - (p3[1] - p1[1]) * d1x) / denom
    if 0.0 <= t <= 1.0 and 0.0 <= u <= 1.0:
        return t
    return None


class FarmLocation(models.Model):
    _inherit = 'farm.location'

    geom_3d_polygon = fields.Char(
        string='3D Airspace Polygon WKT',
        help='WKT representation of Polygon Z, e.g., POLYGON Z ((0 0 10, 0 5 10, 5 5 20, 0 0 10)). '
             'Checked in pure Python (no PostGIS required).',
        default=''
    )

    def check_uav_trajectory_intersection(self, uav_trajectory_wkt):
        """
        3D intersection test between a UAV trajectory and this airspace
        boundary, computed in pure Python (see module docstring).

        Takes a UAV Linestring Z trajectory and checks if it intersects this
        airspace boundary. Returns False when either geometry is missing or
        unparsable.
        """
        self.ensure_one()
        if not self.geom_3d_polygon:
            return False

        polygon = _parse_wkt_points(self.geom_3d_polygon)
        trajectory = _parse_wkt_points(uav_trajectory_wkt)
        if len(polygon) < 3 or len(trajectory) < 1:
            return False

        footprint = [(x, y) for x, y, _ in polygon]
        zs = [z for _, _, z in polygon if z is not None]
        # A 2D polygon (no Z) is treated as a ground-level boundary that any
        # altitude may intersect; a Z polygon bounds a Z slab.
        z_min = min(zs) if zs else -math.inf
        z_max = max(zs) if zs else math.inf

        def z_overlaps(z1, z2):
            # A missing Z on a trajectory point means "altitude unknown":
            # fail closed and assume the Z range overlaps the slab.
            if z1 is None or z2 is None:
                return True
            lo = min(z1, z2)
            hi = max(z1, z2)
            return lo <= z_max + 1e-9 and hi >= z_min - 1e-9

        def z_at(t, z1, z2):
            if z1 is None or z2 is None:
                return z_min  # unknown altitude: inside the slab by construction
            return z1 + t * (z2 - z1)

        # Single-point trajectory: inside footprint + Z overlap?
        if len(trajectory) == 1:
            x, y, z = trajectory[0]
            return _point_in_polygon_2d(x, y, footprint) and z_overlaps(z, z)

        for i in range(len(trajectory) - 1):
            x1, y1, z1 = trajectory[i]
            x2, y2, z2 = trajectory[i + 1]
            # Degenerate (vertical) segment: 2D point inside footprint?
            if abs(x2 - x1) < 1e-12 and abs(y2 - y1) < 1e-12:
                if _point_in_polygon_2d(x1, y1, footprint) and z_overlaps(z1, z2):
                    return True
                continue
            # Either endpoint inside the footprint with Z overlap?
            if z_overlaps(z1, z2):
                if _point_in_polygon_2d(x1, y1, footprint) or _point_in_polygon_2d(x2, y2, footprint):
                    return True
                # Or the 2D segment crosses a footprint edge at a Z inside the slab?
                for j in range(len(footprint)):
                    edge_p1 = footprint[j]
                    edge_p2 = footprint[(j + 1) % len(footprint)]
                    t = _segments_intersect_2d((x1, y1), (x2, y2), edge_p1, edge_p2)
                    if t is not None and z_min - 1e-9 <= z_at(t, z1, z2) <= z_max + 1e-9:
                        return True
        return False

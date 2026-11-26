"""Pure layout validation for synthetic office preview; no placement writes."""
def _rows(value: object) -> bool:
    return type(value) in (list, tuple)


def _id(value: object) -> bool:
    return type(value) is str and bool(value.strip())


def validate_layout(layout: dict) -> None:
    if type(layout) is not dict:
        raise ValueError("LAYOUT_SCOPE_INVALID")
    w, h = layout.get("width"), layout.get("height")
    floors = layout.get("floors")
    if (type(w) is not int or type(h) is not int or (w, h) != (6, 6)
            or layout.get("revision") != "layout-d3-demo" or not _rows(floors)):
        raise ValueError("LAYOUT_SCOPE_INVALID")
    ids = set()
    for floor in floors:
        if type(floor) is not dict or not _id(floor.get("id")):
            raise ValueError("LAYOUT_SCOPE_INVALID")
        if floor["id"] in ids:
            raise ValueError("FLOOR_DUPLICATE")
        ids.add(floor["id"])
        rooms, occupied = {}, set()
        room_rows = floor.get("rooms")
        if not _rows(room_rows):
            raise ValueError("ROOM_INVALID")
        for room in room_rows:
            if type(room) is not dict or not _id(room.get("id")):
                raise ValueError("ROOM_INVALID")
            x, y, rw, rh = (room.get(k) for k in ("x", "y", "w", "h"))
            if (room["id"] in rooms or any(type(v) is not int for v in (x, y, rw, rh))
                    or rw < 1 or rh < 1):
                raise ValueError("ROOM_INVALID")
            # Bound both axes before constructing cells; at most 36 per room.
            if not (0 <= x < w and 0 <= y < h and rw <= w - x and rh <= h - y):
                raise ValueError("ROOM_OVERLAP_OR_BOUNDS")
            cells = {(cx, cy) for cx in range(x, x + rw) for cy in range(y, y + rh)}
            if cells & occupied:
                raise ValueError("ROOM_OVERLAP_OR_BOUNDS")
            rooms[room["id"]] = cells
            occupied |= cells
        stations, positions = set(), set()
        station_rows = floor.get("stations")
        if not _rows(station_rows):
            raise ValueError("STATION_INVALID")
        for station in station_rows:
            if (type(station) is not dict or not _id(station.get("id"))
                    or not _id(station.get("room")) or "agent_instance_id" not in station
                    or station["agent_instance_id"] is not None):
                raise ValueError("STATION_INVALID")
            pos = (station.get("x"), station.get("y"))
            if (any(type(v) is not int for v in pos) or station["id"] in stations
                    or pos in positions or pos not in rooms.get(station["room"], set())):
                raise ValueError("STATION_INVALID")
            stations.add(station["id"])
            positions.add(pos)
        walkable = floor.get("walkable")
        if not _rows(walkable) or len(walkable) > w * h:
            raise ValueError("WALKABLE_INVALID")
        seen = set()
        for point in walkable:
            if not _rows(point) or len(point) != 2 or any(type(v) is not int for v in point):
                raise ValueError("WALKABLE_INVALID")
            pos = tuple(point)
            if not (0 <= pos[0] < w and 0 <= pos[1] < h) or pos in positions or pos in seen:
                raise ValueError("WALKABLE_INVALID")
            seen.add(pos)

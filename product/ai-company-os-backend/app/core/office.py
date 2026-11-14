"""Pure layout validation for synthetic office preview; no placement writes."""
def validate_layout(layout: dict) -> None:
    w,h = layout["width"],layout["height"]
    if (w,h)!=(6,6) or layout["revision"]!="layout-d3-demo":
        raise ValueError("LAYOUT_SCOPE_INVALID")
    ids=set()
    for floor in layout["floors"]:
        if floor["id"] in ids:
            raise ValueError("FLOOR_DUPLICATE")
        ids.add(floor["id"])
        rooms={}
        occupied=set()
        for room in floor["rooms"]:
            if room["id"] in rooms or room["w"]<1 or room["h"]<1:
                raise ValueError("ROOM_INVALID")
            cells={(x,y) for x in range(room["x"],room["x"]+room["w"]) for y in range(room["y"],room["y"]+room["h"])}
            if any(not (0<=x<w and 0<=y<h) for x,y in cells) or cells & occupied:
                raise ValueError("ROOM_OVERLAP_OR_BOUNDS")
            rooms[room["id"]]=cells
            occupied |= cells
        stations=set(); positions=set()
        for station in floor["stations"]:
            pos=(station["x"],station["y"])
            if station["id"] in stations or pos in positions or pos not in rooms.get(station["room"],set()) or station["agent_instance_id"] is not None:
                raise ValueError("STATION_INVALID")
            stations.add(station["id"]); positions.add(pos)
        walkable=[tuple(p) for p in floor["walkable"]]
        if len(set(walkable))!=len(walkable) or any(len(p)!=2 or not (0<=p[0]<w and 0<=p[1]<h) or p in positions for p in walkable):
            raise ValueError("WALKABLE_INVALID")

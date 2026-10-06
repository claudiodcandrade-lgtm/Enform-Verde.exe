"""Spatially partition the offline IBGE feature collection into on-demand map quadrants."""
from __future__ import annotations
import gzip,json,math
from collections import OrderedDict
from pathlib import Path

def write_quadrant_tiles(layers,output_dir,bounds=(-75.0,-35.0,-33.0,6.0),tile_degrees=5.0):
    """Partition and compress populated tiles; retain full geometry for viewport clipping."""
    root=Path(output_dir);root.mkdir(parents=True,exist_ok=True)
    west,south,east,north=map(float,bounds);size=float(tile_degrees)
    if size<=0 or west>=east or south>=north:raise ValueError("Invalid bounds or tile size")
    for old in root.glob("q_*.json.gz"):old.unlink()
    nx=int(math.ceil((east-west)/size));ny=int(math.ceil((north-south)/size))
    feature_counts={k:len(v) for k,v in layers.items()}
    contents={}
    for iy in range(ny):
        y0=south+iy*size;y1=min(north,y0+size)
        for ix in range(nx):
            x0=west+ix*size;x1=min(east,x0+size)
            contents[f"{ix}_{iy}"]={"bbox":[x0,y0,x1,y1],"layers":{k:[] for k in layers}}
    # Partition on feature bounds only. Full geometry is retained in each tile
    # it intersects; the map viewport clips drawing, avoiding expensive GEOS
    # intersections over the entire national feature set during packaging.
    for layer,features in layers.items():
        for feature in features:
            fb=feature.get("bbox")
            if not fb or not feature.get("geometry"):continue
            if fb[2]<west or fb[0]>east or fb[3]<south or fb[1]>north:continue
            ix0=max(0,min(nx-1,int(math.floor((max(west,fb[0])-west)/size))))
            iy0=max(0,min(ny-1,int(math.floor((max(south,fb[1])-south)/size))))
            ix1=max(0,min(nx-1,int(math.floor((min(east,fb[2])-west)/size))))
            iy1=max(0,min(ny-1,int(math.floor((min(north,fb[3])-south)/size))))
            for iy in range(iy0,iy1+1):
                y0=south+iy*size;y1=min(north,y0+size)
                for ix in range(ix0,ix1+1):
                    x0=west+ix*size;x1=min(east,x0+size)
                    if fb[2]<x0 or fb[0]>x1 or fb[3]<y0 or fb[1]>y1:continue
                    contents[f"{ix}_{iy}"]["layers"][layer].append(feature)
    tiles={}
    for key,tile in contents.items():
        counts={k:len(v) for k,v in tile["layers"].items()}
        if not any(counts.values()):continue
        filename=f"q_{key}.json.gz"
        with gzip.open(root/filename,"wt",encoding="utf-8",compresslevel=6) as fh:
            json.dump(tile["layers"],fh,ensure_ascii=False,separators=(",",":"))
        tiles[key]={"file":filename,"bbox":tile["bbox"],"counts":counts}
    manifest={"format_version":1,"bounds":[west,south,east,north],"tile_degrees":size,
              "feature_counts":feature_counts,"tile_count":len(tiles),"tiles":tiles}
    (root/"index.json").write_text(json.dumps(manifest,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    return {"tile_count":len(tiles),"tile_degrees":size,"feature_counts":feature_counts,
            "compressed_bytes":sum(p.stat().st_size for p in root.glob("q_*.json.gz"))}

def load_quadrants_for_bbox(root,bounds,manifest,cache=None,max_cached_tiles=8):
    """Load only intersecting compressed quadrants, retaining a bounded LRU cache."""
    root=Path(root);west,south,east,north=map(float,bounds)
    cache=cache if cache is not None else OrderedDict()
    if not isinstance(cache,OrderedDict):raise TypeError("cache must be an OrderedDict")
    selected=[(key,meta) for key,meta in manifest.get("tiles",{}).items()
              if not (meta["bbox"][2]<west or meta["bbox"][0]>east or meta["bbox"][3]<south or meta["bbox"][1]>north)]
    merged={}
    for key,meta in selected:
        if key not in cache:
            with gzip.open(root/meta["file"],"rt",encoding="utf-8") as fh:cache[key]=json.load(fh)
        else:cache.move_to_end(key)
        for layer,features in cache[key].items():
            merged.setdefault(layer,[]).extend(f for f in features if _intersects(f.get("bbox"),[west,south,east,north]))
        while len(cache)>max_cached_tiles:cache.popitem(last=False)
    return merged

def _intersects(a,b):
    return not a or not (a[2]<b[0] or a[0]>b[2] or a[3]<b[1] or a[1]>b[3])

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Build compressed on-demand quadrants from an offline IBGE map gzip.")
    parser.add_argument("map_gzip", help="Path to offline_ibge_map.json.gz")
    parser.add_argument("output_dir", help="Directory for quadrant tiles and index.json")
    args = parser.parse_args()
    with gzip.open(args.map_gzip, "rt", encoding="utf-8") as fh:
        source_layers = json.load(fh)
    if not isinstance(source_layers, dict):
        raise SystemExit("Offline map bundle must contain a layer object.")
    result = write_quadrant_tiles(source_layers, Path(args.output_dir), (-75.0, -35.0, -33.0, 6.0), 5.0)
    print("OFFLINE_IBGE_QUADRANTS_CACHE_OK", result)

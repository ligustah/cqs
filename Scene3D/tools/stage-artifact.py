#!/usr/bin/env python3
"""Mirror the built artifact package (dist/, after `node tools/build-artifact.mjs`) into a stage directory and print
the `files` map for an Artifact publish that updates an existing artifact incrementally.

    python3 tools/stage-artifact.py <stage-dir> [--out plan.json]

dist/files.json maps each published path to its source (relative to Scene3D/ or dist/, or {from, contentType}).
The stage dir mirrors the published layout: <stage>/orbital-fleet.html plus every published path. The script copies
changed and new files into it, deletes files that are no longer published, and writes a files map in which a removed
path maps to null. Publish with root = <stage>, file_path = <stage>/orbital-fleet.html, and files = that map.
An empty stage dir gives a full publish: everything is "added". Mind the limits of 255 files and 64 MB per publish;
split the map over several publishes to the same URL when it is bigger.
"""
import filecmp
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCENE = os.path.dirname(HERE)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    stage = os.path.abspath(sys.argv[1])
    out = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else None
    os.chdir(SCENE)
    m = json.load(open('dist/files.json'))
    changed, added, missing = [], [], []
    for k, v in m.items():
        v = v['from'] if isinstance(v, dict) else v
        src = next((p for p in (v, os.path.join('dist', v)) if os.path.isfile(p)), None)
        if not src:
            missing.append(k)
            continue
        d = os.path.join(stage, k)
        if not os.path.exists(d):
            added.append(k)
        elif not filecmp.cmp(src, d, shallow=False):
            changed.append(k)
        else:
            continue
        os.makedirs(os.path.dirname(d), exist_ok=True)
        shutil.copyfile(src, d)
    os.makedirs(stage, exist_ok=True)
    page = os.path.join(stage, 'orbital-fleet.html')
    page_changed = not os.path.exists(page) or not filecmp.cmp('dist/orbital-fleet.html', page, shallow=False)
    shutil.copyfile('dist/orbital-fleet.html', page)
    staged = set()
    for r, _, fs in os.walk(stage):
        for f in fs:
            staged.add(os.path.relpath(os.path.join(r, f), stage))
    removed = sorted(staged - set(m) - {'orbital-fleet.html'})
    for k in removed:
        os.remove(os.path.join(stage, k))
    files = {k: ({'from': k, 'contentType': 'text/plain'} if k.endswith('.txt') else k) for k in changed + added}
    for k in removed:
        files[k] = None
    summary = dict(published=len(m), changed=len(changed), added=len(added), removed=len(removed),
                   page_changed=page_changed, missing=missing)
    print(json.dumps(summary), file=sys.stderr)
    text = json.dumps(files)
    if out:
        open(out, 'w').write(text)
    else:
        print(text)


if __name__ == '__main__':
    main()

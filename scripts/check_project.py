#!/usr/bin/env python3
"""Offline structural tests. NOT a substitute for `esphome config/compile`.

Requires PyYAML and Jinja2, already dependencies of the ESPHome build image.
The small resolver models only the package/include/substitution features used
by this project. It neither contacts Home Assistant nor downloads anything.
"""
from __future__ import annotations
from copy import deepcopy
from pathlib import Path
import re
from typing import Any
import yaml
from jinja2 import Environment, StrictUndefined

ROOT=Path(__file__).resolve().parents[1]
class Tagged:
    def __init__(self, tag: str, value: Any): self.tag,self.value=tag,value
    def __deepcopy__(self,memo): return Tagged(self.tag,deepcopy(self.value,memo))
class Loader(yaml.SafeLoader): pass

def construct_mapping(loader,node,deep=False):
    result={}
    for kn,vn in node.value:
        key=loader.construct_object(kn,deep=deep)
        if key in result: raise ValueError(f'Duplicate YAML key: {key}')
        result[key]=loader.construct_object(vn,deep=deep)
    return result
Loader.add_constructor('tag:yaml.org,2002:map',construct_mapping)
for tag in ('!lambda','!secret','!include','!extend'):
    def tagged(loader,node,tag=tag):
        value=(loader.construct_mapping(node,deep=True) if isinstance(node,yaml.MappingNode)
               else loader.construct_scalar(node))
        return Tagged(tag,value)
    Loader.add_constructor(tag,tagged)

def load(path): return yaml.load(Path(path).read_text(encoding='utf-8'),Loader=Loader)

def include_parts(item,here):
    assert isinstance(item,Tagged) and item.tag=='!include'
    spec=item.value
    if isinstance(spec,str): spec={'file':spec}
    target=(here/str(spec['file'])).resolve()
    if not target.is_file(): raise AssertionError(f'Missing include: {target}')
    return target,spec.get('vars',{})

EXPR=re.compile(r'\$\{([^{}]+)\}')
JINJA=Environment(undefined=StrictUndefined)

def merge(a,b):
    if isinstance(a,dict) and isinstance(b,dict):
        out=deepcopy(a)
        for k,v in b.items(): out[k]=merge(out[k],v) if k in out else deepcopy(v)
        return out
    if isinstance(a,list) and isinstance(b,list):
        out=deepcopy(a)
        for item in b:
            if isinstance(item,dict) and 'id' in item:
                for i,old in enumerate(out):
                    if isinstance(old,dict) and old.get('id')==item['id']:
                        out[i]=merge(old,item); break
                else: out.append(deepcopy(item))
            else: out.append(deepcopy(item))
        return out
    return deepcopy(b)

def scalar_defaults(path):
    raw=load(path); env={}
    for p in raw.get('packages',{}).values():
        if isinstance(p,Tagged) and p.tag=='!include':
            dest,_=include_parts(p,Path(path).parent)
            env.update(scalar_defaults(dest))
    env.update({k:v for k,v in raw.get('substitutions',{}).items() if not isinstance(v,Tagged)})
    return env

def render(value,env,here):
    if isinstance(value,Tagged):
        if value.tag=='!include':
            dest,params=include_parts(value,here)
            args=render(params,env,here)
            return render(load(dest),{**env,**args},dest.parent)
        # This project only extends the existing main_display dictionary.
        if value.tag=='!extend': return render(value.value,env,here)
        if value.tag=='!lambda': return render(value.value,env,here)
        if value.tag=='!secret': return f'!secret {value.value}'
    if isinstance(value,dict): return {k:render(v,env,here) for k,v in value.items()}
    if isinstance(value,list): return [render(v,env,here) for v in value]
    if not isinstance(value,str): return value
    def evaluate(expr): return JINJA.compile_expression(expr.strip(),undefined_to_none=False)(**env)
    full=EXPR.fullmatch(value)
    if full:
        result=evaluate(full.group(1))
        return deepcopy(result)
    def repl(m):
        result=evaluate(m.group(1))
        if isinstance(result,bool): return 'true' if result else 'false'
        return str(result)
    return EXPR.sub(repl,value)

def expand_file(path,overrides=None):
    path=Path(path).resolve()
    env=scalar_defaults(path)
    env.update(overrides or {})
    # Resolve ordinary substitution references before evaluating package templates.
    for _ in range(8):
        changed=False
        for k,v in list(env.items()):
            if isinstance(v,str) and '${' in v:
                result=render(v,env,path.parent)
                if result!=v: changed=True; env[k]=result
        if not changed: break
    def expand(path,env):
        raw=load(path); env=dict(env)
        for k,v in raw.get('substitutions',{}).items():
            if isinstance(v,Tagged): env[k]=render(v,env,path.parent)
        assembled={}
        for package in raw.get('packages',{}).values():
            if isinstance(package,Tagged):
                dest,params=include_parts(package,path.parent)
                incoming=expand(dest,{**env,**render(params,env,path.parent)})
            else:
                resolved=render(package,env,path.parent)
                # Conditional package expressions may evaluate to an !include
                # template. Model ESPHome by expanding that returned include.
                if isinstance(resolved,Tagged) and resolved.tag=='!include':
                    dest,params=include_parts(resolved,path.parent)
                    incoming=expand(dest,{**env,**render(params,env,path.parent)})
                else:
                    incoming=resolved
            if not isinstance(incoming,dict): raise AssertionError(f'Package is not a mapping in {path}')
            assembled=merge(assembled,incoming)
        local={k:v for k,v in raw.items() if k not in ('packages','substitutions')}
        return merge(assembled,render(local,env,path.parent))
    return expand(path,env),env

def definition_ids(config):
    ids=[]
    for key in ('globals','script','display','font','color','output','switch','sensor',
                'text_sensor','binary_sensor','button','time','image','graph'):
        for item in config.get(key,[]):
            if isinstance(item,dict) and 'id' in item: ids.append(item['id'])
            if key=='display':
                ids.extend(p['id'] for p in item.get('pages',[]))
    for key in ('http_request',):
        if 'id' in config.get(key,{}): ids.append(config[key]['id'])
    return ids

def all_strings(obj):
    if isinstance(obj,str): yield obj
    elif isinstance(obj,dict):
        for v in obj.values(): yield from all_strings(v)
    elif isinstance(obj,list):
        for v in obj: yield from all_strings(v)

def test_configs():
    # Real ESPHome resolves package definitions in reverse declaration order
    # and requires explicit !extend for the contributed display fragments.
    # These assertions catch the two integration errors found by initial CI.
    for profile in ('esp32-c3', 'esp32-s3-quad-psram'):
        packages = load(ROOT/'profiles'/f'{profile}.yaml')['packages']
        assert list(packages)[-1] == 'defaults', 'Defaults must resolve before metrics'
    for fragment in ('metric-page', 'clock-page', 'camera-alerts'):
        display_id = load(ROOT/'packages'/f'{fragment}.yaml')['display'][0]['id']
        assert isinstance(display_id, Tagged) and display_id.tag == '!extend'
        assert display_id.value == 'main_display'
    print('PASS package order and explicit display extensions')
    profiles=('esp32-c3','esp32-c3-camera','esp32-c3-multi-camera',
              'esp32-s3-quad-psram','esp32-s3-quad-psram-camera',
              'esp32-c3-one-metric')
    for name in profiles:
        config,env=expand_file(ROOT/'tests'/f'{name}.yaml')
        ids=definition_ids(config)
        assert len(ids)==len(set(ids)),f'Duplicate component IDs: {name}'
        strings=list(all_strings(config))
        assert not any('${' in s for s in strings),f'Unresolved substitution in {name}'
        references=set(re.findall(r'\bid\(([A-Za-z_][A-Za-z0-9_]*)\)','\n'.join(strings)))
        assert references<=set(ids),f'Missing IDs {references-set(ids)} in {name}'
        assert len(config['display'])==1
        assert len(config['graph'])==6
        for graph in config['graph']:
            assert 'continuous' not in graph and 'sensor' not in graph
            assert graph['width']==174 and graph['height']==18
            assert graph['traces'][0]['continuous'] is True
        camera=('camera' in name)
        assert ('image' in config)==camera
        assert ('http_request' in config)==camera
        assert ('camera_alert' in ids)==camera
        assert ('psram' in config)==('s3' in name)
        assert [f['size'] for f in config['font'][:5]]==[44,84,36,92,92]
        imported=[s for s in config['sensor'] if s['platform']=='homeassistant']
        assert len(imported)==(1 if name.endswith('one-metric') else 6)
        print(f'PASS {name}: includes/substitutions/IDs/graphs/features')

    # Reusable-camera regression: six instances exceed the former four-source design.
    # Driveway = person OR vehicle; parking = vehicle only; garage = manual only.
    multi,_=expand_file(ROOT/'tests/esp32-c3-multi-camera.yaml')
    multi_ids=set(definition_ids(multi))
    for source in ('driveway','parking','backyard','garage','side','street'):
        assert f'camera_picture_path_{source}' in multi_ids
        assert f'show_camera_snapshot_{source}' in multi_ids
        assert f'camera_source_request_{source}' in multi_ids
        assert f'camera_last_auto_{source}' in multi_ids
    assert 'camera_detector_driveway_1' in multi_ids
    assert 'camera_detector_driveway_2' in multi_ids
    assert 'camera_detector_parking_2' in multi_ids
    assert 'camera_detector_parking_1' not in multi_ids
    assert 'camera_detector_backyard_1' in multi_ids
    assert 'camera_detector_backyard_2' not in multi_ids
    assert 'camera_detector_garage_1' not in multi_ids
    assert 'camera_detector_garage_2' not in multi_ids
    assert len([x for x in multi_ids if x.startswith('camera_picture_path_')]) == 6
    print('PASS six reusable camera instances and independent detector routing')

    # Exercise all nonempty enabled-slot combinations without changing firmware.
    for mask in range(1,64):
        override={f'metric_{i+1}_enabled':'true' if mask & (1<<i) else 'false' for i in range(6)}
        config,_=expand_file(ROOT/'tests/esp32-c3.yaml',override)
        assert len([s for s in config['sensor'] if s['platform']=='homeassistant'])==mask.bit_count()
    print('PASS all 63 nonempty metric/battery combinations')
    # The layout cannot support an empty playlist; static_assert enforces that in C++.
    no_metrics={f'metric_{i}_enabled':'false' for i in range(1,7)}
    cfg,_=expand_file(ROOT/'tests/esp32-c3.yaml',no_metrics)
    rotation=next(x for x in cfg['script'] if x['id']=='display_rotation')
    code=rotation['then'][0]['while']['then'][0]['lambda']
    assert 'constexpr bool any_metric_enabled = false || false || false || false || false || false;' in code
    print('PASS empty playlist reaches a compile-time rejection')

if __name__=='__main__':
    test_configs()
    print('These are offline structural checks, not ESPHome validation or a firmware compile.')

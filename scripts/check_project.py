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
FULL_EXPR=re.compile(r'^\$\{(.*)\}$', re.S)
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
    for profile in ('esp32-c3', 'esp32-c6', 'esp32-s3-quad-psram'):
        packages = load(ROOT/'profiles'/f'{profile}.yaml')['packages']
        assert list(packages)[-1] == 'defaults', 'Shared defaults must resolve first'
    for fragment in ('clock-page', 'camera-alerts', 'page-numeric', 'page-battery', 'page-camera'):
        display_id = load(ROOT/'packages'/f'{fragment}.yaml')['display'][0]['id']
        assert isinstance(display_id, Tagged) and display_id.tag == '!extend'
        assert display_id.value == 'main_display'
    print('PASS package order and explicit display extensions')

    # Renderer-performance invariants: no runtime trig on normal metric/clock
    # pages, no forced once-per-minute redraw, and hardware-specific outline cost.
    metric_raw=(ROOT/'packages'/'page-numeric.yaml').read_text(encoding='utf-8')
    battery_raw=(ROOT/'packages'/'page-battery.yaml').read_text(encoding='utf-8')
    clock_raw=(ROOT/'packages'/'clock-page.yaml').read_text(encoding='utf-8')
    core_raw=load(ROOT/'packages'/'core.yaml')
    assert 'cosf(' not in metric_raw and 'sinf(' not in metric_raw
    assert 'cosf(' not in battery_raw and 'sinf(' not in battery_raw
    assert 'cosf(' not in clock_raw and 'sinf(' not in clock_raw
    assert r'\\${' not in clock_raw, 'Escaped ESPHome substitution found in clock renderer'
    assert '"${clock_face_style}"' in clock_raw
    for page_raw in (metric_raw, battery_raw):
        assert 'MAX_VISIBLE_DOTS = 9' in page_raw
        assert 'more_before' in page_raw and 'more_after' in page_raw
        assert 'it.line(' in page_raw
    time_cfg=core_raw['time'][0]
    assert time_cfg['platform'] == 'homeassistant'
    assert time_cfg['id'] == 'ha_time'
    assert 'on_time' not in time_cfg
    assert 'sntp_time' not in (ROOT/'packages'/'core.yaml').read_text(encoding='utf-8')
    assert 'sntp_time' not in metric_raw
    assert 'sntp_time' not in battery_raw
    assert 'sntp_time' not in clock_raw
    c3_hw=load(ROOT/'hardware'/'esp32-c3-gc9a01.yaml')['substitutions']
    c6_raw=load(ROOT/'hardware'/'esp32-c6-4mb-gc9a01.yaml')
    c6_hw=c6_raw['substitutions']
    s3_hw=load(ROOT/'hardware'/'esp32-s3-quad-psram-gc9a01.yaml')['substitutions']
    assert str(c3_hw['battery_outline_quality']) == '1'
    assert str(c6_hw['battery_outline_quality']) == '1'
    assert str(s3_hw['battery_outline_quality']) == '2'
    assert c3_hw['display_buffer_size'] == '50%'
    assert c6_hw['display_buffer_size'] == '50%'
    assert s3_hw['display_buffer_size'] == '100%'
    assert c6_raw['esp32']['variant'] == 'esp32c6'
    assert c6_raw['esp32']['flash_size'] == '4MB'
    assert 'psram' not in c6_raw
    print('PASS renderer performance invariants and hardware quality split')

    # Clock-style regression coverage. The package must default to the original
    # face, and every documented private override must resolve into the rendered
    # lambda rather than remaining escaped or being replaced by the package default.
    supported_clock_styles = (
        'original',
        'classic_analog',
        'modern_dashboard',
        'fitness_ring',
        'clean_arc',
    )
    defaults = load(ROOT/'packages'/'defaults.yaml')['substitutions']
    assert defaults['clock_face_style'] == 'original'
    assert defaults['backlight_restore_mode'] == 'ALWAYS_ON'

    clock_source = (ROOT/'packages'/'clock-page.yaml').read_text(encoding='utf-8')
    for style in supported_clock_styles:
        if style != 'original':
            assert f'if (clock_style == "{style}")' in clock_source

        cfg, env = expand_file(
            ROOT/'tests'/'esp32-c3-one-metric.yaml',
            {'clock_face_style': style},
        )
        assert env['clock_face_style'] == style
        rendered_strings = list(all_strings(cfg))
        assert any(
            f'clock_style = "{style}"' in value
            for value in rendered_strings
        ), f'Clock style override did not render: {style}'
        assert not any('\\${clock_face_style}' in value for value in rendered_strings)
        assert not any('${clock_face_style}' in value for value in rendered_strings)

    default_cfg, default_env = expand_file(ROOT/'tests'/'esp32-c3-one-metric.yaml')
    assert default_env['clock_face_style'] == 'original'
    assert any(
        'clock_style = "original"' in value
        for value in all_strings(default_cfg)
    )
    print('PASS all selectable clock styles, private overrides, and original default')
    backlight_cfg, backlight_env = expand_file(
        ROOT/'tests'/'esp32-c3-one-metric.yaml',
        {'backlight_restore_mode': 'ALWAYS_OFF'},
    )
    assert backlight_env['backlight_restore_mode'] == 'ALWAYS_OFF'
    backlight_switch = next(
        item for item in backlight_cfg['switch']
        if item.get('id') == 'lcd_backlight_switch'
    )
    assert backlight_switch['restore_mode'] == 'ALWAYS_OFF'
    print('PASS configurable backlight restore mode with ALWAYS_ON default')

    profiles=('esp32-c3','esp32-c3-camera','esp32-c3-multi-camera',
              'esp32-c6','esp32-c6-camera',
              'esp32-s3-quad-psram','esp32-s3-quad-psram-camera',
              'esp32-c3-one-metric')
    for name in profiles:
        config,env=expand_file(ROOT/'tests'/f'{name}.yaml')
        if name == 'esp32-c3':
            assert env['clock_face_style'] == 'modern_dashboard'
            assert any('clock_style = "modern_dashboard"' in text for text in all_strings(config))
        ids=definition_ids(config)
        assert len(ids)==len(set(ids)),f'Duplicate component IDs: {name}'
        strings=list(all_strings(config))
        assert not any('${' in s for s in strings),f'Unresolved substitution in {name}'
        references=set(re.findall(r'\bid\(([A-Za-z_][A-Za-z0-9_]*)\)','\n'.join(strings)))
        assert references<=set(ids),f'Missing IDs {references-set(ids)} in {name}'
        assert len(config['display'])==1
        imported=[s for s in config['sensor'] if s['platform']=='homeassistant']
        assert len(imported)==1
        assert len(config.get('graph',[]))==0
        camera=('camera' in name)
        assert ('image' in config)==camera
        assert ('http_request' in config)==camera
        assert ('camera_alert' in ids)==camera
        if camera:
            image_ids=[x.get('id') for x in config.get('image',[]) if isinstance(x,dict)]
            assert image_ids.count('camera_snapshot')==1
            assert image_ids.count('camera_snapshot_next')==1
            assert 'camera_refresh_loop' in ids
        assert ('psram' in config)==('s3' in name)
        assert [f['size'] for f in config['font'][:5]]==[44,84,36,92,92]
        assert 'rotation_pages' in ids and 'rotation_orders' in ids
        print(f'PASS {name}: includes/substitutions/IDs/features')

    # Reusable-camera regression: six instances exceed the former four-source design.
    # Driveway = person OR vehicle; parking = vehicle only; garage = manual only.
    multi,_=expand_file(ROOT/'tests/esp32-c3-multi-camera.yaml')
    multi_ids=set(definition_ids(multi))
    for source in ('driveway','parking','backyard','garage','side','street'):
        assert f'camera_picture_path_{source}' in multi_ids
        assert f'show_camera_snapshot_{source}' in multi_ids
        assert f'camera_source_request_{source}' in multi_ids
        assert f'camera_last_auto_{source}' in multi_ids
        assert f'camera_detection_mask_{source}' in multi_ids
        assert f'camera_alerts_enabled_{source}' in multi_ids
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

    camera_alert_raw=(ROOT/'packages'/'camera-alerts.yaml').read_text(encoding='utf-8')
    assert "camera_refresh_interval_ms: '0'" in camera_alert_raw
    assert 'camera_snapshot_next' in camera_alert_raw
    assert 'Camera refresh timed out; keeping last good frame' in camera_alert_raw
    assert 'id(display_suspend_callbacks).push_back' in camera_alert_raw
    assert 'Suspended: display off' in camera_alert_raw
    assert '!id(lcd_backlight_switch).state' in camera_alert_raw
    assert 'camera_min_hold_time: 7s' in camera_alert_raw
    assert 'camera_clear_delay: 2s' in camera_alert_raw
    assert 'id: camera_clear_timer' in camera_alert_raw
    assert 'id: camera_detection_state' in camera_alert_raw
    assert 'camera_detection_clear_ready' in camera_alert_raw
    assert 'id(camera_active_detection_mask)' in camera_alert_raw
    print('PASS optional ping-pong camera refresh defaults off and preserves last good frame')
    print('PASS automatic camera alerts follow detector state with minimum hold and clear delay')
    print('PASS camera alerts stop and release resources when the display switch is off')

    assert 'last_camera_alert' in multi_ids
    last_alert=next(x for x in multi['text_sensor'] if x.get('id')=='last_camera_alert')
    assert last_alert['name']=='Last Camera Alert'
    assert next(x for x in multi['text_sensor'] if x.get('id')=='camera_alert_status')['internal'] is True
    print('PASS Last Camera Alert diagnostic and internal engine status')

    template_cfg,_=expand_file(ROOT/'tests/esp32-s3-template-pages.yaml')
    template_ids=set(definition_ids(template_cfg))
    imported=[s for s in template_cfg['sensor'] if s['platform']=='homeassistant']
    assert len(imported)==11
    assert len(template_cfg.get('graph',[]))==0
    for i in range(1,11):
        assert f'rotation_page_numeric_{i}' in template_ids
        assert f'rotation_sensor_numeric_{i}' in template_ids
    assert 'rotation_page_battery_main' in template_ids
    assert 'rotation_battery_sensor_battery_main' in template_ids
    assert 'rotation_page_camera_front' in template_ids
    assert 'rotation_camera_picture_camera_front' in template_ids
    assert 'rotation_camera_image_camera_front' in template_ids
    camera_page_raw=(ROOT/'packages'/'page-camera.yaml').read_text(encoding='utf-8')
    assert 'MAX_VISIBLE_DOTS' not in camera_page_raw
    assert camera_page_raw.count('id(lcd_backlight_switch).state') >= 3
    print('PASS 10 numeric + battery + camera rotation template stress fixture')
    print('PASS sliding nine-dot indicator with overflow chevrons; camera page stays clean')

    home_cfg,_=expand_file(ROOT/'tests/esp32-s3-home-migration.yaml')
    home_ids=set(definition_ids(home_cfg))
    home_imported=[s for s in home_cfg['sensor'] if s['platform']=='homeassistant']
    assert len(home_imported)==5
    for page in ('gazebo','shed','kitchen','master','bunk'):
        assert f'rotation_page_{page}' in home_ids
    for source in ('front','garage','driveway','camper'):
        assert f'camera_alerts_enabled_{source}' in home_ids
    print('PASS Home S3 shape uses five explicit pages and four per-camera alert controls')

    # The fixed slot implementation is intentionally gone.
    for retired in ('metrics.yaml','metric-page.yaml','metric-source.yaml',
                    'metric-unused.yaml','legacy-pages.yaml','page-unused.yaml'):
        assert not (ROOT/'packages'/retired).exists(), f'Retired compatibility file still present: {retired}'
    defaults=load(ROOT/'packages'/'defaults.yaml')['substitutions']
    assert not any(re.match(r'metric_\\d+_', key) for key in defaults)
    print('PASS no fixed-slot compatibility layer remains')

    core_text=(ROOT/'packages'/'core.yaml').read_text(encoding='utf-8')
    assert 'rotation_pages' in core_text
    assert 'rotation_orders' in core_text
    assert 'rotation_enter_callbacks' in core_text
    assert 'rotation_exit_callbacks' in core_text
    assert 'if (count == 0)' in core_text
    assert 'id: suspend_display' in core_text
    assert 'id: resume_display' in core_text
    assert 'display_suspend_callbacks' in core_text
    assert 'lambda: return id(lcd_backlight_switch).state;' in core_text
    assert 'on_turn_off:' in core_text and 'script.execute: suspend_display' in core_text
    assert 'on_turn_on:' in core_text and 'script.execute: resume_display' in core_text
    assert 'restore_mode: ${backlight_restore_mode}' in core_text
    assert '<esp_heap_caps.h>' in core_text
    assert 'Public ESP-IDF heap-capability API' in core_text

    camera_source_raw=(ROOT/'packages'/'camera-source.yaml').read_text(encoding='utf-8')
    assert '!id(lcd_backlight_switch).state' in camera_source_raw
    assert 'camera_detection_mask_${camera_id}' in camera_source_raw
    assert 'detection_mask: !lambda' in camera_source_raw
    assert 'do not queue a duplicate alert' in camera_source_raw

    camera_trigger_raw=(ROOT/'packages'/'camera-trigger.yaml').read_text(encoding='utf-8')
    assert 'on_press:' in camera_trigger_raw
    assert 'on_release:' in camera_trigger_raw
    assert 'camera_detection_state' in camera_trigger_raw
    assert '|=' in camera_trigger_raw and '&=' in camera_trigger_raw
    print('PASS dynamic rotation registry and empty-registry clock fallback')
    print('PASS LCD Backlight is the shared gate for rotation and camera requests')
    print('PASS camera detector press/release events maintain per-source active masks')
    print('PASS active-camera detector changes do not queue duplicate alerts')

if __name__=='__main__':
    test_configs()
    print('These are offline structural checks, not ESPHome validation or a firmware compile.')

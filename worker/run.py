"""Run: python -m worker.run --mode buggy --base-url http://localhost:8000"""
import argparse
import asyncio
import json
import platform
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
from urllib.parse import urlsplit
from .config import load_env
from .policy import OfflinePolicy, OpenAIPolicy, validate_decision
from .core import DEFAULT_ACTIONS, check_contract, observation, validate_actions, validate_target, verdict


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2) + '\n')


async def capture(page):
    return observation((await page.get_by_test_id('quantity').inner_text()).strip(),
                       (await page.get_by_test_id('total').inner_text()).strip())


async def phase(browser, url, actions, directory, name, timeout, fixture_directory=None, policy=None, max_steps=8):
    folder = directory / name
    folder.mkdir()
    result = {'status': 'running', 'context_id': str(uuid.uuid4()), 'actions': [],
              'console': [], 'page_errors': [], 'screenshots': [], 'decisions': []}
    context = None
    tracing = False
    start = time.monotonic()
    try:
        context = await browser.new_context(viewport={'width': 1280, 'height': 900},
                                            service_workers='block', accept_downloads=False)
        async def route(request):
            parts = urlsplit(request.request.url)
            if parts.netloc != urlsplit(url).netloc:
                await request.abort()
            elif fixture_directory is not None:
                files = {'/': 'index.html', '/app.js': 'app.js', '/cart.js': 'cart.js'}
                filename = files.get(parts.path)
                if filename:
                    await request.fulfill(path=str(fixture_directory / filename))
                else:
                    await request.fulfill(status=404, body='Not found')
            else:
                await request.continue_()
        await context.route('**/*', route)
        await context.tracing.start(screenshots=True, snapshots=True, sources=True)
        tracing = True
        page = await context.new_page()
        page.set_default_timeout(5000)
        page.on('console', lambda msg: result['console'].append({'type': msg.type, 'text': msg.text}))
        page.on('pageerror', lambda err: result['page_errors'].append(str(err)))

        async def execute():
            await page.goto(url, wait_until='networkidle', timeout=10000)
            result['initial'] = await capture(page)
            if result['initial'] != {'quantity': 1, 'total_cents': 2400, 'displayed_total': '$24.00'}:
                raise ValueError('Fixture did not start in its expected clean state')
            async def screenshot(index):
                path = f'{name}/{index:02d}.png'
                await page.screenshot(path=str(directory / path), full_page=True)
                result['screenshots'].append(path)
            await screenshot(0)
            executed = []
            for index in range(1, (max_steps if policy else len(actions)) + 1):
                before = await capture(page)
                if policy:
                    enabled = []
                    for button in ['Add item', 'Remove item', 'Reset cart']:
                        if await page.get_by_role('button', name=button, exact=True).is_enabled():
                            enabled.append(button)
                    state = {**before, 'enabled_buttons': enabled}
                    item = {'step': index, 'observation': state, 'status': 'requested'}
                    result['decisions'].append(item)
                    decision = validate_decision(await policy.choose(state, executed), state)
                    item.update(status='validated', decision=decision)
                    if decision['type'] == 'stop':
                        result['stop_reason'] = 'policy_stop'
                        break
                    action = {'type': 'click', 'name': decision['name']}
                else:
                    action = actions[index - 1]
                entry = {'index': index, 'action': action, 'before': before, 'status': 'started'}
                result['actions'].append(entry)
                await page.get_by_role('button', name=action['name'], exact=True).click()
                after = await capture(page)
                entry.update(status='completed', after=after)
                executed.append({'action': action, 'observation': after})
                await screenshot(index)
                if policy and check_contract(after)['status'] == 'fail':
                    result['stop_reason'] = 'contract_candidate'
                    break
            else:
                result['stop_reason'] = 'step_limit' if policy else 'sequence_complete'
            result['final'] = await capture(page)
            result['contract'] = check_contract(result['final'])
            result['status'] = 'completed'
        await asyncio.wait_for(execute(), timeout=timeout)
    except Exception as exc:
        result.update(status='error', error={'type': type(exc).__name__, 'message': str(exc) or 'Phase timed out'})
    finally:
        if context is not None:
            try:
                if tracing:
                    await context.tracing.stop(path=str(folder / 'trace.zip'))
                    result['trace'] = f'{name}/trace.zip'
            except Exception as exc:
                result['artifact_error'] = str(exc)
                result['status'] = 'error'
            finally:
                await context.close()
        result['duration_ms'] = round((time.monotonic() - start) * 1000)
        write_json(folder / 'events.json', result)
    return result


def regression_source(url, actions, fixture_directory=None):
    # JSON string literals are valid Python literals for these string-only arguments.
    lines = ['from playwright.sync_api import sync_playwright, expect', '',
             'with sync_playwright() as p:', '    browser = p.chromium.launch()',
             '    page = browser.new_page()', '']
    if fixture_directory:
        lines += ['    from pathlib import Path',
                  '    import os',
                  '    from urllib.parse import urlsplit',
                  '    root = Path(os.environ.get("BREAKPOINT_FIXTURE_DIR", "dist")).resolve()',
                  '    files = {"/": "index.html", "/app.js": "app.js", "/cart.js": "cart.js"}',
                  '    def serve(route):',
                  '        name = files.get(urlsplit(route.request.url).path)',
                  '        route.fulfill(path=str(root / name)) if name else route.fulfill(status=404, body="Not found")',
                  '    page.route("**/*", serve)']
    lines.append(f'    page.goto({json.dumps(url)})')
    for action in actions:
        lines.append(f'    page.get_by_role("button", name={json.dumps(action["name"])}, exact=True).click()')
    lines += ['    expect(page.get_by_test_id("quantity")).to_have_text("0")',
              '    expect(page.get_by_test_id("total")).to_have_text("$0.00")',
              '    browser.close()', '']
    return '\n'.join(lines)


async def run(args):
    base = validate_target(args.base_url)
    policy_name = args.provider
    if args.actions and policy_name != 'scripted':
        raise ValueError('--actions is only supported with --provider scripted')
    policy = OfflinePolicy() if policy_name == 'offline' else OpenAIPolicy(args.model) if policy_name == 'openai' else None
    actions = validate_actions(json.loads(Path(args.actions).read_text()) if args.actions else DEFAULT_ACTIONS)
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ-') + uuid.uuid4().hex[:8]
    directory = Path(args.output).resolve() / run_id
    directory.mkdir(parents=True)
    url = f'{base}/?mode={args.mode}'
    fixture_directory = Path(args.fixture_directory).resolve() if args.fixture_directory else None
    if fixture_directory:
        for filename in ['index.html', 'app.js', 'cart.js']:
            if not (fixture_directory / filename).is_file():
                raise ValueError(f'Missing fixture file: {filename}')
    report = {'schema_version': 1, 'run_id': run_id, 'created_at': datetime.now(timezone.utc).isoformat(),
              'source': policy.name if policy else 'scripted-python-playwright',
              'model_driven': policy_name == 'openai',
              'autonomous_discovery': False,
              'fixture': args.mode, 'target': url,
              'transport': 'local-file-route' if fixture_directory else 'http', 'actions': actions,
              'timeout_seconds_per_phase': args.timeout, 'max_steps': args.max_steps, 'phases': {},
              'environment': {'python': platform.python_version()}}
    write_json(directory / 'actions.json', actions)
    try:
        from playwright.async_api import async_playwright
        report['environment']['playwright'] = version('playwright')
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            try:
                report['environment']['chromium'] = browser.version
                report['phases']['exploration'] = await phase(browser, url, actions, directory, 'exploration', args.timeout, fixture_directory, policy, args.max_steps)
                if policy:
                    actions = [entry['action'] for entry in report['phases']['exploration']['actions'] if entry['status'] == 'completed']
                    report['actions'] = actions
                    write_json(directory / 'actions.json', actions)
                report['phases']['replay'] = await phase(browser, url, actions, directory, 'replay', args.timeout, fixture_directory)
                report['verdict'] = verdict(report['phases']['exploration'], report['phases']['replay'])
            finally:
                await browser.close()
    except Exception as exc:
        report.update(verdict='runner_error', error={'type': type(exc).__name__, 'message': str(exc)})
    if policy:
        report['policy'] = {'name': policy.name, 'model': policy.model, 'decision_calls': policy.calls,
                            'api_requests': policy.requests, 'usage': policy.usage,
                            'usage_complete': getattr(policy, 'usage_complete', True)}
    report['autonomous_discovery'] = policy_name == 'openai' and report['verdict'] == 'confirmed'
    if report['verdict'] in {'confirmed', 'passed'}:
        (directory / 'regression.py').write_text(regression_source(url, actions, fixture_directory))
        report['regression'] = 'regression.py'
    write_json(directory / 'report.json', report)
    print(json.dumps({'verdict': report['verdict'], 'report': str(directory / 'report.json')}))
    return 2 if report['verdict'] == 'runner_error' else 0


def main():
    try:
        load_env()
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', default='http://localhost:8000')
    parser.add_argument('--mode', choices=['buggy', 'fixed'], default='buggy')
    parser.add_argument('--fixture-directory', help='Serve the three controlled fixture files through browser routing, without a web server')
    parser.add_argument('--provider', choices=['scripted','offline','openai'], default='scripted')
    parser.add_argument('--model', default=os.environ.get('OPENAI_MODEL'))
    parser.add_argument('--max-steps', type=int, choices=range(1,13), default=8, metavar='1..12')
    parser.add_argument('--actions', help='Path to a validated actions.json to replay')
    parser.add_argument('--output', default='artifacts')
    parser.add_argument('--timeout', type=int, choices=range(1, 61), default=30, metavar='1..60')
    args = parser.parse_args()
    try:
        return asyncio.run(run(args))
    except (ValueError, OSError) as exc:
        print(f'Invalid request: {exc}', file=sys.stderr)
        return 2

if __name__ == '__main__':
    sys.exit(main())

"""Pure validation and verdict logic, separate from browser execution."""
import re
from urllib.parse import urlsplit

MAX_ACTIONS = 12
ALLOWED_BUTTONS = {'Remove item', 'Add item', 'Reset cart'}
DEFAULT_ACTIONS = [{'type': 'click', 'name': 'Remove item'}]


def validate_actions(actions):
    if not isinstance(actions, list) or not 1 <= len(actions) <= MAX_ACTIONS:
        raise ValueError('Provide between 1 and 12 actions')
    for action in actions:
        if not isinstance(action, dict) or set(action) != {'type', 'name'}:
            raise ValueError('Each action requires exactly type and name')
        if action['type'] != 'click' or not isinstance(action['name'],str) or action['name'] not in ALLOWED_BUTTONS:
            raise ValueError('Unsupported action')
    return actions


def validate_target(url):
    p = urlsplit(url)
    if p.scheme != 'http' or p.hostname not in {'localhost', '127.0.0.1', 'terminal.local'}:
        raise ValueError('Milestone 2 only supports the local controlled fixture')
    if p.username or p.password or p.query or p.fragment or p.path not in {'', '/'}:
        raise ValueError('Use a plain local origin without path, credentials or query')
    _ = p.port  # Validate port syntax.
    return url.rstrip('/')


def observation(quantity, total):
    if not re.fullmatch(r'\d+', quantity):
        raise ValueError('Quantity is not a nonnegative integer')
    if not re.fullmatch(r'\$\d+(?:,\d{3})*\.\d{2}', total):
        raise ValueError('Total is not a supported USD amount')
    cents = int(total.replace('$', '').replace(',', '').replace('.', ''))
    return {'quantity': int(quantity), 'total_cents': cents, 'displayed_total': total}


def check_contract(obs):
    """Independent business rule; never import storefront implementation."""
    if obs['quantity'] != 0:
        return {'status': 'not_applicable', 'contract': 'empty-cart-zero-total'}
    return {'status': 'fail' if obs['total_cents'] != 0 else 'pass',
            'contract': 'empty-cart-zero-total', 'expected_cents': 0,
            'actual_cents': obs['total_cents']}


def verdict(first, replay):
    if any(p.get('status') != 'completed' for p in (first, replay)):
        return 'runner_error'
    a, b = first['contract'], replay['contract']
    if a['status'] == b['status'] == 'fail' and a == b:
        return 'confirmed'
    if a['status'] == b['status'] == 'pass':
        return 'passed'
    if a['status'] == b['status'] == 'not_applicable':
        return 'inconclusive'
    return 'not_reproduced'

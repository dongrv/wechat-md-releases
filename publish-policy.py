#!/usr/bin/env python3
"""Create the signed desktop update policy after its release assets are present."""
import argparse
import base64
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time

REPOSITORY = 'dongrv/wechat-md-releases'
PLATFORMS = {
    'windows-x86_64': '_x64-setup.exe',
    'macos-aarch64': '_aarch64.dmg',
    'macos-x86_64': '_x64.dmg',
}


def version(value):
    if not re.fullmatch(r'(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)', value):
        raise ValueError('版本必须为 major.minor.patch')
    return tuple(map(int, value.split('.')))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--latest', required=True)
    parser.add_argument('--minimum', required=True)
    parser.add_argument('--notes', default='')
    parser.add_argument('--key', required=True)
    parser.add_argument('--output', default='desktop-policy.json')
    args = parser.parse_args()
    if version(args.minimum) > version(args.latest):
        raise ValueError('最低版本不能高于最新版本')
    if len(args.notes.encode('utf-8')) > 8000:
        raise ValueError('更新说明超过 8000 字节')
    release = json.loads(subprocess.check_output([
        'gh', 'release', 'view', 'desktop-v' + args.latest, '--repo', REPOSITORY,
        '--json', 'isDraft,assets',
    ]))
    if release['isDraft']:
        raise ValueError('发行版仍为草稿')
    names = [asset['name'] for asset in release['assets']]
    missing = [platform for platform, suffix in PLATFORMS.items() if not any(name.endswith(suffix) for name in names)]
    if missing:
        raise ValueError('发行版缺少安装包：' + ', '.join(missing))
    now = int(time.time())
    payload = json.dumps({
        'product': 'io.github.dongrv.wechat-md', 'channel': 'preview',
        'latest': args.latest, 'minimum': args.minimum,
        'release_url': 'https://github.com/' + REPOSITORY + '/releases/tag/desktop-v' + args.latest,
        'notes': args.notes, 'issued_at': now, 'expires_at': now + 365 * 24 * 60 * 60,
        'platforms': list(PLATFORMS),
    }, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    with tempfile.TemporaryDirectory() as directory:
        message = Path(directory) / 'payload'
        signature_file = Path(directory) / 'signature'
        message.write_bytes(payload)
        subprocess.run(['openssl', 'pkeyutl', '-sign', '-rawin', '-inkey', args.key,
                        '-in', str(message), '-out', str(signature_file)], check=True)
        signature = signature_file.read_bytes()
    if len(signature) != 64:
        raise ValueError('签名长度无效')
    envelope = {'payload': base64.b64encode(payload).decode('ascii'),
                'signature': base64.b64encode(signature).decode('ascii')}
    Path(args.output).write_text(json.dumps(envelope, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()

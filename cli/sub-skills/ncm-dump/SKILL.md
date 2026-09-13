---
name: ncm-dump
description: 解密网易云 .ncm 加密音乐为通用 mp3/flac（AES-128 + 自定义 RC4 变体）。当拿到 .ncm 文件无法播放/处理、或需要批量转换时使用。
---

# ncm 解密（网易云加密音乐还原）

## 何时用
用户提供 `.ncm` 文件（网易云客户端 VIP 下载的加密格式，只能网易云播），需要转成通用 mp3/flac 才能用任意播放器播放或处理。

## 环境依赖
- Python 3 + `pycryptodome`：`py -3 -m pip install pycryptodome`
- 验证可选：`ffprobe` / `ffplay`

## 文件格式与算法速记（网易云公开标准）
| 段 | 说明 |
|----|------|
| 文件头 | `CTENFDAM`(8B) → 跳过 2B → 4B key长度(LE) → key数据(**每字节 ^0x64**) |
| RC4 密钥 | key数据 **AES-128-ECB** 解密（密钥 `hzHRAmso5kInbaxW`）→ 去 17 字节前缀 `neteasecloudmusic` → 去 **PKCS#7 填充** → 剩余即 RC4 密钥 |
| 元数据(可选) | 4B meta长度 → meta(每字节 ^0x64) → AES-128-ECB（密钥 `#14ljk_!\]&0U<'(`）→ 去前缀 `163 key(Don't modify):` → base64 → JSON |
| 音频起点 | meta 结束后 + CRC32(4B) + gap(5B) + cover_len(4B) + 封面图片字节 |
| 音频流 | **自定义无状态 RC4**（非标准 RC4） |

音频流变体 RC4 的 PRGA（密钥流只依赖绝对偏移 off，无演进状态）：
```
j  = (off + 1) % 256
a  = S[j]
b  = S[(a + j) % 256]
明文 = 密文 ^ S[(a + b) % 256]
```
其中 S 由标准 RC4 KSA 用 RC4 密钥生成。

## 关键坑（最容易踩）
1. **`neteasecloudmusic` 不是 AES 密钥**——它是 AES 解密后 RC4 密钥的前缀（17 字节）；真正的 AES 密钥是 `hzHRAmso5kInbaxW`(16B)。直接用前者当 AES 密钥会报 "Incorrect AES key length"。
2. key 解密后要 **PKCS#7 去填充**（末尾字节即填充值，通常是 `\r`=13 或 `\x08` 等）。
3. meta 长度可能**不是 16 的倍数**，AES 前先补零到块边界。
4. 音频流用**变体 RC4**，别用 `Crypto.Cipher.ARC4`（标准 RC4 解不出正确数据）。
5. 别漏封面：音频起点必须跳过 CRC32(4) + gap(5) + cover_len(4) + cover 本体，不然开头全是噪音。
6. 扩展名按解密后魔数判断：`ID3`→`.mp3`，`fLaC`→`.flac`，`OggS`→`.ogg`。

## 步骤
1. 确认 pycryptodome 已装（缺则 `py -3 -m pip install pycryptodome`）。
2. 将下方**完整脚本**写入临时文件 `ncmdump.py`（或直接执行下方命令）。
3. 运行解密，例如：`py -3 ncmdump.py 歌曲.ncm 输出目录/` 或 `py -3 ncmdump.py 某目录/ 输出目录/`。
4. 用 `ffprobe` 验证时长/编码器，`ffplay` 试播确认出声。

## 完整脚本
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ncm 解密：网易云 .ncm → 通用 mp3/flac/ogg。依赖 pycryptodome。
用法: py -3 ncmdump.py <ncm文件或目录> [输出目录]"""
import sys, os, glob, struct, json, base64
from Crypto.Cipher import AES

CORE_KEY = bytes.fromhex('687A4852416D736F356B496E62617857')   # hzHRAmso5kInbaxW
META_KEY = bytes.fromhex('2331346C6A6B5F215C5D2630553C2728')   # #14ljk_!\]&0U<'('

def _unpad(b):
    if not b:
        return b
    p = b[-1]
    return b[:-p] if 1 <= p <= 16 and b[-p:] == bytes([p]) * p else b

def ncm_rc4(buf, key):
    """网易云自定义变体 RC4：标准 KSA，无状态 PRGA（密钥流只依赖偏移）。"""
    S = list(range(256)); j = 0
    for i in range(256):
        j = (j + S[i] + key[i % len(key)]) % 256
        S[i], S[j] = S[j], S[i]
    out = bytearray(len(buf))
    for o, c in enumerate(buf):
        j = (o + 1) % 256
        a = S[j]; b = S[(a + j) % 256]
        out[o] = c ^ S[(a + b) % 256]
    return bytes(out)

def parse(data):
    if data[:8] != b'CTENFDAM':
        raise ValueError('不是 ncm 文件')
    off = 10
    klen = struct.unpack_from('<I', data, off)[0]; off += 4
    kd = bytes(b ^ 0x64 for b in data[off:off + klen]); off += klen
    pad = (16 - len(kd) % 16) % 16
    k = AES.new(CORE_KEY, AES.MODE_ECB).decrypt(kd + b'\x00' * pad)
    rk = _unpad(k[17:])                      # RC4 密钥（去前缀+去填充）
    info = None
    if off + 4 <= len(data):
        mlen = struct.unpack_from('<I', data, off)[0]; off += 4
        md = bytes(b ^ 0x64 for b in data[off:off + mlen]); off += mlen
        try:
            mp = (16 - len(md) % 16) % 16
            m = AES.new(META_KEY, AES.MODE_ECB).decrypt(md + b'\x00' * mp)
            m = _unpad(m)
            if m.startswith(b"163 key(Don't modify):"):
                m = m[len(b"163 key(Don't modify):"):]
            info = json.loads(base64.b64decode(m).decode('utf-8'))
        except Exception:
            info = None
    p = off + 4 + 5                        # CRC32 + gap
    cl = struct.unpack_from('<I', data, p)[0] if p + 4 <= len(data) else 0
    p += 4 + cl                            # cover_len + 封面
    return p, rk, info

def decode(data):
    start, rk, info = parse(data)
    if not rk:
        raise ValueError('RC4 密钥为空')
    audio = ncm_rc4(data[start:], rk)
    head = audio[:8]
    ext = '.flac' if head[:4] == b'fLaC' else ('.ogg' if head[:4] == b'OggS' else '.mp3')
    return audio, ext, info

def main():
    args = sys.argv[1:]
    if not args:
        print('用法: py -3 ncmdump.py <ncm文件或目录> [输出目录]'); return
    src = args[0]
    outdir = args[1] if len(args) > 1 else (src if os.path.isdir(src) else '.')
    files = sorted(glob.glob(os.path.join(src, '*.ncm'))) if os.path.isdir(src) else [src]
    os.makedirs(outdir, exist_ok=True)
    ok = 0
    for fp in files:
        name = os.path.basename(fp)
        try:
            with open(fp, 'rb') as f:
                data = f.read()
            audio, ext, info = decode(data)
            base = os.path.splitext(name)[0]
            with open(os.path.join(outdir, base + ext), 'wb') as f:
                f.write(audio)
            print(f'OK: {base}{ext} ({(info or {}).get("songName") or ""})')
            ok += 1
        except Exception as e:
            print(f'FAIL: {name} → {e}')
    print(f'完成：{ok}/{len(files)}')

if __name__ == '__main__':
    main()
```

## 验证命令
```bash
ffprobe -v error -show_entries format=duration -of csv=p=0 输出.mp3   # 看时长是否正常
ffplay -nodisp -autoexit -t 3 输出.mp3                               # 试播 3 秒
```

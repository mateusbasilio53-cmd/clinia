"""Analisa o computador e recomenda o modelo de IA local que ele aguenta.

Uso:
    python -m ia.verificar_pc

Regra prática: o modelo precisa caber na memória da placa de vídeo (VRAM) para ficar rápido.
    qwen2.5:3b  ~1,9 GB  · qwen2.5:7b  ~4,7 GB  · llama3.1:8b ~4,9 GB  · qwen2.5:14b ~9 GB
"""

from __future__ import annotations

import ctypes
import json
import shutil
import subprocess
import sys
import urllib.request

# (VRAM mínima em GB, modelo recomendado, comentário)
RECOMENDACOES = [
    (12, "qwen2.5:14b", "modelo grande: deve errar bem menos; teste também o qwen2.5:7b para comparar"),
    (8, "qwen2.5:7b", "cabe inteiro na placa: bem melhor que o 3b e ainda rápido"),
    (6, "qwen2.5:7b", "cabe quase inteiro: melhor que o 3b, um pouco mais lento"),
    (3.5, "qwen2.5:3b", "o mesmo do PC do Paulo"),
    (0, "qwen2.5:3b", "sem placa de vídeo compatível: vai rodar no processador, mais devagar"),
]


def ram_gb() -> float | None:
    if sys.platform != "win32":
        return None

    class Memoria(ctypes.Structure):
        _fields_ = [
            ("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
            ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
            ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]

    m = Memoria()
    m.dwLength = ctypes.sizeof(Memoria)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    return m.ullTotalPhys / 1024**3


def placas_nvidia() -> list[tuple[str, float]]:
    """Nome e VRAM (GB) de cada placa NVIDIA, via nvidia-smi (vem com o driver)."""
    if not shutil.which("nvidia-smi"):
        return []
    saida = subprocess.run(
        ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
        capture_output=True, text=True, timeout=15,
    ).stdout
    placas = []
    for linha in saida.strip().splitlines():
        nome, mb = (p.strip() for p in linha.rsplit(",", 1))
        placas.append((nome, float(mb) / 1024))
    return placas


def ollama_modelos(url: str = "http://localhost:11434") -> list[str] | None:
    try:
        with urllib.request.urlopen(f"{url}/api/tags", timeout=3) as r:
            return [m["name"] for m in json.loads(r.read())["models"]]
    except Exception:
        return None


def main() -> int:
    print("CLINIA · análise do computador\n")
    ram = ram_gb()
    print(f"  RAM:            {ram:.1f} GB" if ram else "  RAM:            (não consegui medir)")

    placas = placas_nvidia()
    if placas:
        for nome, vram in placas:
            print(f"  Placa NVIDIA:   {nome} · {vram:.1f} GB de VRAM")
    else:
        print("  Placa NVIDIA:   nenhuma encontrada (ou driver sem nvidia-smi)")
    vram = max((v for _, v in placas), default=0)

    modelos = ollama_modelos()
    print(f"  Ollama:         {'aberto · modelos: ' + (', '.join(modelos) or 'nenhum') if modelos is not None else 'não está aberto (ou não instalado)'}")

    minimo, modelo, comentario = next(r for r in RECOMENDACOES if vram >= r[0])
    if ram and ram < 12 and modelo != "qwen2.5:3b":
        modelo, comentario = "qwen2.5:3b", "pouca RAM para um modelo maior"

    print(f"\n  Recomendação:   {modelo}  ({comentario})")
    print("\n  Próximos passos:")
    print(f"    ollama pull {modelo}")
    if modelo != "qwen2.5:3b":
        print("    ollama pull qwen2.5:3b        # para comparar com o resultado do Paulo")
        print(f"    python -m ia.extracao.experimento --modelos qwen2.5:3b,{modelo} --conjunto prova")
    else:
        print("    python -m ia.extracao.experimento --modelos qwen2.5:3b --conjunto prova")
    return 0


if __name__ == "__main__":
    sys.exit(main())

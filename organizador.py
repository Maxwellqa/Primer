#!/usr/bin/env python3
"""
organizador.py - Organiza archivos de una carpeta por tipo/extension.

Uso:
    python organizador.py "C:/ruta/a/mi/carpeta"
    python organizador.py "C:/ruta/a/mi/carpeta" --simular
    python organizador.py "C:/ruta/a/mi/carpeta" --recursivo
    python organizador.py                          # te pregunta la ruta por consola
"""

import argparse
import shutil
from pathlib import Path
from collections import defaultdict

# --- Categorias y sus extensiones ---
CATEGORIAS = {
    "Imagenes": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp",
                 ".tiff", ".tif", ".ico", ".heic", ".raw", ".psd"},
    "Documentos": {".pdf", ".doc", ".docx", ".odt", ".txt", ".rtf", ".tex", ".md"},
    "Hojas_de_calculo": {".xls", ".xlsx", ".csv", ".ods", ".tsv"},
    "Presentaciones": {".ppt", ".pptx", ".odp", ".key"},
    "Audio": {".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma"},
    "Video": {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v"},
    "Comprimidos": {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"},
    "Codigo": {".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".c", ".cpp", ".cs",
               ".html", ".css", ".php", ".rb", ".go", ".rs", ".sh", ".json",
               ".xml", ".yaml", ".yml", ".sql"},
    "Ejecutables_instaladores": {".exe", ".msi", ".dmg", ".deb", ".rpm", ".apk", ".appimage"},
    "Fuentes": {".ttf", ".otf", ".woff", ".woff2"},
    "Ebooks": {".epub", ".mobi", ".azw3"},
}

# Mapa inverso extension -> categoria, para busqueda rapida
EXT_A_CATEGORIA = {
    ext: cat for cat, exts in CATEGORIAS.items() for ext in exts
}

NOMBRES_CATEGORIAS_VALIDAS = set(CATEGORIAS.keys()) | {"Otros", "Sin_extension"}


def categoria_de(archivo: Path) -> str:
    ext = archivo.suffix.lower()
    if not ext:
        return "Sin_extension"
    return EXT_A_CATEGORIA.get(ext, "Otros")


def resolver_conflicto(destino: Path) -> Path:
    """Si ya existe un archivo con ese nombre en destino, le agrega un sufijo numerico."""
    if not destino.exists():
        return destino
    base, ext = destino.stem, destino.suffix
    contador = 1
    while True:
        nuevo = destino.with_name(f"{base}_{contador}{ext}")
        if not nuevo.exists():
            return nuevo
        contador += 1


def organizar_carpeta(carpeta: Path, recursivo: bool, simular: bool,
                       reporte: dict, es_raiz: bool = True):
    for item in list(carpeta.iterdir()):
        if item.is_dir():
            # No tocar carpetas creadas por el propio script en corridas anteriores
            if item.name in NOMBRES_CATEGORIAS_VALIDAS and es_raiz:
                continue
            if recursivo:
                organizar_carpeta(item, recursivo, simular, reporte, es_raiz=False)
            else:
                reporte["subcarpetas_no_tocadas"].append(str(item))
            continue

        if item.is_file():
            # Evitar mover el propio script si esta dentro de la carpeta
            if item.resolve() == Path(__file__).resolve():
                continue

            cat = categoria_de(item)
            carpeta_destino = carpeta / cat
            destino_final = resolver_conflicto(carpeta_destino / item.name)

            reporte["por_categoria"][cat] += 1
            reporte["total_archivos"] += 1
            reporte["espacio_bytes"] += item.stat().st_size

            if not simular:
                carpeta_destino.mkdir(exist_ok=True)
                shutil.move(str(item), str(destino_final))

            reporte["detalle"].append((item.name, cat, str(destino_final)))


def formatear_bytes(b: int) -> str:
    for unidad in ["B", "KB", "MB", "GB"]:
        if b < 1024:
            return f"{b:.1f} {unidad}"
        b /= 1024
    return f"{b:.1f} TB"


def imprimir_reporte(carpeta: Path, reporte: dict, simular: bool):
    print("\n" + "=" * 55)
    print(f"  REPORTE DE ORGANIZACION{'  (SIMULACION)' if simular else ''}")
    print("=" * 55)
    print(f"Carpeta procesada: {carpeta}")
    print(f"Total de archivos procesados: {reporte['total_archivos']}")
    print(f"Espacio total movido: {formatear_bytes(reporte['espacio_bytes'])}")

    print("\nArchivos por categoria:")
    if reporte["por_categoria"]:
        for cat, cantidad in sorted(reporte["por_categoria"].items(),
                                     key=lambda x: -x[1]):
            print(f"  - {cat:<25} {cantidad}")
    else:
        print("  (no se encontraron archivos para organizar)")

    if reporte["subcarpetas_no_tocadas"]:
        print(f"\nSubcarpetas encontradas y NO modificadas "
              f"({len(reporte['subcarpetas_no_tocadas'])}):")
        for sub in reporte["subcarpetas_no_tocadas"]:
            print(f"  - {sub}")

    print("=" * 55 + "\n")


def pedir_ruta_interactiva() -> Path:
    """Pregunta la ruta por consola hasta que sea una carpeta valida."""
    while True:
        entrada = input("Ingresa la ruta de la carpeta a organizar (o 'salir' para cancelar): ").strip()

        if entrada.lower() in ("salir", "exit", "q"):
            print("Operacion cancelada.")
            raise SystemExit(0)

        # Permite pegar rutas entre comillas sin que rompan
        entrada = entrada.strip('"').strip("'")

        carpeta = Path(entrada).expanduser().resolve()

        if carpeta.exists() and carpeta.is_dir():
            return carpeta

        print(f"  -> '{carpeta}' no existe o no es una carpeta. Intenta de nuevo.\n")


def main():
    parser = argparse.ArgumentParser(
        description="Organiza los archivos de una carpeta por tipo/extension.")
    parser.add_argument("carpeta", nargs="?", default=None,
                         help="Ruta de la carpeta a organizar (si no se indica, se pregunta por consola)")
    parser.add_argument("--recursivo", action="store_true",
                         help="Tambien organiza el contenido de las subcarpetas existentes")
    parser.add_argument("--simular", action="store_true",
                         help="Muestra que haria, sin mover ningun archivo")
    args = parser.parse_args()

    if args.carpeta:
        carpeta = Path(args.carpeta).expanduser().resolve()
        if not carpeta.exists() or not carpeta.is_dir():
            print(f"Error: '{carpeta}' no es una carpeta valida.")
            return
    else:
        carpeta = pedir_ruta_interactiva()

    reporte = {
        "por_categoria": defaultdict(int),
        "subcarpetas_no_tocadas": [],
        "total_archivos": 0,
        "espacio_bytes": 0,
        "detalle": [],
    }

    organizar_carpeta(carpeta, args.recursivo, args.simular, reporte)
    imprimir_reporte(carpeta, reporte, args.simular)


if __name__ == "__main__":
    main()

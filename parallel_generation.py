from concurrent.futures import ProcessPoolExecutor, InterpreterPoolExecutor
from noise import snoise2

# =================== ГЛОБАЛЬНЫЕ ВОРКЕРЫ ===================

def _noise_worker(i_start, i_end, height, scale, octaves, persistence, lacunarity, seed):
    result = []
    for i in range(i_start, i_end):
        row = [
            snoise2(i / scale, j / scale,
                    octaves=octaves,
                    persistence=persistence,
                    lacunarity=lacunarity,
                    repeatx=1024,
                    repeaty=1024,
                    base=seed)
            for j in range(height)
        ]
        result.append(row)
    return result


def _color_worker(i_start, i_end, height, scale, intensity, seed):
    result = []
    for i in range(i_start, i_end):
        row = [
            snoise2(i / scale, j / scale,
                    octaves=1,
                    persistence=0.5,
                    lacunarity=2.0,
                    repeatx=1024,
                    repeaty=1024,
                    base=seed + 1) * intensity
            for j in range(height)
        ]
        result.append(row)
    return result

# =================== ОСНОВНЫЕ ФУНКЦИИ ===================

def vectorized_noise(width, height, scale, octaves, persistence, lacunarity, seed, pool: ProcessPoolExecutor | InterpreterPoolExecutor):
    """ПОКА НЕ РАБОТАЕТ С СУБИНТЕРПРЕТАТОРАМИ"""
    workers = 8
    chunk_size = width // workers

    futures = []
    for i in range(workers):
        i_start = i * chunk_size
        i_end = (i + 1) * chunk_size if i < workers - 1 else width
        f = pool.submit(
            _noise_worker,
            i_start, i_end, height, scale,
            octaves, persistence, lacunarity, seed
        )
        futures.append(f)

    print('waiting for workers (noise)...')
    results = [f.result() for f in futures]
    return [row for chunk in results for row in chunk]


def vectorized_color(width, height, scale, intensity, seed, pool: ProcessPoolExecutor | InterpreterPoolExecutor):
    """ПОКА НЕ РАБОТАЕТ С СУБИНТЕРПРЕТАТОРАМИ"""
    workers = 8
    chunk_size = width // workers

    futures = []
    for i in range(workers):
        i_start = i * chunk_size
        i_end = (i + 1) * chunk_size if i < workers - 1 else width
        f = pool.submit(
            _color_worker,
            i_start, i_end, height, scale, intensity, seed
        )
        futures.append(f)

    print('waiting for workers (color)...')
    results = [f.result() for f in futures]
    return [row for chunk in results for row in chunk]
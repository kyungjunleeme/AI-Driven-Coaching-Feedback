from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Callable


def parallel_map(items: List, fn: Callable, max_workers: int = 8):
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = [ex.submit(fn, it) for it in items]
        for f in as_completed(futs):
            results.append(f.result())
    return results


def parallel_scores_per_step(
    step_ids: List[int], scorer: Callable[[int], float], max_workers: int = 12
) -> Dict[int, float]:
    def task(sid: int):
        return sid, scorer(sid)

    out: Dict[int, float] = {}
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = [ex.submit(task, sid) for sid in step_ids]
        for f in as_completed(futs):
            sid, sc = f.result()
            out[sid] = sc
    return out

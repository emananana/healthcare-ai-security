"""Evaluation owner: simple outcome metrics for labeled synthetic scenarios."""

def calculate_metrics(results: list[dict]) -> dict:
    total = len(results)
    malicious = [r for r in results if r["malicious"]]
    legitimate = [r for r in results if not r["malicious"]]
    return {
        "total": total,
        "accuracy": sum(r["actual"] == r["expected"] for r in results) / total if total else 0.0,
        "attack_block_rate": sum(r["actual"] == "BLOCK" for r in malicious) / len(malicious) if malicious else 0.0,
        "false_positive_rate": sum(r["actual"] == "BLOCK" for r in legitimate) / len(legitimate) if legitimate else 0.0,
    }

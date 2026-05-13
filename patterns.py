"""MEV pattern detection algorithms."""
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

class PatternType(Enum):
    SANDWICH = "sandwich"
    JIT = "jit_liquidity"
    BACKRUN = "backrun"
    ARBITRAGE = "arbitrage"
    FRONT_RUNNING = "front_running"

@dataclass
class DetectedPattern:
    pattern_type: PatternType
    confidence: float
    tx_hashes: List[str]
    attacker: str
    profit_eth: float

def detect_jit_liquidity(txs: List[dict]) -> List[DetectedPattern]:
    """Detect JIT (Just-In-Time) liquidity provision."""
    results = []
    for tx in txs:
        if is_liquidity_add(tx) and has_immediate_removal(tx, txs):
            results.append(DetectedPattern(
                pattern_type=PatternType.JIT,
                confidence=0.8,
                tx_hashes=[tx['hash']],
                attacker=tx['from'],
                profit_eth=0.0
            ))
    return results

def is_liquidity_add(tx: dict) -> bool:
    sig = tx.get('input', '')[:10]
    return sig in ['0xe8e33700', '0xf305d719', '0x219f5d17']

def has_immediate_removal(tx: dict, all_txs: List[dict]) -> bool:
    return False

"""Shared on-chain utilities for blockchain explorer connectors.

Provides token contract addresses, CEX address classification helpers,
and USD value estimation.
"""

from __future__ import annotations

# Ethereum mainnet ERC-20 token contracts
TOKEN_CONTRACTS: dict[str, str] = {
    "WBTC": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
    "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
}

# Token decimal places for amount conversion
TOKEN_DECIMALS: dict[str, int] = {
    "WBTC": 8,
    "WETH": 18,
    "USDC": 6,
    "USDT": 6,
}

# Well-known CEX hot wallet addresses (Ethereum mainnet, partial list)
# Source: publicly labeled addresses from Etherscan
KNOWN_CEX_ADDRESSES: dict[str, str] = {
    "0x28c6c06298d514db089934071355e5743bf21d60": "Binance",
    "0x21a31ee1afc51d94c2efccaa2092ad1028285549": "Binance",
    "0xdfd5293d8e347dfe59e90efd55b2956a1343963d": "Binance",
    "0x56eddb7aa87536c09ccc2793473599fd21a8b17f": "Binance",
    "0x3f5ce5fbfe3e9af3971dd833d26ba9b5c936f0be": "Binance (old)",
    "0x71660c4005ba85c37ccec55d0c4493e66fe775d3": "Coinbase",
    "0x503828976d22510aad0201ac7ec88293211d23da": "Coinbase",
    "0xa090e606e30bd747d4e6245a1517ebe430f0057e": "Coinbase",
    "0xfbb1b73c4f0bda4f67dca266ce6ef42f520fbb98": "Bitfinex",
    "0x742d35cc6634c0532925a3b844bc9e7595f2bd1e": "Bitfinex (old)",
    "0x1151314c646ce4e0efd76d1af4760ae66a9fe30f": "Bitfinex",
    "0x2910543af39aba0cd09dbb2d50200b3e800a63d2": "Kraken",
    "0x267be1c1d684f78cb4f6a176c4911b741e4ffdc0": "Kraken",
    "0x53d284357ec70ce289d6d64134dfac8e511c8a3d": "Kraken (cold)",
    "0x6cc5f688a315f3dc28a7781717a9a798a59fda7b": "OKX",
    "0x98ec059dc3adfbdd63429227d09cb8a3e17d6309": "OKX",
}


def classify_address(address: str) -> str | None:
    """Classify an Ethereum address as a known CEX or None if unknown."""
    return KNOWN_CEX_ADDRESSES.get(address.lower())


def is_cex_address(address: str) -> bool:
    """Return True if the address belongs to a known CEX."""
    return address.lower() in KNOWN_CEX_ADDRESSES


def raw_to_token_amount(raw_value: str, decimals: int) -> float:
    """Convert a raw token amount string to a human-readable float."""
    try:
        return int(raw_value) / (10**decimals)
    except (ValueError, OverflowError):
        return 0.0


def estimate_usd_value(
    token_symbol: str,
    token_amount: float,
    prices: dict[str, float] | None = None,
) -> float:
    """Estimate USD value of a token amount.

    Uses provided prices dict or falls back to stablecoin 1:1 assumption.
    Prices dict maps token symbols to USD prices.
    """
    if prices and token_symbol in prices:
        return token_amount * prices[token_symbol]

    # Stablecoin fallback
    if token_symbol in ("USDC", "USDT"):
        return token_amount

    # No price available
    return 0.0

"""Tests for Etherscan on-chain connector."""

from __future__ import annotations

import json
import os
from unittest.mock import MagicMock, patch

from sources.etherscan import EtherscanConnector
from sources.onchain_base import (
    classify_address,
    estimate_usd_value,
    is_cex_address,
    raw_to_token_amount,
)


# Sample Etherscan API response
SAMPLE_ETHERSCAN_RESPONSE = {
    "status": "1",
    "message": "OK",
    "result": [
        {
            "hash": "0xabc123def456",
            "from": "0x28c6c06298d514db089934071355e5743bf21d60",  # Binance
            "to": "0x1111111111111111111111111111111111111111",  # Private
            "value": "100000000000",  # 1000 WBTC (8 decimals)
            "timeStamp": "1738000000",
            "tokenSymbol": "WBTC",
            "tokenDecimal": "8",
        },
        {
            "hash": "0xdef789abc012",
            "from": "0x2222222222222222222222222222222222222222",  # Private
            "to": "0x71660c4005ba85c37ccec55d0c4493e66fe775d3",  # Coinbase
            "value": "5000000000",  # 5000 USDC (6 decimals)
            "timeStamp": "1738001000",
            "tokenSymbol": "USDC",
            "tokenDecimal": "6",
        },
    ],
}


class TestOnchainBase:
    def test_classify_known_cex(self) -> None:
        addr = "0x28c6c06298d514db089934071355e5743bf21d60"
        assert classify_address(addr) == "Binance"

    def test_classify_unknown_address(self) -> None:
        assert classify_address("0x0000000000000000000000000000000000000000") is None

    def test_is_cex_address(self) -> None:
        assert is_cex_address("0x28c6c06298d514db089934071355e5743bf21d60")
        assert not is_cex_address("0x0000000000000000000000000000000000000000")

    def test_raw_to_token_amount_wbtc(self) -> None:
        # 100,000,000,000 raw = 1000 WBTC (8 decimals)
        amount = raw_to_token_amount("100000000000", 8)
        assert amount == 1000.0

    def test_raw_to_token_amount_usdc(self) -> None:
        # 5,000,000,000 raw = 5000 USDC (6 decimals)
        amount = raw_to_token_amount("5000000000", 6)
        assert amount == 5000.0

    def test_raw_to_token_amount_invalid(self) -> None:
        amount = raw_to_token_amount("not_a_number", 6)
        assert amount == 0.0

    def test_estimate_usd_stablecoin(self) -> None:
        usd = estimate_usd_value("USDC", 5000.0)
        assert usd == 5000.0

    def test_estimate_usd_with_prices(self) -> None:
        prices = {"WBTC": 100_000.0}
        usd = estimate_usd_value("WBTC", 10.0, prices)
        assert usd == 1_000_000.0

    def test_estimate_usd_no_price(self) -> None:
        usd = estimate_usd_value("UNKNOWN_TOKEN", 100.0)
        assert usd == 0.0


class TestEtherscanConnector:
    def test_fetch_no_api_key(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            # Ensure ETHERSCAN_API_KEY is not set
            os.environ.pop("ETHERSCAN_API_KEY", None)
            connector = EtherscanConnector()
            result = connector.fetch()

        assert not result.ok
        assert result.error_type == "config_error"
        assert "ETHERSCAN_API_KEY" in (result.error_message or "")

    def test_fetch_success(self) -> None:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(
            SAMPLE_ETHERSCAN_RESPONSE
        ).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with (
            patch.dict(os.environ, {"ETHERSCAN_API_KEY": "test_key"}),
            patch(
                "sources.etherscan.urllib.request.urlopen",
                return_value=mock_response,
            ),
            patch("sources.etherscan._rate_limit"),
        ):
            connector = EtherscanConnector(
                tokens={"WBTC": "0xcontract"},
                prices={"WBTC": 100_000.0},
            )
            result = connector.fetch()

        assert result.ok
        # Check that at least one transfer was found
        assert len(result.evidence) >= 1
        # First transfer should be accumulation (from Binance to private)
        ev = result.evidence[0]
        assert ev.normalized["direction"] == "accumulation"
        assert ev.normalized["from_cex"] == "Binance"

    def test_fetch_api_error(self) -> None:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(
            {"status": "0", "message": "NOTOK", "result": "Max rate limit reached"}
        ).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with (
            patch.dict(os.environ, {"ETHERSCAN_API_KEY": "test_key"}),
            patch(
                "sources.etherscan.urllib.request.urlopen",
                return_value=mock_response,
            ),
            patch("sources.etherscan._rate_limit"),
        ):
            connector = EtherscanConnector(tokens={"WBTC": "0xcontract"})
            result = connector.fetch()

        # API returned error status for all tokens
        assert not result.ok

    def test_format_for_prompt_no_key(self) -> None:
        from evidence.schema import SourceFetchResult

        result = SourceFetchResult.failure(
            source_name="etherscan",
            error_type="config_error",
            error_message="ETHERSCAN_API_KEY not configured",
        )
        connector = EtherscanConnector()
        text = connector.format_for_prompt(result)
        assert "FAILED" in text

    def test_format_for_prompt_with_data(self) -> None:
        from evidence.schema import SourceEvidence, SourceFetchResult

        ev = SourceEvidence(
            source_type="etherscan",
            source_name="Etherscan: WBTC",
            source_url="https://etherscan.io/tx/0xabc",
            retrieved_at="2026-01-01T00:00:00Z",
            canonical_id="0xabc",
            normalized={
                "token_symbol": "WBTC",
                "amount": 100.0,
                "usd_estimate": 10_000_000.0,
                "direction": "accumulation",
                "from_cex": "Binance",
                "to_cex": None,
                "transaction_hash": "0xabc",
                "timestamp": "2026-01-01T00:00:00Z",
            },
        )
        result = SourceFetchResult(
            ok=True, source_name="etherscan", evidence=[ev]
        )
        connector = EtherscanConnector()
        text = connector.format_for_prompt(result)
        assert "WBTC" in text
        assert "ACCUMULATION" in text
        assert "Binance" in text

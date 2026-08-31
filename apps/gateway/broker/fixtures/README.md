# Broker fixtures

Drop a real dump from the IC Markets cTrader **demo** account here and the fixture-backed tests in
`../test_ctrader.py` start running instead of skipping.

`symbols-icmarkets-demo.json`:

```json
{
  "assets":  [{"assetId": 1, "name": "USD"}],
  "symbols": [
    {"symbolId": 41, "name": "XAUUSD", "digits": 2, "pipPosition": 1, "lotSize": 10000,
     "minVolume": 100, "stepVolume": 100, "maxVolume": 1000000,
     "baseAssetId": 4, "quoteAssetId": 1}
  ]
}
```

Capture it from a live `SymbolsListReq` + `SymbolByIdReq` + `AssetListReq` round trip — never by
hand. A guessed `lotSize` is the bug that sends a huge ounce count on a 0.01 lot gold order.

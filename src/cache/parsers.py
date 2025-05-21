

def parse_historical(data: dict) -> list[dict]:
    if not data or 'prices' not in data:
        return []
    else:
        return [{'timestamp': ts, 'price': pr, 'market_cap': mc, 'total_volume': tv}
                for (ts, pr), (_, mc), (_, tv) in zip(data['prices'],
                                                      data['market_caps'],
                                                      data['total_volumes'])]


def parse_ohlc(data: list) -> list[dict]:
    if not data:
        return []
    else:
        return [{'timestamp': ts, 'open': op, 'high': hi, 'low': lo, 'close': cl}
                for ts, op, hi, lo, cl in data]
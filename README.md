# RIPCORD MVP

RIPCORD, Pacifica benzeri perpetual trading ortamları için liquidation öncesi otomatik kurtarma planı üreten bir MVP risk execution firewall prototipidir.

## Özellikler

- Account Risk Twin: liquidation proximity, cross contagion, funding drag, symbol risk contribution
- Policy Firewall: `no_liquidation`, `max_daily_drawdown_pct`, `funding_negative_max_hours`, `never_open_new_risk`
- Rescue Engine: cancel non-reduce orders, reduce-only batch exits, TP/SL attach, optional hedge
- Counterfactual Replay: `with` vs `without RIPCORD` karşılaştırması

## Hızlı Başlangıç

```bash
python3 -m pip install .
PYTHONPATH=src python3 -m ripcord.cli
PYTHONPATH=src python3 -m ripcord.pacifica_cli
PYTHONPATH=src python3 -m ripcord.web_server
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

`ripcord.web_server` komutundan sonra dashboard için `http://127.0.0.1:8787` adresini aç.

## Pacifica Adapter (RIP-01 başlangıcı)

`ripcord.pacifica_cli`, snapshot'ı adapter katmanından alıp aynı risk/rescue döngüsünü çalıştırır.

1. `.env.example` dosyasını baz alarak ortam değişkenlerini ayarla.
2. `RIPCORD_DATA_SOURCE=mock` ile mock payload veya `RIPCORD_DATA_SOURCE=http` ile HTTP endpoint kullan.
3. Komutu çalıştır:

```bash
set -a
source .env.example
set +a
PYTHONPATH=src python3 -m ripcord.pacifica_cli
```

Mock payload'ı özelleştirmek için `RIPCORD_MOCK_FILE` değerine kendi JSON dosyanı verebilirsin.

## Frontend Dashboard

`web/` altındaki frontend, local API endpoint'lerinden veri çekerek risk/policy/plan/replay bloklarını canlı gösterir.

- `GET /api/health`
- `GET /api/run-cycle?mode=mock|adapter`
- `POST /api/run-cycle` (`mode`, `shock_pct`, opsiyonel `snapshot`)

## CLI Çıktısı

CLI, örnek bir hesap snapshot'ı üretir ve şu adımları çalıştırır:

1. Risk hesapla
2. Policy ihlallerini çıkar
3. Rescue plan üret
4. Firewall ile uygula
5. Replay ile `with/without` farkını göster

## Not

Bu adımda Pacifica adapter katmanı eklendi. `mock` kaynak tamamen yerel çalışır; `http` kaynak ise verdiğin endpoint'ten account state çekerek aynı engine üzerinde risk/rescue/replay üretir.
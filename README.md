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

- Bilgi mimarisi: `Overview`, `Risk Breakdown`, `Rescue`, `Replay`, `Policies`
- Canlı veri akışı: auto-refresh, loading/error/empty, retry, stale göstergesi

- `GET /api/health`
- `POST /api/auth/session` (`account_id`) → session token üretir
- `GET /api/auth/me` (header: `Authorization: Bearer <token>` veya `X-RIPCORD-Session`) → aktif account
- `GET /api/run-cycle?mode=mock|adapter&shock_pct=0.07`
- `POST /api/run-cycle` (`mode`, `shock_pct`, opsiyonel `snapshot`, opsiyonel `policy`, opsiyonel `execution`)

## Production kullanıcı akışı

Kısa cevap: **Evet**, kullanıcı bizim panele girip Pacifica'da kullandığı account/wallet kimliğiyle kendi verisini görür.

Bu MVP backend'de akış şöyle işler:

1. Frontend, kullanıcıdan Pacifica account kimliğini alır.
2. `POST /api/auth/session` ile session token oluşturulur.
3. `adapter` modunda `run-cycle`, session’daki `account_id` ile Pacifica endpointlerine gider.
4. Böylece kullanıcı panelde kendi account risk/rescue/replay verisini görür.

Not: Bu sürümde wallet signature challenge (SIWE benzeri) yok; production-hardening için bir sonraki adım doğrudan wallet imza doğrulamasıdır.

## `/api/run-cycle` Sözleşmesi (stabil)

`contract_version: 2026-04-16`

Yanıt gövdesi (özet):

- `ok`: boolean
- `contract_version`: string
- `generated_at`: ISO datetime
- `mode`: `mock|adapter`
- `source`: `mock|adapter|custom`
- `shock_pct`: float
- `policy`: efektif policy konfigürasyonu
- `data`: `risk`, `policy`, `plan`, `execution`, `replay`
- `execution`: signed execution request hazırlık bilgisi (`enabled`, `ready`, `missing`, `signed_request`)

Not: Geriye dönük uyumluluk için `result` alanı `data` ile aynı içeriği taşır.

## Execution entegrasyon hazırlığı

Feature-flag ve imzalı istek hazırlığı `.env` üstünden yönetilir:

- `RIPCORD_EXECUTION_ENABLED=true|false`
- `PACIFICA_EXECUTION_ENDPOINT=https://...`
- `PACIFICA_AGENT_KEY=...`
- `RIPCORD_SIGNING_SECRET=...`
- `PACIFICA_OPEN_ORDERS_PATH=/api/v1/open-orders`
- `RIPCORD_REQUIRE_SESSION=true|false`
- `RIPCORD_SESSION_SECRET=...`
- `RIPCORD_SESSION_TTL_SECONDS=43200`
- `RIPCORD_STATE_DIR=.ripcord_state`

`POST /api/run-cycle` içinde execution kontrolü:

```json
{
	"mode": "adapter",
	"execution": {
		"arm": true,
		"dry_run": true
	}
}
```

- `arm=false` ise live execution tetiklenmez.
- `dry_run=true` ile imzalı istek yalnızca simüle edilir.

## CLI Çıktısı

CLI, örnek bir hesap snapshot'ı üretir ve şu adımları çalıştırır:

1. Risk hesapla
2. Policy ihlallerini çıkar
3. Rescue plan üret
4. Firewall ile uygula
5. Replay ile `with/without` farkını göster

## Not

Bu adımda Pacifica adapter katmanı eklendi. `mock` kaynak tamamen yerel çalışır; `http` kaynak ise verdiğin endpoint'ten account state çekerek aynı engine üzerinde risk/rescue/replay üretir.
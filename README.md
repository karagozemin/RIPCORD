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
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

## CLI Çıktısı

CLI, örnek bir hesap snapshot'ı üretir ve şu adımları çalıştırır:

1. Risk hesapla
2. Policy ihlallerini çıkar
3. Rescue plan üret
4. Firewall ile uygula
5. Replay ile `with/without` farkını göster

## Not

Bu repo Pacifica'ya gerçek network çağrısı yapmaz; hackathon implementasyonu için domain mantığını çalışan bir çekirdek olarak sunar. Bir sonraki adımda adapter katmanına gerçek REST/WS entegrasyonu eklenebilir.
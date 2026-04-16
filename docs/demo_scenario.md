# RIPCORD Demo Senaryosu (MVP)

## Hikaye Akışı

1. **Riskli hesap kur**
   - Testnet/mock hesapta 2-3 yüksek kaldıraç pozisyon aç.
   - En az bir pozisyon cross-margin bulaşma etkisi yaratacak şekilde olsun.
   - En az bir pozisyonda negatif funding drag göster.

2. **Risk yükselişini göster**
   - Dashboard `Overview` ve `Risk Breakdown` ekranında:
     - Risk level (`HIGH/CRITICAL`)
     - Liquidation proximity
     - Symbol risk contribution
     - Funding drag

3. **Arm + Rescue çalıştır**
   - `Rescue` sekmesinde öneri ve timeline göster:
     - non-reduce-only order iptali
     - reduce-only batch exit
     - TP/SL attach
     - policy uygunsa hedge

4. **Firewall etkisini göster**
   - `Policies` sekmesinde policy ihlalleri ve bloklanan aksiyonları göster.
   - `execution.ready` durumunu göster (env eksikse `missing` listesi görünür).

5. **Replay finali**
   - `Replay` sekmesinde with/without kıyasını aç:
     - liquidated true/false
     - equity before/after
     - `saved_loss`

## Fallback Planı

- Adapter endpoint erişilemezse `mode=mock` ile devam et.
- Execution endpoint hazır değilse sadece `execution prep` göster, emir gönderme.
- Demo sırasında API hata verirse `Retry` butonu ile akışı tekrar başlat.

# RIPCORD Demo Scenario (MVP)

## Narrative Flow

1. **Prepare a risky account**
   - Open 2-3 high-leverage positions on testnet/mock.
   - Include at least one position that increases cross-margin contagion.
   - Include at least one position with negative funding drag.

2. **Show risk escalation**
   - In `Overview` and `Risk Breakdown`, show:
     - Risk level (`HIGH/CRITICAL`)
     - Liquidation proximity
     - Symbol risk contribution
     - Funding drag

3. **Run Arm + Rescue**
   - In `Rescue`, show recommendation and timeline:
     - non-reduce-only order cancellation
     - reduce-only batch exit
     - TP/SL attach
     - hedge when policy allows

4. **Show firewall impact**
   - In `Policies`, display policy violations and blocked actions.
   - Display `execution.ready` (if env is missing, `missing` list is visible).

5. **Replay finale**
   - In `Replay`, open with/without comparison:
     - liquidated true/false
     - equity before/after
     - `saved_loss`

## Fallback Plan

- If adapter endpoint is unreachable, continue with `mode=mock`.
- If execution endpoint is not ready, show only `execution prep` and do not submit orders.
- If API fails during demo, restart flow using the `Retry` button.

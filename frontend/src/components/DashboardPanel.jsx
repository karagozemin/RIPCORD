export function DashboardPanel({ data, onRunCycle, loading, error, status, sessionReady, mode }) {
  const risk = data?.data?.risk;
  const replay = data?.data?.replay;

  return (
    <section className="card">
      <h2>Read-only Risk Dashboard</h2>
      <p className="status">Status: {status}</p>
      <p className="status">Mode: {mode} {mode === "adapter" ? "(live account)" : "(mock fallback)"}</p>
      {!sessionReady && <p className="hint">Tip: create a session to enable adapter mode.</p>}
      <button onClick={onRunCycle} disabled={loading}>{loading ? "Running..." : "Run Cycle"}</button>
      {error && <p className="error">{error}</p>}
      {risk && (
        <div className="grid">
          <div className="mini-card">
            <h3>Risk</h3>
            <p>Level: {risk.level}</p>
            <p>Score: {risk.score}</p>
            <p>Liquidation Proximity: {risk.liquidation_proximity}</p>
          </div>
          <div className="mini-card">
            <h3>Replay</h3>
            <p>Saved Loss: {replay.saved_loss}</p>
            <p>Without Liq: {String(replay.without_ripcord.liquidated)}</p>
            <p>With Liq: {String(replay.with_ripcord.liquidated)}</p>
          </div>
        </div>
      )}
      <pre>{data ? JSON.stringify(data, null, 2) : "No data yet"}</pre>
    </section>
  );
}

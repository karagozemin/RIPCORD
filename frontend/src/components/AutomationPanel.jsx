export function AutomationPanel({ policyLevel, setPolicyLevel, arm, setArm, dryRun, setDryRun, disabled }) {
  return (
    <section className="card">
      <h2>Enable Auto-Rescue</h2>
      <div className="row">
        <label>Policy</label>
        <select value={policyLevel} onChange={(event) => setPolicyLevel(event.target.value)} disabled={disabled}>
          <option value="alert_only">alert only</option>
          <option value="suggest_actions">suggest actions</option>
          <option value="auto_rescue">auto-rescue</option>
        </select>
      </div>
      <div className="row">
        <label>
          <input type="checkbox" checked={arm} onChange={(event) => setArm(event.target.checked)} disabled={disabled} /> Arm execution
        </label>
        <label>
          <input type="checkbox" checked={dryRun} onChange={(event) => setDryRun(event.target.checked)} disabled={disabled} /> Dry run
        </label>
      </div>
    </section>
  );
}

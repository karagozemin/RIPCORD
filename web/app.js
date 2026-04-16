const runBtn = document.getElementById("runBtn");
const modeInput = document.getElementById("mode");
const shockInput = document.getElementById("shock");

const riskNode = document.getElementById("risk");
const policyNode = document.getElementById("policy");
const planNode = document.getElementById("plan");
const replayNode = document.getElementById("replay");
const rawNode = document.getElementById("raw");

function riskBadge(level) {
  const cls = level === "CRITICAL"
    ? "badge-critical"
    : level === "HIGH"
      ? "badge-high"
      : level === "MEDIUM"
        ? "badge-medium"
        : "badge-low";
  return `<span class="badge ${cls}">${level}</span>`;
}

function metric(label, value) {
  return `<div class="metric"><span>${label}</span><strong>${value}</strong></div>`;
}

function render(payload) {
  const data = payload.result;
  const risk = data.risk;
  const policy = data.policy;
  const plan = data.plan;
  const replay = data.replay;

  riskNode.innerHTML = [
    metric("Level", riskBadge(risk.level)),
    metric("Score", risk.score),
    metric("Liquidation Proximity", risk.liquidation_proximity),
    metric("Cross Contagion", risk.cross_contagion),
    metric("Funding Drag/H", risk.funding_drag_hourly),
    metric("Top Symbol", Object.keys(risk.symbol_contributions)[0] || "-"),
  ].join("");

  policyNode.innerHTML = [
    metric("Violations", policy.violations.length),
    metric("Blocked", policy.blocked_actions.join(", ") || "none"),
    `<p>${policy.violations.join(", ") || "No violation"}</p>`,
  ].join("");

  planNode.innerHTML = [
    metric("Action Count", plan.actions.length),
    metric("Estimated Reduction", `${plan.estimated_risk_reduction_pct}%`),
    `<p>${plan.rationale.join("<br />")}</p>`,
  ].join("");

  replayNode.innerHTML = [
    metric("Without RIPCORD", replay.without_ripcord.equity_after.toFixed(2)),
    metric("With RIPCORD", replay.with_ripcord.equity_after.toFixed(2)),
    metric("Saved Loss", replay.saved_loss.toFixed(2)),
    metric("Liquidated (Without)", replay.without_ripcord.liquidated),
    metric("Liquidated (With)", replay.with_ripcord.liquidated),
  ].join("");

  rawNode.textContent = JSON.stringify(payload, null, 2);
}

async function runCycle() {
  runBtn.disabled = true;
  runBtn.textContent = "Running...";

  try {
    const response = await fetch("/api/run-cycle", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        mode: modeInput.value,
        shock_pct: Number(shockInput.value),
      }),
    });

    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || "Unknown error");
    }

    render(payload);
  } catch (error) {
    rawNode.textContent = `Error: ${error.message}`;
  } finally {
    runBtn.disabled = false;
    runBtn.textContent = "Run Cycle";
  }
}

runBtn.addEventListener("click", runCycle);
runCycle();

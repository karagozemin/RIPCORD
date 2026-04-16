const runBtn = document.getElementById("runBtn");
const retryBtn = document.getElementById("retryBtn");
const modeInput = document.getElementById("mode");
const shockInput = document.getElementById("shock");
const autoRefreshInput = document.getElementById("autoRefresh");
const intervalInput = document.getElementById("interval");
const statusBadge = document.getElementById("statusBadge");
const staleBadge = document.getElementById("staleBadge");
const lastUpdatedNode = document.getElementById("lastUpdated");
const errorsNode = document.getElementById("errors");

const overviewNode = document.getElementById("view-overview");
const riskNode = document.getElementById("view-risk");
const rescueNode = document.getElementById("view-rescue");
const replayNode = document.getElementById("view-replay");
const policyNode = document.getElementById("view-policies");
const rawNode = document.getElementById("raw");

let refreshTimer = null;
let staleTimer = null;

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

function boolBadge(value) {
  return value ? '<span class="badge badge-high">yes</span>' : '<span class="badge badge-low">no</span>';
}

function setStatus(text, tone = "low") {
  statusBadge.textContent = text;
  statusBadge.className = `badge badge-${tone}`;
}

function markStale(isStale) {
  staleBadge.classList.toggle("hidden", !isStale);
}

function scheduleStaleMarker() {
  if (staleTimer) {
    clearTimeout(staleTimer);
  }
  staleTimer = setTimeout(() => markStale(true), Number(intervalInput.value) * 2000);
}

function renderOverview(data, payload) {
  const risk = data.risk;
  const replay = data.replay;
  const execution = payload.execution || {};

  overviewNode.innerHTML = `
    <article class="card">
      <h2>Risk Summary</h2>
      ${metric("Level", riskBadge(risk.level))}
      ${metric("Score", risk.score)}
      ${metric("Liquidation Proximity", risk.liquidation_proximity)}
      ${metric("Cross Contagion", risk.cross_contagion)}
    </article>
    <article class="card">
      <h2>Rescue Outcome</h2>
      ${metric("Saved Loss", replay.saved_loss.toFixed(2))}
      ${metric("Without Liquidated", boolBadge(replay.without_ripcord.liquidated))}
      ${metric("With Liquidated", boolBadge(replay.with_ripcord.liquidated))}
      ${metric("Execution Ready", boolBadge(Boolean(execution.ready)))}
    </article>
  `;
}

function renderRisk(data) {
  const risk = data.risk;
  const contributionRows = Object.entries(risk.symbol_contributions)
    .sort((a, b) => b[1] - a[1])
    .map(([symbol, contribution]) => metric(`${symbol} Contribution`, `${contribution}%`))
    .join("");

  riskNode.innerHTML = `
    <article class="card">
      <h2>Account Risk Twin</h2>
      ${metric("Risk Level", riskBadge(risk.level))}
      ${metric("Funding Drag / Hour", risk.funding_drag_hourly)}
      ${metric("Reason Count", risk.reasons.length)}
      <p>${risk.reasons.join("<br />")}</p>
    </article>
    <article class="card">
      <h2>Symbol Risk Contribution</h2>
      ${contributionRows || "<p>No positions</p>"}
    </article>
  `;
}

function renderRescue(data) {
  const plan = data.plan;
  const execution = data.execution;
  const timelineRows = [
    ...execution.applied_actions.map((item) => `<li class="ok">Applied: ${item}</li>`),
    ...execution.blocked_actions.map((item) => `<li class="warn">Blocked: ${item}</li>`),
    ...plan.actions
      .filter((action) => !execution.applied_actions.some((item) => item.startsWith(action.action_type)))
      .map((action) => `<li>Suggested: ${action.action_type}</li>`),
  ].join("");

  rescueNode.innerHTML = `
    <article class="card">
      <h2>Rescue Engine</h2>
      ${metric("Recommended Actions", plan.actions.length)}
      ${metric("Estimated Risk Reduction", `${plan.estimated_risk_reduction_pct}%`)}
      <p>${plan.rationale.join("<br />") || "No rationale"}</p>
    </article>
    <article class="card">
      <h2>Action Timeline</h2>
      <ul class="timeline">${timelineRows || "<li>No actions</li>"}</ul>
    </article>
  `;
}

function renderReplay(data) {
  const replay = data.replay;
  replayNode.innerHTML = `
    <article class="card">
      <h2>Without RIPCORD</h2>
      ${metric("Equity Before", replay.without_ripcord.equity_before.toFixed(2))}
      ${metric("Equity After", replay.without_ripcord.equity_after.toFixed(2))}
      ${metric("Liquidated", boolBadge(replay.without_ripcord.liquidated))}
    </article>
    <article class="card">
      <h2>With RIPCORD</h2>
      ${metric("Equity Before", replay.with_ripcord.equity_before.toFixed(2))}
      ${metric("Equity After", replay.with_ripcord.equity_after.toFixed(2))}
      ${metric("Liquidated", boolBadge(replay.with_ripcord.liquidated))}
      ${metric("Saved Loss", replay.saved_loss.toFixed(2))}
    </article>
  `;
}

function renderPolicies(payload) {
  const data = payload.data;
  const policy = payload.policy;
  const evalResult = data.policy;
  const execution = payload.execution || {};

  policyNode.innerHTML = `
    <article class="card">
      <h2>Automation Firewall</h2>
      ${metric("No Liquidation", boolBadge(policy.no_liquidation))}
      ${metric("Max Drawdown %", policy.max_daily_drawdown_pct)}
      ${metric("Funding Negative Max Hours", policy.funding_negative_max_hours)}
      ${metric("Max Effective Leverage", policy.max_effective_leverage)}
      ${metric("Never Open New Risk", boolBadge(policy.never_open_new_risk))}
      ${metric("Hedge Enabled", boolBadge(policy.hedge_enabled))}
    </article>
    <article class="card">
      <h2>Policy Result / Execution Prep</h2>
      ${metric("Violations", evalResult.violations.join(", ") || "none")}
      ${metric("Blocked Actions", evalResult.blocked_actions.join(", ") || "none")}
      ${metric("Execution Enabled", boolBadge(Boolean(execution.enabled)))}
      ${metric("Execution Ready", boolBadge(Boolean(execution.ready)))}
      ${metric("Missing Config", (execution.missing || []).join(", ") || "none")}
    </article>
  `;
}

function render(payload) {
  const data = payload.data || payload.result;
  if (!data) {
    throw new Error("Boş payload alındı");
  }

  renderOverview(data, payload);
  renderRisk(data);
  renderRescue(data);
  renderReplay(data);
  renderPolicies(payload);

  rawNode.textContent = JSON.stringify(payload, null, 2);
}

async function runCycle() {
  runBtn.disabled = true;
  retryBtn.disabled = true;
  runBtn.textContent = "Running...";
  setStatus("loading", "medium");
  errorsNode.textContent = "Loading...";
  markStale(false);

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
      throw new Error(payload.error?.message || payload.error || "Unknown error");
    }

    render(payload);
    const now = new Date();
    lastUpdatedNode.textContent = `Last updated: ${now.toLocaleTimeString()}`;
    errorsNode.textContent = "No errors";
    setStatus("live", "low");
    scheduleStaleMarker();
  } catch (error) {
    rawNode.textContent = `Error: ${error.message}`;
    errorsNode.textContent = error.message;
    setStatus("error", "critical");
    retryBtn.disabled = false;
  } finally {
    runBtn.disabled = false;
    runBtn.textContent = "Run Cycle";
  }
}

function applyAutoRefresh() {
  if (refreshTimer) {
    clearInterval(refreshTimer);
    refreshTimer = null;
  }
  if (!autoRefreshInput.checked) {
    return;
  }
  const intervalMs = Math.max(Number(intervalInput.value), 2) * 1000;
  refreshTimer = setInterval(() => {
    runCycle();
  }, intervalMs);
}

function bindTabs() {
  const tabs = Array.from(document.querySelectorAll(".tab"));
  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((item) => item.classList.remove("active"));
      tab.classList.add("active");
      const viewName = tab.dataset.view;
      ["overview", "risk", "rescue", "replay", "policies"].forEach((name) => {
        const node = document.getElementById(`view-${name}`);
        node.classList.toggle("hidden", name !== viewName);
      });
    });
  });
}

runBtn.addEventListener("click", runCycle);
retryBtn.addEventListener("click", runCycle);
autoRefreshInput.addEventListener("change", applyAutoRefresh);
intervalInput.addEventListener("change", applyAutoRefresh);
bindTabs();
runCycle();

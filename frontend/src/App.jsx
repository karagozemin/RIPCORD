import { useMemo, useState } from "react";
import { ConnectPanel } from "./components/ConnectPanel";
import { AutomationPanel } from "./components/AutomationPanel";
import { DashboardPanel } from "./components/DashboardPanel";

function buildPolicy(policyLevel) {
  if (policyLevel === "alert_only") {
    return {
      never_open_new_risk: true,
      hedge_enabled: false,
    };
  }
  if (policyLevel === "suggest_actions") {
    return {
      never_open_new_risk: true,
      hedge_enabled: true,
    };
  }
  return {
    never_open_new_risk: false,
    hedge_enabled: true,
  };
}

export default function App() {
  const [accountId, setAccountId] = useState("");
  const [sessionToken, setSessionToken] = useState("");
  const [policyLevel, setPolicyLevel] = useState("suggest_actions");
  const [arm, setArm] = useState(false);
  const [dryRun, setDryRun] = useState(true);
  const [payload, setPayload] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const sessionReady = useMemo(() => Boolean(sessionToken), [sessionToken]);

  async function createSession() {
    setError("");
    try {
      const response = await fetch("/api/auth/session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ account_id: accountId }),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error?.message || "Failed to create session");
      }
      setSessionToken(data.token);
    } catch (sessionError) {
      setError(sessionError.message);
    }
  }

  async function runCycle() {
    setLoading(true);
    setError("");
    try {
      const response = await fetch("/api/run-cycle", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(sessionToken ? { Authorization: `Bearer ${sessionToken}` } : {}),
        },
        body: JSON.stringify({
          mode: accountId ? "adapter" : "mock",
          shock_pct: 0.07,
          policy: buildPolicy(policyLevel),
          execution: {
            arm,
            dry_run: dryRun,
          },
        }),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error?.message || "run-cycle failed");
      }
      setPayload(data);
    } catch (runError) {
      setError(runError.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="container">
      <header>
        <h1>RIPCORD Frontend</h1>
        <p>Connect → Read-only Dashboard → Enable Automation</p>
      </header>
      <ConnectPanel
        accountId={accountId}
        setAccountId={setAccountId}
        onCreateSession={createSession}
        sessionReady={sessionReady}
      />
      <AutomationPanel
        policyLevel={policyLevel}
        setPolicyLevel={setPolicyLevel}
        arm={arm}
        setArm={setArm}
        dryRun={dryRun}
        setDryRun={setDryRun}
      />
      <DashboardPanel data={payload} onRunCycle={runCycle} loading={loading} error={error} />
    </main>
  );
}

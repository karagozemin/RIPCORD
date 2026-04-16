import { useMemo, useState } from "react";
import { ConnectPanel } from "./components/ConnectPanel";
import { AutomationPanel } from "./components/AutomationPanel";
import { DashboardPanel } from "./components/DashboardPanel";
import FloatingLines from "./components/FloatingLines";

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
  const [creatingSession, setCreatingSession] = useState(false);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("Idle");

  const normalizedAccountId = accountId.trim();
  const sessionReady = useMemo(() => Boolean(sessionToken), [sessionToken]);
  const canCreateSession = normalizedAccountId.length > 0 && !creatingSession;
  const canUseAdapter = normalizedAccountId.length > 0 && sessionReady;
  const runMode = canUseAdapter ? "adapter" : "mock";

  async function parseApiResponse(response) {
    const raw = await response.text();
    if (!raw || !raw.trim()) {
      return {};
    }
    try {
      return JSON.parse(raw);
    } catch {
      throw new Error(`API returned non-JSON response (status ${response.status})`);
    }
  }

  async function createSession() {
    if (!normalizedAccountId) {
      setError("Enter a Pacifica account ID first.");
      return;
    }

    setError("");
    setStatus("Creating session...");
    setCreatingSession(true);
    try {
      const response = await fetch("/api/auth/session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ account_id: normalizedAccountId }),
      });
      const data = await parseApiResponse(response);
      if (!response.ok) {
        throw new Error(data.error?.message || "Failed to create session");
      }
      if (!data.token) {
        throw new Error("Session response is missing token");
      }
      setSessionToken(data.token);
      setStatus("Session created. Adapter mode is now enabled.");
    } catch (sessionError) {
      const message = String(sessionError?.message || "");
      if (message.includes("Failed to fetch") || message.includes("NetworkError")) {
        setError("Backend API is unreachable. Start `PYTHONPATH=src python3 -m ripcord.web_server` on port 8787.");
        setStatus("Session failed");
      } else {
        setError(message || "Failed to create session");
        setStatus("Session failed");
      }
    } finally {
      setCreatingSession(false);
    }
  }

  function clearSession() {
    setSessionToken("");
    setStatus("Session cleared. Running in mock mode.");
  }

  async function runCycle() {
    if (normalizedAccountId && !sessionReady) {
      setError("Create a session before running adapter mode.");
      setStatus("Waiting for session");
      return;
    }

    setLoading(true);
    setError("");
    setStatus("Running cycle...");
    try {
      const response = await fetch("/api/run-cycle", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(sessionToken ? { Authorization: `Bearer ${sessionToken}` } : {}),
        },
        body: JSON.stringify({
          mode: runMode,
          shock_pct: 0.07,
          policy: buildPolicy(policyLevel),
          execution: {
            arm,
            dry_run: dryRun,
          },
        }),
      });
      const data = await parseApiResponse(response);
      if (!response.ok) {
        throw new Error(data.error?.message || "run-cycle failed");
      }
      if (!data || (!data.data && !data.result)) {
        throw new Error("Run-cycle response is empty or invalid");
      }
      setPayload(data);
      setStatus(`Cycle completed (${runMode})`);
    } catch (runError) {
      const message = String(runError?.message || "");
      if (message.includes("Failed to fetch") || message.includes("NetworkError")) {
        setError("Backend API is unreachable. Start `PYTHONPATH=src python3 -m ripcord.web_server` on port 8787.");
        setStatus("Run failed");
      } else {
        setError(message || "Run-cycle failed");
        setStatus("Run failed");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app-shell">
      <div className="app-background" aria-hidden="true">
        <FloatingLines
          enabledWaves={["top", "middle", "bottom"]}
          lineCount={[10, 15, 20]}
          lineDistance={[8, 6, 4]}
          bendRadius={5.0}
          bendStrength={-0.5}
          interactive={false}
          parallax={false}
        />
      </div>

      <main className="container">
        <header className="app-header">
          <img className="app-logo" src="/ripcord-logo.jpeg" alt="RIPCORD logo" />
          <div>
            <h1>RIPCORD </h1>
            <p>Connect → Read-only Dashboard → Enable Automation</p>
          </div>
        </header>
        <ConnectPanel
          accountId={accountId}
          setAccountId={setAccountId}
          onCreateSession={createSession}
          onClearSession={clearSession}
          sessionReady={sessionReady}
          creatingSession={creatingSession}
          canCreateSession={canCreateSession}
        />
        <AutomationPanel
          policyLevel={policyLevel}
          setPolicyLevel={setPolicyLevel}
          arm={arm}
          setArm={setArm}
          dryRun={dryRun}
          setDryRun={setDryRun}
          disabled={loading}
        />
        <DashboardPanel
          data={payload}
          onRunCycle={runCycle}
          loading={loading}
          error={error}
          status={status}
          sessionReady={sessionReady}
          mode={runMode}
        />
      </main>
    </div>
  );
}

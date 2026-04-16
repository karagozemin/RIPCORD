import { WalletMultiButton } from "@solana/wallet-adapter-react-ui";

export function ConnectPanel({ accountId, setAccountId, onCreateSession, sessionReady }) {
  return (
    <section className="card">
      <h2>Connect your Pacifica account</h2>
      <p>Solana wallet connection is enabled via Wallet Adapter.</p>
      <div className="row">
        <WalletMultiButton />
      </div>
      <div className="row">
        <label htmlFor="accountId">Pacifica Account ID</label>
        <input
          id="accountId"
          value={accountId}
          onChange={(event) => setAccountId(event.target.value)}
          placeholder="example: 0x... or pacifica account"
        />
        <button onClick={onCreateSession}>Create Session</button>
      </div>
      <p>{sessionReady ? "Session ready ✅" : "No session"}</p>
    </section>
  );
}

import { ConnectButton } from "@rainbow-me/rainbowkit";
import { WalletMultiButton } from "@solana/wallet-adapter-react-ui";

export function ConnectPanel({ accountId, setAccountId, onCreateSession, sessionReady }) {
  return (
    <section className="card">
      <h2>Connect your Pacifica account</h2>
      <p>EVM için RainbowKit, Solana için Wallet Adapter aktif.</p>
      <div className="row">
        <ConnectButton />
        <WalletMultiButton />
      </div>
      <div className="row">
        <label htmlFor="accountId">Pacifica Account ID</label>
        <input
          id="accountId"
          value={accountId}
          onChange={(event) => setAccountId(event.target.value)}
          placeholder="ör: 0x... veya pacifica account"
        />
        <button onClick={onCreateSession}>Create Session</button>
      </div>
      <p>{sessionReady ? "Session ready ✅" : "Session yok"}</p>
    </section>
  );
}

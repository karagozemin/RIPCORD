import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import "./styles.css";
import { WalletProviders } from "./walletProviders";

class RootErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, message: "" };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, message: error?.message || "Unknown frontend error" };
  }

  render() {
    if (this.state.hasError) {
      return (
        <main className="container">
          <section className="card">
            <h2>Frontend runtime error</h2>
            <p className="error">{this.state.message}</p>
          </section>
        </main>
      );
    }
    return this.props.children;
  }
}

createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <RootErrorBoundary>
      <WalletProviders>
        <App />
      </WalletProviders>
    </RootErrorBoundary>
  </React.StrictMode>
);

import { getDefaultConfig, RainbowKitProvider, darkTheme } from "@rainbow-me/rainbowkit";
import "@rainbow-me/rainbowkit/styles.css";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { WagmiProvider } from "wagmi";
import { mainnet, arbitrum, base } from "wagmi/chains";

import { ConnectionProvider, WalletProvider } from "@solana/wallet-adapter-react";
import { WalletModalProvider } from "@solana/wallet-adapter-react-ui";
import "@solana/wallet-adapter-react-ui/styles.css";
import { PhantomWalletAdapter, SolflareWalletAdapter } from "@solana/wallet-adapter-wallets";
import { useMemo } from "react";

const projectId = "e40e7554a29d019bedaad883896164a4";

const wagmiConfig = getDefaultConfig({
  appName: "RIPCORD",
  projectId,
  chains: [mainnet, arbitrum, base],
  ssr: false,
});

const queryClient = new QueryClient();

export function WalletProviders({ children }) {
  const endpoint = "https://api.mainnet-beta.solana.com";
  const wallets = useMemo(() => {
    try {
      return [new PhantomWalletAdapter(), new SolflareWalletAdapter()];
    } catch {
      return [];
    }
  }, []);

  return (
    <WagmiProvider config={wagmiConfig}>
      <QueryClientProvider client={queryClient}>
        <RainbowKitProvider theme={darkTheme()}>
          <ConnectionProvider endpoint={endpoint}>
            <WalletProvider wallets={wallets} autoConnect>
              <WalletModalProvider>{children}</WalletModalProvider>
            </WalletProvider>
          </ConnectionProvider>
        </RainbowKitProvider>
      </QueryClientProvider>
    </WagmiProvider>
  );
}

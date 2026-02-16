import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/lib/auth/auth-context";
import { SessionProvider } from "@/lib/session/session-context";

export const metadata: Metadata = {
  title: "FLUX",
  description: "FLUX training app",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        <AuthProvider>
          <SessionProvider>{children}</SessionProvider>
        </AuthProvider>
      </body>
    </html>
  );
}

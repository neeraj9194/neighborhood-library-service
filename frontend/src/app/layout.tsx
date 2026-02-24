import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/Sidebar";
import ErrorBoundary from "@/components/ErrorBoundary";

export const metadata: Metadata = {
  title: "Neighborhood Library",
  description: "Manage your neighborhood library's books, members, and lending operations.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        <div className="app-layout">
          <Sidebar />
          <main className="main-content">
            <ErrorBoundary>{children}</ErrorBoundary>
          </main>
        </div>
      </body>
    </html>
  );
}

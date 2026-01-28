import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
    title: "Content Factory",
    description: "AI Video Generation Platform",
};

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html lang="en">
            <body className={`${inter.className} bg-black text-white antialiased`}>
                <div className="flex min-h-screen">
                    {/* Sidebar */}
                    <aside className="w-64 border-r border-white/10 p-6 flex flex-col gap-8 hidden md:flex">
                        <h1 className="text-xl font-bold bg-gradient-to-r from-blue-500 to-purple-500 bg-clip-text text-transparent">
                            Content Factory
                        </h1>
                        <nav className="flex flex-col gap-2">
                            <a href="/" className="px-4 py-2 bg-white/5 rounded-lg border border-white/10 text-sm">Dashboard</a>
                            <a href="/generate" className="px-4 py-2 hover:bg-white/5 rounded-lg text-sm transition-colors text-white/60 hover:text-white">New Video</a>
                            <a href="/library" className="px-4 py-2 hover:bg-white/5 rounded-lg text-sm transition-colors text-white/60 hover:text-white">Library</a>
                            <a href="/settings" className="px-4 py-2 hover:bg-white/5 rounded-lg text-sm transition-colors text-white/60 hover:text-white">Settings</a>
                        </nav>
                    </aside>

                    {/* Main Content */}
                    <main className="flex-1 p-8">
                        {children}
                    </main>
                </div>
            </body>
        </html>
    );
}
